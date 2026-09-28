#!/usr/bin/env python3
"""placefile.py - read Roblox place and model files with the standard library (release audits).

  placefile.py info FILE [--json]                       format, compression, class counts, instances
  placefile.py tree FILE [--depth N] [--match TEXT]      instance tree (Class Name), filtered
  placefile.py audit FILE --out DIR [--json]            audit.json + props.lua (colours/fonts for bible check)
                                                        + scripts/ (every script's Source, Rojo-style names)
  placefile.py scripts FILE --out DIR                   only extract scripts

Formats: binary .rbxl/.rbxm (chunks raw, LZ4 built in, ZSTD through the optional 'zstandard' module:
`pip install --target ~/.cache/rr-tools/py zstandard`; current Studio saves ZSTD) and XML .rbxlx/.rbxmx.
Read: the instance tree, strings (Name, Source), bools, ints, floats, enums, Color3, Color3uint8, FontFace.
Other property types are skipped, never guessed. It measures what the file holds; runtime performance
needs a device. Exit codes: 0 ok, 1 unreadable file, 2 usage.
"""
import argparse
import hashlib
import json
import os
import re
import struct
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

MAGIC = b"<roblox!\x89\xff\r\n\x1a\n"
SCRIPT_CLASSES = {"Script": ".server.lua", "LocalScript": ".client.lua", "ModuleScript": ".lua"}
PART_CLASSES = {"Part", "MeshPart", "WedgePart", "CornerWedgePart", "TrussPart", "SpawnLocation", "Seat",
                "VehicleSeat", "UnionOperation", "NegateOperation", "IntersectOperation", "PartOperation", "SkateboardPlatform"}
# Open Cloud place publishing does not update these (creator-docs usage-place-publishing.md, 2026-09-28)
OC_UNSUPPORTED = {"EditableImage", "EditableMesh", "PartOperation", "UnionOperation", "NegateOperation",
                  "IntersectOperation", "SurfaceAppearance", "WrapLayer", "WrapTarget", "WrapDeformer", "BaseWrap"}
# an asset reference that points at nothing: rbxassetid://0, rbxassetid:// with no id, ...asset/?id=0
BLANK_ASSET = re.compile(r"^\s*(?:rbxassetid://0*|(?:https?://www\.roblox\.com)?/?asset/?\?id=0*)\s*$", re.I)
EFFECT_CLASSES = ("ParticleEmitter", "Beam", "Trail", "Fire", "Smoke", "Sparkles", "PointLight", "SpotLight",
                  "SurfaceLight", "Sound", "BloomEffect", "SunRaysEffect", "DepthOfFieldEffect", "Atmosphere")


class PlaceError(Exception):
    pass


class Inst:
    __slots__ = ("ref", "cls", "props", "parent")

    def __init__(self, ref, cls):
        self.ref, self.cls, self.props, self.parent = ref, cls, {}, None

    @property
    def name(self):
        return self.props.get("Name", self.cls)


class Place:
    def __init__(self, path, fmt):
        self.path, self.fmt = str(path), fmt
        self.insts, self.meta, self.compression = {}, {}, Counter()

    def children(self):
        kids = {}
        for i in self.insts.values():
            kids.setdefault(i.parent, []).append(i)
        return kids

    def full_name(self, inst):
        parts, seen = [], set()
        while inst is not None and inst.ref not in seen:
            seen.add(inst.ref)
            parts.append(inst.name)
            inst = self.insts.get(inst.parent)
        return ".".join(reversed(parts))

    def classes(self):
        return Counter(i.cls for i in self.insts.values())


# ---------------------------------------------------------------- binary format
def lz4_block(src, usize):
    dst, i, n = bytearray(), 0, len(src)
    while i < n:
        tok = src[i]; i += 1
        lit = tok >> 4
        if lit == 15:
            while True:
                b = src[i]; i += 1; lit += b
                if b != 255:
                    break
        dst += src[i:i + lit]; i += lit
        if i >= n:
            break
        off = src[i] | (src[i + 1] << 8); i += 2
        ml = tok & 15
        if ml == 15:
            while True:
                b = src[i]; i += 1; ml += b
                if b != 255:
                    break
        ml += 4
        start = len(dst) - off
        if off <= 0 or start < 0:
            raise PlaceError("corrupt LZ4 block")
        if off >= ml:
            dst += dst[start:start + ml]
        else:
            for k in range(ml):
                dst.append(dst[start + k])
    if len(dst) != usize:
        raise PlaceError(f"LZ4 size mismatch ({len(dst)} != {usize})")
    return bytes(dst)


