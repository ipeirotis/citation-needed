# Source archive: locators, legal full text, and storage

A verification is only auditable if the exact text that was read is preserved.
Links rot, publisher pages change, and preprints get revised; the archived copy
is what lets the author, a coauthor, or a later run re-open precisely what this
run read. Every source reported on therefore gets two things: a publicly
resolvable locator and an archived full-text copy in the project's source
store.

## Locator requirement

Every source needs a locator a stranger could resolve:

- **DOI, preferred.** Resolve it (follow `https://doi.org/<doi>`) and
  cross-check its metadata against the registrar that actually issued it:
  look up the registration agency first (`https://doi.org/ra/<doi>`) and
  query that agency's API — Crossref for most journal articles, DataCite for
  most datasets and reports, with mEDRA and others in the long tail — rather
  than assuming Crossref for everything. The registrar's metadata must
  identify the same work the bibliography entry describes — judged on the
  whole record, not field-by-field equality. An abbreviated venue, an
  online-first versus print year, or a small title typo with matching authors
  is still the intended work: verify the claim, and flag the bibliography
  discrepancy as a proposed correction in `Author decisions`. Only a DOI that
  resolves to a different work, or to nothing, marks the reference wrong or
  fabricated and keeps it out of the archive. A DOI registered outside
  Crossref is a valid DOI, not a suspect one. While at the registrar, check
  the work's update relations — retractions, errata, corrigenda, expressions
  of concern (Crossref's update metadata incorporates the Retraction Watch
  database). Check both directions where the registrar supports it: the work
  record's own update fields (Crossref's `updated-by`) and a reverse query
  for notices declaring an update to this DOI (Crossref's
  `filter=updates:<doi>`), because the relation is often deposited only on
  the later notice and the original record alone can miss it. An update
  never blocks verification — the verdict still comes
  from reading the text — but it travels with the verdict: record it in the
  ledger entry's `updates:` field and raise it in `Author decisions`, because
  a supported claim resting on a retracted source deserves a flag of its own.
- **Stable public URL, fallback.** For sources without a DOI (standards pages,
  arXiv abstracts, documentation, reports), record the canonical URL and the
  access date — the date goes in the ledger entry's `accessed:` field. Prefer
  the most durable form of the URL (an arXiv abs page over a mirror, a
  versioned document over a landing page).
- **Neither.** A reference that resolves to no DOI and no reachable URL is
  unverifiable. Ask the author what the citation points to; do not guess.

## Finding a legal full text

Search for an open, legitimate copy before involving the author, in this
order:

1. The publisher's own open-access link from the DOI resolution.
2. Unpaywall (`https://api.unpaywall.org/v2/<doi>?email=<contact>`), which
   returns the best legal open-access location and the license when one exists.
3. Preprint servers (arXiv, bioRxiv, SSRN) and the authors' own pages, checking
   that the copy found actually corresponds to the cited work. When only a
   preprint of a published paper is available, it may differ from the version
   of record: note which version was read in the ledger entry.

Never bypass a paywall, never present credentials, and never use pirate
mirrors. When only a paywalled copy exists, the request goes to the author in
`Author decisions`: ask them to download the PDF through their own access (or
print the page to PDF for web sources) and place it in the source store, naming
the exact path expected. A supplied copy is verified before it is believed:
check its title, authors, year, and any embedded DOI against the bibliography
and the registrar record — the same identity check a preprint gets — and send
a mismatched or mislabeled file back to the author rather than reading it as
evidence under the requested key. Until the copy arrives, the claim is verifiable only
to whatever was legally reachable (usually the abstract) and is classified
accordingly. Whatever was legally read still gets archived: snapshot the
abstract or landing page exactly as a mutable web source (see the snapshot
rules below), append `--abstract` before the date-and-hash suffix, and record
it in the ledger with `version-read: abstract-only`, so even a partial
verification points at preserved text.

For non-paper web sources that are freely reachable, take the snapshot
directly: print the page to PDF with a headless browser when one is available,
otherwise save the fetched HTML or extracted text. Snapshots carry their access
date in the filename, since the live page can change.

## Choosing the store

