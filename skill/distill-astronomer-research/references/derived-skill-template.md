# Derived Skill Checklist

## SKILL.md

- Name the research domains that should trigger the skill.
- State that the skill is an evolving method library, not a simulated person.
- Require reading `method-lineage.md` after choosing a branch.
- Require baseline, refinement, fallback, validation, and boundary reporting.
- Require a branch relevance matrix before reviewing a manuscript, proposal, or
  workflow. Enumerate every `research-map.md` branch and classify it as
  `primary`, `supporting`, or `not applicable`.
- Require separate branch-level findings before cross-branch synthesis.

## research-map.md

- Group papers by research branch.
- Link to `method-lineage.md`.
- Include representative ADS bibcodes.

## method-lineage.md

- Organize each branch chronologically.
- Distinguish baseline, expansion, selection rule, and fallback.
- Cite ADS bibcodes.

## method-playbook.md

- Describe reusable workflow choices.
- Include version-aware method selection.
- Include the branch-aware evaluation protocol and its reporting template.
- Require each relevant branch to report observable, applicable lineage,
  strengths to retain, modifications, validation, boundaries, and fallback.

## branch-evaluation-protocol.md

- Copy the standard relevance matrix and branch-level reporting template from
  the distiller reference file.
- Require one row for every `research-map.md` branch.
- Require one review block for every `primary` and `supporting` branch.

## digital-persona-operating-guide.md

- State what the distilled digital persona can do: review, design, triage,
  compare, translate methods into protocols, and identify refresh needs.
- State how to invoke it with a paper, proposal, workflow, data description,
  arXiv link, DOI, ADS bibcode, or local file path.
- Define output modes such as `review`, `design`, `triage`, `comparison`,
  `translation`, and `refresh`.
- Require branch relevance matrix, branch-level findings, validation,
  systematics, failure boundaries, fallback, and source-backed claims for
  serious review or design tasks.
- State that the skill is a research-method operating model, not a simulation or
  impersonation of the astronomer.

## source-policy.md

- Define evidence levels.
- Record local provenance files.
- Separate PDF email markers from explicit corresponding-author wording.
- Distinguish the all-corpus audit/download set from a curated core manifest.
- Link to the project `metadata/corpus_completeness_audit.md` or document the
  exception that prevented all-corpus collection.

## paper-index.md

- Generate from `metadata/paper_manifest.json`.
- State whether the index is complete, role-confirmed, or a curated
  method-distillation core.

## researcher-profile.md

- Record ORCID and corpus counts.
- State that ORCID is an identity anchor, not a complete bibliography.

## collaboration-map.md

- Summarize top-three-author collaborators.
- Include mapped citation edges when available.

## holdout-evaluation.md

- Define a temporal cutoff.
- Compare the early-paper synthesis with held-out later papers.
- Record missed refinements and revise the lineage when needed.

## holdout-review.md

- Complete at least one human-reviewed temporal audit.
- Record supported predictions, missed refinements, and lineage revisions.

## method-graph.md

- Report bounded one-to-two-hop graph scope.
- Mark automatic citation-edge meanings as heuristic until manually reviewed.

## external-comparison-set.md

- Review graph-derived external candidates.
- Keep only papers useful for comparing methods, transfers, or validation choices.

## rolling-holdout-evaluation.md

- Define multiple time cutoffs when the corpus spans enough years.
- Use each earlier period to predict likely method refinements in the next period.

## rolling-holdout-review.md

- Complete a human review of each rolling split.
- Record sparse intervals honestly instead of forcing a strong conclusion.

## deep-paper-cards.md

- Complete full-text cards for lineage-defining papers.
- Label each card as `deep` or `context`.
- Record question, sample, observables, method, systematics, validation, limits,
  and local text-line evidence.

## core-citation-contexts.md

- Extract citation sentences from local full text for core lineage edges.
- Resolve clear inheritance directly and flag only consequential ambiguity for
  user review.

## method-boundaries.md

- State required inputs, calibrated domain, expected performance, failure
  modes, fallback, and explicit abstention conditions.

## version-relations.md

- Record corrections, refinements, transfers, and separate calibration layers.
- Do not treat a newer paper as a universal replacement by default.

## atomic-claim-ledger.md

- Keep important recommendations narrow and traceable.
- Record evidence level, confidence, review state, and local evidence anchors.

## refresh-protocol.md

- Define triggers, refresh order, and preservation rules for curated assets.

## exceptions.md

- Record graph gaps, extraction failures, sparse evaluation intervals,
  corrections, counterexamples, and unresolved conflicts.

## manual-review-queue.md

- Generate after conservative refreshes.
- List changed manifest records, lineage papers without deep cards, unmatched
  full-text contexts, and citation edges requiring user review.
