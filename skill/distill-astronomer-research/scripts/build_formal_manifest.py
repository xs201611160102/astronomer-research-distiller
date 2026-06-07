#!/usr/bin/env python3
"""Build the formal manifest from verified first authors and PDF correspondence evidence."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

from report_utils import load_records


SUPPLEMENTAL_BIBCODE_PATTERN = re.compile(
    r"yCat|ascl\.soft|zndo|PhDT|nsf|IAUGA|IAUS|eas..conf|AAS|BAAS",
    re.I,
)
SUPPLEMENTAL_TEXT_PATTERN = re.compile(
    r"\b(VizieR Online Data Catalog|ASCL|Zenodo|PhD thesis|NSF Award|textbook|review)\b",
    re.I,
)
PROCEEDINGS_TEXT_PATTERN = re.compile(
    r"\b(Proceedings of|International Conference|PMLR|conference proceedings|symposium proceedings)\b",
    re.I,
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def first_text(path: Path, limit: int = 80000) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")[:limit]


def classify_tier(item: dict, config: dict, text: str) -> tuple[str, list[str]]:
    haystack = " ".join(
        str(item.get(key, ""))
        for key in ("bibcode", "title", "pub", "doctype")
    )
    flags = list(item.get("record_flags", []))
    supplemental_tokens = config.get("supplemental_bibcode_tokens", [])
    if any(token in item.get("bibcode", "") for token in supplemental_tokens):
        flags.append("configured_supplemental_bibcode_token")
    if SUPPLEMENTAL_BIBCODE_PATTERN.search(item.get("bibcode", "")) or SUPPLEMENTAL_TEXT_PATTERN.search(haystack):
        flags.append("non_standard_publication_type")
    if PROCEEDINGS_TEXT_PATTERN.search(haystack) or PROCEEDINGS_TEXT_PATTERN.search(text):
        flags.append("proceedings_context")
    flags = sorted(set(flags))
    tier = "supplemental" if flags else "core"
    return tier, flags


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config/astronomer.json"))
    parser.add_argument("--audit-manifest", type=Path, default=Path("metadata/correspondence_audit_manifest.json"))
    parser.add_argument("--verification", type=Path, default=Path("metadata/correspondence_audit_verification.json"))
    parser.add_argument("--first-author-bibcodes", type=Path, default=Path("metadata/verified_first_author_bibcodes.txt"))
    parser.add_argument("--output", type=Path, default=Path("metadata/paper_manifest.json"))
    parser.add_argument("--audit-papers-dir", type=Path, default=Path("correspondence_audit/papers"))
    parser.add_argument("--audit-text-dir", type=Path, default=Path("correspondence_audit/text"))
    parser.add_argument("--papers-dir", type=Path, default=Path("papers"))
    parser.add_argument("--text-dir", type=Path, default=Path("text"))
    args = parser.parse_args()
    config = load_json(args.config)
    audit = {item["bibcode"]: item for item in load_records(args.audit_manifest)}
    verification = {item["bibcode"]: item for item in load_records(args.verification)}
    first_authors = {line.strip() for line in args.first_author_bibcodes.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")}
    selected = first_authors | {bibcode for bibcode, item in verification.items() if item["status"] == "pdf_text_evidence_found"}
    records = []
    for bibcode in sorted(selected, reverse=True):
        if bibcode not in audit:
            raise SystemExit(f"Verified bibcode missing from ADS audit manifest: {bibcode}")
        item = audit[bibcode]
        evidence = verification.get(bibcode, {}).get("evidence", [])
        roles = []
        role_evidence = []
        if bibcode in first_authors:
            roles.append("first_author_verified")
            role_evidence.append("ADS identity audit")
        if any(ev["kind"] == "explicit_corresponding_author" for ev in evidence):
            roles.append("explicit_corresponding_author")
            role_evidence.append("local PDF text explicit corresponding-author verification")
        if any(ev["kind"] == "pdf_email_marker" for ev in evidence):
            roles.append("pdf_email_marker")
            role_evidence.append("local PDF text email-marker verification")
        text = first_text(args.audit_text_dir / f"{bibcode}.txt")
        tier, flags = classify_tier(item, config, text)
        record = {**item, "roles": roles, "role_evidence": role_evidence, "distillation_tier": tier}
        if flags:
            record["record_flags"] = flags
        records.append(record)
        for source_dir, target_dir, suffix in ((args.audit_papers_dir, args.papers_dir, ".pdf"), (args.audit_text_dir, args.text_dir, ".txt")):
            source = source_dir / f"{bibcode}{suffix}"
            target = target_dir / source.name
            if source.exists() and not target.exists():
                target_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
    args.output.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "formal_manifest_records": len(records),
        "first_author_verified": len(first_authors),
        "pdf_evidence_records": sum("pdf_email_marker" in item["roles"] or "explicit_corresponding_author" in item["roles"] for item in records),
        "distillation_tier_counts": {
            "core": sum(item["distillation_tier"] == "core" for item in records),
            "supplemental": sum(item["distillation_tier"] == "supplemental" for item in records),
        },
    }, indent=2))


if __name__ == "__main__":
    main()
