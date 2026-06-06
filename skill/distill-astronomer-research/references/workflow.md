# Workflow

## 1. Initialize

Run:

```sh
python3 scripts/init_astronomer_project.py \
  --project-dir /path/to/astronomer-folder \
  --display-name "Author Name" \
  --skill-name author-research \
  --orcid 0000-0000-0000-0000 \
  --email author@example.edu \
  --legacy-email old-address@example.edu
```

Edit `config/astronomer.json` as new affiliations, email markers, or PDF fallback
URLs are discovered.

## 2. ADS Access Preflight

Run:

```sh
python3 /path/to/skill/scripts/check_ads_access.py
```

The script checks `ADS_DEV_KEY`, `ADS_TOKEN`, and the Apple Keychain service
`ads-api-token`. If no token is found, ask the user to add one before claiming
that ADS author search or the ADS corpus is complete. A fallback corpus built
from local seeds or OpenAlex must be labeled incomplete.

In a managed Codex sandbox, reading the macOS Keychain may require an escalated
command. If the preflight reports missing keychain token but the user says they
added one, rerun the preflight with approval rather than assuming the token is
absent.

## 3. Collect ADS Records

Prefer an ADS library linked by an official profile. Save the normalized browser
scrape as `metadata/ads_official_library.json`.

Also save:

- `metadata/ads_author_search.json`
- `metadata/ads_first_author_search.json`
- `metadata/ads_correspondence_search.json`
- `metadata/ads_correspondence_search_legacy_email.json`, when applicable

Use [ads-collection.md](ads-collection.md) for the expected JSON shape.
The collection script defaults to `--database astronomy`, so routine astronomer
queries exclude ADS physics/general spillover before identity filtering. Use
`--database all` only for explicit spillover audits or genuinely cross-database
publication sets.

Do not stop after finding several representative papers. The collection target is
the broad ADS corpus for the identity, with same-name rejects documented separately.
If ADS API or browser access is unavailable, create an explicit exception and use
OpenAlex, ORCID, publisher pages, or official publication lists only as audit
helpers until ADS can be checked.

Before falling back to web indexes, also harvest local cross-seeds from existing
astronomer projects and installed skills:

```sh
python3 /path/to/skill/scripts/harvest_local_corpus_seeds.py \
  --project-dir . \
  --output metadata/local_corpus_seed_records.json
```

This scans local JSON corpora such as `metadata/ads*.json`,
`metadata/paper_manifest.json`, and future installed-skill `corpus-records.json`
files for the configured name variants. Local cross-seeds are supplemental:
use them to discover missing ADS records, not as a replacement for ADS author
searches.

Before building the download manifest, make the identity anchors explicit in
`config/astronomer.json`: official/historical affiliations, full and initial-only
name variants, recurring topic keywords, stable coauthors, journal or venue
signals, and same-name reject keywords. Then filter the raw ADS sources:

```sh
python3 /path/to/skill/scripts/filter_ads_identity_candidates.py \
  --input metadata/ads_author_search.json \
  --input metadata/ads_first_author_search.json \
  --input metadata/local_corpus_seed_records.json \
  --config config/astronomer.json \
  --accepted metadata/ads_identity_filtered_records.json \
  --rejected metadata/ads_identity_rejected_records.json \
  --first-author-bibcodes metadata/verified_first_author_bibcodes.txt
```

Treat this as a reproducible same-name audit. The accepted file feeds the full
PDF audit; the rejected file documents false positives and ambiguous records.
When current or historical email-marker ADS searches exist, pass those JSON files
as additional `--input` arguments to the same filtering command before building
the audit manifest.

## 4. Audit Full Text

From the astronomer project directory, run the bundled scripts:

```sh
python3 /path/to/skill/scripts/build_ads_audit_manifest.py \
  --library metadata/ads_identity_filtered_records.json
python3 /path/to/skill/scripts/download_public_pdfs.py \
  --manifest metadata/correspondence_audit_manifest.json \
  --papers-dir correspondence_audit/papers \
  --report metadata/correspondence_audit_download_report.json \
  --workers 6 \
  --max-time 45 \
  --gateway-max-time 15 \
  --record-timeout 90 \
  --max-attempts-per-record 3
python3 /path/to/skill/scripts/extract_pdf_texts.py \
  --papers-dir correspondence_audit/papers \
  --text-dir correspondence_audit/text \
  --report metadata/correspondence_audit_text_extract_report.json
python3 /path/to/skill/scripts/verify_correspondence_markers.py
python3 /path/to/skill/scripts/audit_corpus_completeness.py
```

The download step is for every publicly accessible non-conference PDF in
`metadata/correspondence_audit_manifest.json`, not only the papers that look
lineage-defining. Use representative subsets only later, during deep reading.
If some records are unavailable, keep the download report and completeness audit
as the provenance. The downloader reports progress as records complete, tries
arXiv PDF links before ADS gateway and publisher links when ADS identifiers expose
an arXiv ID, and uses short gateway/record timeouts so refused or slow publisher
links do not block the whole corpus.

