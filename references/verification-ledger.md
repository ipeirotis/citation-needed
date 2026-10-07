# Verification ledger: dated, reusable results

Retrieval is the expensive part of this skill, and manuscripts get checked many
times as they evolve. The ledger records every verification as a dated entry in
the host repo so a later run — by this skill, a coauthor, or another agent —
can see what has already been established and against exactly which text,
instead of redoing the work. It is also the audit trail: a verdict without a
date and an archived source behind it is just an assertion.

## Location and discovery

- The ledger lives at `literature/verifications.md` in the host repo root,
  beside the `literature/sources/` archive folder.
- The host repo's `AGENTS.md` (or `CLAUDE.md` when that is what the repo uses)
  should carry a short "Literature verification" section pointing at the
  ledger and the source store, so any agent working in that repo finds them.
  Create or refresh that pointer when writing the ledger, and say so in the
  report — the manuscript and bibliography are never touched, but this
  infrastructure edit is announced, not silent. If the repo has no agent
  instructions file at all, propose creating one in `Author decisions` rather
  than inventing repo conventions unasked.

## Ledger format

Header, once per file:

```markdown
# Literature verifications

store: literature/sources/        <!-- or gs://bucket/prefix, s3://bucket/prefix -->
maintained-by: citation-needed skill
refresh-interval: 12 months       <!-- optional; DOI-backed re-fetch cadence in months, 12 when absent -->
```

A fresh ledger gets this header with `store:` set to the highest-ranked
project declaration (`references/source-archive.md`, "Choosing the store"),
such as the bucket a host's `AGENTS.md` names, whether or not it is
reachable on that first run, and `literature/sources/` only when the
project declares none. Later runs give the header precedence, so a
temporary outage must not move the archive for good: a lower-ranked
declaration or the repo folder used because the declared store was down
is a per-run fallback. The run's entries record the paths actually used
and the report flags them, as for any fallback, and a later run with the
store back relocates them. The opt-in
`companion:` line (defined at the end of this file) is added only when the
author enables the JSONL companion, never as part of the default header.

One entry per verification, newest appended last, with these exact field
labels so entries stay greppable by humans and machines alike:

```markdown
## [2026-08-14T22:31Z] cite:smith2021 — introduction.tex:41
claim: "Smith et al. show that crowdsourced labels reach expert accuracy at one tenth the cost."
claim-hash: ab12cd34ef56
source: doi:10.1145/1234567.1234568
version-read: version of record
archived: literature/sources/smith2021--10.1145_1234567.1234568-4b1f22aa.pdf sha256:9f2a…
license: CC-BY-4.0
updates: none
verdict: partially supported
evidence: "labels reached expert agreement on 3 of 5 tasks" (sec. 5.1) — cost claim not addressed
notes: cost figure may come from a different paper; asked author.
```

- The heading's manuscript location is the file's repository-relative path
  plus line (`sections/introduction.tex:41` when the file lives there),
  never a bare filename: a repository often holds archived drafts with the
  same file names, and a bare name sends a reader to the wrong copy. The
  examples in this file use a root-level `introduction.tex`.
- `claim-hash` is the first 12 hex characters of the SHA-256 of the claim
  sentence with runs of whitespace collapsed to single spaces and case
  preserved — a case change can be a different claim (a gene name, a
  mathematical symbol, a unit), so case is never normalized away. Hashing the
  text rather than keying on file and line keeps entries valid when sections
  move or files are renamed.
- `version-read` distinguishes the version of record from a preprint or an
  abstract-only read; a verdict earned on a preprint does not silently carry
  over to the published version. When the text read is a preprint or another
  alternative version of a DOI-bearing work, record that version's own
  locator and revision beside the label — `version-read: preprint
  (arXiv:2106.01234v2)` — because the work-level DOI resolves to the version
  of record, not to the text actually read.
- `accessed:` records, for URL-backed sources, the date the URL was fetched
  (`accessed: 2026-08-14`). A static file's archive name does not carry the
  access date, so this field is where an audit learns when the URL was
  checked; DOI-backed entries may omit it.