def zstd_frame(src, usize):
    extra = Path.home() / ".cache" / "rr-tools" / "py"
    if extra.is_dir() and str(extra) not in sys.path:
        sys.path.append(str(extra))
    try:
        import zstandard
        return zstandard.ZstdDecompressor().decompress(src, max_output_size=usize)
    except ImportError:
        pass
    try:
        from compression import zstd  # Python 3.14+
        return zstd.decompress(src)
    except ImportError:
        raise PlaceError("ZSTD-compressed chunks (current Studio saves): `pip install --target "
                         "~/.cache/rr-tools/py zstandard`, or save the place as .rbxlx")


class Reader:
    def __init__(self, b):
        self.b, self.p = b, 0

    def take(self, n):
        if self.p + n > len(self.b):
            raise PlaceError("truncated chunk")
        v = self.b[self.p:self.p + n]; self.p += n
        return v

    def u8(self):
        return self.take(1)[0]

    def u16(self):
        return struct.unpack("<H", self.take(2))[0]

    def u32(self):
        return struct.unpack("<I", self.take(4))[0]

    def string(self):
        return self.take(self.u32()).decode("utf-8", "replace")

    def interleaved(self, n, width=4):
        raw = self.take(n * width)
        out = []
        for i in range(n):
            v = 0
            for b in range(width):
                v = (v << 8) | raw[b * n + i]
            out.append(v)
        return out

    def i32s(self, n):
        return [(v >> 1) ^ -(v & 1) for v in self.interleaved(n)]

    def refs(self, n):
        acc, out = 0, []
        for d in self.i32s(n):
            acc += d
            out.append(acc)
        return out

    def rfloats(self, n):
        out = []
        for v in self.interleaved(n):
            v = ((v >> 1) | ((v & 1) << 31)) & 0xFFFFFFFF
            out.append(struct.unpack(">f", v.to_bytes(4, "big"))[0])
        return out


def decode_values(t, r, n):
    """Values of one property for n instances, or None for types this reader skips."""
    if t == 0x01:
        out = []
        for _ in range(n):
            raw = r.take(r.u32())
            out.append(raw.decode("utf-8", "replace"))
        return out
    if t == 0x02:
        return [b != 0 for b in r.take(n)]
    if t == 0x03:
        return r.i32s(n)
    if t == 0x04:
        return r.rfloats(n)
    if t == 0x05:
        return list(struct.unpack(f"<{n}d", r.take(8 * n)))
    if t == 0x0C:
        rr, gg, bb = r.rfloats(n), r.rfloats(n), r.rfloats(n)
        return [("rgbf", a, b, c) for a, b, c in zip(rr, gg, bb)]
    if t == 0x12:
        return [("enum", v) for v in r.interleaved(n)]
    if t == 0x1A:
        rr, gg, bb = r.take(n), r.take(n), r.take(n)
        return [("rgb8", a, b, c) for a, b, c in zip(rr, gg, bb)]
    if t == 0x20:
        out = []
        for _ in range(n):
            fam = r.string(); weight = r.u16(); style = r.u8(); r.string()
            out.append(("font", fam, weight, style))
        return out
    return None


