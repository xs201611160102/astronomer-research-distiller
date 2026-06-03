#!/usr/bin/env python3
"""Extract text from downloaded PDFs with pdftotext."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--papers-dir", type=Path, required=True)
    parser.add_argument("--text-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    args.text_dir.mkdir(parents=True, exist_ok=True)
    report = []
    for pdf in sorted(args.papers_dir.glob("*.pdf")):
        text = args.text_dir / f"{pdf.stem}.txt"
        result = subprocess.run(["pdftotext", str(pdf), str(text)], capture_output=True, text=True)
        status = "extracted" if result.returncode == 0 and text.exists() else "failed"
        report.append({"bibcode": pdf.stem, "pdf": str(pdf), "text": str(text), "status": status, "error": result.stderr.strip()})
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"extracted": sum(item["status"] == "extracted" for item in report)}, indent=2))


if __name__ == "__main__":
    main()
