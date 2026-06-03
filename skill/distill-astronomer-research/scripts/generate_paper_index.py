#!/usr/bin/env python3
"""Generate a derived skill paper index from the formal manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("metadata/paper_manifest.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = json.loads(args.manifest.read_text(encoding="utf-8"))
    lines = ["# Paper Index", "", "| ADS bibcode | Tier | Roles | Title |", "| --- | --- | --- | --- |"]
    for item in records:
        title = item["title"].replace("|", "\\|")
        lines.append(f"| `{item['bibcode']}` | {item['distillation_tier']} | {', '.join(item['roles'])} | {title} |")
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(records)} records to {args.output}")


if __name__ == "__main__":
    main()
