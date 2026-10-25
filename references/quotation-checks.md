# Mechanical quotation checks

Use `scripts/check_quotes.py` before recording fresh quotations as source
evidence in citation checks, uncited-claim investigations, or novelty leads.
The checker establishes **textual presence in one supplied local extraction**.
It does not decide whether the passage supports the claim, whether a source
is the correct work, or whether an omission changes its meaning. Read the
passage and surrounding context separately under `literature-checks.md`.

## Prepare the source

1. Retrieve, identify, read, and archive the actual source under
   `source-archive.md`. Use that version's text, never model memory or search
   snippets. For a PDF or HTML archive, prepare an inspected visible-text
   UTF-8 extraction using the available extraction tool. This prototype does
   not fetch sources, parse PDF/HTML, or perform OCR.
2. Keep extracts and input files in the host's permitted literature store,
   under the same privacy and license rules as the source. A cloud archive
   may need a permitted local staging copy. Do not create local restricted
   copies when the store policy prohibits them; use the existing manual
   quotation check and disclose the unavailable mechanical check instead.
3. Record the original archive hash, extraction command/tool, and extracted
   text hash. The checker reports the SHA-256 of the **text file's bytes**;
   that hash is not the PDF hash or proof of faithful extraction. If the
   text hash was already recorded, pass it as `--expected-sha256`.
4. Check against the retrieved text **before** creating a quotes-only
   artifact. Matching against a file made by copying the proposed quotations
   into it is circular and cannot validate those quotations. A quotes-only
   archive cannot independently check itself.

Do not alter the manuscript, bibliography, or original source. Do not write
runtime artifacts into the installed skill. If no shell/Python 3 is available,
compare quotations manually against the retrieved text and disclose that the
mechanical checker was not run. Retrieval and archive requirements still apply.

## Invoke from the manuscript checkout

Resolve the installed skill's absolute directory from the skill location.
Replace `/path/to/citation-needed` below with it; source/input paths are in
the host checkout, not relative to the installed script.

Write a UTF-8 JSON array of proposed evidence quotations using a file tool
(avoid interpolating source text into shell commands). Include only the
literal quotation, without surrounding display quotation marks, the locator,
or the agent's explanation:

```json
[
  {"id": "claim-1/source-a", "quote": "The treatment did not improve accuracy."},
  {"id": "claim-2/source-a", "quote": "We observed five failures."}
]
```

Run one batch per source extraction:

```bash
python3 /path/to/citation-needed/scripts/check_quotes.py \
  --source literature/sources/source-a.txt \
  --quotes-json literature/quote-input-a.json
```

For one quotation, `--quote-file literature/quote.txt` accepts a UTF-8 file
instead. `--quote` accepts one literal command-line argument, but prefer files
for text containing shell syntax. The script reads local files and prints
JSON to stdout; it performs no network requests and writes no files. Keep
any saved output private or ignored as the source's storage rules require:
the output includes quotations and short surrounding context.

## Interpret the output

- **`exact`**: all occurrences are literal and all their locations are returned.
- **`normalized`**: it occurs after Unicode NFC composition, whitespace
  collapsing (including line wraps and nonbreaking spaces), curly single/
  double quote conversion, and common Latin `ff/fi/fl/ffi/ffl` ligature
  expansion. Case, wording, numeric values, dashes, and other punctuation
  remain significant. Review the returned original `source_text` and each
  location's `mode`. Mixed exact/normalized occurrences and results whose
  locations were truncated are conservatively reported as `normalized`.
- **`not_found`**: inspect the original source, version, and extraction.
  Correct a miscopied quotation from retrieved text and rerun, or report
  that it could not be mechanically confirmed. Do not silently paraphrase
  inside quotation marks or turn this result into an `unsupported` verdict.
- **`manual_review`**: the full quotation was not found and contains an
  ellipsis or bracketed edit. The checker never treats those as wildcards.
  Check its verbatim fragments individually, and read the complete passage
  to judge omissions and edits. A literal source ellipsis/bracket can still
  produce an exact/normalized match when the full text occurs.
- **`error`**: invalid/missing input or an expected-hash mismatch; the check
  did not run successfully. Fix the input or disclose the limitation.

The process exits **0** when every quote is found, **1** when at least one
needs review, and **2** for an invocation/input error. An exit 1 is a usable
report, not a crashed checker; inspect every result in a mixed batch. The
JSON schema is `citation-needed.quote-check/1`. Each result includes the
input id, status, original-text locations, and total occurrence count. Up
to ten locations are returned; use the manuscript's cited page/section and
the surrounding context to choose the right occurrence, never the first
match automatically. Offsets are zero-based character ranges in the original
decoded text with an exclusive end; lines are one-based extraction lines,
not PDF page numbers. Word/number boundaries prevent matches inside larger
words, signed numbers, and decimals; no fuzzy matching or OCR correction is
attempted. A miss can reflect extraction problems, especially hyphenated
line breaks or scanned text.

Confirm the page/section locator against the original source. Record the
checked text's hash, quote ids, statuses, and any manual review in the ledger
entry's `notes:` field, keeping the actual evidence passage and locator in
`evidence:`. Workers return these results with their source material; the
coordinator validates them before writing the ledger and final report. Do
not label a manually checked quotation as a script-confirmed match. A found
quotation can still be irrelevant, misleading out of context, or from the
wrong source: decide support separately.