- `license:` records the redistribution authorization for the archived copy:
  the license name when one was found (`CC-BY-4.0`), `restricted` when the
  copy must not be redistributed and so lives in a private store, `unknown`
  when none was determinable (treated as restricted), or `n/a` when nothing
  was archived. This is what lets a later audit establish why a committed
  copy was permitted to be where it is.
- `updates:` records, for DOI-backed sources, the outcome of the registrar
  update-relation check made at verification time
  (`references/source-archive.md`): `none`, the relation found with its
  target and date (`updates: retraction doi:10.1145/7654321 (2027-01-10)`),
  or `check failed (<reason>)` when the source text was read but the update
  query itself could not complete (timeout, rate limit, registrar outage) —
  never `none` for a check that did not actually run. A failed check leaves
  the evidence-based verdict standing, is surfaced in the report as an
  incomplete retraction screen, and heals on the next reuse, since the reuse
  rules query the registrar again whenever a DOI-backed entry is reused.
  URL-backed entries omit the field, as do entries written before it
  existed.
- `maintained-by:` is informational, naming the tool that writes the file.
  Ledgers written under this skill's earlier names (paper-scholar,
  chapter-and-verse) remain valid and are not rewritten to rebrand them.
- Novelty scans are logged too, since they age and their scope matters. Each
  lead carries the same source-identity, archive, and evidence fields as a
  citation entry — a lead a later run cannot reopen and re-read is not
  reusable evidence:

```markdown
## [2026-08-14T22:47Z] novelty — "we are the first to model X under Y"
searched: <the queries and databases used>
lead: doi:10.1234/abcd — Doe 2023, "Modeling X under Y-like constraints"
  version-read: version of record
  archived: literature/sources/doe2023--10.1234_abcd-7c09d1e2.pdf sha256:4e7b…
  license: unknown
  evidence: "we model X under Y'-constraints using…" (sec. 3) — same setting, different estimator
leads-found: 1; nothing else on point (state this explicitly when a search comes up empty)
```

Outcomes with no retrievable source still get entries — with explicit
sentinels, never invented evidence, because "could not check" and "checked
and unsupported" must stay distinguishable forever:

```markdown
## [2026-08-15T08:40Z] cite:jones2019 — related.tex:12
claim: "…"
claim-hash: 77ab19c02d3e
source: unresolved — key maps to no work in the bibliography
version-read: none
archived: none
license: n/a — nothing archived
verdict: unverifiable
evidence: none — nothing was retrieved; asked the author which work this key denotes
```

A zero-lead novelty scan likewise records `lead: none — searches returned
nothing on point` under its `searched:` line: the absence of a found overlap
is itself a dated finding, distinct from a scan that never ran.

An attempted novelty scan that did not finish records that distinction rather
than masquerading as a zero-lead result:

```markdown
## [2026-08-16T16:48Z] novelty — "we are the first to model X under Y"
searched: incomplete — <queries or channels attempted>; <failure>
lead: not assessed — search did not run to completion
status: search incomplete; nonreusable
```

This entry is audit history only: it never satisfies reuse, irrespective of
age or matching scope, and the next applicable run retries the search.

The third capability — investigating an uncited factual claim — gets its own
entry form, since it is neither a `cite:` verification nor a novelty scan:

```markdown
## [2026-08-15T09:02Z] uncited — methods.tex:57
claim: "It is well known that crowd labels converge with enough redundancy."
claim-hash: c41f88a02b7d
searched: <the queries and databases used>
candidate-source: doi:10.5555/wxyz — Roe 2018, "Redundancy and convergence in crowd labeling"
  version-read: version of record
  archived: literature/sources/roe2018--10.5555_wxyz-1a9e44b0.pdf sha256:8d1c…
  license: restricted — author-supplied copy, private store
  evidence: "convergence holds once redundancy exceeds…" (sec. 2)
status: candidate offered to the author; nothing inserted
```

