#!/usr/bin/env python3
"""Preflight NASA ADS API access before bibliography collection."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path


def keychain_lookup(service: str, account: str | None) -> bool:
    command = ["security", "find-generic-password"]
    if account:
        command.extend(["-a", account])
    command.extend(["-s", service, "-w"])
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0 and bool(result.stdout.strip())


def render_markdown(summary: dict) -> str:
    lines = [
        "# ADS Access Preflight",
        "",
        "NASA ADS is the primary bibliography source for astronomy distillation.",
        "Run this check before collecting papers.",
        "",
        "## Status",
        "",
        f"- ADS token available: `{summary['ads_token_available']}`",
        f"- Sources checked: {', '.join(summary['sources_checked'])}",
        "",
    ]
    if summary["ads_token_available"]:
        lines.extend(
            [
                "## Next Step",
                "",
                "- Run ADS official-library, author-search, and first-author-search collection.",
            ]
        )
    else:
        lines.extend(
            [
                "## Required User Action",
                "",
                "No ADS API token was found. Ask the user to provide one before claiming the ADS corpus is complete.",
                "",
                "Accepted locations:",
                "",
                "- Environment variable: `ADS_DEV_KEY`",
                "- Environment variable: `ADS_TOKEN`",
                "- Apple Keychain generic password service: `ads-api-token`",
                "",
                "Recommended macOS keychain command:",
                "",
                "```sh",
                "security add-generic-password -a \"$USER\" -s ads-api-token -w 'PASTE_ADS_TOKEN_HERE'",
                "```",
                "",
                "Without this token, local cross-seeds, OpenAlex, ORCID, Crossref, and publisher pages are only audit helpers.",
                "Record an exception and do not present the resulting corpus as an ADS-complete bibliography.",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path, default=Path("metadata/ads_access_preflight.json"))
    parser.add_argument("--output-md", type=Path, default=Path("metadata/ads_access_preflight.md"))
    parser.add_argument("--keychain-service", default="ads-api-token")
    parser.add_argument("--keychain-account", default=os.environ.get("USER", ""))
    parser.add_argument("--fail-if-missing", action="store_true")
    args = parser.parse_args()

    sources_checked = []
    token_available = False
    for variable in ("ADS_DEV_KEY", "ADS_TOKEN"):
        sources_checked.append(variable)
        if os.environ.get(variable):
            token_available = True
    sources_checked.append(f"keychain:{args.keychain_service}")
    if keychain_lookup(args.keychain_service, args.keychain_account):
        token_available = True

    summary = {
        "ads_token_available": token_available,
        "sources_checked": sources_checked,
        "keychain_service": args.keychain_service,
        "keychain_account": args.keychain_account,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    raise SystemExit(1 if args.fail_if_missing and not token_available else 0)


if __name__ == "__main__":
    main()
