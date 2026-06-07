#!/usr/bin/env python3
"""Harvest local ADS-like records that mention the target astronomer."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


DEFAULT_PATTERNS = [
    "**/metadata/ads*.json",
    "**/metadata/paper_manifest.json",
    "**/skill/*/references/corpus-records.json",
]
STALE_NAME_PATTERN = re.compile(r"(backup|before_|_before_|with_conference|all_database|snapshot|local_corpus_seed)", re.I)


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def records_from_json(path: Path) -> list[dict]:
    payload = load_json(path)
    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        payload = payload["results"]
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict) and item.get("bibcode")]


def normalize_record(item: dict, source: Path) -> dict:
    links = item.get("links") or []
    if not links and item.get("pdf_links"):
        links = [{"href": href, "text": "PDF"} for href in item.get("pdf_links", [])]
    return {
        "bibcode": item.get("bibcode", ""),
        "title": item.get("title", ""),
        "first_author": item.get("first_author", ""),
        "authors_display": item.get("authors_display", ""),
        "links": links,
        "local_seed_source": str(source),
    }


def compile_patterns(values: list[str]) -> list[re.Pattern[str]]:
    patterns = []
    for value in values:
        value = value.strip()
        if not value:
            continue
        patterns.append(re.compile(re.escape(value), re.I))
        if "," in value:
            surname, given = [part.strip() for part in value.split(",", 1)]
            if given:
                patterns.append(re.compile(re.escape(given) + r"\s+" + re.escape(surname), re.I))
    return patterns


def record_matches(item: dict, patterns: list[re.Pattern[str]]) -> bool:
    haystack = "\n".join(
        str(item.get(key, ""))
        for key in ("authors_display", "first_author", "title", "bibcode")
    )
    return any(pattern.search(haystack) for pattern in patterns)


def candidate_files(root: Path, patterns: list[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in patterns:
        files.extend(root.glob(pattern))
    return sorted(set(path for path in files if path.is_file()))


def should_skip(path: Path, project: Path, include_current_project: bool, include_stale: bool) -> bool:
    resolved = path.resolve()
    if not include_current_project:
        try:
            resolved.relative_to(project)
            return True
        except ValueError:
            pass
    if not include_stale and STALE_NAME_PATTERN.search(resolved.name):
        return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--root", type=Path, action="append", default=[])
    parser.add_argument("--pattern", action="append", default=[])
    parser.add_argument("--name-variant", action="append", default=[])
    parser.add_argument("--config", type=Path, default=Path("config/astronomer.json"))
    parser.add_argument("--output", type=Path, default=Path("metadata/local_corpus_seed_records.json"))
    parser.add_argument("--include-current-project", action="store_true")
    parser.add_argument("--include-stale-snapshots", action="store_true")
    args = parser.parse_args()

    project = args.project_dir.resolve()
    config_path = args.config if args.config.is_absolute() else project / args.config
    config = load_json(config_path) or {}
    variants = args.name_variant or config.get("name_variants", []) or [config.get("display_name", "")]
    patterns = compile_patterns(variants)
    if not patterns:
        raise SystemExit("No name variants configured; pass --name-variant or fill config/astronomer.json")

    roots = [project.parent, Path.home() / ".codex/skills"]
    roots.extend(args.root)
    glob_patterns = args.pattern or DEFAULT_PATTERNS
    by_bibcode: dict[str, dict] = {}
    source_counts = {}
    for root in roots:
        root = root.expanduser().resolve()
        if not root.exists():
            continue
        for path in candidate_files(root, glob_patterns):
            if should_skip(path, project, args.include_current_project, args.include_stale_snapshots):
                continue
            records = records_from_json(path)
            if not records:
                continue
            matched = 0
            for item in records:
                if not record_matches(item, patterns):
                    continue
                matched += 1
                normalized = normalize_record(item, path)
                existing = by_bibcode.setdefault(normalized["bibcode"], normalized)
                sources = set(existing.get("local_seed_sources", []))
                sources.add(str(path))
                existing["local_seed_sources"] = sorted(sources)
            if matched:
                source_counts[str(path)] = matched

    output = args.output if args.output.is_absolute() else project / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(sorted(by_bibcode.values(), key=lambda item: item["bibcode"], reverse=True), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "name_variants": variants,
                "matched_records": len(by_bibcode),
                "source_counts": source_counts,
                "output": str(output),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
