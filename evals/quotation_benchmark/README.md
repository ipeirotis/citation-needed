# Quotation experiment and shared mechanical gates

This suite compares the **same citation-needed skill with and without the
mechanical quotation checker** on 30 paper-derived manuscripts. It does not
compare skill versus no skill. The tested prototype and ordinary skill remain
unchanged; the disabled runtime is an automatically generated ablation.

## Three different kinds of evidence

1. `validate.py` validates the 30-case dataset and executes the real prototype
   checker on 180 quotations. No model or API is involved.
2. `test_quotation_benchmark.py` deliberately constructs compliant and broken
   synthetic outputs to test the grader/harness. These are not agent results.
3. `runner.py` makes real Anthropic Messages API calls with restricted local
   file tools. Only this layer measures the enabled/disabled agent comparison.
   **It is not a Claude Code run.** No complete-skill or search performance
   claim follows from this controlled, supplied-source experiment.

## Run offline checks

Python 3.11+ and the standard library suffice; no dependencies or API key.

```bash
python3 -B -m unittest discover -s evals -p 'test_*.py' -v
python3 -B -m evals.quotation_benchmark.validate --output-dir /tmp/quotation-checks
```

## Run the actual agent experiment on an authenticated machine

Choose a new output directory **outside every Git checkout**. The CLI refuses
an existing destination to prevent overwriting evidence or duplicate billing.
Authentication is never written to a file or included in model/tool inputs.

First test provider access (one tiny request):

```bash
python3 -B -m evals.quotation_benchmark.runner --gcloud-secret --smoke-only \
  --output-dir "$HOME/quotation-eval/provider-smoke-1"
```

Then test one pair before paying for the complete run:

```bash
python3 -B -m evals.quotation_benchmark.runner --gcloud-secret --cases M01 \
  --output-dir "$HOME/quotation-eval/paired-pilot-1"
```

Run all 30 cases in both conditions (60 agent runs, one repetition):

```bash
python3 -B -m evals.quotation_benchmark.runner --gcloud-secret \
  --output-dir "$HOME/quotation-eval/round-1"
```

`--gcloud-secret` uses your already-authenticated `gcloud`, explicitly selects
`arinj128@gmail.com`, and reads `anthropic-api-key` in `writing-skills-resources`
through a captured subprocess pipe. It never prints the value or saves it.
Alternatively omit the flag and supply `ANTHROPIC_API_KEY` in your local
environment. Never paste a key into chat. Google login on a Mac is not a login
in a separate cloud execution environment.

The default requested model is `claude-haiku-5-5`. Override `--model` to use a
different permitted model. Both conditions share model/settings; the requested
and returned model IDs are recorded. An alias is not proof of an immutable
server-side model snapshot. Default limits are 16 API turns and 4,096 generated
tokens per request, not per run; `--max-turns`/`--max-tokens` change them. Runs
are sequential, with no automatic paid retries. In harness v2 an API/network
error saves the partial responses, tool events, grades and a safe error message,
then stops the suite. Requests without responses are recorded as unaccounted;
their usage is unknown. The original v1 runner missed `RemoteDisconnected`, so
the uploaded experiment has one interrupted run without a saved grade.
Three repetitions require
`--repetitions 3` (180 runs); begin with one to measure actual usage.

Preparation without any API call:

```bash
python3 -B -m evals.quotation_benchmark.runner --prepare-only \
  --output-dir "$HOME/quotation-eval/prepared-1"
```

Each fresh workspace contains only one altered manuscript, its source, a
bibliography, an initially header-only ledger and skill runtime files. Every
third case declares a JSONL companion in **both** conditions. Answer keys,
graders, prior results, evaluator contracts and credentials stay outside the
workspace. Global skills and personal MCP servers cannot enter this API harness.
Condition order is shuffled reproducibly. Each run has a separate conversation.

The enabled condition has the installed checker and its tool wrapper. The
disabled condition removes that script/reference and only the checker-specific
instructions; normal manual checking, archive and ledger rules remain. Tools
otherwise match: read/search files, hash files/text, copy source bytes, write
literature artifacts. No arbitrary shell, code execution or external network
tool is exposed. Writes are confined to `literature/`; attempted input/runtime
writes are logged and fail preservation. Source reads are independently logged.

Harness v2 adds line/character-offset metadata to `read_file` and line numbers
to `search_file`; raw text is unchanged. This makes the manuscript locations
required by the skill available directly. `--legacy-file-tools` retains v1
response shapes. Tool versions are recorded in the run plan: do not pool
future v2 runs with the original v1 experiment as if conditions were identical.
The default output-token limit is unchanged. A higher limit is a new experiment
setting, not a retroactive repair of a truncated run.

## What is graded

