# ADS Collection

## Preferred Sources

Use this order:

1. ADS library linked from an official institutional profile.
2. ADS author search with affiliation and topic checks.
3. ADS first-author search.
4. ADS full-text searches for current and historical email markers.
5. ORCID, publisher pages, OpenAlex, and Crossref as audit helpers.

ADS API access requires a token for reliable scripted collection. Run
`scripts/check_ads_access.py` first. It checks `ADS_DEV_KEY`, `ADS_TOKEN`, and
the Apple Keychain service `ads-api-token`. If no token is available, ask the
user to provide one before claiming ADS completeness. A logged-in browser scrape
can be used as a fallback, but it must be recorded as an exception.
When running inside Codex, macOS Keychain reads may need approval outside the
sandbox; rerun the preflight with escalation before concluding that the token is
missing.

Completeness rule: collect enough ADS sources to cover the identity broadly before
distillation. At minimum, merge the official ADS library when available with ADS
author search and first-author search results. The correspondence/email searches
are role-evidence searches, not complete bibliography searches.
`collect_ads_records.py` defaults to `--database astronomy`, which appends
`database:astronomy` to API queries unless the query already contains an explicit
`database:` term. Use `--database all` only when auditing same-name spillover or
when the target has important cross-disciplinary publications that ADS classifies
outside the astronomy database.
When current or historical email addresses are known, run ADS full-text searches
for those markers and feed the resulting JSON through the same identity filter.
Those records help recover possible corresponding-author evidence, but final role
promotion still depends on PDF text verification or publisher-page wording.

Local cross-seeds from already distilled astronomer projects or installed skills
are allowed as supplemental discovery aids. They must be produced by
`harvest_local_corpus_seeds.py` or an equivalent source that preserves bibcode,
title, authorship text, links, and source provenance. Do not hard-code one
astronomer's library as the general source.

## Normalized Record Shape

Each ADS record should use:

```json
{
  "bibcode": "2024ApJS..271...41X",
  "title": "Paper title",
  "first_author": "Surname, Given",
  "authors_display": "Surname, Given; ...",
  "links": [
    {
      "href": "https://ui.adsabs.harvard.edu/link_gateway/.../EPRINT_PDF",
      "text": "Preprint PDF"
    }
  ]
}
```

The scripts tolerate missing `first_author`, but require `bibcode`, `title`, and
`links`.

Pass every collected normalized ADS source to `build_ads_audit_manifest.py` with
repeated `--library` arguments. The script de-duplicates by bibcode and preserves
source provenance in `role_evidence`.
Meeting abstracts, conference records, and symposium proceedings are excluded
from the PDF audit manifest by default and saved separately as
`metadata/conference_records_excluded_from_audit.json`. Treat them as provenance
or supplemental leads, not as download targets, unless the user explicitly
requests `--include-conference-records`.

The audit manifest includes arXiv PDF URLs when ADS identifiers contain arXiv
IDs. `download_public_pdfs.py` orders links arXiv-first, then ADS EPRINT gateway,
then configured fallback and publisher-style links. Its progress output and
gateway/record timeouts are part of the corpus audit: preserve the download
report even when some URLs are refused or skipped as long-tail failures.

## Identity Checks

ADS name searches can return same-name and same-initial authors, including records
from non-astronomy fields. Make identity filtering a reproducible configuration
step instead of a one-off manual judgment.

Fill `config/astronomer.json` with:

- `name_variants`: full ADS author-name variants.
- `identity_filter.first_author_initial_variants`: initial-only forms to accept
  only when other identity signals agree.
- `identity_filter.topic_keywords`: recurring astronomy topics, instruments,
  surveys, methods, and objects from the target's official profile and papers.
- `identity_filter.trusted_coauthors`: stable collaborators that recur across
  multiple career stages.
- `identity_filter.affiliation_keywords`: official and historical institutions.
- `identity_filter.reject_keywords`: non-target fields that appear in ADS raw
  results for the same name.

Then run:

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

Use `metadata/ads_identity_filtered_records.json` as the ADS source for the audit
manifest. Keep `metadata/ads_identity_rejected_records.json` so future refreshes
can explain why same-name records were excluded. Review low-score accepted records
and high-score rejected records manually before treating the corpus as complete.
