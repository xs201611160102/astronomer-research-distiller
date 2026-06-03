#!/usr/bin/env python3
"""Render curated atomic method claims with evidence and review state."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    items = json.loads(args.ledger.read_text(encoding="utf-8"))
    lines = [
        "# Atomic Claim Ledger",
        "",
        "Each item is intentionally narrow. Use source-backed claims directly; label cross-paper synthesis as inference. Recheck low-confidence or pending items before making a strong recommendation.",
        "",
    ]
    for item in items:
        lines.extend(
            [
                f"## `{item['claim_id']}`",
                "",
                f"- Claim: {item['claim']}",
                f"- Claim type: `{item['claim_type']}`",
                f"- Evidence level: `{item['evidence_level']}`",
                f"- Confidence: `{item['confidence']}`",
                f"- Review status: `{item['review_status']}`",
                f"- Sources: {', '.join(f'`{source}`' for source in item['sources'])}",
                f"- Local evidence: {item['local_evidence']}",
                "",
            ]
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"atomic_claims": len(items), "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