Meeting abstracts, conference records, and symposium proceedings are excluded
from the PDF audit manifest by default and written to
`metadata/conference_records_excluded_from_audit.json`. They are usually superseded
by later papers and should not consume download or correspondence-audit effort.
Only pass `--include-conference-records` when the user explicitly requests a
conference-proceedings audit.

Corresponding-author review is required, not optional. After text extraction,
`verify_correspondence_markers.py` scans the audit corpus for explicit
corresponding-author wording and configured current or historical email markers.
Keep these evidence levels separate: explicit wording can promote
`explicit_corresponding_author`; first-page or PDF email hits remain
`pdf_email_marker` until manually reviewed.

## 5. Build Formal Manifest

Create `metadata/verified_first_author_bibcodes.txt` after ADS author-order and
identity checks. Then run:

```sh
python3 /path/to/skill/scripts/build_formal_manifest.py
python3 /path/to/skill/scripts/generate_paper_index.py
```

The formal manifest can be smaller than the audit corpus when it contains only
confirmed first-author and corresponding-author roles. If so, label it as a
curated core or role-confirmed manifest in `README.md`, `source-policy.md`, and
`paper-index.md`; do not call it the complete publication list.

## 6. Distill

Generate the reusable review assets first:

```sh
python3 /path/to/skill/scripts/generate_research_assets.py \
  --lineage skill/<author-skill>/references/method-lineage.md \
  --profile-md skill/<author-skill>/references/researcher-profile.md \
  --graph-md skill/<author-skill>/references/collaboration-map.md \
  --holdout-md skill/<author-skill>/references/holdout-evaluation.md
python3 /path/to/skill/scripts/build_method_graph.py \
  --lineage skill/<author-skill>/references/method-lineage.md \
  --markdown-output skill/<author-skill>/references/method-graph.md
python3 /path/to/skill/scripts/generate_rolling_holdout.py \
  --output skill/<author-skill>/references/rolling-holdout-evaluation.md
python3 /path/to/skill/scripts/render_deep_cards.py \
  --cards distillation/deep-paper-cards.json \
  --output skill/<author-skill>/references/deep-paper-cards.md
python3 /path/to/skill/scripts/extract_citation_contexts.py \
  --seeds distillation/core-citation-context-seeds.json \
  --text-dir text \
  --output-json metadata/core-citation-contexts.json \
  --output-md skill/<author-skill>/references/core-citation-contexts.md
python3 /path/to/skill/scripts/render_method_boundaries.py \
  --boundaries distillation/method-boundaries.json \
  --output skill/<author-skill>/references/method-boundaries.md
python3 /path/to/skill/scripts/render_version_relations.py \
  --relations distillation/version-relations.json \
  --output skill/<author-skill>/references/version-relations.md
python3 /path/to/skill/scripts/render_claim_ledger.py \
  --ledger distillation/atomic-claims.json \
  --output skill/<author-skill>/references/atomic-claim-ledger.md
python3 /path/to/skill/scripts/refresh_distillation_assets.py \
  --project-dir . \
  --lineage skill/<author-skill>/references/method-lineage.md \
  --skill-dir skill/<author-skill>
```

Read representative PDFs across time, not only highly cited or recent papers.
Write:

- `distillation/method-synthesis.md`
- `skill/<author-skill>/references/research-map.md`
- `skill/<author-skill>/references/method-lineage.md`
- `skill/<author-skill>/references/method-playbook.md`
- `skill/<author-skill>/references/source-policy.md`

Review and complete analytical fields in `distillation/paper-cards.json` for
lineage-defining papers. Use `metadata/evidence-ledger.jsonl` for claim provenance.
Complete `references/holdout-review.md` after comparing the provisional lineage
with held-out later papers. Review `metadata/external-comparison-candidates.json`
and keep a curated method-level subset in `references/external-comparison-set.md`.
Complete `references/rolling-holdout-review.md` for multiple cutoff years when
the corpus spans enough time. Treat graph edge semantics as heuristic unless
manually checked or overridden in project configuration.
Keep full-text deep cards separate from generated skeletons so that refreshes do
not overwrite manual reading. Ask the user only about citation-context ambiguity
that would materially change the method lineage.
Maintain `references/refresh-protocol.md` and `references/exceptions.md`.
Explicitly abstain when user data are outside the validated domain with no
justified fallback. Preserve external conflicts instead of forcing agreement.

## 7. Validate

```sh
python3 /path/to/skill/scripts/validate_lineage_refs.py
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skill/<author-skill>
```

Review the diff and sync the derived skill to `~/.codex/skills/<author-skill>`
only after the evidence and lineage are coherent.

## 8. Refresh

After collecting a newer ADS snapshot, rerun the asset generator. Inspect
`metadata/update-report.json` for added and removed bibcodes, update cards and
lineage where needed, then rerun holdout review.
Refresh the bounded method graph and rolling holdout review when the active
lineage changes materially.
Refresh boundaries, version relations, atomic claims, and exceptions whenever
new evidence changes a recommendation or failure mode.
Use the conservative refresh command after ADS and PDF preflight. It does not
collect ADS records, download PDFs, or refresh the network-backed OpenAlex graph
unless explicitly requested with `--include-method-graph`.
