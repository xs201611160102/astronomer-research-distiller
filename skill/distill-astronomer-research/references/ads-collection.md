# ADS Collection

## Preferred Sources

Use this order:

1. ADS library linked from an official institutional profile.
2. ADS author search with affiliation and topic checks.
3. ADS first-author search.
4. ADS full-text searches for current and historical email markers.
5. ORCID, publisher pages, OpenAlex, and Crossref as audit helpers.

ADS API access may require a token. When unavailable, use the logged-in browser
session and save a normalized JSON scrape.

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

## Identity Checks

Reject same-name records when affiliation, topic, coauthor network, ORCID, or
publication history conflicts with the target identity. Keep a short audit note
for ambiguous records.

