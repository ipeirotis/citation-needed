---
name: citation-needed
description: Verify whether sources support claims in a manuscript, investigate uncited factual claims, scan a stated contribution for overlapping prior work, audit bibliography metadata against DOI registrars to catch mangled, fabricated, or retracted references, or sweep the project's verification ledger for sources read as preprints or partial texts whose published or fuller version may since have become available. Use when the task requires retrieving and reading actual papers, authoritative sources, or registrar records, producing claim-level evidence and novelty leads. Maintains the host repo's literature archive (the exact text legally read, in a cloud bucket or repo folder) and a dated verification ledger, with an opt-in JSONL companion, so later runs reuse past results, when its validation and refresh rules confirm the evidence still stands, instead of repeating settled work. Do not use for prose editing, citation style formatting, number verification, data analysis, or unsupported citation judgments from memory.
---

# Citation Needed

Check manuscript claims against sources retrieved and read during the task, and bibliography entries against their DOI registrars' records. Treat citation verification as an evidence audit and novelty scanning as a search for leads, not a definitive priority verdict. Never silently edit the manuscript or its bibliography.

## Select a capability

1. **Verify citations:** map each in-scope manuscript claim to its cited source and classify support.
2. **Investigate an uncited claim:** retrieve candidate authoritative sources without inserting a citation automatically.
3. **Scan novelty:** search for overlapping prior work and return candidates for the author to assess.
4. **Audit bibliography metadata:** confirm each bibliography entry identifies a real work, its fields checked against its DOI registrar's record, without reading sources or checking claims.
5. **Reconcile versions of record:** sweep the host repo's verification ledger for sources read as preprints or partial texts, detect published or fuller versions now available, and flag the claims whose evidence sat in text that changed — re-checks are proposed, never performed silently.

If the request does not identify the manuscript claims, bibliography entries, or search scope, ask one focused question before retrieval.

## Gate the work

Require a retrieval surface that can search for and fetch the actual source text — for the bibliography audit, live registrar metadata; the version sweep needs the detection channels its targets require (registrar metadata for DOI-backed targets, plain fetch for URL-backed ones) plus text retrieval to diff, sweeping what it can reach and reporting the rest as unswept. If a source cannot be accessed, classify the claim as unverifiable — in a bibliography audit, the entry as unconfirmed; in a version sweep, record the text-unreachable outcome in the ledger without touching any claim's verdict; never substitute memory, a search snippet, or another paper's characterization. Ledger entries are the one exception: a past verification recorded in the host repo's ledger is dated evidence, not memory, and may be reported even when retrieval is unavailable — always with its date, never as fresh work.

Require also somewhere to write: the host repo's ledger for every capability, and the archive store for every capability that reads source text (all but the bibliography audit, which archives nothing). A session that can retrieve but cannot write what its capability needs stops before the first fetch and names what is read-only, since a fresh result without its ledger entry, or a verdict without its archived text, cannot be audited later. Reporting past ledger entries as dated history needs no write.

## Reuse before you retrieve

Before fetching anything, read the host repo's verification ledger (`literature/verifications.md`) if it exists; `references/verification-ledger.md` defines the format and the reuse rules. A claim already verified against the same source, or a bibliography entry already audited, is not re-checked once the ledger's validation and freshness checks all pass — where a check calls for a re-fetch (a mutable URL, an elapsed refresh interval, a registrar update query), that fetch happens first. Reused results are reported with their dates. This is what keeps repeated runs cheap and keeps the audit trail continuous across sessions.

## Run the protocol

For capabilities 1–3, read `references/literature-checks.md` before acting and follow its order: inventory claims, consult the ledger, verify cited claims, then scan novelty or fill gaps. For the bibliography audit, read and follow `references/bibliography-audit.md` instead: it checks entries against registrar metadata and reads no sources. For the version sweep, read and follow `references/version-reconciliation.md`: it sweeps the ledger, not the manuscript, and changes no verdicts. Every source read gets a resolvable locator (a DOI, or failing that a stable public URL) and an archived copy of the exact text read — full text when legally obtainable, otherwise the abstract or page snapshot that was actually reachable — per `references/source-archive.md` — a cloud bucket when the project has one configured, otherwise the host repo's `literature/sources/` folder. When the project declares a private store, rights-restricted material goes to the highest-ranked declared store that is both reachable and verified private, passing over one that is down or fails its privacy check; only when no declared store qualifies does work that needs a restricted source keep no copy and record each capability's can't-complete outcome instead (`references/source-archive.md` lists them). A project with no private store keeps restricted copies in an ignored `literature/sources/` folder, under the same reference's ignore check. Paywalled sources are requested from the author, never bypassed. Keep proposed citation or claim changes visibly separate from findings.

After the inventory and ledger-reuse pass pin the remaining work, follow `references/parallel-retrieval.md`: when subagents are available, launch one worker per distinct source (or per bibliography entry or version baseline as that protocol defines), concurrently up to the platform limit. For capabilities 1–3, finish and validate the citation-source stage before launching one worker per novelty or uncited-claim question with that evidence available. The coordinator remains the sole ledger writer and validates every worker result before reporting. If subagents are unavailable, use the same staged work units sequentially and disclose that execution mode.

## Return

Return exactly:

1. **Scope and retrieval:** claims checked (marking which were reused from the ledger), search boundaries, sources fetched and archived, and access failures.
2. **Citation audit:** one row per claim and cited source, so a claim citing several works gets a row per work and an unsupported citation never hides behind a supporting one; each row classified as supported, partially supported, unsupported, or unverifiable, with evidence; reused rows carry their original verification date.
3. **Novelty and source leads:** candidate work, overlap, and why the author should inspect it; never claim exhaustive novelty.
4. **Author decisions:** flagged citation or wording candidates, requests for paywalled PDFs the author must supply, and unresolved questions. Nothing is edited automatically.

A bibliography audit instead returns exactly the three sections defined in `references/bibliography-audit.md`: **Scope and lookups**, **Bibliography audit** (the entry-level table), and **Author decisions**. A version sweep likewise returns the three sections defined in `references/version-reconciliation.md`: **Scope and detection**, **Version reconciliation**, and **Author decisions**.

Append the fresh results to the host repo's ledger as dated entries and confirm the writes landed *before* returning the report — on platforms where the report ends the turn, an append promised for afterward never happens. The report then names the files actually written — the host repo's `literature/verifications.md`, the JSONL companion when the ledger header declares one, and any archived copies — with the entry format, reuse rules, and companion rules defined in `references/verification-ledger.md`.