An `uncited` entry reuses when the claim-hash matches, the recorded
candidate-source identity (its DOI or canonical URL) is unchanged, and the
archived copy validates, with the same freshness checks a `cite:` entry gets
before its evidence is presented again — the mutable-URL re-fetch, the
registrar-update and periodic-refresh rules for DOI-backed sources, and the
version predicate (a candidate read as an abstract or preprint is retried,
not reused, once fuller text may be available). The
bibliography-identity condition alone does not apply while the claim remains
uncited, since there is no citation to resolve. Once
the author adopts the candidate, the claim is a cited claim: later runs check
it under `cite:` with its new key, and the `uncited` entry stands as history.

When the search finds no suitable source, the entry records that outcome with
sentinels rather than a fabricated candidate:

```markdown
## [2026-08-15T10:05Z] uncited — methods.tex:57
claim: "It is well known that crowd labels converge with enough redundancy."
claim-hash: c41f88a02b7d
searched: <the queries and databases used>
candidate-source: none — searches returned no authoritative source
status: reported to the author; the claim currently has no supporting source
```

A no-candidate investigation ages like a novelty scan: reuse it only while
the claim text and the recorded `searched:` scope still match and the entry
is younger than about six months — the source that did not exist last year
may exist now.

If an uncited-claim search did not finish, use
`candidate-source: not assessed — search did not run to completion` and
`status: search incomplete; nonreusable`, with the attempted queries and actual
failure on `searched:`. It is audit history, not a no-candidate finding, and the
next applicable run retries it. Uncited-search attempts supersede at the claim
level, not at the candidate-source level: for a matching `claim-hash`, only the
latest entry governs reuse. Thus a newer incomplete entry invalidates every
older candidate or no-candidate result for that claim, even though its
`candidate-source` sentinel differs, and forces the promised retry. After a
completed retry, that newer completed entry becomes the governing result.

Bibliography audits get their own entry form, since they verify a
reference's identity rather than a claim (`references/bibliography-audit.md`
defines the pass and its verdicts):

```markdown
## [2026-08-15T11:12Z] bib:smith2021
entry-hash: 9c3d21e4ab07
source: doi:10.1145/1234567.1234568
registrar: Crossref
updates: none
verdict: discrepant
evidence: registrar title, authors, and DOI match the entry; year is 2021 in
  the entry, 2020 in the registrar record (online-first) — correction proposed
```

- `entry-hash` is the first 12 hex characters of the SHA-256 of the
  bibliography entry's effective source text — the BibTeX entry or
  reference-list item with any `@string`, `crossref`, or `xdata` indirection
  expanded to the referenced values, so editing a shared definition
  re-audits every entry that inherits from it — with runs of whitespace
  collapsed to single spaces and case preserved, the same hashing rule as
  `claim-hash`. An edited entry is audited fresh automatically.
- `source:` names the DOI the entry carries; for a DOI-less entry it names
  what the audit actually checked — the registrar record matched by search
  (`source: doi:10.1234/abcd — matched by search; proposed addition`), the
  entry's own URL (with `accessed:`), or `none found`.
- There is no `archived:` line: nothing is fetched beyond registrar metadata
  or the entry's own page, and the registrar fields quoted in `evidence:`
  are what a later audit needs.

A `bib:` entry reuses when the bibliography entry's current text still
hashes to the recorded `entry-hash` and the verdict is `confirmed` or
`discrepant` — and reuse re-queries the registrar's update relations exactly
as a DOI-backed `cite:` reuse does, so a retraction surfaces even for a
settled entry. The same staleness checks apply in miniature: a verdict
earned from the entry's own URL gets the mutable-URL re-fetch before reuse
(an unreachable page downgrades it to dated history), and a
registrar-backed verdict older than the header's `refresh-interval:` is
re-compared against a freshly fetched registrar record before reuse, since
metadata can be corrected without any update relation being deposited.
`mismatched` and `unconfirmed` verdicts are always retried —
registrar coverage grows and the author may have supplied context — with the
prior outcome still reported as dated history. Supersession for `bib:`
entries is by `entry-hash`: the newest entry for a hash governs.

