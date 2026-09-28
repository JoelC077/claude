#!/usr/bin/env python3
"""rr-soundsmith audio library: read/write WAV (standard library), decode .ogg/.mp3/.flac through ffmpeg when one is
found, probe their headers when not, and measure: ITU-R BS.1770-4 loudness (momentary max, short-term max,
integrated, EBU LRA), 4x true peak, sample peak, clipping runs, DC offset, lead/tail silence, loop seam, spectral
bands (phone band) and stereo correlation.

  python3 audiolib.py FILE [FILE...] [--json]      quick measurement (sound.py analyze adds the checks)

numpy is optional: with it everything is fast; without it loudness runs in pure Python (slow on long files) and true
peak, spectral bands and correlation are skipped, which the report says. ffmpeg: $RR_SOUND_FFMPEG, then `ffmpeg` on
PATH, then the imageio-ffmpeg wheel (pip install --target ~/.cache/rr-tools/py imageio-ffmpeg).
$RR_SOUND_NO_FFMPEG=1 disables decoding (header-only probes).
Conventions: mono is measured as dual mono (+3.01 dB, as heard on two speakers); files shorter than 400 ms are
zero-padded to one momentary block; silence threshold -60 dBFS.
"""
import json, math, os, shutil, struct, subprocess, sys
from array import array
from pathlib import Path

try:
    import numpy as np
except ImportError:  # pragma: no cover - exercised by selftest with RR_SOUND_NO_NUMPY
    np = None
if os.environ.get("RR_SOUND_NO_NUMPY"):
    np = None

SILENCE_DB = -60.0
CLIP_LEVEL = 0.9995
WEIGHTS = {1: [1.0, 1.0], 2: [1.0, 1.0], 3: [1.0, 1.0, 1.0], 6: [1.0, 1.0, 1.0, 0.0, 1.41, 1.41]}


class AudioError(Exception):
    pass


def db(x, floor=-200.0):
    return 20 * math.log10(x) if x > 0 else floor


# ------------------------------------------------------------------ WAV
def _parse_fmt(b):
    tag, ch, rate, _, align, bits = struct.unpack("<HHIIHH", b[:16])
    if tag == 0xFFFE and len(b) >= 26:
        tag = struct.unpack("<H", b[24:26])[0]
    if tag not in (1, 3):
        raise AudioError(f"WAV codec tag {tag} is not PCM or float")
    return {"tag": tag, "channels": ch, "rate": rate, "align": align, "bits": bits}


def read_wav(path):
    data = Path(path).read_bytes()
    if data[:4] not in (b"RIFF", b"RF64") or data[8:12] != b"WAVE":
        raise AudioError("not a RIFF/WAVE file")
    pos, fmt, pcm, info = 12, None, None, {}
    while pos + 8 <= len(data):
        cid, size = data[pos:pos + 4], struct.unpack("<I", data[pos + 4:pos + 8])[0]
        if size == 0xFFFFFFFF or pos + 8 + size > len(data):
            size = len(data) - pos - 8
        body = data[pos + 8:pos + 8 + size]
        if cid == b"fmt ":
            fmt = _parse_fmt(body)
        elif cid == b"data":
            pcm = body
        elif cid == b"LIST" and body[:4] == b"INFO":
            p = 4
            while p + 8 <= len(body):
                k, n = body[p:p + 4].decode("latin-1"), struct.unpack("<I", body[p + 4:p + 8])[0]
                info[k] = body[p + 8:p + 8 + n].rstrip(b"\0").decode("utf-8", "replace")
                p += 8 + n + (n & 1)
        pos += 8 + size + (size & 1)
    if not fmt or pcm is None:
        raise AudioError("WAV without fmt or data chunk")
    ch, bits, tag = fmt["channels"], fmt["bits"], fmt["tag"]
    width = bits // 8
    n = len(pcm) // (width * ch)
    pcm = pcm[:n * width * ch]
    chans = _decode_pcm(pcm, ch, bits, tag)
    return {"rate": fmt["rate"], "channels": chans, "bits": bits, "float": tag == 3, "info": info,
            "format": "wav", "codec": "float" if tag == 3 else "pcm", "frames": n}


