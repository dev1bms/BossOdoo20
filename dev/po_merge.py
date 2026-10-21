"""Merge an Odoo .pot into a module's <lang>.po, keeping existing translations.

    python dev/po_merge.py <template.pot> <addon_dir> <lang> [new_terms.json ...]

`lang` is the file name (es, ar). new_terms.json: {"msgid": {"es": "...", "ar": "..."}}.
Untranslated entries are listed on stderr; they stay empty (Odoo then shows the source text).
"""
import json
import re
import sys
from pathlib import Path

HEADER = {"es": "Spanish (es_ES)", "ar": "Arabic (ar_001)"}


def unquote(lines):
    return "".join(json.loads(line) for line in lines)


def quote(text):
    if "\n" not in text[:-1] and len(text) < 70:
        return json.dumps(text, ensure_ascii=False)
    parts = re.findall(r"[^\n]*\n|[^\n]+$", text)
    return '""\n' + "\n".join(json.dumps(p, ensure_ascii=False) for p in parts)


def parse(path):
    """Return [(comments, msgid, msgstr)] of a .po/.pot file (header entry excluded)."""
    entries, comments, key, buf = [], [], None, {"msgid": [], "msgstr": []}
    text = Path(path).read_text(encoding="utf-8") if Path(path).exists() else ""
    for line in text.splitlines() + [""]:
        if line.startswith("#"):
            comments.append(line)
        elif line.startswith(("msgid ", "msgstr ")):
            key, rest = line.split(" ", 1)
            buf[key] = [rest]
        elif line.startswith('"') and key:
            buf[key].append(line)
        elif not line.strip() and key:
            msgid = unquote(buf["msgid"])
            if msgid:
                entries.append((comments, msgid, unquote(buf["msgstr"])))
            comments, key, buf = [], None, {"msgid": [], "msgstr": []}
    return entries


def main(pot, addon, lang, *extra):
    out_path = Path(addon) / "i18n" / f"{lang}.po"
    known = {msgid: msgstr for _c, msgid, msgstr in parse(out_path) if msgstr}
    for path in extra:
        for msgid, tr in json.loads(Path(path).read_text(encoding="utf-8")).items():
            if tr.get(lang):
                known.setdefault(msgid, tr[lang])
    module = Path(addon).name
    lines = [f"# Translation of BOSS module {module}: {HEADER.get(lang, lang)}.",
             'msgid ""', 'msgstr ""',
             '"Content-Type: text/plain; charset=UTF-8\\n"',
             '"Content-Transfer-Encoding: \\n"', ""]
    missing = []
    for comments, msgid, _ in parse(pot):
        msgstr = known.get(msgid, "")
        if not msgstr and not msgid.startswith(("Display Name", "ID", "Last ", "Created ")):
            missing.append(msgid)
        lines += comments + [f"msgid {quote(msgid)}", f"msgstr {quote(msgstr)}", ""]
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"{out_path}: {len(missing)} untranslated", file=sys.stderr)
    for msgid in missing:
        print("  -", msgid[:90].replace("\n", " "), file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:])