Relocations get entries too, since past entries are never edited: when an
archived file moves (a fallback copy uploaded to the configured store once it
is reachable again), append a `relocation` entry, and let the reuse-time
archive check resolve a file through its newest relocation before comparing
hashes:

```markdown
## [2026-08-15T10:02Z] relocation — smith2021--10.1145_1234567.1234568-4b1f22aa.pdf
from: literature/sources/smith2021--10.1145_1234567.1234568-4b1f22aa.pdf
to: gs://bucket/prefix/smith2021--10.1145_1234567.1234568-4b1f22aa.pdf
sha256: 9f2a… (unchanged)
```

Successful refreshes are recorded the same append-only way: when a DOI-backed
file reaches its refresh interval, is re-fetched, and proves unchanged, append
a `refresh` entry so the refresh clock restarts — otherwise every later run
would re-download a source the cadence says to leave alone. The clock for a
file reads from its newest `refresh` entry, falling back to the original
verification's date:

```markdown
## [2026-08-15T10:20Z] refresh — smith2021--10.1145_1234567.1234568-4b1f22aa.pdf
checked: registrar updates none; re-fetched; sha256 unchanged (9f2a…)
```

Version sweeps (`references/version-reconciliation.md`) get their own entry
form, keyed by source identity and baseline — one entry per swept baseline
group, so a work read as two different revisions or snapshots yields two,
whatever the outcomes — recording what the sweep detected and which claims
it touches:

```markdown
## [2026-08-16T09:12Z] vor — arXiv:2106.05432
version-read: preprint (arXiv:2106.05432v2) — baseline sha256:4e7b…
published: doi:10.1109/tkde.2026.998877 — Crossref is-preprint-of relation
updates: none
archived: literature/sources/lee2026--10.1109_tkde.2026.998877-8e02d4b1.pdf sha256:66c0…
license: CC-BY-4.0
changed: sec. 5 rewritten; sec. 7 added; abstract reworded; later sections renumbered +1
claims: 19f3c07be2a4 affected — evidence sat in old sec. 5.1, passage reworded;
  5d80aa41c9e7 intact — passage unchanged, now sec. 3
status: re-checks proposed to the author; no verdict changed
```

```markdown
## [2026-08-16T09:12Z] vor — arXiv:2107.04567
version-read: preprint (arXiv:2107.04567v1) — baseline sha256:9c31…
published: none found — checked arXiv journal-ref, Crossref relations, bibliographic search
status: recorded; a later sweep may re-ask after ~6 months
```

- `published:` names the found version-of-record DOI — or, for a URL-backed
  target, the canonical URL now serving the fuller text, with the fetch date
  in the entry's `accessed:` field — and the channel that established it, or
  `none found` with the channels checked. When more than one authoritative
  publication relation exists (a conference version and a later journal
  version, say), record every match: the target is ambiguous, the choice of
  governing version goes to `Author decisions`, and no comparison runs
  until the author decides. `none found` is recorded only when
  every applicable channel actually ran: a transient channel failure
  (timeout, rate limit, outage) is recorded as `detection incomplete`,
  naming the failed channels — an outcome the next sweep retries, never a
  negative result that stands. When no version of record is found but the
  preprint server shows a newer revision than the baseline, `revised:`
  names it and the channel that showed it (`revised: arXiv:2107.04567v3 —
  arXiv abs page`); `changed:` and `claims:` then record the comparison
  against that revision exactly as for a publication, while `published:
  none found` still ages under the usual window for the publication
  channels only; the preprint server's metadata is re-checked on every
  sweep, so a later revision is never held to that window. When
  publication is established but only a paywalled copy exists, the found DOI
  is recorded with `text not legally reachable`: the paywall flow runs, and
  every dependent claim is affected pending the text.
