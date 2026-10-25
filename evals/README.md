# Eval suite

Test fixtures with known-good, known-bad, partially supported, and
unverifiable citations, used to benchmark the skill's classifications and
catch regressions via the skill-creator eval loop. `evals.json` holds the
prompts and assertions; the runner is the **Anthropic `skill-creator`
skill** (not part of this repo), whose loop spawns one with-skill and one
baseline subagent per eval, grades each assertion per its
`agents/grader.md`, aggregates with its `scripts/aggregate_benchmark.py`,
and builds the review viewer with its `eval-viewer/generate_review.py`. On
platforms without that skill, the same loop can be run by hand from those
four steps. Results and workspaces stay outside this repo.

## Ground truth provenance

Every expected verdict below was pinned against the live source or
registrar on **2026-08-16** — none of it comes from model memory. If a
fixture ever seems to misbehave, re-verify these facts first: registrar
records and pages can drift (Crossref's record for `10.18653/v1/N19-1423`
carried an empty title field on the verification date, for example).

### `fixtures/audit-manuscript/` (citation audit; expected verdicts)

| Claim in `paper.tex` | Expected | Ground truth (verified 2026-08-16) |
|---|---|---|
| Transformer big model reaches 28.4 BLEU on WMT 2014 EN-DE (`vaswani2017`) | supported | arXiv:1706.03762 abstract: "Our model achieves 28.4 BLEU on the WMT 2014 English-to-German translation task" |
| Transformer required substantially more training compute than prior recurrent models (`vaswani2017`) | unsupported | Same abstract states the opposite: "a small fraction of the training costs of the best models from the literature" |
| BERT reaches GLUE 80.5% and substantially reduces annotation costs in industry (`devlin2019`) | partially supported | arXiv:1810.04805 abstract states GLUE 80.5% (7.7% absolute improvement); the paper does not address annotation costs |
| Small numbers of non-expert annotators match expert quality on several NLP tasks (`snow2008`) | supported | ACL Anthology D08-1027 (EMNLP 2008): non-expert label aggregation reaches expert-level quality on most of its five tasks |
| Adaptive task routing cuts labeling cost by over a third (`kellner2021`) | unverifiable | The key resolves to no work: `refs.bib` has no `kellner2021` entry (deliberate) |

### `fixtures/bib-audit/` (bibliography metadata audit; expected verdicts)

| Entry | Expected | Ground truth (verified 2026-08-16) |
|---|---|---|
| `sheng2008` | confirmed | Crossref `10.1145/1401890.1401965`: "Get another label? …", Sheng/Provost/Ipeirotis, KDD 2008, ACM — complete record, fields match |
| `vaswani2017` | discrepant | DataCite `10.48550/arXiv.1706.03762`: year 2017; the entry deliberately says 2018 — year correction expected as a proposal |
| `liu2019` | mismatched | Its DOI `10.18653/v1/N19-1423` resolves to Devlin et al., NAACL 2019 (Crossref: first author Devlin, 2019; title field empty on verification date) — not the fabricated database-tuning paper the entry describes |
| `snow2008` | discrepant | Crossref DOI `10.3115/1613715.1613751` exists for the work ("Cheap and fast---but is it good?", Snow, EMNLP '08) even though the ACL Anthology page displays no DOI — a registrar match whose only gap is the entry's omitted DOI is discrepant, with the DOI proposed as an addition. *Corrected 2026-08-16 after the first eval run: the initial expectation ("confirmed via URL") checked only the Anthology page, not a registrar search — the skill's own protocol out-verified the fixture author.* |
| `ramanathan2014` | unconfirmed | Fabricated entry; Crossref bibliographic search returns no plausible match — expected verdict is a question for the author, never a fabrication ruling on absence alone |

### `fixtures/uncited-claim/`

The claim ("repeated labeling improves label quality when annotators are
noisy") is the subject of Sheng, Provost & Ipeirotis, KDD 2008
(`doi:10.1145/1401890.1401965`), among others. Any on-topic candidate with
a resolvable locator and a quoted passage counts; the specific paper is not
required. The integrity expectations are: nothing inserted into
`notes.md`, candidate offered as a proposal, `uncited` ledger entry
appended.

## What the assertions test

Three things, in every eval: **classification accuracy** (the verdicts
above), **integrity** (fixtures byte-identical after the run; proposals
never applied), and **the audit trail** (a dated
`literature/verifications.md` in the host copy with the right entry forms).
The baseline (no skill) runs the same prompts; the deltas are the value the
skill adds.

## Maintenance

### Offline quotation-checker tests

Run `python3 -B -m unittest discover -s evals -p 'test_check_quotes.py' -v`.
These deterministic tests exercise the bundled script and CLI on synthetic
text, including altered quotations, permitted normalization, review-only
edits, source locations, input errors, and source-file preservation. They
need no model, network, or third-party Python package. They test textual
presence, not citation-support accuracy or end-to-end agent performance;
the three agent evals above remain separate.

- Fixtures cite real works so retrieval is real; expected verdicts are
  therefore hostage to the live records. Re-run the provenance checks
  above before blaming the skill for a changed verdict.
- Trigger-description optimization (the second half of the original
  tracker item) is deliberately deferred until the skill's behavior
  settles; see `tasks.md`.
