#!/usr/bin/env python3
"""Check quotation presence in a local UTF-8 source extraction; no network or writes.

Exit 0: every quotation found. Exit 1: at least one needs review.
Exit 2: input/invocation error. A match is not a citation-support verdict.
"""

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path


SCHEMA = "citation-needed.quote-check/1"
MAX_LOCATIONS = 10
TYPOGRAPHY = str.maketrans({
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi", "\ufb04": "ffl",
})
LIMITATION = (
    "Presence in this supplied text does not establish source identity, retrieval, "
    "extraction fidelity, contextual accuracy, or support for the manuscript claim."
)


def normalize(text):
    """Return normalized text and original [start, end) spans per output character."""
    out, spans = [], []

    def emit(cluster, start, end):
        for char in unicodedata.normalize("NFC", cluster.translate(TYPOGRAPHY)):
            if char.isspace():
                if out and out[-1] == " ":
                    spans[-1] = (spans[-1][0], end)
                    continue
                char = " "
            out.append(char)
            spans.append((start, end))

    cluster, start = "", 0
    for i, char in enumerate(text):
        # Keep combining marks and Hangul composition together for original offsets.
        if cluster and not unicodedata.combining(char):
            joins = (unicodedata.normalize("NFC", cluster + char)
                     != unicodedata.normalize("NFC", cluster) + char)
            if not joins:
                emit(cluster, start, i)
                cluster, start = "", i
        if not cluster:
            start = i
        cluster += char
    if cluster:
        emit(cluster, start, len(text))
    # Outer whitespace is not part of the search, but preserve offsets into the source.
    lo = 1 if out and out[0] == " " else 0
    hi = len(out) - (1 if out and out[-1] == " " else 0)
    return "".join(out[lo:hi]), spans[lo:hi]


def word_char(char):
    return char.isalnum() or char == "_" or bool(unicodedata.combining(char))


def bounded(text, quote, start, end):
    """Avoid matching part of a word, identifier, signed number or decimal."""
    if word_char(quote[0]) and start and word_char(text[start - 1]):
        return False
    if word_char(quote[-1]) and end < len(text) and word_char(text[end]):
        return False
    starts_number = quote[0].isdigit() or (
        len(quote) > 1 and quote[0] in ".," and quote[1].isdigit())
    if starts_number and start:
        prev = text[start - 1]
        if prev in "+-\u2212":
            return False
        if quote[0].isdigit() and prev in ".,":
            return False
    if quote[-1].isdigit() and end + 1 < len(text):
        if text[end] in ".," and text[end + 1].isdigit():
            return False
    if (len(quote) > 1 and quote[-1] in ".," and quote[-2].isdigit()
            and end < len(text) and text[end].isdigit()):
        return False
    if (len(quote) > 1 and quote[0] in ".," and quote[1].isdigit()
            and start and text[start - 1].isdigit()):
        return False
    return True


def occurrences(text, quote):
    found = []
    count, pos = 0, 0
    while True:
        start = text.find(quote, pos)
        if start < 0:
            return count, found
        end = start + len(quote)
        if bounded(text, quote, start, end):
            count += 1
            if len(found) < MAX_LOCATIONS:
                found.append((start, end))
        pos = start + 1


def location(source, start, end):
    return {
        "start": start, "end": end,
        "line_start": source.count("\n", 0, start) + 1,
        "line_end": source.count("\n", 0, end - 1) + 1,
        "source_text": source[start:end],
        "context": source[max(0, start - 80):min(len(source), end + 80)],
    }