- `changed:` is the section-level summary of the comparison; `claims:` lists
  each governing dependent entry resting on the source — identified by
  claim-hash for `cite:` and `uncited` entries, and by its normalized
  novelty claim (the heading with timestamp and `novelty — ` prefix
  stripped) for a novelty lead, whose form carries no claim-hash — marked
  `affected` or
  `intact` per the evidence-passage lookup. `updates:` carries the registrar
  update-relation outcome with the same semantics as a `cite:` entry.
- When the archived text the verdicts were earned on is confirmed missing
  or fails its SHA-256 check, the entry records an unreconcilable outcome
  in place of a comparison — `changed: not comparable — archived text
  failed its integrity check` — with every dependent claim `affected` and
  the broken archive raised in `Author decisions`. A store that simply
  cannot be checked this run (an outage, missing credentials) defers the
  comparison instead: the entry records the found publication with the
  diff pending, the outage is reported, and the next sweep completes the
  comparison — unreconcilable requires a confirmed missing file or hash
  mismatch, never an unreachable store. An unreconcilable entry is never
  treated as found-and-diffed: it stands as the dated record that
  publication was found, and the source leaves sweep scope only when
  re-verification lands fresh entries against the new text.
- A `vor` entry never changes a verdict. Supersession is by source identity
  plus the baseline read — the `version-read:` label together with the
  baseline sha256 it records: the newest entry for that pair governs, so a
  work verified against two different revisions, or two same-label
  snapshots with different hashes, keeps one governing entry per baseline,
  each comparing against the text its claims' verdicts were earned on. A `none found` outcome stands
  for about six months — publication lag is months, not days — so a sweep
  inside that window skips the target unless the author asks for a full
  re-sweep; a `text not legally reachable` outcome ages the same way, since
  open access appears on embargo timescales — but it is invalidated at once
  when the requested copy arrives in the source store: an author-supplied
  text is diffed on the next sweep or verification run, never held to the
  window. A URL-backed target's `none found` carries no shelf for its
  canonical URL either — that re-fetch is a single request, so every sweep
  re-runs it and a changed page invalidates the cached outcome; only the
  broader detection channels stay cached. A `detection incomplete` outcome
  never stands: the next sweep retries it. A found-and-diffed entry is not
  redone — provided its `claims:` list still covers every governing entry
  resting on that baseline. A claim verified against the baseline after the
  sweep reopens the target: the next sweep maps the new dependencies
  against the already-archived fuller text and recorded diff — no
  re-detection needed, but the standing freshness screens below apply to a
  reopened entry exactly as to a skipped one, so a stale or changed fuller
  text is re-fetched before any new claim is classified against it — and
  appends a fresh entry. An entry
  whose `updates:` line records a failed check is likewise not fully
  standing: the next sweep re-runs the registrar update screen — nothing
  else — and appends the outcome, the same healing a DOI-backed citation
  reuse gives its own failed screen. Standing is freshness-screened even
  when the last check succeeded, exactly as reusing a `cite:` entry is:
  before a sweep honors a found-and-diffed entry, re-query the registrar
  update relations for every DOI in the entry's version chain — the
  baseline's own DOI and each publication DOI, since notices attach to
  either side — and, when the found version's recorded fetch is older than
  the header's `refresh-interval:`, re-fetch and hash-compare the file per
  the refresh rules above, since silent replacements never surface as
  update relations; a URL-backed fuller text's page is re-fetched as well. A newly deposited retraction or erratum,
  a changed page, or hash drift ends the standing, is flagged to the
  author, and yields a fresh entry. The bridge
  stands until re-verification lands fresh entries with `version-read:
  version of record` against the source, which drops it out of sweep scope.

## Reuse rules

Consult the ledger after the claim inventory is pinned and before the first
search. Supersession is per `(claim-hash, source identity)` pair: the newest
entry for that pair governs, so a sentence that cites two works keeps one
live entry per work, and a newer check of one source never hides the other's.
The governing entry is reusable when all of these hold:

