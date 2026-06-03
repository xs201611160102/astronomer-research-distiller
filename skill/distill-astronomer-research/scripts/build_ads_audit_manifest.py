#!/usr/bin/env python3
"""Build a PDF audit manifest from a normalized ADS library scrape."""

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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", type=Path, default=Path("metadata/ads_official_library.json"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("metadata/correspondence_audit_manifest.json"),
    )
    args = parser.parse_args()

    library = json.loads(args.library.read_text(encoding="utf-8"))
    records = []
    for item in library:
        records.append(
            {
                "bibcode": item["bibcode"],
                "title": normalize_title(item.get("title", "")),
                "authors_display": item.get("authors_display", ""),
                "roles": ["official_ads_library_correspondence_audit_candidate"],
                "role_evidence": ["record included in official ADS library"],
                "pdf_links": choose_pdf_links(item.get("links", [])),
                "distillation_tier": "audit",
            }
        )
    args.output.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"records": len(records), "with_pdf_links": sum(bool(item["pdf_links"]) for item in records)}, indent=2))


if __name__ == "__main__":
    main()
