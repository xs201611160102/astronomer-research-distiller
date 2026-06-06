#!/usr/bin/env python3
"""Filter ADS same-name candidates with configurable identity signals."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


DEFAULT_ASTRONOMY_VENUES = [
    "Astronomical Journal",
    "Astronomy & Astrophysics",
    "Astrophysical Journal",
    "Astrophysical Journal Supplement",
    "Monthly Notices",
    "Nature Astronomy",
    "Research in Astronomy and Astrophysics",
]

DEFAULT_REJECT_KEYWORDS = [
    "reinforced concrete",
    "seismic performance",
    "shake table",
    "plant disease",
    "nanomedicine",
    "hydraulic",
    "soil",
    "crop",
    "remote sensing",
    "wastewater",
    "photovoltaic",
    "battery",
]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def norm(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").casefold()).strip()


def text_blob(record: dict) -> str:
    fields = [
        record.get("bibcode", ""),
        record.get("title", ""),
        record.get("first_author", ""),
        record.get("authors_display", ""),
        record.get("pub", ""),
        record.get("doctype", ""),
        " ".join(record.get("identifier", []) or []),
        " ".join(record.get("aff", []) or []),
    ]
    return norm(" ".join(str(item) for item in fields if item))


def author_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").casefold())


def load_records(paths: list[Path]) -> list[dict]:
    by_bibcode = {}
    for path in paths:
        payload = load_json(path)
        if isinstance(payload, dict) and "results" in payload:
            payload = payload["results"]
        if not isinstance(payload, list):
            raise SystemExit(f"Expected a list of ADS records in {path}")
        for item in payload:
            bibcode = item.get("bibcode")
            if not bibcode:
                continue
            merged = by_bibcode.setdefault(bibcode, {**item, "source_files": []})
            merged["source_files"].append(str(path))
            for key in ("title", "first_author", "authors_display", "year", "pub", "doctype", "identifier", "aff", "links"):
                if not merged.get(key) and item.get(key):
                    merged[key] = item[key]
    return sorted(by_bibcode.values(), key=lambda item: item["bibcode"], reverse=True)


def matching_terms(blob: str, terms: list[str]) -> list[str]:
    return [term for term in terms if norm(term) and norm(term) in blob]


def score_record(record: dict, config: dict) -> tuple[int, list[str], list[str]]:
    identity = config.get("identity_filter", {})
    blob = text_blob(record)
    authors_blob = norm(record.get("authors_display", ""))
    aff_blob = norm(" ".join(record.get("aff", []) or []))
    pub_blob = norm(record.get("pub", ""))
    first_key = author_key(record.get("first_author", ""))
    name_keys = {author_key(item) for item in config.get("name_variants", [])}
    initial_keys = {author_key(item) for item in identity.get("first_author_initial_variants", [])}

    accept_topics = identity.get("topic_keywords", [])
    coauthors = identity.get("trusted_coauthors", [])
    affiliations = identity.get("affiliation_keywords", [])
    venues = identity.get("venue_keywords", DEFAULT_ASTRONOMY_VENUES)
    reject_terms = identity.get("reject_keywords", DEFAULT_REJECT_KEYWORDS)

    score = 0
    reasons: list[str] = []
    rejects = matching_terms(blob, reject_terms)

    if first_key in name_keys:
        score += 3
        reasons.append("first author matches configured full name variant")
    elif first_key in initial_keys:
        score += 1
        reasons.append("first author matches configured initial-only variant")

    hits = matching_terms(blob, accept_topics)
    if hits:
        score += min(4, 2 + len(hits) // 3)
        reasons.append("topic signals: " + ", ".join(hits[:8]))

    hits = matching_terms(authors_blob, coauthors)
    if hits:
        score += min(4, 2 + len(hits) // 3)
        reasons.append("trusted coauthor signals: " + ", ".join(hits[:8]))

    hits = matching_terms(aff_blob, affiliations)
    if hits:
        score += min(3, 1 + len(hits) // 2)
        reasons.append("affiliation signals: " + ", ".join(hits[:8]))

    hits = matching_terms(pub_blob, venues)
    if hits:
        score += 1
        reasons.append("astronomy venue signal: " + ", ".join(hits[:3]))

    if rejects:
        score -= 3
    return score, reasons, rejects


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--config", type=Path, default=Path("config/astronomer.json"))
    parser.add_argument("--accepted", type=Path, required=True)
    parser.add_argument("--rejected", type=Path, required=True)
    parser.add_argument("--first-author-bibcodes", type=Path, required=True)
    parser.add_argument("--min-score", type=int, default=None)
    args = parser.parse_args()

    config = load_json(args.config)
    identity = config.get("identity_filter", {})
    min_score = args.min_score if args.min_score is not None else int(identity.get("min_score", 3))
    initial_keys = {author_key(item) for item in identity.get("first_author_initial_variants", [])}
    name_keys = {author_key(item) for item in config.get("name_variants", [])}

    accepted = []
    rejected = []
    first_author_bibcodes = []
    for record in load_records(args.input):
        score, reasons, rejects = score_record(record, config)
        annotated = {
            **record,
            "identity_score": score,
            "identity_reasons": reasons,
            "identity_reject_signals": rejects,
        }
        if score >= min_score and reasons and not (rejects and score < min_score + 2):
            accepted.append(annotated)
            first_key = author_key(record.get("first_author", ""))
            if first_key in name_keys or first_key in initial_keys:
                first_author_bibcodes.append(record["bibcode"])
        else:
            rejected.append(annotated)

    args.accepted.parent.mkdir(parents=True, exist_ok=True)
    args.rejected.parent.mkdir(parents=True, exist_ok=True)
    args.accepted.write_text(json.dumps(accepted, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.rejected.write_text(json.dumps(rejected, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.first_author_bibcodes.write_text(
        "\n".join(sorted(set(first_author_bibcodes), reverse=True)) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "inputs": [str(path) for path in args.input],
                "accepted": len(accepted),
                "rejected": len(rejected),
                "verified_first_author_candidates": len(set(first_author_bibcodes)),
                "min_score": min_score,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