def read_binary(data, path):
    if not data.startswith(MAGIC):
        raise PlaceError("not a binary Roblox file")
    if len(data) < 32:
        raise PlaceError("truncated header")
    P = Place(path, "binary")
    classes, pos = {}, 32
    while pos + 16 <= len(data):
        tag = data[pos:pos + 4].rstrip(b"\0").decode("ascii", "replace")
        clen, ulen, _ = struct.unpack_from("<III", data, pos + 4)
        pos += 16
        if clen == 0:
            body = data[pos:pos + ulen]; pos += ulen; P.compression["raw"] += 1
        else:
            raw = data[pos:pos + clen]; pos += clen
            if raw[:4] == b"\x28\xb5\x2f\xfd":
                body = zstd_frame(raw, ulen); P.compression["zstd"] += 1
            else:
                body = lz4_block(raw, ulen); P.compression["lz4"] += 1
        r = Reader(body)
        if tag == "META":
            for _ in range(r.u32()):
                k = r.string(); P.meta[k] = r.string()
        elif tag == "INST":
            cid = r.u32(); cname = r.string(); r.u8(); n = r.u32()
            refs = r.refs(n)
            classes[cid] = (cname, refs)
            for ref in refs:
                P.insts[ref] = Inst(ref, cname)
        elif tag == "PROP":
            cid = r.u32(); pname = r.string(); t = r.u8()
            if cid not in classes:
                continue
            refs = classes[cid][1]
            try:
                vals = decode_values(t, r, len(refs))
            except (PlaceError, struct.error):
                vals = None
            if vals is not None:
                for ref, v in zip(refs, vals):
                    P.insts[ref].props[pname] = v
        elif tag == "PRNT":
            r.u8(); n = r.u32()
            kids, pars = r.refs(n), r.refs(n)
            for k, p in zip(kids, pars):
                if k in P.insts:
                    P.insts[k].parent = p if p >= 0 else None
        elif tag == "END":
            break
    return P


# ---------------------------------------------------------------- XML format
def _xml_value(el):
    tag = el.tag
    if tag in ("string", "ProtectedString", "BinaryString"):
        return el.text or ""
    if tag == "bool":
        return (el.text or "").strip() == "true"
    if tag == "Content":
        return (el.findtext("url") or el.findtext("uri") or "").strip()
    if tag in ("int", "int64"):
        try:
            return int((el.text or "0").strip())
        except ValueError:
            return None
    if tag in ("float", "double"):
        try:
            return float((el.text or "0").strip())
        except ValueError:
            return None
    if tag == "token":
        try:
            return ("enum", int((el.text or "0").strip()))
        except ValueError:
            return None
    if tag == "Color3":
        try:
            return ("rgbf", float(el.findtext("R")), float(el.findtext("G")), float(el.findtext("B")))
        except (TypeError, ValueError):
            return None
    if tag == "Color3uint8":
        try:
            v = int((el.text or "0").strip())
        except ValueError:
            return None
        return ("rgb8", (v >> 16) & 255, (v >> 8) & 255, v & 255)
    if tag == "Font":
        fam = el.findtext("Family/url") or ""
        try:
            weight = int(el.findtext("Weight") or 400)
        except ValueError:
            weight = 400
        return ("font", fam, weight, el.findtext("Style") or "Normal")
    return None


def read_xml(data, path):
    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        raise PlaceError(f"XML parse error: {e}")
    if root.tag != "roblox":
        raise PlaceError("not a Roblox XML file")
    P = Place(path, "xml")
    for m in root.findall("Meta"):
        P.meta[m.get("name", "")] = m.text or ""
    counter = [0]

    def walk(item, parent):
        counter[0] += 1
        ref = counter[0]
        inst = Inst(ref, item.get("class", "?"))
        inst.parent = parent
        props = item.find("Properties")
        if props is not None:
            for el in props:
                v = _xml_value(el)
                if v is not None and el.get("name"):
                    inst.props[el.get("name")] = v
        P.insts[ref] = inst
        for child in item.findall("Item"):
            walk(child, ref)

    for item in root.findall("Item"):
        walk(item, None)
    return P


def load(path):
    path = Path(path)
    data = path.read_bytes()
    if data.startswith(MAGIC):
        return read_binary(data, path)
    head = data[:200].lstrip()
    if head.startswith(b"<roblox") or head.startswith(b"<?xml"):
        return read_xml(data, path)
    raise PlaceError("not a Roblox place or model file (.rbxl/.rbxm/.rbxlx/.rbxmx)")


# ---------------------------------------------------------------- audit
def hexof(v):
    if v[0] == "rgb8":
        r, g, b = v[1:]
    else:
        r, g, b = (max(0, min(255, round(c * 255))) for c in v[1:])
    return f"#{r:02X}{g:02X}{b:02X}"


