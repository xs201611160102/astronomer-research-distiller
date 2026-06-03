#!/usr/bin/env python3
"""Download public PDFs from ADS links and configured journal fallbacks."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import subprocess
from pathlib import Path


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def is_pdf(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 1000 and path.read_bytes()[:4] == b"%PDF"


def download(url: str, destination: Path, connect_timeout: int, max_time: int) -> tuple[bool, str]:
    temporary = destination.with_suffix(".part")
    temporary.unlink(missing_ok=True)
    result = subprocess.run(
        [
            "curl", "-L", "--fail", "--silent", "--show-error",
            "--connect-timeout", str(connect_timeout), "--max-time", str(max_time),
            "-o", str(temporary), url,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and is_pdf(temporary):
        temporary.replace(destination)
        return True, ""
    temporary.unlink(missing_ok=True)
    return False, result.stderr.strip() or "download did not produce a valid PDF"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--papers-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path("config/astronomer.json"))
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--connect-timeout", type=int, default=10)
    parser.add_argument("--max-time", type=int, default=60)
    args = parser.parse_args()
    fallbacks = load_json(args.config).get("pdf_fallbacks", {})
    args.papers_dir.mkdir(parents=True, exist_ok=True)

    def process(item: dict) -> dict:
        destination = args.papers_dir / f"{item['bibcode']}.pdf"
        if is_pdf(destination):
            return {**item, "download_status": "existing", "file": str(destination)}
        attempts = []
        for url in item.get("pdf_links", []) + fallbacks.get(item["bibcode"], []):
            ok, error = download(url, destination, args.connect_timeout, args.max_time)
            attempts.append({"url": url, "error": error})
            if ok:
                return {**item, "download_status": "downloaded", "file": str(destination)}
        return {**item, "download_status": "unavailable", "attempts": attempts}

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        report = list(executor.map(process, load_json(args.manifest)))
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    counts = {}
    for item in report:
        counts[item["download_status"]] = counts.get(item["download_status"], 0) + 1
    print(json.dumps(counts, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
