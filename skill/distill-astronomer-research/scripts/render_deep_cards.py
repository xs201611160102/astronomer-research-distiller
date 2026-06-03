#!/usr/bin/env python3
"""Render manually curated deep paper cards as a readable Markdown reference."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


FIELDS = [
    ("science_question", "Science Question"),
    ("data_and_sample", "Data And Sample"),
    ("observables", "Observables"),
    ("method", "Method"),
    ("systematics", "Systematics"),
    ("validation", "Validation"),
    ("limitations", "Limitations"),
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cards", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    cards = json.loads(args.cards.read_text(encoding="utf-8"))
    lines = [
        "# Deep Paper Cards",
        "",
        "These cards are Codex syntheses from downloaded full text. Use the ADS bibcode and listed text lines to recheck precise claims.",
        "",
    ]
    for card in cards:
        lines.extend(
            [
                f"## `{card['bibcode']}` {card['title']}",
                "",
                f"- Card level: `{card.get('card_level', 'deep')}`",
                f"- Branch: {card['lineage_branch']}",
                f"- Role in lineage: {card['lineage_role']}",
                f"- Evidence: `{card['evidence_source']}`",
            ]
        )
        for key, label in FIELDS:
            lines.append(f"- {label}: {card[key]}")
        lines.append("")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"deep_cards": len(cards), "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
