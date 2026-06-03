#!/usr/bin/env bash
set -euo pipefail

skill_dir="$(cd "$(dirname "$0")/../skill/distill-astronomer-research" && pwd)"
fixture_dir="$(cd "$(dirname "$0")/fixtures" && pwd)"
project_dir="$(mktemp -d "${TMPDIR:-/private/tmp}/astronomer-skill-distiller-smoke.XXXXXX")"

python3 "$skill_dir/scripts/init_astronomer_project.py" \
  --project-dir "$project_dir" \
  --display-name "Ada Astronomer" \
  --skill-name ada-astronomer-research \
  --email ada@example.edu \
  --legacy-email ada.old@example.edu
python3 "$skill_dir/scripts/check_ads_access.py" \
  --output-json "$project_dir/metadata/ads_access_preflight.json" \
  --output-md "$project_dir/metadata/ads_access_preflight.md"
cp "$fixture_dir/ads_official_library.json" "$project_dir/metadata/ads_official_library.json"
python3 "$skill_dir/scripts/build_ads_audit_manifest.py" \
  --library "$project_dir/metadata/ads_official_library.json" \
  --output "$project_dir/metadata/correspondence_audit_manifest.json"
python3 "$skill_dir/scripts/audit_corpus_completeness.py" \
  --project-dir "$project_dir" \
  --output-json "$project_dir/metadata/corpus_completeness_audit.json" \
  --output-md "$project_dir/metadata/corpus_completeness_audit.md"
cp "$fixture_dir/2024Test....1A.txt" "$project_dir/correspondence_audit/text/2024Test....1A.txt"
python3 "$skill_dir/scripts/verify_correspondence_markers.py" \
  --config "$project_dir/config/astronomer.json" \
  --manifest "$project_dir/metadata/correspondence_audit_manifest.json" \
  --text-dir "$project_dir/correspondence_audit/text" \
  --report "$project_dir/metadata/correspondence_audit_verification.json"
printf '2024Test....1A\n' > "$project_dir/metadata/verified_first_author_bibcodes.txt"
python3 "$skill_dir/scripts/build_formal_manifest.py" \
  --config "$project_dir/config/astronomer.json" \
  --audit-manifest "$project_dir/metadata/correspondence_audit_manifest.json" \
  --verification "$project_dir/metadata/correspondence_audit_verification.json" \
  --first-author-bibcodes "$project_dir/metadata/verified_first_author_bibcodes.txt" \
  --output "$project_dir/metadata/paper_manifest.json" \
  --audit-papers-dir "$project_dir/correspondence_audit/papers" \
  --audit-text-dir "$project_dir/correspondence_audit/text" \
  --papers-dir "$project_dir/papers" \
  --text-dir "$project_dir/text"
mkdir -p "$project_dir/skill/ada-astronomer-research/references"
python3 "$skill_dir/scripts/generate_paper_index.py" \
  --manifest "$project_dir/metadata/paper_manifest.json" \
  --output "$project_dir/skill/ada-astronomer-research/references/paper-index.md"
python3 "$skill_dir/scripts/validate_lineage_refs.py" \
  --manifest "$project_dir/metadata/paper_manifest.json" \
  --lineage "$fixture_dir/method-lineage.md"
python3 "$skill_dir/scripts/generate_research_assets.py" \
  --config "$project_dir/config/astronomer.json" \
  --manifest "$project_dir/metadata/paper_manifest.json" \
  --verification "$project_dir/metadata/correspondence_audit_verification.json" \
  --lineage "$fixture_dir/method-lineage.md" \
  --text-dir "$project_dir/text" \
  --cards-json "$project_dir/distillation/paper-cards.json" \
  --cards-md "$project_dir/distillation/paper-cards.md" \
  --ledger "$project_dir/metadata/evidence-ledger.jsonl" \
  --graph-json "$project_dir/metadata/research-graph.json" \
  --snapshot "$project_dir/metadata/distillation-snapshot.json" \
  --update-report "$project_dir/metadata/update-report.json" \
  --profile-md "$project_dir/skill/ada-astronomer-research/references/researcher-profile.md" \
  --graph-md "$project_dir/skill/ada-astronomer-research/references/collaboration-map.md" \
  --holdout-md "$project_dir/skill/ada-astronomer-research/references/holdout-evaluation.md"
python3 "$skill_dir/scripts/generate_rolling_holdout.py" \
  --config "$project_dir/config/astronomer.json" \
  --manifest "$project_dir/metadata/paper_manifest.json" \
  --cutoffs 2022,2023 \
  --output "$project_dir/skill/ada-astronomer-research/references/rolling-holdout-evaluation.md"
