# Tasks

Feature tracker for the citation-needed skill. Agents: read this before working
on the repo. New requests go under **Backlog** with the date they were filed;
when work lands, move the item to **Done** with the landing date and the files
that implement it. Items under **Proposed** are ideas awaiting the author's
approval — do not implement them unprompted. Items the author has decided
against move to **Decided, no action** with the decision recorded — do not
reopen them without a new request.

## Done

- **2026-10-07 — Ledger headings carry repository-relative paths.** A
  heading's manuscript location is the file's repository-relative path and
  line, never a bare filename, since archived drafts in a host repo can
  share file names. Raised in Codex review of the first ledger written into
  IliasTriant/inattentiveness_paper#14. (`references/verification-ledger.md`)

- **2026-10-07 — One audit row per claim and cited source.** A claim citing
  several works gets a row per work, so an unsupported citation no longer
  hides behind a supporting one in an aggregate verdict. Raised in a second
  Codex review on IliasTriant/inattentiveness_paper#14.
  (`SKILL.md`, `references/literature-checks.md`)

- **2026-10-07 — The gate requires a writable ledger, and an archive before
  text is archived.** Every capability needs a writable ledger, and its
  JSONL companion when one is declared. Capabilities
  1–3 also need the archive before the first fetch; the bibliography audit
  never does; a version sweep runs metadata detection with the ledger alone
  and needs the archive only once a found text must be archived, recording
  `detection incomplete` when it cannot. Same review; the bibliography and
  sweep exemptions came from Codex review of ipeirotis/citation-needed#7.
  (`SKILL.md`)

- **2026-10-07 — Novelty leads pass source checks before reuse.** A novelty
  entry is reused as current only when every retained lead passes the
  archive-hash, version, mutable-URL, refresh, and registrar-update checks a
  `cite:` source passes. Same review. (`references/verification-ledger.md`)

- **2026-10-07 — A LaTeX root is audited through its include graph.** When
  the request names a LaTeX root or wrapper, the claim inventory covers the
  transitive `\input`/`\include` graph, never sibling files it does not
  include, and records the resolved file set in `Scope and retrieval`; an
  unresolved include is a question, not a guess; `\includeonly` and
  untaken conditional branches narrow the set. Raised in Codex review of
  the skill vendored into IliasTriant/inattentiveness_paper#14, whose
  submission root keeps nearly all prose in included section files.
  (`references/literature-checks.md`)

- **2026-10-07 — A newer preprint revision is reconciled, not just noted.**
  When a version sweep finds no version of record but a newer revision than
  the baseline, the revision is fetched, archived, and compared under steps
  3 and 4 like a publication, and recorded in the `vor` entry's new
  `revised:` field; `published: none found` still ages under the usual
  window for the publication channels, while the preprint server's
  metadata is re-checked on every sweep so a later revision is never held
  to it; a newly listed journal reference or DOI also reopens the target,
  and a reopened target reruns every channel before a new `none found` is
  recorded. Raised in the same Codex review; the per-sweep re-check and its
  refinements came from Codex review of ipeirotis/citation-needed#7.
  (`references/version-reconciliation.md`,
  `references/verification-ledger.md`)

- **2026-10-06 — Restricted storage rules agree across the skill.** A host
  with no private store keeps restricted copies in an ignored
  `literature/sources/`; `SKILL.md` no longer defers that case. When the
  path is not ignored, the skill proposes the rule in `Author decisions`
  instead of editing `.gitignore`, and restricted work waits until it is
  added. The quotes artifact may go to a public repo (on the author's
  explicit decision) only on a host with no private store configured.
  Raised in review of ipeirotis/citation-needed#6.
  (`SKILL.md`, `references/source-archive.md`)

