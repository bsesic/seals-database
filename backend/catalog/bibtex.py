"""Minimal, dependency-free BibTeX parsing + import for Publications.

Handles the realistic subset produced by Zotero / Google Scholar / JabRef:
multiple ``@type{key, field = {value} | "value" | bare, ...}`` entries with
balanced nested braces. Not a full BibTeX engine — ``@string`` macros,
``@preamble`` and cross-references are ignored (entries of those types are
skipped). Good enough for a research bibliography; values can be corrected in
the admin afterwards.
"""

import re
import unicodedata

from catalog.models import Publication

_SKIP_TYPES = {"comment", "preamble", "string"}

# LaTeX accent command -> Unicode combining mark.
_COMBINING = {
    '"': "̈", "'": "́", "`": "̀", "^": "̂", "~": "̃",
    "=": "̄", ".": "̇", "v": "̌", "c": "̧", "u": "̆",
    "H": "̋", "r": "̊",
}
_ACCENT_RE = re.compile(
    r"\\([" + re.escape('"' + "'" + "`^~=.vcuHr") + r"])\s*\{?\s*([A-Za-z])\s*\}?"
)
# Standalone LaTeX letter/symbol commands.
_SPECIALS = {
    r"\ss": "ß", r"\o": "ø", r"\O": "Ø", r"\ae": "æ", r"\AE": "Æ", r"\oe": "œ",
    r"\OE": "Œ", r"\aa": "å", r"\AA": "Å", r"\l": "ł", r"\L": "Ł",
    r"\&": "&", r"\%": "%", r"\_": "_", r"\#": "#", r"\$": "$",
}


def _delatex(s):
    """Decode common LaTeX accents/escapes, e.g. ``{\\"o}`` -> ``ö``."""
    def repl(m):
        return unicodedata.normalize("NFC", m.group(2) + _COMBINING[m.group(1)])

    s = _ACCENT_RE.sub(repl, s)
    for key in sorted(_SPECIALS, key=len, reverse=True):
        s = s.replace(key, _SPECIALS[key])
    return s


def _read_braced(text, open_idx):
    """Given index of an opening '{', return (index_after_close, inner_text)."""
    depth = 0
    for i in range(open_idx, len(text)):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i + 1, text[open_idx + 1:i]
    return len(text), text[open_idx + 1:]


def _split_top_level(body):
    """Split a field body on top-level commas (not inside {} or "")."""
    parts, depth, in_quote, buf = [], 0, False, []
    for c in body:
        if c == "{":
            depth += 1
        elif c == "}":
            depth = max(0, depth - 1)
        elif c == '"' and depth == 0:
            in_quote = not in_quote
        if c == "," and depth == 0 and not in_quote:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(c)
    if buf:
        parts.append("".join(buf))
    return parts


def _clean_value(raw):
    v = raw.strip()
    if v.startswith("{") and v.endswith("}"):
        v = v[1:-1]
    elif v.startswith('"') and v.endswith('"'):
        v = v[1:-1]
    v = _delatex(v)
    v = v.replace("{", "").replace("}", "")
    v = re.sub(r"\s+", " ", v).strip()
    return v


def parse_bibtex(text):
    """Parse BibTeX text into a list of dicts.

    Each dict: ``entry_type``, ``key``, ``raw`` and lowercase field names
    (title, author, year, journal, ...).
    """
    entries = []
    i = 0
    while True:
        at = text.find("@", i)
        if at == -1:
            break
        brace = text.find("{", at)
        if brace == -1:
            break
        entry_type = text[at + 1:brace].strip().lower()
        end, inner = _read_braced(text, brace)
        i = end
        if entry_type in _SKIP_TYPES or not entry_type:
            continue
        chunks = _split_top_level(inner)
        if not chunks:
            continue
        entry = {"entry_type": entry_type, "key": chunks[0].strip(), "raw": text[at:end]}
        for chunk in chunks[1:]:
            if "=" not in chunk:
                continue
            name, _, value = chunk.partition("=")
            name = name.strip().lower()
            if name:
                entry[name] = _clean_value(value)
        if entry["key"]:
            entries.append(entry)
    return entries