python3 "$skill_dir/scripts/render_deep_cards.py" \
  --cards "$fixture_dir/deep-paper-cards.json" \
  --output "$project_dir/skill/ada-astronomer-research/references/deep-paper-cards.md"
python3 "$skill_dir/scripts/extract_citation_contexts.py" \
  --seeds "$fixture_dir/core-citation-context-seeds.json" \
  --text-dir "$project_dir/text" \
  --output-json "$project_dir/metadata/core-citation-contexts.json" \
  --output-md "$project_dir/skill/ada-astronomer-research/references/core-citation-contexts.md"
python3 "$skill_dir/scripts/render_method_boundaries.py" \
  --boundaries "$fixture_dir/method-boundaries.json" \
  --output "$project_dir/skill/ada-astronomer-research/references/method-boundaries.md"
python3 "$skill_dir/scripts/render_version_relations.py" \
  --relations "$fixture_dir/version-relations.json" \
  --output "$project_dir/skill/ada-astronomer-research/references/version-relations.md"
python3 "$skill_dir/scripts/render_claim_ledger.py" \
  --ledger "$fixture_dir/atomic-claims.json" \
  --output "$project_dir/skill/ada-astronomer-research/references/atomic-claim-ledger.md"
cp "$fixture_dir/deep-paper-cards.json" "$project_dir/distillation/deep-paper-cards.json"
cp "$fixture_dir/core-citation-context-seeds.json" "$project_dir/distillation/core-citation-context-seeds.json"
cp "$fixture_dir/method-boundaries.json" "$project_dir/distillation/method-boundaries.json"
cp "$fixture_dir/version-relations.json" "$project_dir/distillation/version-relations.json"
cp "$fixture_dir/atomic-claims.json" "$project_dir/distillation/atomic-claims.json"
python3 "$skill_dir/scripts/refresh_distillation_assets.py" \
  --project-dir "$project_dir" \
  --lineage "$fixture_dir/method-lineage.md" \
  --skill-dir skill/ada-astronomer-research \
  --skip-base-assets
python3 - "$project_dir" <<'PY'
import json
import sys
from pathlib import Path

project = Path(sys.argv[1])
branch_protocol = project / "skill/ada-astronomer-research/references/branch-evaluation-protocol.md"
assert branch_protocol.exists()
assert "Build The Relevance Matrix" in branch_protocol.read_text()
ads_preflight = json.loads((project / "metadata/ads_access_preflight.json").read_text())
assert "ADS_DEV_KEY" in ads_preflight["sources_checked"]
manifest = json.loads((project / "metadata/paper_manifest.json").read_text())
assert len(manifest) == 1
assert manifest[0]["roles"] == [
    "first_author_verified",
    "explicit_corresponding_author",
    "pdf_email_marker",
]
cards = json.loads((project / "distillation/paper-cards.json").read_text())
assert cards[0]["lineage_branch"] == "Test Calibration"
assert cards[0]["lineage_stage"] == "Baseline"
assert (project / "metadata/evidence-ledger.jsonl").exists()
assert (project / "metadata/update-report.json").exists()
corpus_audit = json.loads((project / "metadata/corpus_completeness_audit.json").read_text())
assert corpus_audit["ads_unique_bibcodes"] == 2
assert corpus_audit["audit_manifest_records"] == 2
assert "No PDF download report found" in " ".join(corpus_audit["warnings"])
rolling = (project / "skill/ada-astronomer-research/references/rolling-holdout-evaluation.md").read_text()
assert "Cutoff 2023" in rolling
assert "2024Test....1A" in rolling
deep_cards = (project / "skill/ada-astronomer-research/references/deep-paper-cards.md").read_text()
assert "Can the fixture render a deep card?" in deep_cards
assert "Card level: `deep`" in deep_cards
contexts = json.loads((project / "metadata/core-citation-contexts.json").read_text())
assert contexts[0]["hit_count"] == 1
boundaries = (project / "skill/ada-astronomer-research/references/method-boundaries.md").read_text()
assert "The fixture is absent." in boundaries
relations = (project / "skill/ada-astronomer-research/references/version-relations.md").read_text()
assert "`refines`" in relations
claims = (project / "skill/ada-astronomer-research/references/atomic-claim-ledger.md").read_text()
assert "FIXTURE-CLAIM" in claims
queue = json.loads((project / "metadata/manual-review-queue.json").read_text())
assert queue["lineage_without_deep_card"] == []
assert queue["citation_contexts_without_hits"] == []
print("Smoke test passed")
PY
