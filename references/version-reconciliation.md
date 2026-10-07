# Version-of-record reconciliation: has the preprint been published?

A verdict earned on a preprint or a partial text rests on text that can be
superseded. The ledger's reuse rules already cover the passive case — an
entry earned on a preprint or an abstract-only read is retried, not reused,
once fuller text may be available — but that rule fires only when a
verification run happens to touch the claim again. This pass is the
proactive half: sweep the ledger for sources read as something less than the
version of record, detect that a published or fuller version now exists, and
point the author at the claims whose evidence sat in text that changed —
without waiting for a reuse attempt.

A sweep detects and proposes; it never issues, revises, or retires a
verdict.

**Gate condition.** Live retrieval, as for every capability — but the
channels a sweep needs follow from its targets: DOI-bearing and
preprint-registered targets need registrar metadata (DOI resolution, the
registration agencies' APIs, preprint servers), while URL-backed targets
need only the fetch, plus text retrieval to diff whatever is found. When a
channel is missing, sweep the targets whose channels are available and
report the rest as unswept for lack of access — never fake their
detection; with no channel available at all, stop. Ledgered past sweeps
remain reportable as dated history either way. The sweep also needs a ledger: with no
`literature/verifications.md` in the host repo, or none of its entries read
as less than the version of record, there is nothing to sweep — report that
outcome plainly rather than inventing targets.

## When to run

The author invokes the sweep directly — by handing the skill the
verification ledger, or by asking whether anything verified against a
preprint has since been published. A verification run that notices
preprint- or abstract-read entries on sources outside its scope does not
pull them in; it offers the sweep in `Author decisions` instead
(`references/literature-checks.md`, step 2).

## The protocol

Run the steps in order: the target list is pinned before the first lookup,
so nothing a search returns can reshape which sources get swept.

### 1. Inventory the sweep targets

Read the ledger and collect every governing entry — per the supersession
rules in `references/verification-ledger.md` — whose `version-read` records
a read of something less than the version of record: preprints (with their
recorded locator and revision), abstract-only reads, partial snapshots. An
entry where nothing was read at all (`version-read: none`, an unresolved or
unretrieved source) is not a target — there is no text to reconcile, and
retrying an unverifiable verdict is a verification run's job under the
reuse rules, not the sweep's. Entries of
every form participate — `cite:`, `uncited`, and novelty leads all record
`version-read`, and each is a dated reliance on a specific text. Dedupe by
source identity, but never collapse distinct baselines: entries verified
against different revisions or snapshots of the same work (a v1 versus a v2
preprint read, two dated page snapshots) group by source identity plus the
recorded `version-read` and archived hash — one comparison group per
baseline, each carrying the claim-hashes and evidence locations of what
rests on that baseline, because a claim is only ever classified against the
text its verdict was earned on. Skip a target — a baseline group — whose
own governing `vor` entry still stands under the ledger's reuse rules — a publication already
found and diffed whose `claims:` list still covers every governing entry
resting on the baseline, or a none-found or text-unreachable result younger
than about six months — unless the author explicitly asks for a full
re-sweep. A dependency ledgered against a reconciled baseline after its
sweep reopens only the mapping step: once the ledger's standing freshness
screens pass, the archived fuller text and recorded diff serve as-is and
the new claims are classified against them. For a URL-backed target, a
recent `none found` never suppresses the canonical-URL re-fetch itself —
only the broader detection channels stay cached — so such a target enters
the sweep for that one check even inside the window. A preprint target
gets the same exception for its preprint server's metadata: that one
request runs on every sweep, and a revision newer than the baseline and
than any `revised:` already recorded reopens the target at once, while a
recent `none found` keeps only the publication channels cached. A
text-unreachable result dies early: the requested copy arriving in the
source store reopens the target at once, without waiting out the window.

Dispatch each remaining baseline group as one independent worker under
`references/parallel-retrieval.md` when subagents are available, concurrently
up to the platform limit. The coordinator validates the detection and diff
results, maps all returned dependencies exactly once, and remains the only
ledger writer; without subagents, sweep the same baseline units sequentially.

### 2. Detect the published or fuller version

Check the cheapest authoritative signal first, per target:

- **The preprint's own registrar record.** Preprint DOIs (bioRxiv, SSRN,
  arXiv's DataCite DOIs) carry publication relations such as
  `is-preprint-of`; check the reverse direction too where the registrar
  supports it, per the source-archive convention, since the relation is
  often deposited on only one side.
- **The preprint server's metadata.** arXiv's abs page and API expose the
  journal reference and DOI that authors add after publication. A newer
  preprint revision (a v4 where v2 was read) is not publication, but it is
  newer text the verdicts were not earned on. When no version of record is
  found, the newest revision is this target's fuller version: record it in
  the `vor` entry's `revised:` field and run steps 3 and 4 against it
  exactly as for a publication. When a version of record is also found, the
  publication governs the comparison and the revision is only recorded.
- **Registrar bibliographic search** (title, authors, year window) as the
  fallback, held to the bibliography audit's confidence standard: only a
  record that confidently identifies the same work counts, and a near-miss
  goes to the author as a question, never silently adopted as a match.
  More than one confident publication relation — a conference version and
  a later journal version, say — is likewise never silently resolved:
  record every match in the `vor` entry, classify the target ambiguous,
  and ask the author which version governs before any comparison runs.
- **A target that already carries the work-level DOI** — the preprint was
  read because the version of record was not legally reachable — is already
  published. For it, detection means checking whether a legal full text is
  reachable now: the publisher's link from DOI resolution, Unpaywall, an
  embargo that has lapsed.
- **A URL-backed target** — an abstract-only or partial snapshot of a
  source with no DOI — gets its canonical URL re-fetched: the page may now
  expose or link the fuller text it once withheld. Compare what comes back
  against the archived snapshot under the source-archive snapshot rules
  before treating anything as new. This re-fetch is one request and runs
  on every sweep: a standing `none found` entry never suppresses it, and a
  changed page invalidates that cached outcome.

While at the registrar, run the update-relations screen from
`references/source-archive.md` on every DOI in the version chain — the
baseline's own DOI (a preprint's registrar DOI included) and each detected
publication DOI — because retraction and erratum notices attach to one
side of the chain or the other, and a reverse query for one identifier
does not cover notices targeting the rest. A retraction or erratum
surfacing during a sweep is flagged exactly as at verification time.
A target with no publication found is a dated finding, not a failure: record
which channels were checked.