def _decode_pcm(pcm, ch, bits, tag):
    if np is not None:
        if tag == 3:
            x = np.frombuffer(pcm, dtype="<f4" if bits == 32 else "<f8").astype(np.float64)
        elif bits == 8:
            x = (np.frombuffer(pcm, dtype=np.uint8).astype(np.float64) - 128) / 128
        elif bits == 16:
            x = np.frombuffer(pcm, dtype="<i2") / 32768.0
        elif bits == 24:
            b = np.frombuffer(pcm, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
            v = b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)
            x = np.where(v >= 1 << 23, v - (1 << 24), v) / 8388608.0
        elif bits == 32:
            x = np.frombuffer(pcm, dtype="<i4") / 2147483648.0
        else:
            raise AudioError(f"{bits}-bit PCM not supported")
        x = x.reshape(-1, ch)
        return [np.ascontiguousarray(x[:, c]) for c in range(ch)]
    if tag == 3:
        a = array("f" if bits == 32 else "d"); a.frombytes(pcm)
        vals = a
    elif bits == 8:
        vals = [(b - 128) / 128 for b in pcm]
    elif bits == 16:
        a = array("h"); a.frombytes(pcm); vals = [v / 32768.0 for v in a]
    elif bits == 24:
        vals = []
        for i in range(0, len(pcm), 3):
            v = pcm[i] | (pcm[i + 1] << 8) | (pcm[i + 2] << 16)
            vals.append((v - (1 << 24) if v >= 1 << 23 else v) / 8388608.0)
    elif bits == 32:
        a = array("i"); a.frombytes(pcm); vals = [v / 2147483648.0 for v in a]
    else:
        raise AudioError(f"{bits}-bit PCM not supported")
    return [array("d", vals[c::ch]) for c in range(ch)]


