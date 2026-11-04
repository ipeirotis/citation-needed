# Quotation benchmark: initial results, 2026-11-04

**30 real-paper manuscript adaptations; 180 quotation targets. Offline tests complete. Actual Claude enabled/disabled comparison NOT RUN.**

## What was executed

- The unchanged prototype `scripts/check_quotes.py`, imported and called on all 180 quotation/source pairs.
- 1292 dataset checks covering source/manuscript hashes, licences, source-grounded review records, target coverage, alterations, claim hashes and manuscript locations: all passed.
- 63 offline unit/adversarial tests: all passed, with no skips. This includes 17 tests of the three shared gates. Synthetic compliant/broken reports and a stub API response are test materials, not Claude outputs.
- Preparation of all 60 isolated case/condition workspaces, with matched inputs and no answer keys in the model workspace: all passed. No model was called during preparation.
- Real credential preflight: stopped before any API request because `gcloud` is not installed here. This does not assess the user's Google permissions or provider quota.

## Actual mechanical checker results

| Quotation type | Items | Found | Not found | Manual review |
|---|---:|---:|---:|---:|
| accurate | 30 | 30 | 0 | 0 |
| formatting | 30 | 30 | 0 | 0 |
| altered_wording | 30 | 0 | 16 | 14 |
| altered_number | 30 | 0 | 18 | 12 |
| misleading_omission | 30 | 0 | 0 | 30 |
| benign_omission | 30 | 0 | 0 | 30 |

The exact/narrow-normalization controls all match (60/60). None of the 60 altered-wording/number quotations is accepted as a match. Both kinds of ellipsis go to review, as designed. Across all 180 targets the checker emits 30 exact matches, 30 normalized matches, 34 not-found results and 86 review requests.

All 180 results conform to the prototype's documented status contract. **That is not 100% semantic quotation accuracy.** The expected status key describes the same documented contract; it is separate from the valid/invalid ground truth.

Observed limitations:

1. The checker cannot distinguish the 30 meaning-changing omissions from the 30 legitimate shortened quotations. Both return `manual_review`.
2. Ordinary reference brackets in a changed quotation trigger its editorial-edit guard: 26 altered-wording/number cases return `manual_review`, rather than the more specific `not_found` outcome.
3. Thirty valid shortened quotations need contextual review. This is review burden, not proof that the script falsely called them invalid: it does not issue a semantic invalid verdict.
4. Harmless line wraps, repeated spaces and nonbreaking spaces are covered, but this dataset does not measure PDF/OCR/extraction errors or broad source diversity. It is one publisher/year and a narrow set of mutation templates.

Checker wall time: **0.552 seconds**, Python 3.12.14. No API tokens or API cost were used for these mechanical checks. Timing is local execution time, not an estimate of agent overhead.

## Shared gates

The adversarial tests verify detection of missing/wrong archives; self-hashed quotes-only archives; missing independent source-read traces; missing licence fields; incorrect claim hashes; invalid/backdated timestamps; rewritten ledger history; missing claim entries; input changes; unexpected output files; archive symlinks; and mismatched optional JSONL companions. They also test compliant local output, retained historical entries and an explicit archive exemption.

These are tests of the **grader**, not measurements of how often Claude meets each requirement. The shared checks are a local fresh-citation profile. They do not fully test cloud-store privacy/access, live registrar/retraction queries, source licensing truth, reuse freshness or all bibliography/novelty/version-specific record forms.

## Agent comparison status

| Condition | Planned runs | Completed | Verdict accuracy | Shared failure rate | Tokens/time |
|---|---:|---:|---|---|---|
| Checker enabled | 30 | 0 | Not measured | Not measured | Not measured |
| Checker disabled | 30 | 0 | Not measured | Not measured | Not measured |

This environment has no authenticated Google Cloud/Anthropic credentials. A Mac's local login does not transfer to it. Therefore **there is no evidence yet that the checker improves Claude, and no agent-performance baseline is claimed**.

The [runner instructions](../../quotation_benchmark/README.md) load `anthropic-api-key` from Secret Manager without printing it, run a small provider test, then one pair and finally all 60 runs. Raw traces/workspaces stay outside GitHub; review and publish aggregate results afterward. The API runner uses restricted file tools and is not a Claude Code invocation.

## Reproduce and inspect

```bash
python3 -B -m unittest discover -s evals -p 'test_*.py' -v
python3 -B -m evals.quotation_benchmark.validate --output-dir /tmp/quotation-checks
```

- [Dataset and attribution](../../quotation-dataset/README.md), [paper list](../../quotation-dataset/papers.csv), [answer key](../../quotation-dataset/answer-key.json).
- [Per-item checker CSV](checker-results.csv), [checker JSON](checker-results.json), [dataset validation](validation.json).
- [Offline test records](test-results.json), [workspace preflight](preparation-checks.json), [agent status](agent-status.json).
- [Shared checker](../../quotation_benchmark/shared.py), [quotation grader](../../quotation_benchmark/grade.py), [agent runner](../../quotation_benchmark/runner.py).

The source-grounded key was reviewed by Codex against the pinned passages, without independent human sign-off. The original authors did not write or endorse the modified manuscripts. Source prose and evaluation adaptations are CC BY 4.0 with attribution; code follows the repository license.
