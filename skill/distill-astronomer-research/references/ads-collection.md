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

## Identity Checks

Reject same-name records when affiliation, topic, coauthor network, ORCID, or
publication history conflicts with the target identity. Keep a short audit note
for ambiguous records.
