# Distillation Guide

## Read Across Time

For each topic, sample early, middle, and recent papers. Identify:

1. baseline observable-level idea;
2. new inputs introduced later;
3. scale expansion;
4. instrument or survey transfer;
5. validation layers;
6. failure boundaries;
7. fallback method when advanced inputs are missing.

This is a deep-reading rule, not a collection rule: before sampling, attempt to
download and extract the full public ADS audit corpus and record the completeness
audit. Representative reading must never be described as a complete publication
download.

Do not flatten papers into a theme list. A derived skill should explain which
generation to use and why.

Generate structured paper-card skeletons first. For lineage-defining papers,
complete the science question, data and sample, observables, method, systematics,
validation, limitations, branch, and stage fields after reading the text.
Use `card_level: deep` for method-defining or boundary-changing papers. Use
`card_level: context` for applications, reviews, conference summaries, and
transition papers. Context cards may be shorter, but must remain honest about
limited evidence.

Use temporal holdout templates to review whether an early-paper synthesis
anticipates later refinements. Prefer multiple rolling cutoffs when the corpus
spans enough years. Treat this as a human-audited calibration exercise, not an
automatic score.

Build a bounded one-to-two-hop citation neighborhood around lineage-defining
papers. Use it to discover external comparison candidates and possible method
transfers. Citation proximity does not prove methodological similarity, and
automatic semantic-edge labels remain heuristic until checked against the
citing paper or manually overridden.

## Required Lineage Shape

Each branch in `method-lineage.md` should contain:

```markdown
## Branch Name

### Baseline
- `ADS bibcode`: original reusable idea.

### Expansion
- `ADS bibcode`: added capability and required inputs.

### Selection Rule
Use the baseline when ... Add the refinement when ... Fall back when ...
```

## Required Evaluation Protocol

Every derived astronomer skill must evaluate manuscripts, proposals, and
workflows branch by branch before producing an overall judgment.

1. Read every branch heading in `research-map.md`.
2. Build a branch relevance matrix with one row per branch.
3. Classify each branch as:
   - `primary`: central to the target work;
   - `supporting`: not central, but able to expose assumptions, systematics,
     validation gaps, or useful fallback methods;
   - `not applicable`: no material connection; state the reason briefly.
4. For each `primary` and `supporting` branch, report:
   - observable or claim under review;
   - applicable baseline and refinement papers;
   - strengths to retain;
   - required modifications;
   - systematics and failure boundaries;
   - validation plan;
   - fallback method.
5. Synthesize only after the branch-level passes. Preserve disagreements between
   branches instead of forcing one preferred method to dominate.

Do not infer that a branch is irrelevant merely because the manuscript gives it
fewer pages. Calibration, extinction, selection functions, catalog construction,
and downstream parameter inference can constrain one another.

## Synthesis Discipline

- Label cross-paper conclusions as Codex inference.
- Cite ADS bibcodes for source-backed claims.
- Prefer representative full-text evidence over title-only inference.
- Keep the skill procedural: research habits, choices, validation, and limits.
- Do not imitate the astronomer's prose or personality.
