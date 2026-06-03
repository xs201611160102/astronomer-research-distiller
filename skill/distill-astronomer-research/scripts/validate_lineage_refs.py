#!/usr/bin/env python3
"""Validate that ADS bibcodes cited in a method lineage exist in the formal manifest."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("metadata/paper_manifest.json"))
    parser.add_argument("--lineage", type=Path, required=True)
    args = parser.parse_args()
    manifest = {item["bibcode"] for item in json.loads(args.manifest.read_text(encoding="utf-8"))}
    refs = sorted(set(re.findall(r"`(\d{4}[^`]+)`", args.lineage.read_text(encoding="utf-8"))))
    missing = [ref for ref in refs if ref not in manifest]
    print(json.dumps({"lineage_bibcodes": len(refs), "missing_from_manifest": missing}, indent=2))
    raise SystemExit(bool(missing))


if __name__ == "__main__":
    main()