def font_family(url):
    m = re.search(r"families/([^/]+?)\.json", url or "")
    return m.group(1) if m else (url or "?")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def audit(P, top=40):
    cls = P.classes()
    parts = [i for i in P.insts.values() if i.cls in PART_CLASSES]
    unanchored = [i for i in parts if i.props.get("Anchored") is False]
    colours, fonts = {}, {}
    for i in P.insts.values():
        for k, v in i.props.items():
            if isinstance(v, tuple) and v[0] in ("rgb8", "rgbf"):
                hx = hexof(v)
                e = colours.setdefault(hx, {"count": 0, "example": "", "props": set()})
                e["count"] += 1; e["props"].add(k)
                if not e["example"]:
                    e["example"] = P.full_name(i)
            elif isinstance(v, tuple) and v[0] == "font":
                fam = font_family(v[1])
                e = fonts.setdefault(fam, {"count": 0, "example": "", "url": v[1]})
                e["count"] += 1
                if not e["example"]:
                    e["example"] = P.full_name(i)
    scripts = []
    for i in P.insts.values():
        if i.cls in SCRIPT_CLASSES:
            src = i.props.get("Source", "")
            scripts.append({"path": P.full_name(i), "class": i.cls, "bytes": len(src.encode()),
                            "lines": src.count("\n") + (1 if src else 0),
                            "disabled": i.props.get("Disabled") is True or i.props.get("Enabled") is False})
    ws = next((i for i in P.insts.values() if i.cls == "Workspace"), None)
    stamp = next((i for i in P.insts.values() if i.cls == "ModuleScript" and i.name == "RR_Version"), None)
    m = re.search(r'version\s*=\s*"([^"]+)"', stamp.props.get("Source", "")) if stamp else None
    placeholders = sorted({P.full_name(i) for i in P.insts.values() if i.name.upper().startswith("PLACEHOLDER")})
    blank_assets = sorted({f"{P.full_name(i)}.{k}" for i in P.insts.values() for k, v in i.props.items()
                           if k != "Source" and isinstance(v, str) and v and BLANK_ASSET.match(v)})
    size = os.path.getsize(P.path)
    return {
        "file": P.path, "format": P.fmt, "bytes": size, "sha256": sha256(P.path),
        "compression": dict(P.compression), "instances": len(P.insts),
        "classes": dict(cls.most_common()),
        "counts": {
            "parts": len(parts), "meshparts": cls.get("MeshPart", 0), "unanchored_parts": len(unanchored),
            "scripts": len(scripts), "script_bytes": sum(s["bytes"] for s in scripts),
            "effects": {c: cls.get(c, 0) for c in EFFECT_CLASSES if cls.get(c, 0)},
        },
        "streaming_enabled": ws.props.get("StreamingEnabled") if ws else None,
        "oc_unsupported": {c: n for c, n in cls.items() if c in OC_UNSUPPORTED},
        "stamp_version": m.group(1) if m else None,
        "placeholders": placeholders[:50],
        "blank_assets": blank_assets[:50],
        "colours": [{"hex": h, "count": e["count"], "example": e["example"], "props": sorted(e["props"])}
                    for h, e in sorted(colours.items(), key=lambda kv: -kv[1]["count"])][:top],
        "colour_total": len(colours),
        "fonts": [{"family": f, "count": e["count"], "example": e["example"], "url": e["url"]}
                  for f, e in sorted(fonts.items(), key=lambda kv: -kv[1]["count"])],
        "scripts": scripts,
    }


def safe(name):
    s = re.sub(r"[^A-Za-z0-9_. -]", "_", name).strip(" .") or "_"
    return s[:80]


