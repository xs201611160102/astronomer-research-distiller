#!/usr/bin/env python3
"""Collect normalized ADS records with the ADS API."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path


API_URL = "https://api.adsabs.harvard.edu/v1/search/query"
FIELDS = "bibcode,title,author,links_data,year,pub,doctype,identifier,aff"


def keychain_token(service: str, account: str | None) -> str:
    command = ["security", "find-generic-password"]
    if account:
        command.extend(["-a", account])
    command.extend(["-s", service, "-w"])
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def get_token(args: argparse.Namespace) -> str:
    return (
        os.environ.get("ADS_DEV_KEY")
        or os.environ.get("ADS_TOKEN")
        or keychain_token(args.keychain_service, args.keychain_account)
    )


def fetch_page(token: str, query: str, start: int, rows: int, sort: str) -> dict:
    params = urllib.parse.urlencode(
        {
            "q": query,
            "fl": FIELDS,
            "rows": rows,
            "start": start,
            "sort": sort,
        }
    )
    request = urllib.request.Request(
        f"{API_URL}?{params}",
        headers={"Authorization": f"Bearer {token}", "User-Agent": "astronomer-skill-distiller/1.0"},
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.load(response)


def link_gateway_links(bibcode: str) -> list[dict]:
    return [
        {
            "href": f"https://ui.adsabs.harvard.edu/link_gateway/{bibcode}/EPRINT_PDF",
            "text": "Preprint PDF",
        },
        {
            "href": f"https://ui.adsabs.harvard.edu/link_gateway/{bibcode}/PUB_PDF",
            "text": "Publisher PDF",
        },
    ]


def normalize(doc: dict) -> dict:
    authors = doc.get("author") or []
    title = doc.get("title") or []
    return {
        "bibcode": doc.get("bibcode", ""),
        "title": title[0] if title else "",
        "first_author": authors[0] if authors else "",
        "authors_display": "; ".join(authors),
        "year": doc.get("year"),
        "pub": doc.get("pub", ""),
        "doctype": doc.get("doctype", ""),
        "identifier": doc.get("identifier", []),
        "aff": doc.get("aff", []),
        "links": link_gateway_links(doc.get("bibcode", "")),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rows", type=int, default=200)
    parser.add_argument("--max-records", type=int, default=1000)
    parser.add_argument("--sort", default="date desc")
    parser.add_argument("--delay", type=float, default=0.2)
    parser.add_argument("--keychain-service", default="ads-api-token")
    parser.add_argument("--keychain-account", default=os.environ.get("USER", ""))
    args = parser.parse_args()

    token = get_token(args)
    if not token:
        raise SystemExit("No ADS token found. Run check_ads_access.py and add ADS token first.")

    records = []
    start = 0
    num_found = None
    while len(records) < args.max_records:
        payload = fetch_page(token, args.query, start, min(args.rows, args.max_records - len(records)), args.sort)
        response = payload.get("response", {})
        num_found = response.get("numFound", 0)
        docs = response.get("docs", [])
        if not docs:
            break
        records.extend(normalize(doc) for doc in docs)
        start += len(docs)
        if start >= num_found:
            break
        time.sleep(args.delay)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"query": args.query, "numFound": num_found, "written": len(records), "output": str(args.output)}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
