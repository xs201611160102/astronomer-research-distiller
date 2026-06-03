#!/usr/bin/env python3
"""Extract curated citation contexts from locally downloaded paper text."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def compact(lines: list[str]) -> str:
    return re.sub(r"\s+", " ", " ".join(line.strip() for line in lines)).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=Path, required=True)
    parser.add_argument("--text-dir", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--window", type=int, default=1)
    args = parser.parse_args()

    seeds = json.loads(args.seeds.read_text(encoding="utf-8"))
    extracted = []
    for seed in seeds:
        source = seed["source_bibcode"]
        text_path = args.text_dir / f"{source}.txt"
        lines = text_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        pattern = re.compile(seed["pattern"], re.I)
        hits = [
            index
            for index in range(len(lines))
            if pattern.search(compact(lines[index : index + args.window + 1]))
        ]
        item = {
            **seed,
            "source_text": str(text_path),
            "hit_count": len(hits),
            "contexts": [
                {
                    "line": index + 1,
                    "text": compact(lines[max(0, index - args.window) : index + args.window + 1]),
                }
                for index in hits[: seed.get("max_hits", 2)]
            ],
        }
        extracted.append(item)

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(extracted, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md = [
        "# Core Citation Contexts",
        "",
        "These contexts were extracted from downloaded full text. Semantic labels are Codex judgments based on the cited sentence and nearby text. Review items with `needs_user_review: true` before using them to revise the lineage.",
        "",
    ]
    for item in extracted:
        md.extend(
            [
                f"## `{item['source_bibcode']}` -> `{item['target_bibcode']}`",
                "",
                f"- Relation: `{item['relation']}`",
                f"- Confidence: `{item['confidence']}`",
                f"- Needs user review: `{str(item.get('needs_user_review', False)).lower()}`",
                f"- Extraction pattern: `{item['pattern']}`",
                f"- Matching contexts: {item['hit_count']}",
            ]
        )
        for context in item["contexts"]:
            md.append(f"- Line {context['line']}: {context['text']}")
        md.append("")
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"citation_edges": len(extracted), "with_hits": sum(bool(item["hit_count"]) for item in extracted)}, indent=2))


if __name__ == "__main__":
    main()