- the claim text still hashes to the recorded `claim-hash`;
- the bibliography still resolves the citation to the same work: the same
  DOI, or for DOI-less sources the same canonical URL as recorded — the
  archived copy's integrity is the separate check below, not the
  bibliography's identity;
- the recorded `version-read` is still the best text reachable: an entry
  earned on a preprint or an abstract-only read is retried, not reused, once
  a fuller text (the version of record, the full paper) may be available — an
  unchanged DOI never carries a preprint verdict onto the published version.
  When this predicate forces the retry, consult the `vor` entry governing
  this entry's own baseline — matched by source identity plus the recorded
  `version-read` and archived hash, never by source alone — first: a version
  sweep may already have archived the fuller text and recorded where the
  evidence passage moved, turning the retry into a targeted read instead of
  a fresh hunt;
- the archived copy still exists at its recorded path (or in the configured
  store) and matches its recorded SHA-256 — a verdict whose exact text can no
  longer be reopened is not reusable. When the store cannot be checked this
  run, the prior verdict may still be reported as dated history, but say the
  archive went unverified rather than presenting the entry as reused;
- the recorded verdict is supported, partially supported, or unsupported — an
  unverifiable verdict is always worth retrying, since access may have improved.

A reused verdict enters the citation audit with its original date, marked as
reused; it is never presented as fresh work. Re-verify regardless of the ledger
when the author asks or when the claim or bibliography entry changed. A
mutable-URL snapshot gets one extra check before reuse: re-fetch the live page
and compare it with the archived snapshot where the evidence sits — unchanged
means the verdict reuses, changed means fresh verification, and an unreachable
page downgrades the entry to dated history ("verified against the page as of
<date>"), never presented as current. A DOI-identified version of record
skips the per-reuse re-fetch but is not assumed immutable: when reusing it,
query the registrar's metadata for updates (errata, corrigenda, retractions,
replacement versions — Crossref's update relations, checked in both
directions per `references/source-archive.md`). An update means
re-fetch and re-verify, and any hash drift found on a re-fetch is handled per
`references/source-archive.md`. Declared updates are all the registrar can
show; silent replacements it cannot, so DOI-backed entries also get a
periodic content refresh: when the recorded fetch is older than the header's
`refresh-interval:` (in months; 12 when the field is absent), re-fetch the
file once and compare hashes — drift means a new dated copy and fresh
verification. Between refreshes the verdict still stands on the archived text
it was earned against; the refresh bounds how long a silent replacement can
go unnoticed.

Novelty scans go stale in a way citation checks do not — the literature moves.
Treat a novelty entry older than about six months as a starting point for a
fresh scan, not a current answer, and state the scan date whenever one is
reused. Supersession for novelty entries is by the quoted novelty claim
itself — the heading text after stripping the timestamp and the
`novelty — ` prefix, with runs of whitespace collapsed, since the form
carries no claim-hash and heading timestamps never repeat: the newest scan
for that normalized claim governs, and only the governing scan's leads
count as live dependencies anywhere else (the version sweep included) — an
older scan's leads are history, never current dependencies. Age is not the only predicate: reuse a novelty entry only when the
manuscript's novelty claim still reads as the recorded one and the entry's
`searched:` scope covers what the current request asks. A reworded
contribution, a new database, or a broadened boundary gets a fresh scan
whatever the entry's age — an old answer to a different question is not a
current answer to this one. Each retained lead must also pass the source
checks a `cite:` entry's source passes under the reuse rules above: its
archived copy present at its recorded path with a matching SHA-256, its
`version-read` still the best text reachable, the mutable-URL re-fetch and
refresh interval, and the registrar update screen for a DOI. A lead that
fails one is re-checked before the entry is reported as current; until
then the entry is history.

## Append, never rewrite