The agent writes `literature/quotation-audit.json` alongside its normal report
and ledger. Each target gets `valid`, `invalid` or unresolved `review`, the
original complete source sentence as evidence, a paragraph locator and a
specific explanation. A larger verbatim source passage containing that sentence
is acceptable. Labels are fixed by the external reviewed key, **not by the
tested checker**. Missing/duplicate items or required evidence fail the eval.

Metrics: verdict accuracy; error recall; false alarms on valid controls;
unresolved errors and valid items; evidence/locator failures; each shared gate;
checker use; API input/output/cache tokens; requests and wall time. No cost is
invented from subscription billing. Correct numerical/lexical labels cannot
override a required shared failure. Generic review does not count as detecting
an omission. Omission explanations require independent contextual review before
a final passing result, even when the mechanical grade passes.

Checker-use compliance binds each whole quotation to the pinned source bytes.
V2 permits the prototype's narrow whitespace/typography equivalence. A fragment,
changed word/number or different source does not satisfy a required check.
This is distinct from the checker's valid/invalid judgment.

The three reusable local gates in `shared.py` are:

- **Archive:** source text was actually returned by the evaluator's file-read
  tools; the ledger points to a safe local archive; recorded hash, archive bytes
  and the independently pinned source hash agree; source-identity filename hash
  and a license field are present. A self-hashed quotes-only file fails.
- **Ledger:** declared store, UTC timestamp within the run, append-only prior
  history, one fresh entry per expected claim–source pair, required fields,
  canonical claim hashes, verdict taxonomy, locators, and exact JSONL agreement
  when a companion is declared. Ledger verdicts must agree with the structured
  quotation report. Prior entries are retained and excluded from
  fresh coverage/timestamp checks. Shared grader v2 recognizes the same DOI
  followed by a human-readable annotation, while rejecting a different or
  ambiguous DOI. Claim hashes, locations and JSONL equality are unchanged.
- **Preservation:** original inputs and runtime keep their bytes/type/mode;
  new files stay in declared literature output paths; no symlinks; denied
  protected-write attempts fail the gate. The API tools enforce that boundary
  during the run as well as the grader checking end-state snapshots.

The evaluator owns the contract, snapshots and events. Allowing the model to
write them would invalidate the checks. The shared checker can be called outside
this runner:

```bash
python3 -B -m evals.quotation_benchmark.shared snapshot \
  --workspace /path/to/host --output /path/to/evaluator/before.json
python3 -B -m evals.quotation_benchmark.shared grade \
  --workspace /path/to/host --contract /path/to/evaluator/contract.json \
  --before /path/to/evaluator/before.json --events /path/to/evaluator/events.json \
  --output /path/to/evaluator/shared-grade.json
```

This is the local **fresh citation/quotation** contract. Metadata-only audits
may explicitly exempt archiving; a version sweep needs a contract describing
which texts were actually read. Cloud permissions, licensing truth, live
registrar queries, ledger reuse/freshness, bibliography/novelty/version-specific
record forms, and semantic support are not fully verified by this implementation.
Do not describe it as a universal checker for every skill requirement.

## Results and publication

Raw outputs, contracts, traces and workspaces stay outside the repository.
`results.csv` and `summary.md` are rebuilt as real runs complete. Per-run
`grading.json` retains the three shared gates and item outcomes. A completed
run is not automatically a pass; contextual review may remain pending.

Reviewed aggregate results are published under `evals/results/quotation-30-2026-11-04/`.
The [initial summary](../results/quotation-30-2026-11-04/summary.md) records
offline tests before credentials were available here. The subsequent
[uploaded agent experiment](../results/quotation-30-2026-11-04/paired-run-141405/report.md)
contains actual API results: 39 completed of 60 planned runs, 11 complete pairs,
original and corrected grades, and explicit unknown outcomes. The corrections
are an offline regrade; no model was rerun. Raw bundles remain outside GitHub.

To reproduce that reanalysis with the original extracted bundle, use its
`main/` directory and the published, evidence-bound AI review decisions:

```bash
python3 -B -m evals.quotation_benchmark.analyze_run \
  --run-root /path/to/20261104-141405/main \
  --reviews evals/results/quotation-30-2026-11-04/paired-run-141405/context-review.json \
  --bundle /path/to/20261104-141405-results.zip \
  --output-dir /tmp/quotation-reanalysis-new
```

The reanalysis makes no provider calls and never runs scripts from the bundle.
It checks baseline code/dataset pins, source/manuscript bytes, saved snapshots,
usage receipts, original grades and actual checker tool inputs. The trusted
v1 shared grader is loaded from published commit `919f9ec` in this repository's
Git history. A new destination is required. `results.csv` has one row per planned
run; `item-results.csv` has one row per planned target. Unfinished targets are
unknown, and paired overhead uses only cases completed in both conditions.

Provider API references checked 2026-11-04:
- https://platform.claude.com/docs/en/api/messages/create
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview
