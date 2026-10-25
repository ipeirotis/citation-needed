# Agent guide: developing citation-needed

This repository is a standalone agent skill for retrieval-grounded literature
checks: verifying that a manuscript's citations support the claims attached to
them, investigating uncited factual claims, and scanning stated contributions
for overlapping prior work — it resolves every "[citation needed]" against
sources it actually retrieves and reads. It was extracted from the scholar
lane of [blue-pencil](https://github.com/ipeirotis/blue-pencil) (whose dispatch
command is `/paper:verify-citations`, formerly `/paper:scholar`) so it can
ship and evolve independently of that editorial skill. The skill was named
paper-scholar at extraction, then chapter-and-verse, before settling on
citation-needed — old references to those names denote this repo.

## Layout

- `SKILL.md` — entry point and trigger description; keep it short and route
  depth to `references/`.
- `references/literature-checks.md` — the core protocol: inventory claims,
  consult the ledger, verify citations, scan novelty, report.
- `references/bibliography-audit.md` — the standalone metadata audit: does
  each bibliography entry identify a real work, checked against the DOI
  registrars; no sources read, no claims judged.
- `references/version-reconciliation.md` — the proactive version sweep:
  detect when a source read as a preprint or partial text has a published or
  fuller version, diff the texts, and prompt re-checks; no verdict changes.
- `references/source-archive.md` — locator (DOI/URL) requirements, legal
  full-text retrieval, and where archived copies go (bucket or repo folder).
- `references/verification-ledger.md` — the dated results ledger written into
  host repos, its reuse rules, and the opt-in JSONL companion for tooling.
- `agents/openai.yaml` — interface metadata for non-Claude agent platforms.
- `scripts/check_quotes.py` — read-only UTF-8 quotation-presence checker;
  `references/quotation-checks.md` defines its use and limitations.
- `evals/` — the eval suite: fixture manuscripts and bibliographies with
  verified ground truth (`evals/README.md` records the provenance),
  `evals.json` prompts and assertions for the skill-creator eval loop.
  Run results and workspaces stay outside this repo.
- `tasks.md` — the feature tracker (see below).

## Two repos to keep straight

This repo holds the skill. A **host repo** is the manuscript repository the
skill runs inside at verification time. Artifacts the skill creates at run
time — `literature/sources/`, `literature/verifications.md`, the pointer
section in the host `AGENTS.md` — belong to host repos and must never appear
here. Files here describe behavior; files there are that behavior's output.

## Working on the skill

- Read `tasks.md` before starting: it is the feature tracker. Record new
  feature requests there with a date; when work lands, move the item to Done
  with the date and the files that implement it.
- The `description` frontmatter in `SKILL.md` is the trigger — keep it in sync
  with capabilities whenever behavior changes.
- Preserve the integrity model in any edit: retrieved-not-remembered (a
  memory-cited source is fabrication), leads-not-verdicts for novelty,
  inaccessible ≠ unsupported, never edit the manuscript or bibliography, never
  bypass paywalls.
- Blue-pencil's `/paper:verify-citations` began as the same protocol, but
  the author decided (2026-08-15, recorded in `tasks.md`) that the two
  projects evolve independently: do not track, upstream, or downstream
  changes between them. This repo is authoritative for its own behavior,
  and divergence from blue-pencil is accepted.