Entries are appended, and past entries are never edited or deleted: the
history of what was checked, when, and against which text is the point. When a
claim is re-verified against the same source, the newer entry for that
claim-and-source pair supersedes the older by its heading timestamp — headings carry date and time (UTC) precisely so that same-day
entries cannot tie ambiguously. If parallel runs both appended and the file
conflicts, keep both sets of entries in timestamp order; should two entries
for the same claim still carry the same timestamp with different verdicts,
neither is reusable — report the conflict to the author instead of silently
picking one.

## Machine-readable companion (JSONL)

The Markdown ledger is the record, and its stable field labels keep it
greppable; nothing more is required. When other tooling needs to consume
results without parsing Markdown, the project declares a companion file in
the ledger header (`companion: literature/verifications.jsonl`). While that
line is present, every ledger append also appends the matching lines to the
companion, in the same order, and the report names both files among the
writes. With no `companion:` line, no JSONL is written — that is the
default.

- **The path is validated before anything is written.** The `companion:`
  value must resolve to a repository-relative, non-symlink path inside the
  host repo, ending in `.jsonl`, and distinct from the manuscript, the
  bibliography, and every other existing file that is not already the
  companion. A value failing any of these checks gets nothing written —
  created, backfilled, or regenerated — and is reported in
  `Author decisions` instead: the rule that the skill never overwrites the
  author's files outranks the header.
- **Derived, never authoritative.** Runs consult only the Markdown ledger —
  reuse rules, supersession, and archive checks never read the companion.
  The JSONL is a view for external tooling: whenever the two disagree (a
  failed write, a merge that touched one file, a conflicted companion),
  regenerate the JSONL from the Markdown in full; never edit the Markdown
  to match the JSONL. The append-only rule protects the Markdown record —
  the companion, being derived, may be regenerated wholesale.
- **Enablement and backfill.** The author can ask the skill to enable the
  companion, or add the `companion:` header line by hand; either way, the
  next run creates the file and backfills one line per existing entry, in
  ledger order, before appending fresh work — a companion missing half the
  ledger is a trap for tooling. Adding the header line is an announced
  infrastructure edit, like the `AGENTS.md` pointer, never a silent one.
- **Line format.** One JSON object per ledger entry, one entry per line:
  - `ts`: the heading timestamp, verbatim (`2026-08-14T22:31Z`);
  - `type`: the entry form — `cite`, `uncited`, `novelty`, `bib`,
    `relocation`, `refresh`, or `vor`;
  - `heading`: the heading text after the timestamp, verbatim
    (`cite:smith2021 — introduction.tex:41`);
  - one key per field label, spelled exactly as in the Markdown (hyphens
    preserved: `claim-hash`, `version-read`), holding the value verbatim
    with continuation lines joined by single spaces — verbatim includes any
    surrounding quotes, which are part of the value, not Markdown syntax;
  - indented sub-fields flatten onto the same object — except under a
    repeatable label: a novelty entry's `lead:` blocks become a `leads`
    array (the one renamed key), one object per lead carrying the lead
    line under `lead` plus its indented sub-fields.

```json
{"ts":"2026-08-14T22:31Z","type":"cite","heading":"cite:smith2021 — introduction.tex:41","claim":"\"Smith et al. show that crowdsourced labels reach expert accuracy at one tenth the cost.\"","claim-hash":"ab12cd34ef56","source":"doi:10.1145/1234567.1234568","version-read":"version of record","archived":"literature/sources/smith2021--10.1145_1234567.1234568-4b1f22aa.pdf sha256:9f2a…","license":"CC-BY-4.0","updates":"none","verdict":"partially supported","evidence":"\"labels reached expert agreement on 3 of 5 tasks\" (sec. 5.1) — cost claim not addressed","notes":"cost figure may come from a different paper; asked author."}
```

Lines are appended, never edited, exactly like the entries they mirror;
supersession stays a reader concern, resolved by `ts` under the reuse
rules above. A conflicted or stale companion after parallel runs is
repaired the same way as any drift: merge the Markdown per the rules in
the previous section, then regenerate the JSONL from it.