def write_wav(path, rate, chans, bits=16, info=None):
    """chans: list of equal-length float sequences in -1..1. bits 16/24 PCM or 32 float. info: {INAM, ICMT, ISFT}."""
    ch, n = len(chans), len(chans[0])
    if np is not None:
        x = np.stack([np.asarray(c, dtype=np.float64) for c in chans], axis=1)
        x = np.clip(x, -1.0, 1.0)
        if bits == 16:
            raw = np.round(np.clip(x * 32768, -32768, 32767)).astype("<i2").tobytes()
        elif bits == 24:
            v = np.round(np.clip(x * 8388608, -8388608, 8388607)).astype(np.int32).reshape(-1)
            raw = np.stack([v & 255, (v >> 8) & 255, (v >> 16) & 255], axis=1).astype(np.uint8).tobytes()
        else:
            raw = x.astype("<f4").tobytes()
    else:
        out = bytearray()
        for i in range(n):
            for c in range(ch):
                s = max(-1.0, min(1.0, chans[c][i]))
                if bits == 16:
                    out += struct.pack("<h", max(-32768, min(32767, round(s * 32768))))
                elif bits == 24:
                    out += struct.pack("<i", max(-8388608, min(8388607, round(s * 8388608))))[:3]
                else:
                    out += struct.pack("<f", s)
        raw = bytes(out)
    tag = 3 if bits == 32 else 1
    fmt = struct.pack("<HHIIHH", tag, ch, rate, rate * ch * bits // 8, ch * bits // 8, bits)
    chunks = [b"fmt " + struct.pack("<I", len(fmt)) + fmt]
    if info:
        body = b"INFO"
        for k, v in info.items():
            s = v.encode("utf-8") + b"\0"
            body += k.encode("ascii")[:4].ljust(4) + struct.pack("<I", len(s)) + s + (b"\0" if len(s) & 1 else b"")
        chunks.append(b"LIST" + struct.pack("<I", len(body)) + body)
    chunks.append(b"data" + struct.pack("<I", len(raw)) + raw + (b"\0" if len(raw) & 1 else b""))
    payload = b"WAVE" + b"".join(chunks)
    Path(path).write_bytes(b"RIFF" + struct.pack("<I", len(payload)) + payload)


# ------------------------------------------------------------------ other formats
def find_ffmpeg():
    if os.environ.get("RR_SOUND_NO_FFMPEG"):
        return None
    if os.environ.get("RR_SOUND_FFMPEG"):
        return os.environ["RR_SOUND_FFMPEG"]
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    extra = str(Path.home() / ".cache" / "rr-tools" / "py")
    if extra not in sys.path:
        sys.path.append(extra)
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


LAYOUTS = {"mono": 1, "stereo": 2, "2.1": 3, "3.0": 3, "quad": 4, "4.0": 4, "5.0": 5, "5.0(side)": 5, "5.1": 6,
           "5.1(side)": 6, "6.1": 7, "7.1": 8}


def decode_ffmpeg(path, exe):
    r = subprocess.run([exe, "-hide_banner", "-nostdin", "-i", str(path), "-map", "0:a:0", "-f", "f32le",
                        "-acodec", "pcm_f32le", "-"], capture_output=True)
    err = r.stderr.decode("utf-8", "replace")
    if r.returncode != 0:
        raise AudioError("ffmpeg could not decode: " + err.strip().splitlines()[-1][:160] if err.strip() else "ffmpeg failed")
    import re
    outs = re.findall(r"Audio: pcm_f32le[^,]*, (\d+) Hz, ([^,\n]+)", err)
    ins = re.findall(r"Stream #0:\d+[^:]*: Audio: ([a-z0-9_]+)", err)
    if not outs:
        raise AudioError("ffmpeg output stream not recognised")
    rate, lay = int(outs[-1][0]), outs[-1][1].strip()
    m = re.match(r"(\d+) channels", lay)
    ch = int(m[1]) if m else LAYOUTS.get(lay, 2)
    if np is not None:
        x = np.frombuffer(r.stdout, dtype="<f4").astype(np.float64)
        x = x[:len(x) // ch * ch].reshape(-1, ch)
        chans = [np.ascontiguousarray(x[:, c]) for c in range(ch)]
    else:
        a = array("f"); a.frombytes(r.stdout[:len(r.stdout) // (4 * ch) * 4 * ch])
        chans = [array("d", a[c::ch]) for c in range(ch)]
    return {"rate": rate, "channels": chans, "bits": None, "float": True, "info": {}, "codec": ins[0] if ins else "?",
            "frames": len(chans[0])}


def probe_header(path):
    """Length, rate and channels without decoding (flac, ogg vorbis/opus, mp3). Returns dict or raises."""
    b = Path(path).read_bytes()
    if b[:4] == b"fLaC":
        si = b[8:8 + 34]
        rate = (si[10] << 12) | (si[11] << 4) | (si[12] >> 4)
        ch = ((si[12] >> 1) & 7) + 1
        bps = (((si[12] & 1) << 4) | (si[13] >> 4)) + 1
        total = ((si[13] & 15) << 32) | struct.unpack(">I", si[14:18])[0]
        return {"format": "flac", "codec": "flac", "rate": rate, "nch": ch, "bits": bps, "duration": total / rate if rate else 0}
    if b[:4] == b"OggS":
        seg_n = b[26]
        p = 27 + seg_n
        pkt = b[p:p + 64]
        last = b.rfind(b"OggS")
        gran = struct.unpack("<q", b[last + 6:last + 14])[0]
        if pkt[:7] == b"\x01vorbis":
            ch, rate = pkt[11], struct.unpack("<I", pkt[12:16])[0]
            return {"format": "ogg", "codec": "vorbis", "rate": rate, "nch": ch, "bits": None, "duration": gran / rate}
        if pkt[:8] == b"OpusHead":
            ch, pre, rate = pkt[9], struct.unpack("<H", pkt[10:12])[0], struct.unpack("<I", pkt[12:16])[0]
            return {"format": "ogg", "codec": "opus", "rate": rate or 48000, "nch": ch, "bits": None,
                    "duration": max(0, gran - pre) / 48000}
        raise AudioError("ogg stream is neither vorbis nor opus")
    p = 0
    if b[:3] == b"ID3":
        p = 10 + ((b[6] & 127) << 21 | (b[7] & 127) << 14 | (b[8] & 127) << 7 | (b[9] & 127))
    while p + 4 <= len(b):
        if b[p] == 0xFF and (b[p + 1] & 0xE0) == 0xE0:
            h = struct.unpack(">I", b[p:p + 4])[0]
            ver, layer = (h >> 19) & 3, (h >> 17) & 3
            bri, sri, mode = (h >> 12) & 15, (h >> 10) & 3, (h >> 6) & 3
            if ver != 1 and layer == 1 and bri not in (0, 15) and sri != 3:
                rates = {3: [44100, 48000, 32000], 2: [22050, 24000, 16000], 0: [11025, 12000, 8000]}[ver]
                kbps = ([0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320] if ver == 3 else
                        [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160])[bri]
                rate, spf = rates[sri], 1152 if ver == 3 else 576
                ch = 1 if mode == 3 else 2
                side = (32 if ch == 2 else 17) if ver == 3 else (17 if ch == 2 else 9)
                x = p + 4 + side
                if b[x:x + 4] in (b"Xing", b"Info") and struct.unpack(">I", b[x + 4:x + 8])[0] & 1:
                    frames = struct.unpack(">I", b[x + 8:x + 12])[0]
                    dur = frames * spf / rate
                else:
                    dur = (len(b) - p) * 8 / (kbps * 1000)
                return {"format": "mp3", "codec": "mp3", "rate": rate, "nch": ch, "bits": None, "duration": dur}
        p += 1
    raise AudioError("unknown audio format (expected wav, ogg, mp3 or flac)")


def load(path):
    """Decoded audio dict (rate, channels, ...) or {'decoded': False, ...header probe} when no decoder exists."""
    path = Path(path)
    head = path.read_bytes()[:12]
    size = path.stat().st_size
    if head[:4] in (b"RIFF", b"RF64") and head[8:12] == b"WAVE":
        d = read_wav(path)
        d.update(decoded=True, bytes=size, format="wav")
        return d
    probe = probe_header(path)
    exe = find_ffmpeg()
    if exe:
        d = decode_ffmpeg(path, exe)
        d.update(decoded=True, bytes=size, format=probe["format"], bits=probe.get("bits"), src_rate=probe["rate"])
        return d
    probe.update(decoded=False, bytes=size, frames=None)
    return probe


# ------------------------------------------------------------------ BS.1770-4 K-weighting
def kweight_coeffs(rate):
    """Two biquads (high shelf, RLB high-pass) for any sample rate; equal to the spec tables at 48 kHz."""
    G, f0, Q = 3.999843853973347, 1681.974450955533, 0.7071752369554196
    K = math.tan(math.pi * f0 / rate)
    Vh = 10 ** (G / 20)
    Vb = Vh ** 0.4996667741545416
    a0 = 1 + K / Q + K * K
    s1 = ([(Vh + Vb * K / Q + K * K) / a0, 2 * (K * K - Vh) / a0, (Vh - Vb * K / Q + K * K) / a0],
          [1.0, 2 * (K * K - 1) / a0, (1 - K / Q + K * K) / a0])
    f0, Q = 38.13547087602444, 0.5003270373238773
    K = math.tan(math.pi * f0 / rate)
    a0 = 1 + K / Q + K * K
    s2 = ([1.0, -2.0, 1.0], [1.0, 2 * (K * K - 1) / a0, (1 - K / Q + K * K) / a0])
    return [s1, s2]


def _biquad_py(x, b, a):
    b0, b1, b2 = b
    _, a1, a2 = a
    x1 = x2 = y1 = y2 = 0.0
    out = array("d", bytes(8 * len(x)))
    for i, v in enumerate(x):
        y = b0 * v + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1, y2, y1 = x1, v, y1, y
        out[i] = y
    return out


def _kernel(rate):
    n = 1 << max(10, math.ceil(math.log2(rate * 0.35)))
    imp = array("d", [1.0] + [0.0] * (n - 1))
    for b, a in kweight_coeffs(rate):
        imp = _biquad_py(imp, b, a)
    return np.asarray(imp)


_KCACHE = {}


def kfilter(x, rate):
    """K-weighted copy of one channel (numpy: FFT overlap-add with the exact impulse response, tail < 1e-30)."""
    if np is None:
        y = x
        for b, a in kweight_coeffs(rate):
            y = _biquad_py(y, b, a)
        return y
    h = _KCACHE.setdefault(rate, _kernel(rate))
    x = np.asarray(x, dtype=np.float64)
    blk = 1 << 18
    nfft = 1 << math.ceil(math.log2(blk + len(h)))
    H = np.fft.rfft(h, nfft)
    y = np.zeros(len(x) + len(h))
    for s in range(0, len(x), blk):
        seg = x[s:s + blk]
        yy = np.fft.irfft(np.fft.rfft(seg, nfft) * H, nfft)[:len(seg) + len(h)]
        y[s:s + len(yy)] += yy
    return y[:len(x)]


def _cumsq(y):
    if np is not None:
        return np.concatenate([[0.0], np.cumsum(np.asarray(y) ** 2)])
    c, s = array("d", [0.0]), 0.0
    for v in y:
        s += v * v
        c.append(s)
    return c


def block_powers(chans, rate, win, step):
    """Weighted mean-square per block (sum_i G_i z_i) for windows `win` s every `step` s over zero-padded audio."""
    n = len(chans[0])
    nch = len(chans)
    w = WEIGHTS.get(nch) or [1.0] * nch
    if nch == 1:
        w = [2.0]  # dual mono
    W, S = int(round(win * rate)), int(round(step * rate))
    if n < W:
        n_blocks = 1
    else:
        n_blocks = (n - W) // S + 1
    out = [0.0] * n_blocks
    for c, x in enumerate(chans):
        if w[c] == 0:
            continue
        cs = _cumsq(kfilter(x, rate))
        last = len(cs) - 1
        for j in range(n_blocks):
            a, b = j * S, min(j * S + W, last)
            out[j] += w[c] * (cs[b] - cs[a]) / W
    return out


def lufs(p):
    return -0.691 + 10 * math.log10(p) if p > 0 else -200.0


def loudness(chans, rate):
    """{'m_max','s_max','integrated','lra'} in LUFS/LU (None where the file is too short)."""
    n = len(chans[0])
    mom = block_powers(chans, rate, 0.4, 0.1)
    res = {"m_max": round(lufs(max(mom)), 2)}
    gated = [p for p in mom if lufs(p) > -70]
    if gated:
        rel = lufs(sum(gated) / len(gated)) - 10
        g2 = [p for p in gated if lufs(p) > rel]
        res["integrated"] = round(lufs(sum(g2) / len(g2)), 2) if g2 else None
    else:
        res["integrated"] = None
    if n >= 3 * rate:
        st = block_powers(chans, rate, 3.0, 0.1)
        res["s_max"] = round(lufs(max(st)), 2)
        g = [p for p in st if lufs(p) > -70]
        if g:
            rel = lufs(sum(g) / len(g)) - 20
            vals = sorted(lufs(p) for p in g if lufs(p) > rel)
            if vals:
                pc = lambda q: vals[min(len(vals) - 1, int(round(q * (len(vals) - 1))))]  # noqa: E731
                res["lra"] = round(pc(0.95) - pc(0.10), 2)
    res.setdefault("s_max", None)
    res.setdefault("lra", None)
    return res


# ------------------------------------------------------------------ peaks and the rest
_TPH = None


def _tp_filter():
    global _TPH
    if _TPH is None:
        L, taps = 4, 32
        N = L * taps
        n = np.arange(N) - (N - 1) / 2
        h = np.sinc(n / L * 0.96) * np.kaiser(N, 8.0)
        _TPH = np.array([h[k::L] / h[k::L].sum() for k in range(L)])
    return _TPH


def true_peak(chans):
    """4x oversampled peak (dBTP) or None without numpy."""
    if np is None:
        return None
    ph = _tp_filter()
    best = 0.0
    for x in chans:
        x = np.asarray(x)
        best = max(best, float(np.max(np.abs(x))) if len(x) else 0.0)
        for p in ph:
            if len(x):
                best = max(best, float(np.max(np.abs(np.convolve(x, p, mode="same")))))
    return round(db(best), 2)


def sample_peak(chans):
    m = 0.0
    for x in chans:
        if len(x):
            m = max(m, float(np.max(np.abs(x))) if np is not None else max(abs(v) for v in x))
    return m


def clip_runs(chans, min_run=3):
    runs = 0
    for x in chans:
        if np is not None:
            hot = np.abs(np.asarray(x)) >= CLIP_LEVEL
            if not hot.any():
                continue
            d = np.diff(np.concatenate([[0], hot.astype(np.int8), [0]]))
            starts, ends = np.where(d == 1)[0], np.where(d == -1)[0]
            runs += int(np.sum((ends - starts) >= min_run))
        else:
            r = 0
            for v in x:
                if abs(v) >= CLIP_LEVEL:
                    r += 1
                else:
                    runs += r >= min_run
                    r = 0
            runs += r >= min_run
    return runs


def edges(chans, rate):
    thr = 10 ** (SILENCE_DB / 20)
    n = len(chans[0])
    first, last = n, -1
    for x in chans:
        if np is not None:
            idx = np.nonzero(np.abs(np.asarray(x)) > thr)[0]
            if len(idx):
                first, last = min(first, int(idx[0])), max(last, int(idx[-1]))
        else:
            for i, v in enumerate(x):
                if abs(v) > thr:
                    first = min(first, i)
                    break
            for i in range(n - 1, -1, -1):
                if abs(x[i]) > thr:
                    last = max(last, i)
                    break
    if last < 0:
        return None, None
    return round(first / rate * 1000, 1), round((n - 1 - last) / rate * 1000, 1)


def dc_offset(chans):
    return max(abs(float(np.mean(x))) if np is not None else abs(sum(x) / len(x)) for x in chans) if len(chans[0]) else 0.0


def seam(chans, rate):
    """Loop wrap. ratio = the last->first step over the largest step within 20 ms either side of the wrap (a click
    shows as ratio > 2 with jump > 0.01); level_db = RMS difference of the 200 ms either side (information only:
    rhythmic loops differ by design)."""
    k, w = max(2, int(0.02 * rate)), max(2, int(0.2 * rate))
    worst = {"jump": 0.0, "ratio": 0.0, "level_db": 0.0}
    for x in chans:
        x = [float(v) for v in x[-k:]] + [float(v) for v in x[:k]] if np is None else np.concatenate([x[-k:], x[:k]])
        d = [abs(x[i + 1] - x[i]) for i in range(len(x) - 1)]
        jump = d[k - 1]
        near = max(d[:k - 1] + d[k:]) if np is None else float(max(np.max(d[:k - 1]), np.max(d[k:])))
        ratio = jump / near if near > 0 else (0.0 if jump == 0 else 99.0)
        worst["jump"] = max(worst["jump"], round(float(jump), 4))
        worst["ratio"] = max(worst["ratio"], round(float(ratio), 2))
    for x in chans:
        head = math.sqrt(sum(float(v) ** 2 for v in x[:w]) / w)
        tail = math.sqrt(sum(float(v) ** 2 for v in x[-w:]) / w)
        worst["level_db"] = max(worst["level_db"], round(abs(db(head, -120) - db(tail, -120)), 2))
    return worst


def phone_loss(chans, rate):
    """dB of momentary-max loudness lost through a rough phone-speaker model (4th-order high-pass at 450 Hz,
    2nd-order low-pass at 10 kHz). None without numpy."""
    if np is None:
        return None
    full = loudness(chans, rate)["m_max"]
    out = []
    for x in chans:
        x = np.asarray(x)
        nfft = 1 << math.ceil(math.log2(2 * len(x) + 1))
        f = np.fft.rfftfreq(nfft, 1 / rate)
        H = 1 / np.sqrt(1 + (450 / np.maximum(f, 1e-9)) ** 8) / np.sqrt(1 + (f / 10000) ** 4)
        out.append(np.fft.irfft(np.fft.rfft(x, nfft) * H, nfft)[:len(x)])
    return round(full - loudness(out, rate)["m_max"], 2)


BANDS = [("sub", 0, 150), ("low", 150, 400), ("phone", 400, 5000), ("air", 5000, 1e9)]


def spectrum(chans, rate):
    """Power share per band, spectral centroid (Hz) and L/R correlation; None without numpy."""
    if np is None:
        return None
    x = np.mean(np.stack([np.asarray(c) for c in chans]), axis=0)
    nfft = 4096
    if len(x) < nfft:
        x = np.pad(x, (0, nfft - len(x)))
    win = np.hanning(nfft)
    frames = range(0, len(x) - nfft + 1, nfft // 2)
    P = np.zeros(nfft // 2 + 1)
    for s in frames:
        P += np.abs(np.fft.rfft(x[s:s + nfft] * win)) ** 2
    f = np.fft.rfftfreq(nfft, 1 / rate)
    tot = float(P[1:].sum()) or 1.0
    bands = {name: round(float(P[(f >= lo) & (f < hi)].sum()) / tot, 3) for name, lo, hi in BANDS}
    cen = float((f * P).sum() / (P.sum() or 1.0))
    corr = None
    if len(chans) >= 2 and len(chans[0]) > 1:
        a, b = np.asarray(chans[0]), np.asarray(chans[1])
        if a.std() > 0 and b.std() > 0:
            corr = round(float(np.corrcoef(a, b)[0, 1]), 3)
    return {"bands": bands, "centroid_hz": round(cen), "corr": corr}


def measure(path, loop=False):
    """Everything sound.py analyze needs, as one dict. Header-only (decoded False) when no decoder is available."""
    d = load(path)
    rep = {"file": str(path), "format": d.get("format"), "codec": d.get("codec"), "bytes": d.get("bytes"),
           "decoded": d.get("decoded", False), "numpy": np is not None, "info": d.get("info", {})}
    if not rep["decoded"]:
        rep.update(rate=d["rate"], nch=d["nch"], bits=d.get("bits"), duration=round(d["duration"], 3),
                   note="no decoder: length and format only; export WAV or install ffmpeg for loudness")
        return rep
    chans, rate = d["channels"], d["rate"]
    n = len(chans[0])
    rep.update(rate=d.get("src_rate", rate), decode_rate=rate, nch=len(chans), bits=d.get("bits"),
               float=d.get("float"), duration=round(n / rate, 4))
    if n == 0:
        rep["note"] = "empty audio"
        return rep
    rep.update(loudness(chans, rate))
    sp = sample_peak(chans)
    rep["sample_peak"] = round(db(sp), 2)
    rep["true_peak"] = true_peak(chans)
    rep["clip_runs"] = clip_runs(chans)
    rep["dc"] = round(dc_offset(chans), 5)
    rep["lead_ms"], rep["tail_ms"] = edges(chans, rate)
    if loop:
        rep["seam"] = seam(chans, rate)
    sp = spectrum(chans, rate)
    if sp:
        rep.update(sp)
        rep["phone_loss_db"] = phone_loss(chans, rate)
    return rep


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--loop", action="store_true", help="also measure the loop seam")
    a = ap.parse_args(argv)
    out = []
    for f in a.files:
        try:
            out.append(measure(f, loop=a.loop))
        except (AudioError, OSError, struct.error) as e:
            out.append({"file": f, "error": str(e)})
    if a.json:
        print(json.dumps(out, indent=1))
    else:
        for r in out:
            print(json.dumps(r))
    return 1 if any("error" in r for r in out) else 0


if __name__ == "__main__":
    sys.exit(main())
