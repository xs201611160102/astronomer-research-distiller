#!/usr/bin/env python3
"""Report whether the collected corpus is broad enough before distillation."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


ADS_SOURCE_NAMES = [
    "ads_official_library.json",
    "ads_author_search.json",
    "ads_first_author_search.json",
    "ads_correspondence_search.json",
    "ads_correspondence_search_legacy_email.json",
]


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def normalized_records(path: Path) -> list[dict]:
    payload = load_json(path, [])
    if isinstance(payload, dict) and "results" in payload:
        payload = payload["results"]
    return payload if isinstance(payload, list) else []


def count_ads_sources(metadata: Path) -> tuple[dict[str, int], set[str], set[str], set[str]]:
    counts = {}
    raw_bibcodes = set()
    filtered_bibcodes = set()
    rejected_bibcodes = set()
    candidate_paths = []
    for name in ADS_SOURCE_NAMES:
        candidate_paths.append(metadata / name)
    candidate_paths.extend(sorted(metadata.glob("ads*.json")))
    seen_paths = set()
    for path in candidate_paths:
        if path in seen_paths:
            continue
        seen_paths.add(path)
        if not path.exists():
            continue
        records = normalized_records(path)
        record_bibcodes = {item.get("bibcode", "") for item in records if item.get("bibcode")}
        if not record_bibcodes:
            continue
        counts[path.name] = len(records)
        if path.name == "ads_identity_filtered_records.json":
            filtered_bibcodes.update(record_bibcodes)
        elif path.name == "ads_identity_rejected_records.json":
            rejected_bibcodes.update(record_bibcodes)
        else:
            raw_bibcodes.update(record_bibcodes)
    return counts, raw_bibcodes, filtered_bibcodes, rejected_bibcodes


def download_counts(report_path: Path) -> Counter:
    report = load_json(report_path, []) or []
    return Counter(item.get("download_status", "unknown") for item in report)


def openalex_count(path: Path) -> int:
    payload = load_json(path, []) or []
    if isinstance(payload, dict) and "results" in payload:
        payload = payload["results"]
    return len(payload) if isinstance(payload, list) else 0


def local_seed_count(path: Path) -> int:
    payload = load_json(path, []) or []
    return len(payload) if isinstance(payload, list) else 0


def render_markdown(summary: dict) -> str:
    lines = [
        "# Corpus Completeness Audit",
        "",
        "Run this before method distillation. The formal manifest may be a curated",
        "core set, but the audit corpus should first attempt to cover all collected",
        "ADS records and all publicly downloadable PDFs.",
        "",
        "## Counts",
        "",
        f"- ADS raw records, de-duplicated: {summary['ads_raw_unique_bibcodes']}",
        f"- ADS identity-filtered records: {summary['ads_identity_filtered_bibcodes']}",
        f"- ADS same-name rejected records: {summary['ads_identity_rejected_bibcodes']}",
        f"- ADS corpus baseline records: {summary['ads_corpus_baseline_bibcodes']}",
        f"- Local cross-seed records: {summary['local_seed_records']}",
        f"- ADS audit manifest records: {summary['audit_manifest_records']}",
        f"- Audit PDFs downloaded or already present: {summary['downloaded_or_existing_pdfs']}",
        f"- Audit PDF text files: {summary['audit_text_files']}",
        f"- Formal manifest records: {summary['formal_manifest_records']}",
        f"- OpenAlex audit-helper records: {summary['openalex_records']}",
        "",
        "## ADS Source Files",
        "",
        "| File | Records |",
        "| --- | ---: |",
    ]
    for name, count in sorted(summary["ads_source_counts"].items()):
        lines.append(f"| `{name}` | {count} |")
    if not summary["ads_source_counts"]:
        lines.append("| None found | 0 |")
    lines.extend(
        [
            "",
            "## Download Status",
            "",
            "| Status | Count |",
            "| --- | ---: |",
        ]
    )
    for status, count in sorted(summary["download_status_counts"].items()):
        lines.append(f"| `{status}` | {count} |")
    if not summary["download_status_counts"]:
        lines.append("| None found | 0 |")
    lines.extend(["", "## Warnings", ""])
    if summary["warnings"]:
        lines.extend(f"- {warning}" for warning in summary["warnings"])
    else:
        lines.append("- None.")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--metadata-dir", type=Path, default=Path("metadata"))
    parser.add_argument("--audit-manifest", type=Path, default=Path("metadata/correspondence_audit_manifest.json"))
    parser.add_argument("--download-report", type=Path, default=Path("metadata/correspondence_audit_download_report.json"))
    parser.add_argument("--audit-text-dir", type=Path, default=Path("correspondence_audit/text"))
    parser.add_argument("--formal-manifest", type=Path, default=Path("metadata/paper_manifest.json"))
    parser.add_argument("--local-seeds", type=Path, default=Path("metadata/local_corpus_seed_records.json"))
    parser.add_argument("--openalex-works", type=Path, default=Path("metadata/openalex_works.json"))
    parser.add_argument("--output-json", type=Path, default=Path("metadata/corpus_completeness_audit.json"))
    parser.add_argument("--output-md", type=Path, default=Path("metadata/corpus_completeness_audit.md"))
    parser.add_argument("--fail-on-warning", action="store_true")
    args = parser.parse_args()

    project = args.project_dir.resolve()

    def resolve(path: Path) -> Path:
        return path if path.is_absolute() else project / path

    metadata = resolve(args.metadata_dir)
    ads_source_counts, ads_raw_bibcodes, ads_filtered_bibcodes, ads_rejected_bibcodes = count_ads_sources(metadata)
    ads_baseline_bibcodes = ads_filtered_bibcodes or ads_raw_bibcodes
    audit_manifest = normalized_records(resolve(args.audit_manifest))
    download_counter = download_counts(resolve(args.download_report))
    downloaded_or_existing = download_counter.get("downloaded", 0) + download_counter.get("existing", 0)
    audit_text_files = len(list(resolve(args.audit_text_dir).glob("*.txt"))) if resolve(args.audit_text_dir).exists() else 0
    formal_manifest = normalized_records(resolve(args.formal_manifest))
    warnings = []
    if not ads_source_counts:
        warnings.append("No normalized ADS source file was found; collect ADS records before distillation.")
    if ads_filtered_bibcodes and not ads_rejected_bibcodes:
        warnings.append("ADS identity-filtered records exist but no same-name rejected file was found; keep rejected records for provenance.")
    if ads_baseline_bibcodes and len(audit_manifest) < len(ads_baseline_bibcodes):
        warnings.append("ADS audit manifest has fewer records than the de-duplicated ADS source corpus.")
    if audit_manifest and not download_counter:
        warnings.append("No PDF download report found; run download_public_pdfs.py for the full audit manifest.")
    download_report_records = sum(download_counter.values())
    if audit_manifest and download_counter and download_report_records < len(audit_manifest):
        warnings.append("PDF download report has fewer records than the ADS audit manifest; rerun download_public_pdfs.py.")
    if downloaded_or_existing and audit_text_files < downloaded_or_existing:
        warnings.append("Fewer text files than downloaded/existing PDFs; run extract_pdf_texts.py on the audit corpus.")
    if formal_manifest and len(formal_manifest) < len(audit_manifest):
        warnings.append(
            "Formal manifest is smaller than the audit corpus. This is acceptable only if it is explicitly documented as a curated core set."
        )

    summary = {
        "ads_source_counts": ads_source_counts,
        "ads_raw_unique_bibcodes": len(ads_raw_bibcodes),
        "ads_identity_filtered_bibcodes": len(ads_filtered_bibcodes),
        "ads_identity_rejected_bibcodes": len(ads_rejected_bibcodes),
        "ads_corpus_baseline_bibcodes": len(ads_baseline_bibcodes),
        "ads_unique_bibcodes": len(ads_baseline_bibcodes),
        "local_seed_records": local_seed_count(resolve(args.local_seeds)),
        "audit_manifest_records": len(audit_manifest),
        "download_status_counts": dict(download_counter),
        "download_report_records": download_report_records,
        "downloaded_or_existing_pdfs": downloaded_or_existing,
        "audit_text_files": audit_text_files,
        "formal_manifest_records": len(formal_manifest),
        "openalex_records": openalex_count(resolve(args.openalex_works)),
        "warnings": warnings,
    }
    output_json = resolve(args.output_json)
    output_md = resolve(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    raise SystemExit(1 if args.fail_on_warning and warnings else 0)


if __name__ == "__main__":
    main()
