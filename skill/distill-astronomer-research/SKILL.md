---
name: distill-astronomer-research
description: Build a traceable Codex skill from an astronomer's papers. Use when the user asks to download, organize, audit, or distill an astronomer's publications, especially from ADS; identify first-author or corresponding-author papers; handle author-name ambiguity; extract PDF text; separate explicit corresponding-author evidence from email-marker evidence; synthesize research themes; or construct a chronological method lineage with baseline methods, refinements, validation layers, and fallback versions.
---

# Distill Astronomer Research

Create one project folder per astronomer and produce an installable research-method
skill. Prefer NASA ADS for astronomy bibliography and preserve evidence provenance.

## Start Here

1. Read [workflow.md](references/workflow.md) before starting a new astronomer.
2. Read [ads-collection.md](references/ads-collection.md) when collecting ADS records.
3. Read [evidence-policy.md](references/evidence-policy.md) before assigning authorship roles.
4. Read [distillation-guide.md](references/distillation-guide.md) before writing the derived skill.
5. Read [project-layout.md](references/project-layout.md) before creating files.
6. Read [branch-evaluation-protocol.md](references/branch-evaluation-protocol.md)
   before generating the review workflow of a derived skill.

## Required Workflow

1. Create a project with `scripts/init_astronomer_project.py`.
2. Confirm identity from an official profile, ORCID, ADS library, affiliations, and
   topic continuity. Record uncertainty instead of guessing.
3. Collect the official ADS library when available. Supplement it with ADS author
   and first-author searches.
4. Build an ADS audit manifest and download publicly accessible PDFs.
5. Extract PDF text and scan current plus historical email markers.
6. Separate:
   - first-author records confirmed from ADS author order and identity checks;
   - explicit corresponding-author wording;
   - PDF first-page email-marker evidence;
   - unverified metadata candidates.
7. Build the formal paper manifest from confirmed roles only.
8. Generate researcher assets with `scripts/generate_research_assets.py`: ORCID
   profile, paper-card skeletons, provenance ledger, top-three-author collaboration
   map, internal citation edges, update diff, and temporal holdout template.
9. Build a bounded method graph with `scripts/build_method_graph.py`: classify
   citation edges heuristically, expand one to two hops around lineage papers, and
   generate external comparison candidates for manual review.
10. Generate rolling temporal holdout templates with
    `scripts/generate_rolling_holdout.py`, then complete a human-reviewed audit for
    multiple cutoff years when the corpus spans enough time.
11. Distill themes from representative full texts and complete the paper cards for
   lineage-defining papers. Preserve manually curated cards separately and render
   them with `scripts/render_deep_cards.py`.
12. Extract core full-text citation contexts with
   `scripts/extract_citation_contexts.py`. Resolve clear method inheritance
   directly; ask the user only about ambiguous edges that would change the lineage.
13. Build `method-lineage.md`: baseline, refinements, required inputs, validation
    layers, fallback generation, and extrapolation boundaries.
14. Add a branch-aware evaluation protocol to the derived skill. Require every
    manuscript, workflow, or proposal review to enumerate all branches in
    `research-map.md`, classify their relevance, review each relevant branch
    separately, and synthesize only after the branch-level reviews are complete.
15. Curate and render method boundaries, version relations, and atomic claims
    with `scripts/render_method_boundaries.py`,
    `scripts/render_version_relations.py`, and `scripts/render_claim_ledger.py`.
    Maintain `refresh-protocol.md` and `exceptions.md`.
16. Use `scripts/refresh_distillation_assets.py` for conservative local refreshes.
    It must preserve curated JSON, skip network graph refresh unless explicitly
    requested, and generate a manual-review queue.
17. Generate and validate the derived astronomer skill, update the project README,
    and install only after review.

## Guardrails

- Use ADS as the primary astronomy bibliography.
- Do not rely on one ADS full-text query: coverage is incomplete.
- Search historical affiliations and email addresses.
- Record ORCID as an identity anchor when available, but do not treat it as a
  complete publication list.
- Treat OpenAlex, Crossref, and similar services as audit helpers, not identity truth.
- Do not equate every author email with strict corresponding-author status.
- Do not flatten papers across time: newer methods may refine earlier ideas.
- Do not automatically prefer the newest paper when its required inputs are absent.
- Do not simulate the astronomer's voice or claim to represent the person.
- Keep paper-specific claims traceable to ADS bibcodes and PDF evidence.
- For astronomy-focused attribution, prioritize first authors, corresponding
  authors, and at most the first three listed authors. Do not infer detailed
  contribution roles without source evidence.
- Use lightweight text extraction for normal LaTeX-generated astronomy PDFs.
  Escalate only when extraction visibly fails.
- Evaluate the distilled lineage with a temporal holdout review before treating it
  as a stable research-method model.
- Do not let the most obvious branch dominate a review. Enumerate every branch in
  `research-map.md`, mark its relevance, review all relevant branches separately,
  and state why non-applicable branches were excluded.
- If the user's data fall outside the validated domain and no justified fallback
  exists, say that the distilled method should not be applied directly.
- If external evidence conflicts with the distilled lineage, preserve the
  disagreement and uncertainty instead of forcing a merged conclusion.

## Derived Skill Requirements

The generated astronomer skill must include:

- `SKILL.md`
- `references/research-map.md`
- `references/method-lineage.md`
- `references/method-playbook.md`
- `references/branch-evaluation-protocol.md`
- `references/source-policy.md`
- `references/paper-index.md`
- `references/researcher-profile.md`
- `references/collaboration-map.md`
- `references/holdout-evaluation.md`
- `references/holdout-review.md`
- `references/method-graph.md`
- `references/external-comparison-set.md`
- `references/rolling-holdout-evaluation.md`
- `references/rolling-holdout-review.md`
- `references/deep-paper-cards.md`
- `references/core-citation-contexts.md`
- `references/method-boundaries.md`
- `references/version-relations.md`
- `references/atomic-claim-ledger.md`
- `references/refresh-protocol.md`
- `references/exceptions.md`
- `references/manual-review-queue.md`

Use [derived-skill-template.md](references/derived-skill-template.md) as the checklist.
