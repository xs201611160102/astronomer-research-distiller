#!/usr/bin/env python3
"""Build a PDF audit manifest from normalized ADS record scrapes."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path


def normalize_title(value: str) -> str:
    value = html.unescape(value or "")
    value = value.replace("–", "-").replace("—", "-").replace("−", "-")
    return re.sub(r"\s+", " ", value).strip()


def choose_pdf_links(links: list[dict]) -> list[str]:
    urls = [item["href"] for item in links if item.get("href")]
    return sorted(
        (url for url in urls if url.endswith(("EPRINT_PDF", "PUB_PDF"))),
        key=lambda url: (not url.endswith("EPRINT_PDF"), url),
    )


def arxiv_pdf_links(identifiers: list[str]) -> list[str]:
    links = []
    for identifier in identifiers or []:
        match = re.search(r"(?:arXiv:|arxiv/)?(\d{4}\.\d{4,5})(?:v\d+)?", identifier, re.I)
        if match:
            links.append(f"https://arxiv.org/pdf/{match.group(1)}")
    return sorted(set(links))


def load_records(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "results" in payload:
        payload = payload["results"]
    if not isinstance(payload, list):
        raise SystemExit(f"Expected a list of ADS records in {path}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--library",
        type=Path,
        action="append",
        default=None,
        help="Normalized ADS JSON file. Pass multiple times to merge official, author, and first-author searches.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("metadata/correspondence_audit_manifest.json"),
    )
    args = parser.parse_args()

    libraries = args.library or [Path("metadata/ads_official_library.json")]
    by_bibcode: dict[str, dict] = {}
    for library_path in libraries:
        if not library_path.exists():
            raise SystemExit(f"ADS source file not found: {library_path}")
        for item in load_records(library_path):
            bibcode = item["bibcode"]
            existing = by_bibcode.setdefault(
                bibcode,
                {
                    "bibcode": bibcode,
                    "title": normalize_title(item.get("title", "")),
                    "authors_display": item.get("authors_display", ""),
                    "links": [],
                    "identifier": [],
                    "source_files": [],
                },
            )
            if not existing["title"] and item.get("title"):
                existing["title"] = normalize_title(item.get("title", ""))
            if not existing["authors_display"] and item.get("authors_display"):
                existing["authors_display"] = item.get("authors_display", "")
            existing["links"].extend(item.get("links", []))
            existing["identifier"].extend(item.get("identifier", []) or [])
            existing["source_files"].append(str(library_path))

    records = []
    for item in sorted(by_bibcode.values(), key=lambda record: record["bibcode"], reverse=True):
        source_files = sorted(set(item["source_files"]))
        pdf_links = sorted(set(arxiv_pdf_links(item.get("identifier", [])) + choose_pdf_links(item.get("links", []))))
        records.append(
            {
                "bibcode": item["bibcode"],
                "title": item["title"],
                "authors_display": item["authors_display"],
                "roles": ["ads_corpus_audit_candidate"],
                "role_evidence": [f"record included in {source}" for source in source_files],
                "pdf_links": pdf_links,
                "distillation_tier": "audit",
            }
        )
    args.output.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "source_files": [str(path) for path in libraries],
                "records": len(records),
                "with_pdf_links": sum(bool(item["pdf_links"]) for item in records),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
