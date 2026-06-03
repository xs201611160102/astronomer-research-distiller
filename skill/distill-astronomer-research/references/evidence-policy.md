# Evidence Policy

## Role Levels

- **first_author_verified**: ADS author order plus identity check.
- **explicit_corresponding_author**: PDF or publisher page explicitly says
  corresponding author, co-corresponding author, or equivalent Chinese wording.
- **pdf_email_marker**: first-page PDF text contains a configured current or
  historical contact email. This is useful evidence, but recheck the PDF or
  publisher page when strict role distinctions matter.
- **metadata_candidate**: OpenAlex, Crossref, ADS full-text query, or another
  metadata source suggests a role. Do not promote without primary evidence.

## Rules

1. Record provenance for every promoted role.
2. Keep explicit wording and email-marker evidence separate.
3. Search historical email addresses and affiliations.
4. Treat conference abstracts, errata, data catalogs, and full papers as
   different publication types.
5. Do not infer corresponding authorship from author position.
6. Do not infer identity from initials alone.
7. In astronomy, prioritize first-author and corresponding-author papers. Track
   at most the first three listed authors for collaboration context unless the
   project explicitly needs a broader network.
8. Store ORCID as an identity anchor when available. Do not assume ORCID coverage
   is complete.
