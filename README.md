# citation-needed

A retrieval-grounded agent skill for verifying manuscript citations,
investigating uncited factual claims, finding prior-work leads relevant to
novelty claims, and auditing bibliography metadata against the DOI registrars
to catch mangled or fabricated references — it resolves every
"[citation needed]" in your manuscript against sources it actually retrieves
and reads. It also keeps past verifications honest: a ledger sweep detects
when a preprint it verified against has since been published and flags the
claims whose evidence sat in text that changed.

## Install

Copy or clone this repository into your agent's skills directory, for example:

```bash
git clone https://github.com/ipeirotis/citation-needed.git ~/.agents/skills/citation-needed
```

Then ask the agent to check specified citations or contribution claims, to
audit the bibliography's metadata, or to sweep the verification ledger for
preprints that have since been published. Checking claims requires literature
search and access to the actual source text; a bibliography audit needs only
live access to the DOI registrars and any URLs the entries carry; a version
sweep needs the detection channels its targets require — the registrars for
DOI-backed sources, a plain fetch for URL-backed ones — plus access to
fetch the fuller text it diffs.

## Usage

In Claude Code the skill name is the command — `/citation-needed` — and what
you hand it selects the capability:

```
/citation-needed paper.tex                       # audit every citation in the manuscript
/citation-needed sections/related.tex            # audit one section's citations
/citation-needed refs.bib                        # audit the bibliography's metadata
/citation-needed "It is well known that crowd labels converge with redundancy."
                                                 # find a source for an uncited claim
/citation-needed "We are the first to model X under Y."
                                                 # scan the claimed contribution for prior work
/citation-needed literature/verifications.md     # sweep the ledger for preprints since published
```

A manuscript or section file gets a citation audit; a bibliography file gets
a metadata audit against the DOI registrars; a quoted factual claim gets a
source investigation; a contribution statement gets a novelty scan; the
verification ledger itself gets a version sweep — has anything verified
against a preprint since been published, and which claims should be
re-checked?
When the scope is ambiguous, the skill asks one focused question before
retrieving anything. On agents without slash commands, plain requests work
the same way ("check whether the citations in section 3 support their
claims").

## What it writes into your repo

Verification is cumulative: the skill leaves an auditable record in the
manuscript repository it runs in.

- `literature/sources/` — a copy of the exact text it read for every source —
  the full text when legally obtainable, otherwise the abstract or page
  snapshot that was reachable — named by citation key and DOI, with SHA-256
  hashes recorded. If the project
  configures a cloud store (a `LITERATURE_STORE` env var or a `store:`
  line naming a `gs://` or `s3://` prefix), copies go there instead.
- `literature/verifications.md` — a dated, append-only ledger of every
  verification: the claim, its source's DOI or URL, the archived copy's hash,
  the verdict, and the supporting passage. Later runs reuse these entries
  instead of re-fetching, and your repo's `AGENTS.md` gets a short pointer
  section so other agents find them. If the ledger header declares a
  `companion:` file, a derived `literature/verifications.jsonl` is kept in
  lockstep — one JSON object per entry — for other tooling to consume; the
  Markdown remains the authoritative record.

Every source needs a publicly verifiable DOI or at minimum a stable URL. For
paywalled sources the skill asks you to supply the PDF (via your own access,
or print-to-PDF for web pages) rather than bypassing anything. Note that
committing paywalled PDFs to a public repo republishes them — the skill warns
and prefers a private bucket in that case.

## Safety model

The skill never verifies a source from memory, distinguishes inaccessible
sources from unsupported claims, treats novelty results as leads rather than
verdicts, and presents citation or wording changes only as proposals for the
author. It never edits the manuscript or its bibliography; the only files it
writes are the `literature/` artifacts and a pointer section in the repo's
agent-instructions file (`AGENTS.md`, or `CLAUDE.md` when that is what the
repo uses — and when the repo has neither, it proposes creating one rather
than writing it unasked), and it announces those writes in its report.

## Development

### Prototype quotation checker

The skill uses `scripts/check_quotes.py` to check fresh evidence quotations
against local UTF-8 text extracted from the retrieved source. It reports
literal or narrowly normalized matches with source locations, and flags
missing or edited quotations for review. It needs Python 3 and no additional
packages. It does not retrieve papers, read PDFs directly, or judge whether
the passage supports the manuscript's claim. See
[`references/quotation-checks.md`](references/quotation-checks.md) for input
formats, invocation, archive/extraction handling, and exit codes.

Run the offline checker tests with:

```bash
python3 -B -m unittest discover -s evals -p 'test_check_quotes.py' -v
```

See `AGENTS.md` for repo conventions and `tasks.md` for the feature tracker.