- **2026-10-06 — Ignore check and diff-pending kept for store outages.** The
  ignored local folder (hosts with no private store) again requires
  confirming with `git check-ignore` that the path is ignored before a
  restricted copy is written there. A version sweep during a store outage
  reports `detection incomplete` when the newer version's restricted text
  cannot be archived, and defers the comparison with the diff pending only
  in the case `version-reconciliation.md` defines (newer text archived, old
  baseline's store unreachable). An existing verdict whose archive is in the
  unreachable store is reported as dated history, not superseded by a new
  `unverifiable` entry.
  Raised in review of ipeirotis/citation-needed#6.
  (`references/source-archive.md`, `references/verification-ledger.md`)

- **2026-10-06 — A fresh ledger records the declared store.** The ledger
  header's `store:` line is set to the highest-ranked project declaration
  (for example the bucket a host's `AGENTS.md` names) whether or not it is
  reachable that run, not copied
  from the example header, and never from a fallback taken because the
  declared store was unreachable; the header outranks later declarations,
  so a wrong first value would move the archive permanently. Raised in a
  host-repo review (ipeirotis/sql-llm#28). A declared bucket that fails the
  privacy check is skipped for restricted material, and the next
  verified-private declaration takes it before any work waits; `SKILL.md`
  states the same order.
  (`references/verification-ledger.md`, `references/source-archive.md`,
  `SKILL.md`)

- **2026-10-05 — Restricted copies never fall back into the worktree.** When
  a configured private store is unreachable or not verified private, work
  that needs a rights-restricted source keeps no copy and reports each
  capability's can't-complete outcome (unverifiable, search incomplete, or
  detection incomplete), so no result is recorded without archived evidence; the
  ignored local folder remains an option only for hosts with no private
  store. Raised in a host-repo review (ipeirotis/sql-llm#28), whose
  instructions keep paywalled PDFs out of the repository.
  (`references/source-archive.md`, `SKILL.md`)

- **2026-08-16 — Parallel retrieval orchestration.** After the inventory and
  ledger-reuse boundary, citation checks now launch one subagent per distinct
  source (sharing one retrieval across all claims citing it); bibliography
  audits launch one per entry, novelty work one per independent question, and
  version sweeps one per baseline group, up to the platform's worker limit.
  Citation workers finish before novelty and uncited-claim workers begin, so
  later searches can use cited-source evidence; incomplete searches are
  explicitly nonreusable rather than recorded as zero-lead findings, and a
  newer incomplete uncited search supersedes older claim-level results. Timed-
  out workers must be cancelled and confirmed terminated before retry or
  takeover so archive writers cannot overlap. The coordinator validates
  results and exclusively writes the ledger, with a documented sequential
  fallback when subagents are unavailable.
  (`references/parallel-retrieval.md`, `references/literature-checks.md`,
  `references/bibliography-audit.md`, `references/version-reconciliation.md`,
  `references/verification-ledger.md`, `SKILL.md`)

- **2026-08 — Extract the scholar lane from blue-pencil into a standalone
  skill.** Core protocol carried over with blue-pencil couplings removed.
  (`SKILL.md`, `references/literature-checks.md`)
- **2026-08-14 — (a) Repo docs for agents and feature tracking.**
  (`AGENTS.md`, `tasks.md`)
- **2026-08-14 — (b) Archive the full text of every source read.** Cloud
  bucket (GCS/S3) when the project configures one and access verifies;
  otherwise `literature/sources/` in the host repo. SHA-256 recorded per file.
  (`references/source-archive.md`)
- **2026-08-14 — (c) Verifiable locators and the paywall flow.** Every source
  needs a DOI (cross-checked against its registration agency's metadata —
  Crossref, DataCite, or whichever agency issued it) or at minimum a stable
  public URL with access date. Legal open-access copies are searched first
  (publisher, Unpaywall, preprint servers); paywalled sources are requested
  from the author — download the PDF or print the page to PDF and place it in
  the store — never bypassed. (`references/source-archive.md`)
- **2026-08-14 — (d) Dated verification ledger in the host repo.** Results
  stored as append-only dated entries in `literature/verifications.md`, keyed
  by claim-text hash and source identity, with reuse rules so runs never
  redo settled work; pointed to from the host repo's `AGENTS.md`.
  (`references/verification-ledger.md`)

- **2026-08-14 — Rename the skill to chapter-and-verse.** "Give chapter and
  verse" = cite the exact authority for a claim; pairs with blue-pencil's
  idiom naming and avoids the crowded CiteCheck/refchecker namespace. The
  store env var became `LITERATURE_STORE` (rename-proof). Blue-pencil's
  dispatch command was renamed `/paper:scholar` → `/paper:verify-citations`
  (symmetric with `/paper:verify-numbers`). GitHub repo rename to
  `ipeirotis/chapter-and-verse` is done by the owner in repo settings; old
  URLs redirect.

- **2026-08-15 — Rename the skill to citation-needed.** Final name in the
  paper-scholar → chapter-and-verse → citation-needed sequence, superseding
  the chapter-and-verse rename above: the author judged that name hard to
  remember, and "[citation needed]" is the Wikipedia tag every academic
  already knows — resolving it is literally the skill's job. The GitHub repo is
  `ipeirotis/citation-needed` (old URLs redirect). `LITERATURE_STORE` and all
  host-repo artifact paths were already rename-proof; host ledgers written
  under earlier names stay valid, since `maintained-by:` is informational.
  (`SKILL.md`, `README.md`, `AGENTS.md`, `tasks.md`, `agents/openai.yaml`,
  `references/verification-ledger.md`)

- **2026-08-15 — Global consistency pass after the slim-out and renames.**
  Aligned the verdict taxonomy — `literature-checks.md` step 3 now defines
  all four verdicts including *partially supported*, which SKILL.md, the
  reporting conventions, the ledger examples, and the reuse rules already
  used — and replaced the leftover blue-pencil framing ("this lane", "the
  master rule") with standalone wording.
  (`references/literature-checks.md`)

- **2026-08-15 — Retraction and erratum check at verification time.** Fresh
  DOI-backed verifications now check the registrar's update relations —
  retractions, errata, corrigenda, expressions of concern; Crossref's update
  metadata incorporates the Retraction Watch database — at DOI resolution,
  flag the update with the verdict in the citation audit and `Author
  decisions`, and record it in the entry's `updates:` field. The reuse-side
  slice had already shipped with the ledger (2026-08-15): reusing a
  DOI-backed entry re-queries the registrar before the old verdict stands.
  (`references/source-archive.md`, `references/literature-checks.md`,
  `references/verification-ledger.md`)

- **2026-08-15 — Bibliography metadata audit.** Fourth capability, approved
  by the author: a cheap standalone pass confirming each bibliography entry
  identifies a real work — its DOI resolved and compared whole-record against
  the registrar per the source-archive tolerance rules, DOI-less entries
  matched by registrar search or their own URL, update relations screened
  along the way. Verdicts confirmed / discrepant / mismatched / unconfirmed
  (registrar absence is a question for the author, never a fabrication
  verdict on its own); results ledgered as `bib:` entries keyed by
  entry-hash; corrections and DOI additions only ever proposed. The trigger
  description now excludes "citation style formatting" rather than all
  BibTeX work. (`references/bibliography-audit.md`, `SKILL.md`,
  `references/verification-ledger.md`, `AGENTS.md`, `README.md`)

- **2026-08-16 — Version-of-record reconciliation (proactive half).** Fifth
  capability, approved by the author: a ledger sweep that detects when a
  source read as a preprint or partial text has a published or fuller
  version — registrar preprint relations, arXiv journal-ref, bibliographic
  search, with the update-relations screen along the way — archives the new
  text when legally reachable, diffs it against the archived read at section
  and evidence-passage granularity, and proposes re-checks for claims whose
  evidence changed; intact claims keep their dated verdicts, and no verdict
  ever changes in a sweep. Results ledgered as dated `vor` entries keyed by
  source identity (none-found results stand ~6 months); verification runs
  use the baseline's governing `vor` entry as a bridge when the version
  predicate blocks reuse, and offer the sweep for out-of-scope preprint
  reads instead of pulling them in. The reuse-time slice had already shipped in the ledger
  rules (2026-08-14). (`references/version-reconciliation.md`,
  `references/verification-ledger.md`, `references/literature-checks.md`,
  `SKILL.md`, `README.md`, `AGENTS.md`, `agents/openai.yaml`)

- **2026-08-16 — Machine-readable ledger companion.** Approved by the
  author: an opt-in `companion:` line in the ledger header keeps a derived
  JSONL beside `verifications.md` — one JSON object per entry, `ts`, `type`,
  and `heading` plus keys copied verbatim from the Markdown field labels,
  appended in the same write as every Markdown append and backfilled when
  first enabled. The Markdown stays the record: runs never read the
  companion, and on any disagreement the JSONL is regenerated from the
  Markdown, never the reverse. Without the header line nothing changes —
  the stable field labels keep the Markdown greppable, as before.
  (`references/verification-ledger.md`, `SKILL.md`, `README.md`,
  `AGENTS.md`)

- **2026-08-16 — Eval suite.** Approved by the author: fixture manuscripts
  and bibliographies with known-good, known-bad, partially supported, and
  unverifiable citations, exercising the citation audit, the bibliography
  audit, and the uncited-claim investigation. Expected verdicts were pinned
  against the live sources and registrars on 2026-08-16 — never model
  memory — with provenance recorded in `evals/README.md` (including two
  facts memory had wrong: the Snow et al. anthology ID and an empty title
  field in the BERT Crossref record). Runs use the skill-creator eval loop
  (with-skill vs. no-skill baseline, graded assertions on classification
  accuracy, integrity, and the audit trail); results and workspaces stay
  outside the repo. The trigger-description-optimization slice is
  deliberately deferred to the Backlog until behavior settles.
  (`evals/evals.json`, `evals/fixtures/`, `evals/README.md`, `AGENTS.md`)

## Proposed (awaiting approval)

(empty — ideas awaiting the author's approval go here)

## Backlog

- **2026-08-16 — Trigger-description optimization.** The deferred second
  half of the eval-suite item: optimize the `SKILL.md` trigger description
  with the skill-creator description-optimization loop once the skill's
  behavior has settled (three features landed 2026-08-16 alone; let the
  dust clear first).

## Decided, no action

- **2026-08-15 — No blue-pencil sync.** The author decided the behaviors
  landed here (source archive, locator rules, verification ledger, reuse
  rules, retraction screen, bibliography audit) stay standalone: blue-pencil
  is not updated, nothing is upstreamed or downstreamed, and this repo's
  protocol evolves independently from blue-pencil's scholar lane. Divergence
  between the two is accepted, not tracked — the standing sync note in
  `AGENTS.md` was retired accordingly. Closes the 2026-08-15 backlog item.
- **2026-08-15 — Facts-and-figures extraction dropped.** The author decided
  the planned carve-out of blue-pencil's analyst lane into
  `ipeirotis/facts-and-figures` is not needed; the backlog item is closed
  without action. If the idea is revived, it will be tracked in its own
  repo, not here.
