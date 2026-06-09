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


def read_context(source_root: Path, source: str, line: int, context_lines: int) -> list[tuple[int, str]]:
    path = Path(source)
    if not path.is_absolute():
        path = source_root / path
    if not path.exists() or line < 1:
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    start = max(1, line - context_lines)
    end = min(len(lines), line + context_lines)
    return [(number, lines[number - 1]) for number in range(start, end + 1)]


def format_source_line(item, source_root: Path, context_lines: int) -> list[str]:
    if isinstance(item, dict):
        source = item.get("source")
        line = item.get("line")
        text = item.get("text", "")
        parts = []
        if source:
            parts.append(str(source))
        if line:
            parts.append(f"line {line}")
        prefix = f"{', '.join(parts)}: " if parts else ""
        rendered = [f"- {prefix}{text}"]
        if source and isinstance(line, int) and context_lines > 0:
            context = read_context(source_root, str(source), line, context_lines)
            if context:
                start = context[0][0]
                end = context[-1][0]
                rendered.append(f"  Context lines {start}-{end}:")
                for number, context_text in context:
                    marker = ">" if number == line else " "
                    rendered.append(f"  {marker} {number}: {context_text}")
        return rendered
    return [f"- {item}"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cards", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--source-root",
        type=Path,
        default=None,
        help="Root used to resolve relative source paths in source_lines. Defaults to the cards file grandparent, or the current directory.",
    )
    parser.add_argument(
        "--context-lines",
        type=int,
        default=1,
        help="Number of neighboring lines to render on each side of a source line. Use 0 to disable.",
    )
    args = parser.parse_args()

    cards = json.loads(args.cards.read_text(encoding="utf-8"))
    source_root = args.source_root
    if source_root is None:
        source_root = args.cards.parent.parent if args.cards.parent.name == "distillation" else Path(".")
    source_root = source_root.resolve()
    lines = [
        "# Deep Paper Cards",
        "",
        "These cards are Codex syntheses from downloaded full text. Use the ADS bibcode, listed text lines, and rendered neighboring context to recheck precise claims.",
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
        source_lines = card.get("source_lines", [])
        if source_lines:
            lines.extend(["", "### Source Lines", ""])
            for item in source_lines:
                lines.extend(format_source_line(item, source_root, args.context_lines))
        lines.append("")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"deep_cards": len(cards), "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
