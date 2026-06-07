#!/usr/bin/env python3
"""Extract text from downloaded PDFs with pdftotext."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from report_utils import count_by, load_records, write_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--papers-dir", type=Path, required=True)
    parser.add_argument("--text-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Optional audit manifest. When provided, extract only PDFs whose bibcodes are in the manifest.",
    )
    args = parser.parse_args()
    args.text_dir.mkdir(parents=True, exist_ok=True)
    allowed_bibcodes = None
    if args.manifest:
        allowed_bibcodes = {item["bibcode"] for item in load_records(args.manifest)}
    report = []
    for pdf in sorted(args.papers_dir.glob("*.pdf")):
        if allowed_bibcodes is not None and pdf.stem not in allowed_bibcodes:
            continue
        text = args.text_dir / f"{pdf.stem}.txt"
        result = subprocess.run(["pdftotext", str(pdf), str(text)], capture_output=True, text=True)
        status = "extracted" if result.returncode == 0 and text.exists() else "failed"
        report.append({"bibcode": pdf.stem, "pdf": str(pdf), "text": str(text), "status": status, "error": result.stderr.strip()})
    counts = count_by(report, "status")
    summary = {"total_records": len(report), "status_counts": counts, "extracted": counts.get("extracted", 0)}
    write_report(args.report, report, summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