def check_quote(source, quote, quote_id, normalized_source=None):
    if not isinstance(quote, str) or not quote.strip():
        raise ValueError("quotation must be a nonempty string")
    result = {"id": quote_id, "quote": quote, "locations": [], "occurrences": 0}
    normalized, spans = normalized_source if normalized_source is not None else normalize(source)
    needle, _ = normalize(quote)
    if not needle:
        raise ValueError("quotation is empty after normalization")
    count, hits = occurrences(normalized, needle)
    matches = [(spans[a][0], spans[b - 1][1]) for a, b in hits]
    if count:
        locations = [location(source, a, b) for a, b in matches]
        for loc in locations:
            loc["mode"] = "exact" if loc["source_text"] == quote else "normalized"
        # All accepted equivalents count, even if one of them is a literal hit.
        # With truncated locations, conservatively report the batch as normalized.
        mode = "exact" if count == len(locations) and all(
            loc["mode"] == "exact" for loc in locations) else "normalized"
        result.update(status=mode, found=True, occurrences=count, locations=locations)
        if count > 1:
            result["review"] = "Multiple occurrences: confirm which passage the citation refers to."
    else:
        edited = bool(re.search(r"\.{3}|\u2026|\[[^\]]*\]", quote))
        result.update(
            status="manual_review" if edited else "not_found", found=False,
            reason=("Omissions or bracketed edits are not matched as wildcards; check each "
                    "verbatim fragment separately and review the full context." if edited else
                    "Not found in the supplied extraction. Inspect source/version/extraction; "
                    "this is not an unsupported-claim verdict."),
        )
    return result


def read_text(path, source=False):
    raw = path.read_bytes()
    if source and (path.suffix.lower() in {".pdf", ".html", ".htm"}
                   or raw.startswith(b"%PDF-")):
        raise ValueError("source must be extracted visible UTF-8 text, not PDF or HTML")
    text = raw.decode("utf-8")
    if not text.strip() or "\x00" in text:
        raise ValueError("input must be nonempty UTF-8 text without NUL bytes")
    return raw, text


def quotations(args):
    if args.quote is not None:
        entries = [{"id": "1", "quote": args.quote}]
    elif args.quote_file is not None:
        _, text = read_text(args.quote_file)
        entries = [{"id": "1", "quote": text}]
    else:
        _, text = read_text(args.quotes_json)
        entries = json.loads(text)
        if not isinstance(entries, list) or not entries:
            raise ValueError("quotes JSON must be a nonempty array")
    output, seen = [], set()
    for i, entry in enumerate(entries, 1):
        if isinstance(entry, str):
            entry = {"id": str(i), "quote": entry}
        if not isinstance(entry, dict) or set(entry) - {"id", "quote"}:
            raise ValueError("each quotation must be a string or an object with id/quote fields")
        quote_id, quote = entry.get("id", str(i)), entry.get("quote")
        if not isinstance(quote_id, str) or not quote_id.strip() or quote_id in seen:
            raise ValueError("quotation ids must be unique, nonempty strings")
        if not isinstance(quote, str) or not quote.strip():
            raise ValueError("each quotation must be a nonempty string")
        seen.add(quote_id)
        output.append((quote_id, quote))
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="local UTF-8 source extraction")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--quote", help="literal quotation without enclosing display quotes")
    group.add_argument("--quote-file", type=Path, help="UTF-8 file containing one literal quotation")
    group.add_argument("--quotes-json", type=Path, help="nonempty array of strings or {id, quote} objects")
    parser.add_argument("--expected-sha256", help="expected hash of the source TEXT file, not its PDF")
    args = parser.parse_args(argv)
    try:
        entries = quotations(args)
        raw, source = read_text(args.source, source=True)
        digest = hashlib.sha256(raw).hexdigest()
        if args.expected_sha256 is not None:
            if not re.fullmatch(r"[0-9a-fA-F]{64}", args.expected_sha256):
                raise ValueError("expected SHA-256 must contain exactly 64 hex characters")
            if args.expected_sha256.lower() != digest:
                raise ValueError("source SHA-256 does not match the expected text hash")
        normalized = normalize(source)
        results = [check_quote(source, quote, qid, normalized) for qid, quote in entries]
        report = {
            "schema": SCHEMA,
            "source": {"path": str(args.source), "sha256": digest, "bytes": len(raw)},
            "normalization": "NFC, whitespace collapse, curly quotation marks, common Latin ligatures",
            "offsets": "zero-based Python character offsets into original decoded text; end exclusive; lines one-based",
            "locations_limit": MAX_LOCATIONS,
            "results": results,
            "summary": {"total": len(results), "found": sum(r["found"] for r in results)},
            "limitation": LIMITATION,
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if all(r["found"] for r in results) else 1
    except (OSError, UnicodeError, ValueError) as error:
        print(json.dumps({"schema": SCHEMA, "status": "error", "error": str(error)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