Decide once per project, in this order, and record the choice in the ledger
header so later runs land in the same place:

1. **Explicit configuration.** A store declared by the project wins, and when
   declarations disagree the order is fixed: the `store:` line in the ledger
   header (`literature/verifications.md`) outranks the host repo's
   `AGENTS.md` literature section, which outranks a `LITERATURE_STORE`
   environment variable. The ledger header is where the existing archive
   already lives, and evidence continuity beats per-run convenience. Use the
   highest-ranked reachable declaration for this run and report any conflict
   among them in `Author decisions` rather than resolving it silently. A
   fresh ledger header still records the highest-ranked declaration, not a
   lower one used because it was down (`verification-ledger.md`). A declaration names
   a `gs://bucket/prefix`, an `s3://bucket/prefix`, or a repository-relative
   path such as `literature/sources/` — the recorded form of the repo-folder
   default, which is valid header syntax, not an error.
2. **Confirm access before trusting it.** Verify the tool and credentials
   actually work (`gcloud storage ls` / `gsutil ls` for GCS, `aws s3 ls` for
   S3) before uploading. If the configured store is unreachable, fall back to
   the repo folder and say so in the report rather than failing silently.
   The fallback is license-aware: rights-restricted material never falls
   back into the repository worktree, ignored or not. The host chose a
   private store for it, and an ignored file still sits where cleanup,
   backups, artifact collection or a changed ignore rule can expose it. While
   the private store is unreachable, or not yet verified private (see
   "Private bucket" below), work that needs a restricted source waits: keep
   no copy anywhere and record no result drawn from that text. This governs
   fresh work that has to read and archive a text; an existing verdict whose
   archive sits in the unreachable store follows the ledger's reuse rule
   instead (reported as dated history with its archive unverified, and no
   new entry). For fresh work, report each
   capability's usual can't-complete outcome with the store as the reason:
   `unverifiable` for citation verification, **search incomplete** (never
   reusable) for an uncited-claim investigation or novelty scan, and for a
   version sweep `detection incomplete` naming the store outage, which the
   next sweep retries (not the text-unreachable outcome, whose reuse window
   would hold it for months) and which changes no dependent verdict. That
   last outcome is for a newer version whose restricted text cannot be
   archived. When the newer text is archived (for instance it is freely
   redistributable and takes the repo-folder fallback) and only the old
   baseline sits in the unreachable store, the comparison is deferred with
   the diff pending, as `version-reconciliation.md` step 3 says. A later run with a working store does the
   work and archives the evidence together; a result is only recorded with
   its archived evidence (see `verification-ledger.md`). Only freely redistributable material takes the
   ordinary repo-folder fallback. A
   fallback is a per-run exception, never a new project choice: the
   configured store stays authoritative in the ledger header, the run's
   entries record the fallback paths actually used, and the report flags the
   stray copies so a later run with a working store can upload them and
   append a dated `relocation` entry per the ledger's entry forms — the
   archive check on reuse follows a file's newest relocation entry, so paths
   move without rewriting history.
3. **Repo folder fallback.** With no configured bucket, archive into
   `literature/sources/` at the host repo root.

## Naming and integrity

- A filename is a readable label plus a mandatory identity hash, and
  uniqueness lives entirely in the hash, never in the label. Every archived
  file's base name is `<key>--<slug>-<id8>`:
  - `<key>`: the citation key, put through the same character rule as the
    slug (lowercased, every character outside `a-z 0-9 . _ -` replaced by
    `_`, so a key like `group/paper2024` cannot open a subdirectory) and
    truncated to 40 characters.
    A source outside the bibliography uses the synthetic key (first author's
    family name plus year from registrar metadata, `doe2023`); with no usable
    metadata, the key part is omitted.
  - `<slug>`: the DOI with `/` replaced by `_`, or without a DOI the title —
    lowercased, every character outside `a-z 0-9 . _ -` replaced by `_`, and
    truncated to 60 characters. The slug is a human-readable label only.
  - `<id8>`: the first 8 hex characters of the SHA-256 of the source's
    canonical identity, computed before any sanitization — the raw DOI
    string, else the canonical URL, else the original citation key plus
    title. Two sources whose labels collide in any way (same title, keys
    differing only by case, DOIs that sanitize alike) still get distinct
    names, deterministically, with no dependence on what the archive already
    contains or which source arrived first.
  The truncation caps bound every base name well under common 255-byte
  filename-component limits, and the same rule covers every case — cited or
  not, DOI or not (for example
  `smith2021--10.1145_1234567.1234568-4b1f22aa.pdf`). Snapshots of mutable
  pages additionally append the access date and the first 8 hex characters
  of the file's own SHA-256 (`--2026-08-14-9f2a3c1d`), so two same-day
  fetches that differ can never share a name; abstract snapshots insert
  `--abstract` before that suffix.
