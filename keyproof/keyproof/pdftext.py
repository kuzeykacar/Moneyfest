"""Get the visible text out of a PDF, on this computer only (no upload anywhere).

Uses pypdf when it is installed; otherwise a small built-in reader that handles the usual
text operators (Tj, TJ, ', ") in plain or Flate-compressed content streams.
"""

import re
import zlib


def extract_text(data: bytes, limit=6000) -> str:
    try:
        import io

        import pypdf  # optional
        r = pypdf.PdfReader(io.BytesIO(data))
        text = "\n".join((p.extract_text() or "") for p in r.pages[:4])
        if text.strip():
            return _tidy(text)[:limit]
    except Exception:
        pass
    return _tidy(_builtin(data))[:limit]


def _tidy(t):
    t = t.replace("\r", "\n")
    t = re.sub(r"[ \t]+", " ", t)
    return re.sub(r"\n\s*\n+", "\n", t).strip()


def _streams(data):
    for m in re.finditer(rb"<<(.{0,400}?)>>\s*stream\r?\n", data, re.S):
        start = m.end()
        end = data.find(b"endstream", start)
        if end < 0:
            continue
        raw = data[start:end].rstrip(b"\r\n")
        if b"FlateDecode" in m.group(1):
            try:
                raw = zlib.decompress(raw)
            except Exception:
                try:
                    raw = zlib.decompressobj().decompress(raw)
                except Exception:
                    continue
        elif b"/Filter" in m.group(1):
            continue                      # images and other encodings: no text
        yield raw


def _lit(s):
    out, i = bytearray(), 0
    esc = {b"n": b"\n", b"r": b"\r", b"t": b"\t", b"b": b"\b", b"f": b"\f"}
    while i < len(s):
        c = s[i:i + 1]
        if c == b"\\" and i + 1 < len(s):
            n = s[i + 1:i + 2]
            if n in esc:
                out += esc[n]; i += 2
            elif n.isdigit():
                m = re.match(rb"[0-7]{1,3}", s[i + 1:])
                out.append(int(m.group(0), 8) & 255); i += 1 + len(m.group(0))
            elif n in b"\r\n":
                i += 2
            else:
                out += n; i += 2
        else:
            out += c; i += 1
    return out.decode("cp1252", "replace")


STR = rb"\((?:\\.|[^\\)])*\)|<[0-9A-Fa-f\s]*>"


def _builtin(data):
    lines = []
    for s in _streams(data):
        if b"BT" not in s:
            continue
        cur = []
        for m in re.finditer(rb"(\[(?:" + STR + rb"|[^\]])*\])\s*TJ|(" + STR + rb")\s*(?:Tj|'|\")|(T\*|Td|TD|Tm|ET)\b", s):
            if m.group(3):
                if cur:
                    lines.append("".join(cur)); cur = []
                continue
            chunk = m.group(1) or m.group(2)
            for sm in re.finditer(STR, chunk):
                v = sm.group(0)
                if v.startswith(b"("):
                    cur.append(_lit(v[1:-1]))
                else:
                    h = re.sub(rb"\s", b"", v[1:-1])
                    try:
                        b = bytes.fromhex(h.decode() + ("0" if len(h) % 2 else ""))
                        cur.append(b.decode("utf-16-be", "replace") if len(b) % 2 == 0 and b[:1] == b"\x00" else b.decode("cp1252", "replace"))
                    except ValueError:
                        pass
        if cur:
            lines.append("".join(cur))
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    print(extract_text(open(sys.argv[1], "rb").read()))
