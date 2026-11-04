# Thirty real-paper quotation manuscripts

Thirty distinct **PLOS ONE research articles published in 2023**, retrieved from
Europe PMC's public full-text XML API on 2026-11-04. Each article's own JATS
license statement explicitly grants **CC BY 4.0** redistribution. Titles,
authors, DOI, PMCID, retrieval URL and XML/text hashes are in `manifest.json`.
This is a convenience sample from one publisher/year, not a representative
sample of research literature.

## What a manuscript is

`manuscripts/M01.md` through `M30.md` are **modified evaluation adaptations**,
not authentic drafts written by the original authors. The complete extracted
abstract/body prose is retained except that six selected sentences are turned
into explicitly attributed quotation blocks, with controlled alterations.
The manuscript header announces these modifications and preserves attribution.
Tables, figures, reference lists and peer-review attachments are excluded.
JATS extraction is plain text, not a faithful rendering of mathematics or PDF
layout. This experiment targets only the six labelled prose quotation blocks.

`sources/M01.txt` through `M30.txt` preserve the unaltered extraction, including
stable paragraph IDs and section names. This supplied local text is the pinned
reference for both agent conditions. Runtime archives must reproduce its bytes;
copying proposed quotations into a new file cannot satisfy the archive gate.

Each manuscript has six targets (180 in total):

| Kind | Per manuscript | Total | Final judgment |
|---|---:|---:|---|
| Accurate, unchanged quotation | 1 | 30 | Valid |
| Harmless whitespace formatting | 1 | 30 | Valid |
| Altered wording | 1 | 30 | Invalid as a direct quotation |
| Altered number | 1 | 30 | Invalid |
| Ellipsis removing a negation | 1 | 30 | Invalid: meaning changes |
| Intact complete sentence with trailing ellipsis | 1 | 30 | Valid shortened quotation |

Formatting varies among line wraps, nonbreaking spaces and repeated spaces.
Quotation IDs are permuted deterministically per manuscript: Q1 is not always
the same category. All targets come from distinct paragraphs within a paper.
There are 90 valid controls and 90 defects. Numeric edits include years, sample
sizes, quantities and identifiers, not just reported statistical results.

## Answer key and review

`answer-key.json` records every original passage, altered quote, paragraph,
manuscript line, complete claim/hash, expected verdict and rationale.
Ground truth is the retrieved source, not model memory or the tested checker.
Original/mutated text and surrounding paragraphs received source-grounded Codex
review; **there is no independent human sign-off**. Omission labels specifically
contrast removal of an explicit negation with retention of a complete sentence.
The published key makes this an open development benchmark, not a hidden test.
All cases are baseline cases; no unseen/held-out evaluation is claimed.

The expected *script status* is a separate label from the final judgment.
The prototype sends omissions and bracket-containing nonmatches to review;
`manual_review` is never treated as proof that an omission is misleading.
This includes ordinary reference brackets inside a changed quotation.

## Reproduce

The published extracted texts permit offline validation without re-downloading:

```bash
python3 -B -m evals.quotation_benchmark.validate --output-dir /tmp/quotation-checks
```

To fetch the exact original XML snapshots into an external cache:

```bash
python3 -B -m evals.quotation_benchmark.fetch_sources --cache /tmp/quotation-source-cache
python3 -B -m evals.quotation_benchmark.build_dataset \
  --cache /tmp/quotation-source-cache \
  --candidates /tmp/quotation-source-cache/candidates.json
```

The fetcher verifies XML hashes and fails if the live source changed. Building
resets contextual review fields to pending; review them again before publishing.
Do not silently update a source, its extraction or its key to improve a score.

## Attribution and license

All original article prose remains under each article's CC BY 4.0 license.
The source files and manifest name every original author, title and DOI and
link the license. Evaluation modifications by Arin Jain's SPUR project are
also offered under CC BY 4.0. No original author endorsement is implied.
Executable benchmark code follows the repository's existing code license.

API documentation: https://europepmc.org/RestfulWebService
