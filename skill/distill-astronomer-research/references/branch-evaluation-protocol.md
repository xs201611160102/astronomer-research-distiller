# Branch-Aware Evaluation Protocol

Copy this protocol into every derived astronomer skill as
`references/branch-evaluation-protocol.md`. Use it when reviewing a manuscript,
proposal, catalog, or workflow.

## Step 1: Build The Relevance Matrix

Read every branch heading in `research-map.md`. Do not start from the manuscript's
most prominent result.

| Research branch | Relevance | Observable or claim touched | Reason |
| --- | --- | --- | --- |
| Branch from `research-map.md` | `primary`, `supporting`, or `not applicable` | What the branch can test | Why it is included or excluded |

Use:

- `primary` when the branch is central to the target work.
- `supporting` when the branch can expose assumptions, systematics, validation
  gaps, or fallback methods.
- `not applicable` only when there is no material connection. State why.

## Step 2: Review Every Relevant Branch

Complete one block for each `primary` and `supporting` branch.

```markdown
## Branch: <name>

- Relevance: `primary` or `supporting`
- Observable or claim:
- Baseline:
- Selected refinement:
- Required inputs:
- Strengths to retain:
- Required modifications:
- Systematics and failure boundaries:
- Validation plan:
- Fallback:
- Evidence: ADS bibcodes and local evidence anchors
- Inference: label cross-paper synthesis explicitly
```

## Step 3: Synthesize Across Branches

After the branch-level reviews:

1. List the parts that can be retained.
2. List required modifications in priority order.
3. State fallback methods and their trigger conditions.
4. Preserve disagreements between branches.
5. Separate source-backed findings from inference.

## Guardrails

- Do not infer importance from page count alone.
- Do not let downstream parameter inference displace calibration, extinction,
  selection-function, or catalog-construction checks.
- Do not treat a supporting branch as optional when it changes the error budget,
  validity domain, or interpretation.
- State explicitly when the distilled corpus lacks a suitable method for a
  relevant branch.
