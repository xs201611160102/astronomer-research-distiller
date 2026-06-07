#!/usr/bin/env python3
"""Generate rolling temporal holdout templates from a formal paper manifest."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def parse_cutoffs(value: str) -> list[int]:
    return sorted({int(item.strip()) for item in value.split(",") if item.strip()})


def year_from_item(item: dict) -> int:
    if item.get("year"):
        return int(item["year"])
    match = re.match(r"(\d{4})", item.get("bibcode", ""))
    return int(match.group(1)) if match else 0


def format_paper(item: dict) -> str:
    return f"- {year_from_item(item)}: `{item.get('bibcode', '')}` - {item.get('title', '')}"


def main() -> None:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--manifest", type=Path, default=Path("metadata/paper_manifest.json"))
    parser.add_argument("--config", type=Path, default=Path("config/astronomer.json"))
    parser.add_argument("--cutoffs", help="Comma-separated cutoff years; overrides config")
    parser.add_argument("--cutoff", action="append", default=[], help="Single cutoff year. May be repeated.")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    config = load_json(args.config, {}) or {}
    if args.cutoff:
        cutoffs = [int(year) for year in args.cutoff]
    elif args.cutoffs:
        cutoffs = parse_cutoffs(args.cutoffs)
    else:
        cutoffs = config.get("rolling_holdout_cutoffs", [])
    cutoffs = sorted({int(year) for year in cutoffs})
    if not cutoffs:
        cutoffs = [int(config.get("holdout_cutoff_year", 2023))]

    manifest = sorted(load_json(args.manifest, []) or [], key=lambda item: (year_from_item(item), item.get("bibcode", "")))
    lines = [
        "# Rolling Temporal Holdout Evaluation",
        "",
        "Use each split as a time-aware audit. Read only the training-period papers first, write expected next refinements, then compare against the held-out papers. This checks whether the distilled lineage captures reusable reasoning rather than merely retelling later results.",
        "",
    ]
    for index, cutoff in enumerate(cutoffs):
        next_cutoff = cutoffs[index + 1] if index + 1 < len(cutoffs) else None
        train = [item for item in manifest if year_from_item(item) <= cutoff]
        test = [
            item
            for item in manifest
            if year_from_item(item) > cutoff and (next_cutoff is None or year_from_item(item) <= next_cutoff)
        ]
        window = f"{cutoff + 1}-{next_cutoff}" if next_cutoff else f"{cutoff + 1}+"
        lines.extend(
            [
                f"## Cutoff {cutoff}: evaluate {window}",
                "",
                f"- Training records: {len(train)}",
                f"- Held-out records: {len(test)}",
                "",
                "### Questions",
                "",
                "1. Which baseline methods should remain stable?",
                "2. Which inputs, surveys, populations, or validation layers are likely to be added next?",
                "3. Which actual held-out papers are explained by the earlier synthesis?",
                "4. What was missed, and which lineage note should be revised?",
                "",
                "### Held-Out Papers",
                "",
            ]
        )
        lines.extend(format_paper(item) for item in test)
        if not test:
            lines.append("- No formal-manifest papers in this interval.")
        lines.append("")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"cutoffs": cutoffs, "records": len(manifest), "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
