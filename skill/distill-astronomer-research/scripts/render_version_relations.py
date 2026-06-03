#!/usr/bin/env python3
"""Render curated paper, method, and correction version relations as Markdown."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--relations", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    items = json.loads(args.relations.read_text(encoding="utf-8"))
    lines = [
        "# Version And Correction Relations",
        "",
        "Use this file before recommending a paper, catalog, or method generation. Relations are manually curated; do not infer replacement merely from publication date.",
        "",
    ]
    for item in items:
        lines.extend(
            [
                f"## `{item['source']}` `{item['relation']}` `{item['target']}`",
                "",
                f"- Scope: {item['scope']}",
                f"- Effect: {item['effect']}",
                f"- Recommendation: {item['recommendation']}",
                f"- Evidence: {item['evidence_source']}",
                "",
            ]
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"version_relations": len(items), "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