- Compute the SHA-256 of every archived file and record it in the ledger entry.
  The hash is what lets a later run confirm it is looking at the same text: on
  re-download, compare hashes, and if they differ, save the new copy under the
  same date-and-hash suffix scheme as snapshots
  (`smith2021--10.1145_1234567.1234568-4b1f22aa--2026-08-15-4e7b21aa.pdf`)
  instead of overwriting — the original stays untouched at its recorded path so the text
  that was actually audited stays reopenable — and note the change in the
  ledger. A publisher silently replacing the PDF behind a DOI, or a revised
  preprint, is exactly the drift the hashes exist to catch.

## Copyright and repo hygiene

- Free to read is not free to redistribute. Record the license Unpaywall or
  the publisher reports in the ledger entry's `license:` field, and commit a
  copy to a public repo only when that license explicitly permits
  redistribution (CC BY and kin). A paper that is
  merely readable on the publisher's site with no such license is treated
  like a paywalled one for storage purposes: private bucket, `.gitignore`d
  local folder, or quotes and metadata only. The ignored local folder is an
  option only for a host with no private store configured; a host that has
  one keeps restricted material out of its worktree entirely (step 2 above
  covers an outage of that store). Before writing a restricted copy to that
  folder, confirm the ignore rule actually covers the path
  (`git check-ignore -q <path>`); if it does not, add the rule first or keep
  quotes and metadata only, since an unignored PDF is one `git add` away
  from a public commit.
- A paywalled or rights-restricted PDF committed to a **public** repository is
  republication, and the author's consent does not change that: approval is
  not a license. When no redistribution license exists, the public repo is
  simply off the menu — use a private bucket, a `.gitignore`d local
  `literature/sources/` (archived on the author's machine but not pushed;
  only when no private store is configured), or the quotes-only artifact. The one exception is an author who actually holds
  the needed rights — their own accepted manuscript under a publisher
  self-archiving policy, material whose copyright is theirs — and that
  asserted basis is recorded in the entry's `license:` field, because it is
  the authorization a later audit will need.
- The quotes-and-metadata fallback is itself an archived artifact, not a gap
  in the archive: write `<base-name>--quotes.md` (base name per the naming
  rules above) containing the locator, the version consulted, the access
  date, and each quoted passage with its page or section; hash and record it
  like any other archived file, with `license: restricted — quotes only`.
  The hashed quotes file is what keeps such verifications reusable. Brevity
  and attribution make quotation defensible in many jurisdictions, not lawful
  in all of them, so the quotes artifact follows the same storage rule as any
  restricted material by default — private store, or ignored local folder
  only when no private store is configured —
  and lands in a public repo only when the author, told the basis is
  quotation rather than a license, explicitly decides so.
- "Private bucket" is verified, not assumed. A configured bucket counts as
  private for restricted material only after its access controls check out —
  public-access prevention or the absence of `allUsers`-style grants on GCS,
  the public-access block on S3 — because reachability and working
  credentials prove nothing about visibility. When the check cannot be run or
  is inconclusive, ask the author to confirm the bucket is private before
  uploading anything rights-restricted: a publicly readable bucket
  republishes a PDF as surely as a public repo does. Until it is confirmed
  (or when it proves public), restricted material is handled exactly as
  during a store outage (step 2 of "Choosing the store").
- PDFs are binary and repos bloat: before committing any single file over
  ~10 MB, or once the archive folder crosses ~100 MB, raise Git LFS or a bucket
  with the author instead of pushing silently.