### 3. Fetch and compare the texts

When a published or fuller version exists and a legal copy is reachable,
retrieve and archive it under `references/source-archive.md` — naming, hash,
license, and store selection as usual. Before comparing, validate the old
side per the ledger's archive check: the archived text the verdicts were
earned on must still exist at its recorded path (following relocation
entries) and match its recorded SHA-256. When the store holding the
baseline simply cannot be checked this run (an outage, missing
credentials), the comparison is deferred, not failed: record the detection
outcome with the diff pending, report the outage, and let the next sweep
complete it. A target whose old text is confirmed missing or fails the
hash check is **unreconcilable**: never diff against a reconstructed
stand-in. Its `vor` entry records that outcome in place of a comparison
(entry form in `references/verification-ledger.md`) — the found publication
and the newly archived text still stand, every dependent claim is treated
as affected, since nothing can be confirmed intact without the text the
verdicts were earned on, and the broken archive itself is raised in
`Author decisions`. Re-checking those claims is fresh verification against
the new text, not a targeted diff. For a reconcilable target, compare the
new text against the validated archived copy, at two granularities:

- **Sections**, for the summary: which were rewritten, added, or removed.
  Renumbering alone is mapping, not change — record the map.
- **Evidence passages**, for the per-claim decision: locate each dependent
  entry's quoted `evidence:` passage in the new text. Found materially
  unchanged, wherever it moved — and with its surrounding paragraph free of
  newly added or altered qualifiers, limitations, or corrections bearing on
  the claim — means the claim is *intact*; a passage reworded in substance,
  not found at all, or intact only with changed surrounding context that
  bears on the claim, means *affected*.

A quotes-only artifact — the `--quotes.md` fallback of
`references/source-archive.md` — is never a full baseline, however cleanly
its hash validates: it preserves selected passages, not the text's
structure. For such a baseline, skip the section-level comparison and
report it as unavailable; classify dependents by the evidence-passage
lookup alone, locating each preserved quotation in the new text.

When publication is established but the text is not legally reachable, do
not bypass: the outcome is recorded as published with the text unreachable,
the standard paywall flow applies (request the PDF in `Author decisions`,
archive whatever was legally readable — usually the abstract snapshot), and
every dependent claim is treated as affected pending the text, since without
it no passage can be confirmed intact.

### 4. Map the dependent claims

Classify every claim resting on the source — by claim-hash for `cite:` and
`uncited` entries; a novelty lead, whose entry form carries no claim-hash,
is identified by its normalized novelty claim: the heading with the
timestamp and `novelty — ` prefix stripped, whitespace collapsed. Neither class
changes a verdict now:

- An **affected** claim — evidence reworded, moved out of recognition, or in
  a removed section — becomes a re-check proposal in `Author decisions`: its
  verdict may not survive the new text.
- An **intact** claim keeps its dated verdict, and the ledger's version
  predicate still forces a retry at the next verification run — but the
  sweep's record makes that retry a targeted read of an already-archived
  text instead of a fresh hunt. The sweep never promotes the verdict itself:
  judging support requires the claim as the manuscript now words it, and the
  manuscript is outside a sweep's scope.

### 5. Update the ledger, then report

Append one dated `vor` entry per swept baseline group — found, none-found,
and text-unreachable outcomes alike (entry form and reuse rules in
`references/verification-ledger.md`) — and confirm the writes landed before
returning the report. Then report exactly three sections:

- **Scope and detection:** targets swept, targets skipped under a
  still-standing `vor` entry, detection channels queried, and lookups that
  failed.
- **Version reconciliation:** one row per swept baseline group — what was
  read and what was found, and how; when a version was found and compared,
  the section-level changes (or the unreconcilable outcome when the
  archived text failed its integrity check) and each dependent claim marked
  affected or intact; a diff-pending row — a found version whose baseline
  store was unreachable this run — names the found version and leaves its
  dependencies unclassified until the next sweep completes the comparison;
  a none-found row records the channels checked instead.
- **Author decisions:** each re-check proposal, each paywalled
  version-of-record request, each ambiguous publication match as a question,
  any retraction or erratum the update screen surfaced, and any newer
  preprint revision compared in place of a publication. Nothing is edited
  and no verdict changes.

## Boundaries

- **Detection, not adjudication.** The sweep never issues, revises, or
  retires a verdict; re-verification is citation verification's job
  (`references/literature-checks.md`), on the author's go-ahead or at the
  next run the reuse rules force.
- **Fetched, not remembered.** Publication status comes from a registrar
  record, the preprint server, or the publisher's page fetched this
  session — never from model memory that a paper "came out last year".
- **The usual lines hold.** Paywalls are never bypassed, the manuscript and
  bibliography are never edited, and every copy archived follows the
  source-archive rules.
