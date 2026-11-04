# Quotation checker: reviewed partial API experiment, 2026-11-04

**Both conditions judged every quotation correctly in completed runs. The
checker showed no accuracy gain on the 11 fully completed pairs and increased
usage. Almost every completed run still failed the required ledger gate.**
This is limited evidence from simple planted errors, one repetition and an
interrupted experiment. It does not establish that the checker is generally
ineffective or that the complete skill is reliable.

## What actually ran

The user ran published commit
[`919f9ec`](https://github.com/ipeirotis/citation-needed/commit/919f9ec91deed4780f2fde0f46e585206e8757b0)
locally and supplied the result bundle. This was the Anthropic Messages API
harness with restricted file tools, **not Claude Code**. The requested and
returned model ID was `claude-haiku-5-5`. The same skill was used in both
conditions; only the mechanical checker integration was disabled in the control.

The dataset contains [30 CC BY 4.0 paper-derived manuscript adaptations](../../../quotation-dataset/README.md),
six labelled quotation targets each. Sources were supplied locally; this does
not measure source discovery, live retrieval or ordinary claim-support accuracy.

Of 60 planned runs, **44 began, 43 have saved run records and 39 completed**.
Four ended at the 4,096-token response limit without writing an audit. Run 44,
M03/checker-enabled, lost its API connection; v1 missed `RemoteDisconnected`
and exited before saving that run's grade. Sixteen later runs never started.
The interrupted request's tokens, elapsed time and billing are unknown.

| Condition | Completed | Token-limited | Interrupted without record | Never started | Planned |
|---|---:|---:|---:|---:|---:|
| Checker enabled | 19 | 3 | 1 | 7 | 30 |
| Checker disabled | 20 | 1 | 0 | 9 | 30 |

The provider smoke call passed. A two-run M01 pilot also completed, with 6/6
correct verdicts in each condition and ledger failures in both. Smoke and pilot
usage/results are recorded separately in [execution notes](execution-notes.json)
and excluded from every main comparison below. No additional paid calls were
made during this review or regrading.

## Quotation performance

| Measure | Checker enabled | Checker disabled |
|---|---:|---:|
| Correct verdicts in completed runs | 114/114 | 120/120 |
| Planted errors detected in completed runs | 57/57 | 60/60 |
| False alarms among completed valid controls | 0/57 | 0/60 |
| Required evidence or source-locator failures in completed runs | 0/114 | 0/120 |
| Correct targets resolved / all planned targets | 114/180 | 120/180 |
| Unknown targets from unfinished runs | 66 | 60 |
| Overall passing runs / all planned runs | 0/30 | 1/30 |

Every quotation type—accurate, formatting, altered wording, altered number,
benign omission and misleading omission—scored 19/19 with the checker and
20/20 without among completed runs. There are 30 planned items of each type
per condition. The missing outcomes are **unknown**, not observed quotation
misclassifications. Conditional accuracy and planned coverage answer different
questions; neither should replace the other.

Codex reviewed all 78 completed-run omission explanations against the pinned
sentences and surrounding paragraphs. All were accepted; two minor wording
slips were noted. This was **AI review with the answer key visible, not blind
or independent human review**. [Decisions](context-review.json) are bound to
source, quotation, context and explanation hashes. The uploaded bundle's
earlier Claude Opus 5.5 AI review remains part of the original evidence.

## Shared gates: original grades and offline corrections

These are failures **among completed runs**. A required shared failure still
fails the run even when all six quotation verdicts are correct.

| Failed gate | Enabled, original | Enabled, regraded | Disabled, original | Disabled, regraded |
|---|---:|---:|---:|---:|
| Source archive | 5/19 | 1/19 | 1/20 | 0/20 |
| Verification ledger | 19/19 | 19/19 | 19/20 | 19/20 |
| Input/runtime preservation | 0/19 | 0/19 | 0/20 | 0/20 |
| Checker-use condition | 9/19 | 1/19 | 0/20 | 0/20 |

Two grading defects were corrected explicitly; no model output was edited:

- **DOI identity:** v1 treated `doi:10.1371/... (explanation)` as a different
  source. V2 recognizes the same unambiguous DOI followed by annotation. Four
  enabled archive failures and one disabled archive failure disappear. Incorrect
  claim hashes, manuscript locations and companion contents still fail.
- **Checker-use whitespace:** v1 required byte-identical quotation strings even
  when the prototype accepts the whitespace difference. V2 permits the
  prototype's narrow typography/whitespace equivalence against the pinned
  source bytes. Eight enabled compliance failures disappear. M16 still fails
  because only a fragment of its required Q2 quotation was submitted.

Genuine remaining failures include incorrect manuscript locations (18/19
enabled, 19/20 disabled), JSONL/Markdown disagreement (3 enabled, 4 disabled),
claim coverage problems and incorrect claim hashes. These counts overlap.
M25/enabled has an existing archive but records a truncated hash, so its
archive gate correctly fails. M04/disabled remains the **only overall pass
under both grading versions**.

The original tools returned source paragraph IDs and character offsets without
line metadata. Agents could count lines in the returned text, but direct line
information was missing. That is a harness usability defect affecting the
ledger result; it prevents attributing every location failure solely to the
skill. Wrong locations have not been waived retrospectively.

For all saved records, including the four token-limited runs, regraded failures
are archive 4/22 versus 1/21, ledger 22/22 versus 20/21, preservation 0/22 versus
0/21, and condition compliance 2/22 versus 0/21. Unstarted/interrupted runs have
no assessable gate result. [Regrading details](regrading.json) retain each
original failure and its corrected counterpart.

## Tokens and time

Only **11 cases completed in both conditions**: M04, M10, M14, M15, M17, M22,
M25, M26, M28, M29 and M30. Both conditions scored 66/66 on those pairs.

| Usage on the same 11 completed pairs | Checker enabled | Checker disabled | Change |
|---|---:|---:|---:|
| Input tokens | 5,572,497 | 4,105,887 | +35.7% |
| Output tokens | 217,117 | 176,954 | +22.7% |
| API requests | 125 | 103 | +21.4% |
| Total elapsed seconds | 908.4 | 735.0 | +23.6% |
| Median run seconds | 78.6 | 62.0 | +16.6 seconds |

The median **within-pair** time increase was 17.1 seconds. That differs from
subtracting the two condition medians. No prompt cache tokens were recorded.

Across all 43 saved main records, enabled runs used 10,214,572 input and 418,037
output tokens across 231 requests; disabled runs used 8,751,255 input and 373,919
output tokens across 208 requests. These totals cover unequal case sets and
include token-limited runs, so they are not a fair paired-overhead estimate.
They also exclude unreceipted usage from the interrupted run; no total billed
cost is inferred.

## Concrete examples

[Selected evidence](examples.json) contains quotation judgments and small ledger
excerpts. M22/enabled Q2 caught a removed negation; M30/enabled Q2 caught a
changed date; M28/disabled caught both a changed date and a removed negation.
No planted error was missed and no false positive was observed among the
completed targets. The unfinished runs demonstrate execution failures, rather
than known incorrect judgments.

M07/enabled used source-file line numbers as manuscript locations. M25/enabled
recorded a truncated archive hash. M14/enabled demonstrates the difference
between a harmless DOI annotation and an incorrect manuscript locator.

## What changed after this experiment

The prototype quotation checker, skill instructions, dataset and answer key
remain unchanged. Eval infrastructure now records safe partial failure receipts,
allows the narrow grading corrections above, and provides file line metadata
for future runs. Regression tests cover dropped connections, source binding,
whitespace, ambiguous DOI identities, unknown outcomes and paired denominators.
The output-token default has not been increased. Original v1 results are not
pooled with unrun v2 conditions.

Post-review verification passed 72 offline tests and 1,292 dataset checks.
These validate the code and fixtures; they are separate from the agent scores.

Recommended next steps are to test harder, independently reviewed quotation
cases; assess the ledger with usable location tools; and preregister a fresh
paired run with an adequate output budget and recorded harness settings. The
present dataset is at ceiling for completed quotation judgments, so repeating
the same easy cases would give limited evidence about accuracy improvements.

## Reproduce and inspect

- [Run-level CSV: all 60 planned rows](results.csv),
  [item-level CSV: all 360 planned targets](item-results.csv),
  [machine-readable metrics](metrics.json).
- [Integrity checks and original artifact hashes](integrity.json),
  [AI review decisions](context-review.json), [execution notes](execution-notes.json).
- [Read-only reanalysis code](../../../quotation_benchmark/analyze_run.py) and
  [instructions](../../../quotation_benchmark/README.md#results-and-publication).

The original ZIP SHA-256 is
`2eb622014e3d81c4621c07d1c6185d835424b087cb57e04198506676d738f009`.
All 43 original quotation/shared grades and compliance outcomes were reproduced;
all saved workspace snapshots and receipted usage totals matched. The input
manuscript/source hashes match the published fixtures. Analysis did not execute
the uploaded analysis script. Original raw workspaces, model thinking blocks,
local paths and full traces are excluded from GitHub; reproducing the actual
run regrade requires the original bundle.