def extract_scripts(P, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    used, written = set(), []
    for i in sorted(P.insts.values(), key=lambda x: P.full_name(x)):
        if i.cls not in SCRIPT_CLASSES:
            continue
        chain, cur = [], P.insts.get(i.parent)
        while cur is not None:
            chain.append(safe(cur.name)); cur = P.insts.get(cur.parent)
        rel = Path(*reversed(chain)) if chain else Path(".")
        base = rel / (safe(i.name) + SCRIPT_CLASSES[i.cls])
        n = 2
        while str(base) in used:
            base = rel / (safe(i.name) + f"~{n}" + SCRIPT_CLASSES[i.cls]); n += 1
        used.add(str(base))
        dest = out / base
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(i.props.get("Source", ""), encoding="utf-8")
        written.append({"file": str(base), "path": P.full_name(i), "class": i.cls})
    (out / "index.json").write_text(json.dumps(written, indent=1))
    return written


def props_lua(a):
    """Colours and fonts as Luau lines, so rr-bible's `check` can name the nearest token."""
    lines = ["-- generated by placefile.py audit: every colour and font the place file stores (for bible check)"]
    for c in a["colours"]:
        r, g, b = (int(c["hex"][k:k + 2], 16) for k in (1, 3, 5))
        lines.append(f"local _ = Color3.fromRGB({r}, {g}, {b}) -- x{c['count']} {','.join(c['props'])} e.g. {c['example']}")
    for f in a["fonts"]:
        lines.append(f'local _ = Font.new("{f["url"]}") -- x{f["count"]} e.g. {f["example"]}')
    return "\n".join(lines) + "\n"


def write_audit(P, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    a = audit(P)
    a["extracted"] = len(extract_scripts(P, out / "scripts"))
    (out / "audit.json").write_text(json.dumps(a, indent=1))
    (out / "props.lua").write_text(props_lua(a))
    return a


# ---------------------------------------------------------------- test writer (selftest fixtures)
def _lz4_compress(src):
    """Greedy LZ4 block compressor (4-byte hash matches). Used by selftest to make fixtures."""
    out, i, anchor, table, n = bytearray(), 0, 0, {}, len(src)

    def emit(lit, ml=None, off=0):
        L = len(lit)
        tok_l = min(L, 15)
        tok_m = 0 if ml is None else min(ml - 4, 15)
        out.append((tok_l << 4) | tok_m)
        if L >= 15:
            r = L - 15
            while r >= 255:
                out.append(255); r -= 255
            out.append(r)
        out.extend(lit)
        if ml is None:
            return
        out.extend(struct.pack("<H", off))
        if ml - 4 >= 15:
            r = ml - 4 - 15
            while r >= 255:
                out.append(255); r -= 255
            out.append(r)

    while i + 12 < n:
        key = bytes(src[i:i + 4])
        cand = table.get(key)
        table[key] = i
        if cand is not None and i - cand < 65535 and src[cand:cand + 4] == src[i:i + 4]:
            ml = 4
            while i + ml < n - 5 and src[cand + ml] == src[i + ml]:
                ml += 1
            emit(src[anchor:i], ml, i - cand)
            i += ml; anchor = i
        else:
            i += 1
    emit(src[anchor:])
    return bytes(out)


def write_binary(path, insts, compress=True):
    """insts: list of (ref, class, parent_ref_or_None, {prop: value}); values: str, bool, ('rgb8',r,g,b),
    ('rgbf',r,g,b), ('font',family_url,weight,style_int). Produces a valid binary place (fixtures only)."""
    def s(x):
        b = x.encode(); return struct.pack("<I", len(b)) + b

    def inter(vals, width=4):
        raw = [v.to_bytes(width, "big") for v in vals]
        return bytes(raw[i][b] for b in range(width) for i in range(len(vals)))

    def zig(v):
        return ((v << 1) ^ (v >> 31)) & 0xFFFFFFFF

    def refs(vals):
        prev, d = 0, []
        for v in vals:
            d.append(zig(v - prev)); prev = v
        return inter(d)

    def rfl(vals):
        out = []
        for f in vals:
            u = struct.unpack(">I", struct.pack(">f", f))[0]
            out.append(((u << 1) | (u >> 31)) & 0xFFFFFFFF)
        return inter(out)

    def chunk(tag, body, comp):
        if comp:
            c = _lz4_compress(body)
            return tag + struct.pack("<III", len(c), len(body), 0) + c
        return tag + struct.pack("<III", 0, len(body), 0) + body

    by_cls = {}
    for ref, c, par, props in insts:
        by_cls.setdefault(c, []).append((ref, par, props))
    chunks = [chunk(b"META", struct.pack("<I", 1) + s("ExplicitAutoJoints") + s("true"), False)]
    for cid, (c, items) in enumerate(sorted(by_cls.items())):
        chunks.append(chunk(b"INST", struct.pack("<I", cid) + s(c) + b"\0" + struct.pack("<I", len(items))
                            + refs([r for r, _, _ in items]), compress))
        names = sorted({k for _, _, p in items for k in p} | {"Name"})
        for pn in names:
            vals = [p.get(pn, c if pn == "Name" else None) for _, _, p in items]
            kind = next((v for v in vals if v is not None), None)
            if isinstance(kind, bool):
                body = bytes(1 if v else 0 for v in vals); t = 0x02
            elif isinstance(kind, str):
                body = b"".join(s(v or "") for v in vals); t = 0x01
            elif isinstance(kind, tuple) and kind[0] == "rgb8":
                body = bytes(v[1] for v in vals) + bytes(v[2] for v in vals) + bytes(v[3] for v in vals); t = 0x1A
            elif isinstance(kind, tuple) and kind[0] == "rgbf":
                body = rfl([v[1] for v in vals]) + rfl([v[2] for v in vals]) + rfl([v[3] for v in vals]); t = 0x0C
            elif isinstance(kind, tuple) and kind[0] == "font":
                body = b"".join(s(v[1]) + struct.pack("<HB", v[2], v[3]) + s("") for v in vals); t = 0x20
            else:
                continue
            chunks.append(chunk(b"PROP", struct.pack("<I", cid) + s(pn) + bytes([t]) + body, compress))
    kids = [r for r, _, _, _ in insts]
    pars = [(-1 if p is None else p) for _, _, p, _ in insts]
    chunks.append(chunk(b"PRNT", b"\0" + struct.pack("<I", len(kids)) + refs(kids) + refs(pars), compress))
    chunks.append(chunk(b"END\0", b"</roblox>", False))
    head = MAGIC + struct.pack("<Hii", 0, len(by_cls), len(insts)) + b"\0" * 8
    Path(path).write_bytes(head + b"".join(chunks))


# ---------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("info"); p.add_argument("file"); p.add_argument("--json", action="store_true")
    p = sp.add_parser("tree"); p.add_argument("file"); p.add_argument("--depth", type=int, default=3)
    p.add_argument("--match", default="")
    p = sp.add_parser("audit"); p.add_argument("file"); p.add_argument("--out", required=True)
    p.add_argument("--json", action="store_true")
    p = sp.add_parser("scripts"); p.add_argument("file"); p.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    try:
        P = load(a.file)
    except (OSError, PlaceError) as e:
        print(f"placefile: {a.file}: {e}")
        return 1
    if a.cmd == "info":
        info = {"format": P.fmt, "compression": dict(P.compression), "instances": len(P.insts),
                "classes": dict(P.classes().most_common())}
        if a.json:
            print(json.dumps(info, indent=1))
        else:
            top = ", ".join(f"{c} {n}" for c, n in P.classes().most_common(12))
            print(f"{P.fmt} {dict(P.compression) or ''} | {len(P.insts)} instances | {top}")
    elif a.cmd == "tree":
        kids = P.children()

        def show(parent, d):
            for i in sorted(kids.get(parent, []), key=lambda x: x.name):
                full = P.full_name(i)
                if not a.match or a.match.lower() in full.lower():
                    print("  " * d + f"{i.cls} {i.name}")
                if d + 1 < a.depth:
                    show(i.ref, d + 1)
        show(None, 0)
    elif a.cmd == "audit":
        r = write_audit(P, a.out)
        if a.json:
            print(json.dumps({k: v for k, v in r.items() if k != "scripts"}, indent=1))
        else:
            c = r["counts"]
            print(f"audit: {r['instances']} instances, {c['parts']} parts ({c['unanchored_parts']} unanchored), "
                  f"{c['scripts']} scripts ({c['script_bytes']} B), {r['colour_total']} colours, "
                  f"{len(r['fonts'])} fonts, stamp {r['stamp_version'] or 'none'}, "
                  f"OC-unsupported {r['oc_unsupported'] or 'none'} -> {a.out}")
    elif a.cmd == "scripts":
        w = extract_scripts(P, a.out)
        print(f"{len(w)} scripts -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
