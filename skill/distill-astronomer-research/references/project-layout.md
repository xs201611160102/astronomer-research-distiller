# Project Layout

```text
<astronomer>/
├── README.md
├── config/
│   └── astronomer.json
├── metadata/
│   ├── ads_official_library.json
│   ├── correspondence_audit_manifest.json
│   ├── correspondence_audit_download_report.json
│   ├── correspondence_audit_text_extract_report.json
│   ├── corpus_completeness_audit.json
│   ├── corpus_completeness_audit.md
│   ├── correspondence_audit_verification.json
│   ├── evidence-ledger.jsonl
│   ├── research-graph.json
│   ├── method-graph.json
│   ├── external-comparison-candidates.json
│   ├── core-citation-contexts.json
│   ├── manual-review-queue.json
│   ├── distillation-snapshot.json
│   ├── update-report.json
│   ├── paper_manifest.json
│   └── verified_first_author_bibcodes.txt
├── correspondence_audit/
│   ├── papers/
│   └── text/
├── papers/
├── text/
├── distillation/
│   ├── method-synthesis.md
│   ├── paper-cards.json
│   ├── paper-cards.md
│   ├── deep-paper-cards.json
│   ├── core-citation-context-seeds.json
│   ├── method-boundaries.json
│   ├── version-relations.json
│   └── atomic-claims.json
└── skill/
    └── <author-skill>/
        ├── SKILL.md
        └── references/
            ├── researcher-profile.md
            ├── collaboration-map.md
            ├── holdout-evaluation.md
            ├── method-graph.md
            ├── external-comparison-set.md
            ├── rolling-holdout-evaluation.md
            ├── rolling-holdout-review.md
            ├── deep-paper-cards.md
            ├── core-citation-contexts.md
            ├── method-boundaries.md
            ├── version-relations.md
            ├── atomic-claim-ledger.md
            ├── refresh-protocol.md
            ├── exceptions.md
            └── manual-review-queue.md
```

Keep audit downloads separate from formal evidence. The audit area should attempt
to cover every publicly downloadable PDF in the merged ADS corpus. Only copy
promoted records into `papers/` and `text/`, and clearly label that promoted set
as a curated core when it is smaller than the audit corpus.

Download, text-extraction, and correspondence reports use `{summary, records}`.
The formal manifest may include `record_flags` and `distillation_tier:
supplemental` for software, catalogs, theses, awards, reviews, and proceedings
context records.