def _format_author(name):
    """Normalise one author to 'Surname, First' order."""
    name = name.strip()
    if not name:
        return ""
    if "," in name:
        return name
    parts = name.split()
    if len(parts) == 1:
        return parts[0]
    return f"{parts[-1]}, {' '.join(parts[:-1])}"


def _authors_list(entry):
    raw = entry.get("author") or entry.get("editor") or ""
    return [_format_author(a) for a in re.split(r"\s+and\s+", raw) if a.strip()]


def format_din(entry):
    """Best-effort DIN-1505-style citation string from a parsed entry."""
    authors = _authors_list(entry)
    if len(authors) > 3:
        author_str = f"{authors[0]} [u.a.]"
    else:
        author_str = "; ".join(authors)

    title = entry.get("title", "")
    year = entry.get("year", "")
    bits = []
    if author_str:
        bits.append(f"{author_str}: ")
    bits.append(title.rstrip(".") + "." if title else "")

    etype = entry["entry_type"]
    if etype == "article":
        host = entry.get("journal", "")
        vol = entry.get("volume", "")
        num = entry.get("number", "")
        tail = f" In: {host}" if host else ""
        if vol:
            tail += f" {vol}"
        if num:
            tail += f".{num}"
        if year:
            tail += f" ({year})"
        if entry.get("pages"):
            tail += f", S. {entry['pages'].replace('--', '–')}"
        bits.append(tail + "." if tail else "")
    elif etype in ("incollection", "inproceedings", "inbook"):
        host = entry.get("booktitle", "")
        tail = f" In: {host}" if host else ""
        place, pub = entry.get("address", ""), entry.get("publisher", "")
        loc = ": ".join(x for x in (place, pub) if x)
        if loc:
            tail += f". {loc}"
        if year:
            tail += f", {year}"
        if entry.get("pages"):
            tail += f", S. {entry['pages'].replace('--', '–')}"
        bits.append(tail + "." if tail else "")
    else:  # book, misc, thesis, ...
        place, pub = entry.get("address", ""), entry.get("publisher", "")
        loc = " : ".join(x for x in (place, pub) if x)
        tail = ""
        if loc:
            tail += f" {loc}"
        if year:
            tail += f", {year}" if loc else f" {year}"
        bits.append(f"{tail}." if tail.strip() else "")

    return re.sub(r"\s+", " ", "".join(bits)).strip()


def apply_entry(entry, pub):
    """Populate a Publication from a parsed entry (does not save)."""
    pub.bibtex_key = entry["key"]
    pub.bibtex_raw = entry.get("raw", pub.bibtex_raw)
    pub.entry_type = entry["entry_type"]
    pub.title = entry.get("title", "")
    pub.authors = "; ".join(_authors_list(entry))
    year = entry.get("year", "")
    m = re.search(r"\d{4}", year)
    pub.year = int(m.group()) if m else None
    pub.doi = entry.get("doi", "")
    pub.url = entry.get("url", "")
    pub.citation_din = format_din(entry)
    return pub


def import_bibtex(text):
    """Upsert Publications from BibTeX text (keyed on ``bibtex_key``).

    Returns ``(created, updated, errors)`` where errors is a list of strings.
    """
    created, updated, errors = 0, 0, []
    for entry in parse_bibtex(text):
        try:
            pub = Publication.objects.filter(bibtex_key=entry["key"]).first()
            is_new = pub is None
            if is_new:
                pub = Publication(bibtex_key=entry["key"])
            apply_entry(entry, pub)
            pub.save()
            created += is_new
            updated += not is_new
        except Exception as exc:  # noqa: BLE001 — report, keep importing
            errors.append(f"{entry.get('key', '?')}: {exc}")
    return created, updated, errors
