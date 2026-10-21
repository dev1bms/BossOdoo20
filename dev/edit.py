"""Exact text replacement keeping UTF-8 and LF (Windows text mode would write CRLF)."""
from pathlib import Path


def edit(path, *pairs):
    p = Path(path)
    s = p.read_bytes().decode("utf-8")
    for old, new in pairs:
        if old not in s:
            raise ValueError(f"{path}: not found: {old[:80]!r}")
        s = s.replace(old, new)
    p.write_bytes(s.encode("utf-8"))
