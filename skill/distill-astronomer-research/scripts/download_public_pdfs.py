#!/usr/bin/env python3
"""Download public PDFs from ADS links and configured journal fallbacks."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def is_pdf(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 1000 and path.read_bytes()[:4] == b"%PDF"


def url_kind(url: str) -> str:
    host = urlparse(url).netloc.casefold()
    if "arxiv.org" in host:
        return "arxiv"
    if "adsabs.harvard.edu" in host:
        return "ads_gateway"
    return "fallback"


def ordered_links(pdf_links: list[str], fallback_links: list[str]) -> list[str]:
    def priority(url: str) -> tuple[int, str]:
        kind = url_kind(url)
        if kind == "arxiv":
            return (0, url)
        if kind == "ads_gateway" and url.endswith("EPRINT_PDF"):
            return (1, url)
        if kind == "fallback":
            return (2, url)
        return (3, url)

    return sorted(dict.fromkeys((pdf_links or []) + (fallback_links or [])), key=priority)


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


def progress(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--papers-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path("config/astronomer.json"))
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--connect-timeout", type=int, default=10)
    parser.add_argument("--max-time", type=int, default=45)
    parser.add_argument("--gateway-max-time", type=int, default=15)
    parser.add_argument("--record-timeout", type=int, default=90)
    parser.add_argument("--max-attempts-per-record", type=int, default=3)
    parser.add_argument("--progress-every", type=int, default=1)
    args = parser.parse_args()
    fallbacks = load_json(args.config).get("pdf_fallbacks", {}) if args.config.exists() else {}
    args.papers_dir.mkdir(parents=True, exist_ok=True)

    def process(item: dict) -> dict:
        started = time.monotonic()
        destination = args.papers_dir / f"{item['bibcode']}.pdf"
        if is_pdf(destination):
            return {**item, "download_status": "existing", "file": str(destination)}
        attempts = []
        links = ordered_links(item.get("pdf_links", []), fallbacks.get(item["bibcode"], []))
        for url in links[: max(0, args.max_attempts_per_record)]:
            elapsed = time.monotonic() - started
            if elapsed >= args.record_timeout:
                attempts.append({"url": url, "error": f"record timeout after {elapsed:.1f}s before attempt"})
                break
            per_url_max_time = args.gateway_max_time if url_kind(url) == "ads_gateway" else args.max_time
            remaining = max(1, int(args.record_timeout - elapsed))
            ok, error = download(url, destination, args.connect_timeout, min(per_url_max_time, remaining))
            attempts.append({"url": url, "kind": url_kind(url), "error": error})
            if ok:
                return {**item, "download_status": "downloaded", "file": str(destination), "attempts": attempts}
        skipped = max(0, len(links) - len(attempts))
        result = {**item, "download_status": "unavailable", "attempts": attempts}
        if skipped:
            result["skipped_link_count"] = skipped
        return result

    manifest = load_json(args.manifest)
    total = len(manifest)
    progress(
        "download_public_pdfs: "
        f"records={total} workers={args.workers} max_time={args.max_time}s "
        f"gateway_max_time={args.gateway_max_time}s record_timeout={args.record_timeout}s "
        f"max_attempts_per_record={args.max_attempts_per_record}"
    )
    report = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process, item): item for item in manifest}
        counts = {}
        for completed, future in enumerate(concurrent.futures.as_completed(futures), start=1):
            item = future.result()
            report.append(item)
            counts[item["download_status"]] = counts.get(item["download_status"], 0) + 1
            if args.progress_every and (completed % args.progress_every == 0 or completed == total):
                progress(
                    "download_public_pdfs: "
                    f"{completed}/{total} {item['bibcode']} {item['download_status']} "
                    f"counts={json.dumps(counts, sort_keys=True)}"
                )
    report.sort(key=lambda item: item["bibcode"], reverse=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    counts = {}
    for item in report:
        counts[item["download_status"]] = counts.get(item["download_status"], 0) + 1
    print(json.dumps(counts, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
