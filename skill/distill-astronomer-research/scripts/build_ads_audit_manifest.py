#!/usr/bin/env python3
"""Build a PDF audit manifest from normalized ADS record scrapes."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

CONFERENCE_PUB_PATTERN = re.compile(
    r"Meeting Abstracts|Bulletin of the American Astronomical Society|AAS/Division|"
    r"IAU Symposium|EAS[0-9]|European Astronomical Society|TESS Science Conference|"
    r"Machine Learning for Astrophysics|Early Disk-Galaxy Formation|"
    r"Proceedings|Conference Series|ASP Conf|PMLR|International Conference",
    re.I,
)
CONFERENCE_BIBCODE_PATTERN = re.compile(r"^[0-9]{4}(BAAS|AAS)|IAUS|eas..conf|mla..conf|tsc3.conf|DDA", re.I)
PROCEEDINGS_CONTEXT_PATTERN = re.compile(r"\b(proceedings|conference|symposium|PMLR)\b", re.I)


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
        match = re.search(r"(?:arXiv:|arxiv/)(\d{4}\.\d{4,5})(?:v\d+)?", identifier, re.I)
        if not match:
            match = re.match(r"\d{4}arXiv(\d{4})(\d{5})[A-Z]?$", identifier, re.I)
        if match:
            arxiv_id = match.group(1) if "." in match.group(1) else f"{match.group(1)}.{match.group(2)}"
            links.append(f"https://arxiv.org/pdf/{arxiv_id}")
    return sorted(set(links))


def load_records(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "results" in payload:
        payload = payload["results"]
    if not isinstance(payload, list):
        raise SystemExit(f"Expected a list of ADS records in {path}")
    return payload


def is_conference_record(item: dict) -> bool:
    return bool(
        CONFERENCE_PUB_PATTERN.search(item.get("pub") or "")
        or CONFERENCE_BIBCODE_PATTERN.search(item.get("bibcode") or "")
    )


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
    parser.add_argument(
        "--excluded-output",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--include-conference-records",
        action="store_true",
        help="Include meeting abstracts and conference records in the PDF audit manifest.",
    )
    args = parser.parse_args()
    excluded_output = args.excluded_output or args.output.parent / "conference_records_excluded_from_audit.json"

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
                    "year": item.get("year"),
                    "pub": item.get("pub", ""),
                    "doctype": item.get("doctype", ""),
                    "links": [],
                    "identifier": [],
                    "source_files": [],
                },
            )
            if not existing["title"] and item.get("title"):
                existing["title"] = normalize_title(item.get("title", ""))
            if not existing["authors_display"] and item.get("authors_display"):
                existing["authors_display"] = item.get("authors_display", "")
            if not existing.get("year") and item.get("year"):
                existing["year"] = item.get("year")
            if not existing.get("pub") and item.get("pub"):
                existing["pub"] = item.get("pub", "")
            if not existing.get("doctype") and item.get("doctype"):
                existing["doctype"] = item.get("doctype", "")
            existing["links"].extend(item.get("links", []))
            existing["identifier"].extend(item.get("identifier", []) or [])
            existing["source_files"].append(str(library_path))

    records = []
    excluded = []
    for item in sorted(by_bibcode.values(), key=lambda record: record["bibcode"], reverse=True):
        source_files = sorted(set(item["source_files"]))
        pdf_links = sorted(set(arxiv_pdf_links(item.get("identifier", [])) + choose_pdf_links(item.get("links", []))))
        record = {
            "bibcode": item["bibcode"],
            "title": item["title"],
            "authors_display": item["authors_display"],
            "year": item.get("year"),
            "pub": item.get("pub", ""),
            "doctype": item.get("doctype", ""),
            "identifier": sorted(set(item.get("identifier", []))),
            "roles": ["ads_corpus_audit_candidate"],
            "role_evidence": [f"record included in {source}" for source in source_files],
            "pdf_links": pdf_links,
            "distillation_tier": "audit",
        }
        if PROCEEDINGS_CONTEXT_PATTERN.search(f"{item.get('pub', '')} {item.get('title', '')}"):
            record["record_flags"] = ["metadata_proceedings_context"]
        if is_conference_record(item) and not args.include_conference_records:
            excluded.append({**record, "exclusion_reason": "conference_or_meeting_record"})
        else:
            records.append(record)
    args.output.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    excluded_output.parent.mkdir(parents=True, exist_ok=True)
    excluded_output.write_text(json.dumps(excluded, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "source_files": [str(path) for path in libraries],
                "records": len(records),
                "conference_records_excluded": len(excluded),
                "with_pdf_links": sum(bool(item["pdf_links"]) for item in records),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
