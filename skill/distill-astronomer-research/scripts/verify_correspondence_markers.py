#!/usr/bin/env python3
"""Find explicit correspondence wording and configured email markers in PDF text."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def context(text: str, match: re.Match[str], width: int = 220) -> str:
    return re.sub(r"\s+", " ", text[max(0, match.start() - width):match.end() + width]).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config/astronomer.json"))
    parser.add_argument("--manifest", type=Path, default=Path("metadata/correspondence_audit_manifest.json"))
    parser.add_argument("--text-dir", type=Path, default=Path("correspondence_audit/text"))
    parser.add_argument("--report", type=Path, default=Path("metadata/correspondence_audit_verification.json"))
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    emails = config.get("emails", []) + config.get("legacy_emails", [])
    email_pattern = re.compile("|".join(re.escape(email).replace(r"\@", r"\s*@\s*") for email in emails), re.I) if emails else None
    names = config.get("explicit_name_patterns") or [re.escape(name) for name in config.get("name_variants", [])]
    name_pattern = "(?:" + "|".join(names) + ")" if names else r".{0,80}"
    explicit_patterns = [
        re.compile(rf"{name_pattern}.{{0,180}}correspond", re.I | re.S),
        re.compile(rf"correspond.{{0,180}}{name_pattern}", re.I | re.S),
        re.compile(rf"通信作者.{{0,180}}{name_pattern}", re.I | re.S),
    ]
    report = []
    for item in json.loads(args.manifest.read_text(encoding="utf-8")):
        text_path = args.text_dir / f"{item['bibcode']}.txt"
        evidence = []
        if text_path.exists():
            text = text_path.read_text(encoding="utf-8", errors="replace")[:50000]
            if email_pattern:
                match = email_pattern.search(text)
                if match:
                    evidence.append({"kind": "pdf_email_marker", "context": context(text, match)})
            for pattern in explicit_patterns:
                match = pattern.search(text)
                if match:
                    evidence.append({"kind": "explicit_corresponding_author", "context": context(text, match)})
        report.append({"bibcode": item["bibcode"], "title": item["title"], "status": "pdf_text_evidence_found" if evidence else "manual_review_needed", "evidence": evidence})
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "candidates": len(report),
        "pdf_text_evidence_found": sum(item["status"] == "pdf_text_evidence_found" for item in report),
        "explicit_corresponding_author": sum(any(ev["kind"] == "explicit_corresponding_author" for ev in item["evidence"]) for item in report),
        "pdf_email_marker": sum(any(ev["kind"] == "pdf_email_marker" for ev in item["evidence"]) for item in report),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
