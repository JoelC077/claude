#!/usr/bin/env python3
"""opencloud.py - Roblox Open Cloud client for rr-release-train: place publishing, Luau tests, server restart.

  opencloud.py probe                                   can this machine reach the API host? (no key needed)
  opencloud.py request FILE --universe U --place P [--type Saved|Published]
                                                       print the request a publish would send (key redacted)

Library (release.py): publish_place(), run_luau(), restart_servers(), describe_publish(), probe().
Key: environment variable ROBLOX_API_KEY only; never read from a file in the repo, never printed.
RR_OPENCLOUD_BASE overrides https://apis.roblox.com (selftest points it at a local mock server).
Endpoints and limits: rr-bible tech.publish.oc_* (source RBXOC). POSTs are retried only on HTTP 429, so a
publish is never sent twice after an ambiguous server error. Exit codes: 0 ok, 1 failed, 2 usage.
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_BASE = "https://apis.roblox.com"
KEY_ENV = "ROBLOX_API_KEY"
SIZE_LIMIT = 10485760  # fallback only; release.py passes rr-bible tech.publish.oc_size_limit


class OCError(Exception):
    def __init__(self, msg, status=0, body=""):
        super().__init__(msg)
        self.status, self.body = status, body


def base():
    return os.environ.get("RR_OPENCLOUD_BASE", DEFAULT_BASE).rstrip("/")


def api_key():
    return os.environ.get(KEY_ENV, "").strip()


def content_type(path):
    return "application/xml" if str(path).lower().endswith(".rbxlx") else "application/octet-stream"


def _call(method, path, key, data=None, ctype=None, timeout=180):
    url = path if path.startswith("http") else base() + path
    headers = {"x-api-key": key, "Accept": "application/json"}
    if ctype:
        headers["Content-Type"] = ctype
    for attempt in range(4):
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            retry = e.code == 429 or (method == "GET" and e.code >= 500)
            if retry and attempt < 3:
                time.sleep(min(int(e.headers.get("Retry-After") or 0) or 2 ** attempt, 30))
                continue
            raise OCError(f"{method} {url} -> HTTP {e.code}: {body[:300]}", e.code, body)
        except (urllib.error.URLError, OSError) as e:
            raise OCError(f"{method} {url} -> network: {getattr(e, 'reason', e)}")


def _json(body):
    try:
        return json.loads(body) if body.strip() else {}
    except json.JSONDecodeError:
        return {"raw": body[:500]}


def describe_publish(universe, place, file, vtype):
    f = Path(file)
    url = f"{base()}/universes/v1/{universe}/places/{place}/versions?versionType={vtype}"
    return {"method": "POST", "url": url, "headers": {"x-api-key": f"${KEY_ENV}", "Content-Type": content_type(f)},
            "body": str(f), "bytes": f.stat().st_size if f.is_file() else None,
            "curl": f"curl -sS -X POST '{url}' -H \"x-api-key: ${KEY_ENV}\" -H 'Content-Type: {content_type(f)}' "
                    f"--data-binary @'{f}'"}


def publish_place(universe, place, file, vtype, key, limit=SIZE_LIMIT):
    """POST the place file; returns the new place version number."""
    if vtype not in ("Saved", "Published"):
        raise OCError(f"versionType must be Saved or Published, not {vtype}")
    data = Path(file).read_bytes()
    if len(data) > limit:
        raise OCError(f"{file} is {len(data)} bytes, over the {limit}-byte API limit: publish from Studio")
    _, body = _call("POST", f"/universes/v1/{universe}/places/{place}/versions?versionType={vtype}", key,
                    data=data, ctype=content_type(file))
    num = _json(body).get("versionNumber")
    if not isinstance(num, int):
        raise OCError(f"unexpected publish response: {body[:200]}")
    return num


def run_luau(universe, place, version, script, key, timeout_s=300, poll_s=3.0):
    """Run a Luau script on one saved place version; waits for the task. Returns {state, results, error, logs}."""
    path = f"/cloud/v2/universes/{universe}/places/{place}/versions/{version}/luau-execution-session-tasks"
    _, body = _call("POST", path, key, data=json.dumps({"script": script, "timeout": f"{int(timeout_s)}s"}).encode(),
                    ctype="application/json")
    task = _json(body)
    tpath = task.get("path")
    if not tpath:
        raise OCError(f"no task path in response: {body[:200]}")
    deadline = time.time() + timeout_s + 120
    while task.get("state") not in ("COMPLETE", "FAILED", "CANCELLED"):
        if time.time() > deadline:
            raise OCError(f"Luau task {tpath} did not finish in {timeout_s + 120}s")
        time.sleep(poll_s)
        task = _json(_call("GET", f"/cloud/v2/{tpath}", key)[1])
    logs = []
    try:
        data = _json(_call("GET", f"/cloud/v2/{tpath}/logs", key)[1])
        for page in data.get("luauExecutionSessionTaskLogs", []):
            logs += [str(m) for m in page.get("messages", [])]
    except OCError:
        pass
    return {"state": task.get("state"), "results": (task.get("output") or {}).get("results", []),
            "error": task.get("error"), "logs": logs[-50:], "task": tpath}


def restart_servers(universe, key, place_ids=None, bleed_minutes=10):
    """Restart servers on older versions; bleed-off 1-60 min lets running trips finish (0 = immediate)."""
    body = {"closeAllVersions": False, "bleedOffServers": bleed_minutes > 0}
    if bleed_minutes > 0:
        body["bleedOffDurationMinutes"] = max(1, min(60, int(bleed_minutes)))
    if place_ids:
        body["placeIds"] = [int(p) for p in place_ids]
    _call("POST", f"/cloud/v2/universes/{universe}:restartServers", key, data=json.dumps(body).encode(),
          ctype="application/json")
    return body


def probe(timeout=8):
    """(reachable, detail). Any HTTP answer counts as reachable; a proxy refusal or DNS failure does not."""
    try:
        urllib.request.urlopen(urllib.request.Request(base() + "/", method="GET"), timeout=timeout)
        return True, "HTTP 200"
    except urllib.error.HTTPError as e:
        return True, f"HTTP {e.code} (host answered)"
    except (urllib.error.URLError, OSError) as e:
        return False, f"unreachable: {getattr(e, 'reason', e)}"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("probe", help="check the API host is reachable from here")
    p = sp.add_parser("request", help="print the publish request (dry run, key redacted)")
    p.add_argument("file")
    p.add_argument("--universe", required=True)
    p.add_argument("--place", required=True)
    p.add_argument("--type", default="Published", choices=["Saved", "Published"])
    a = ap.parse_args(argv)
    if a.cmd == "probe":
        ok, detail = probe()
        print(f"{base()}: {detail}; key {'set' if api_key() else 'not set'} in ${KEY_ENV}")
        return 0 if ok else 1
    d = describe_publish(a.universe, a.place, a.file, a.type)
    print(json.dumps({k: v for k, v in d.items() if k != "curl"}, indent=1))
    print(d["curl"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
