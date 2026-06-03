#!/usr/bin/env python3
"""Render curated method applicability boundaries as Markdown."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--boundaries", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    items = json.loads(args.boundaries.read_text(encoding="utf-8"))
    lines = [
        "# Method Boundaries",
        "",
        "Use this matrix before recommending a method. If the user's data fall outside the calibrated domain and no validated fallback exists, say that the distilled framework should not be applied directly.",
        "",
    ]
    for item in items:
        lines.extend(
            [
                f"## {item['method']}",
                "",
                f"- Branch: {item['branch']}",
                f"- Representative papers: {', '.join(f'`{bibcode}`' for bibcode in item['bibcodes'])}",
                f"- Required inputs: {item['required_inputs']}",
                f"- Calibrated domain: {item['calibrated_domain']}",
                f"- Expected performance: {item['expected_performance']}",
                f"- Failure modes: {item['failure_modes']}",
                f"- Fallback: {item['fallback']}",
                f"- Abstain when: {item['abstain_when']}",
                f"- Evidence: {item['evidence_source']}",
                "",
            ]
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"method_boundaries": len(items), "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
