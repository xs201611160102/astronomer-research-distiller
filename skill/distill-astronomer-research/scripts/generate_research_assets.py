#!/usr/bin/env python3
"""Generate researcher-profile, paper-card, graph, provenance, and holdout assets."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
from collections import Counter
from pathlib import Path
from typing import Optional


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def normalize_title(value: str) -> str:
    value = html.unescape(value or "").lower()
    value = value.replace("–", "-").replace("—", "-").replace("−", "-")
    return re.sub(r"[^a-z0-9]+", "", value)


def year_from_bibcode(bibcode: str) -> int | None:
    match = re.match(r"(\d{4})", bibcode)
    return int(match.group(1)) if match else None


def split_authors(value: str, limit: int) -> list[str]:
    authors = []
    for item in (value or "").split(";"):
        item = re.sub(r"\s+and\s+\d+\s+more\s*$", "", item.strip())
        if item:
            authors.append(item)
    return authors[:limit]


def author_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def parse_lineage(path: Optional[Path]) -> dict[str, list[dict]]:
    if not path or not path.exists():
        return {}
    branch = ""
    stage = ""
    result: dict[str, list[dict]] = {}
    pending_refs = []
    pending_description = ""

    def flush() -> None:
        nonlocal pending_refs, pending_description
        for bibcode in pending_refs:
            result.setdefault(bibcode, []).append({"branch": branch, "stage": stage, "description": pending_description.strip()})
        pending_refs = []
        pending_description = ""

    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            flush()
            branch = line[3:].strip()
        elif line.startswith("### "):
            flush()
            stage = line[4:].strip()
        elif line.startswith("- "):
            flush()
            pending_refs = re.findall(r"`(\d{4}[^`]+)`", line)
            pending_description = line.split(":", 1)[1].strip() if ":" in line else line[2:].strip()
        elif pending_refs and line.startswith("  "):
            pending_description += " " + line.strip()
        else:
            flush()
    flush()
    return result


def abstract_excerpt(text_path: Path) -> str:
    if not text_path.exists():
        return ""
    text = re.sub(r"\s+", " ", text_path.read_text(encoding="utf-8", errors="replace")[:30000])
    match = re.search(r"\babstract\b[.:]?\s*(.{200,2200}?)(?:\bkeywords?\b|\bsubject headings?\b|\b1\.?\s+introduction\b)", text, re.I)
    return (match.group(1) if match else "").strip()


def extract_openalex_edges(openalex_path: Path, manifest: list[dict]) -> list[dict]:
    payload = load_json(openalex_path, {}) or {}
    works = payload.get("results", []) if isinstance(payload, dict) else (payload if isinstance(payload, list) else [])
    formal_by_title = {normalize_title(item["title"]): item["bibcode"] for item in manifest}
    id_to_bibcode = {}
    for work in works:
        bibcode = formal_by_title.get(normalize_title(work.get("title", "")))
        if bibcode and work.get("id"):
            id_to_bibcode[work["id"]] = bibcode
    edges = []
    for work in works:
        source = formal_by_title.get(normalize_title(work.get("title", "")))
        if not source:
            continue
        for target_id in work.get("referenced_works", []):
            target = id_to_bibcode.get(target_id)
            if target:
                edges.append({"source": source, "target": target, "relation": "cites"})
    return sorted(edges, key=lambda item: (item["source"], item["target"]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config/astronomer.json"))
    parser.add_argument("--manifest", type=Path, default=Path("metadata/paper_manifest.json"))
    parser.add_argument("--verification", type=Path, default=Path("metadata/correspondence_audit_verification.json"))
    parser.add_argument("--openalex-works", type=Path, default=Path("metadata/openalex_works.json"))
    parser.add_argument("--lineage", type=Path)
    parser.add_argument("--text-dir", type=Path, default=Path("text"))
    parser.add_argument("--cards-json", type=Path, default=Path("distillation/paper-cards.json"))
    parser.add_argument("--cards-md", type=Path, default=Path("distillation/paper-cards.md"))
    parser.add_argument("--ledger", type=Path, default=Path("metadata/evidence-ledger.jsonl"))
    parser.add_argument("--graph-json", type=Path, default=Path("metadata/research-graph.json"))
    parser.add_argument("--profile-md", type=Path, required=True)
    parser.add_argument("--graph-md", type=Path, required=True)
    parser.add_argument("--holdout-md", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, default=Path("metadata/distillation-snapshot.json"))
    parser.add_argument("--update-report", type=Path, default=Path("metadata/update-report.json"))
    args = parser.parse_args()

    config = load_json(args.config, {}) or {}
    manifest = load_json(args.manifest, []) or []
    verification = {item["bibcode"]: item for item in load_json(args.verification, []) or []}
    author_limit = int(config.get("top_author_limit", 3))
    lineage = parse_lineage(args.lineage)
    target_keys = {author_key(token) for token in config.get("name_variants", [])}
    aliases = {author_key(key): value for key, value in config.get("collaborator_aliases", {}).items()}
    cards = []
    ledger = []
    collaborators = Counter()
    for item in manifest:
        bibcode = item["bibcode"]
        top_authors = split_authors(item.get("authors_display", ""), author_limit)
        for author in top_authors:
            key = author_key(author)
            if key not in target_keys:
                collaborators[aliases.get(key, author)] += 1
        verification_item = verification.get(bibcode, {})
        evidence = verification_item.get("evidence", [])
        lineage_items = lineage.get(bibcode, [])
        cards.append(
            {
                "bibcode": bibcode,
                "year": year_from_bibcode(bibcode),
                "title": item.get("title", ""),
                "roles": item.get("roles", []),
                "top_authors": top_authors,
                "abstract_excerpt": abstract_excerpt(args.text_dir / f"{bibcode}.txt"),
                "science_question": "",
                "data_and_sample": "",
                "observables": "",
                "method": " ".join(dict.fromkeys(entry["description"] for entry in lineage_items)),
                "systematics": "",
                "validation": "",
                "limitations": "",
                "lineage_branch": "; ".join(dict.fromkeys(entry["branch"] for entry in lineage_items)),
                "lineage_stage": "; ".join(dict.fromkeys(entry["stage"] for entry in lineage_items)),
            }
        )
        for source in item.get("role_evidence", []):
            ledger.append({"bibcode": bibcode, "claim_type": "authorship_role", "source_type": "manifest", "evidence_level": "metadata_or_manual_audit", "source": source})
        for evidence_item in evidence:
            ledger.append({"bibcode": bibcode, "claim_type": "correspondence_marker", "source_type": "pdf_text", "evidence_level": evidence_item.get("kind", "pdf_text"), "source": evidence_item.get("context", "")})
        for lineage_item in lineage_items:
            ledger.append({"bibcode": bibcode, "claim_type": "method_lineage", "source_type": "codex_synthesis", "evidence_level": "inference_from_paper_sequence", "source": f"{lineage_item['branch']} / {lineage_item['stage']}: {lineage_item['description']}"})

    citation_edges = extract_openalex_edges(args.openalex_works, manifest)
    graph = {
        "top_author_limit": author_limit,
        "collaborators": [{"name": name, "paper_count": count} for name, count in collaborators.most_common()],
        "citation_edges_within_formal_manifest": citation_edges,
    }
    write_json(args.cards_json, cards)
    args.cards_md.parent.mkdir(parents=True, exist_ok=True)
    args.cards_md.write_text(
        "# Paper Cards\n\n"
        "Machine-generated metadata skeletons for Codex review. Fill analytical fields after reading representative PDFs.\n\n"
        + "\n".join(
            f"## `{card['bibcode']}` {card['title']}\n\n"
            f"- Year: {card['year']}\n- Roles: {', '.join(card['roles'])}\n"
            f"- Top authors: {'; '.join(card['top_authors'])}\n"
            f"- Abstract excerpt: {card['abstract_excerpt'][:600]}\n"
            "- Science question:\n- Data and sample:\n- Observables:\n- Method:\n"
            "- Systematics:\n- Validation:\n- Limitations:\n- Lineage branch and stage:\n"
            for card in cards
        ),
        encoding="utf-8",
    )
    args.ledger.parent.mkdir(parents=True, exist_ok=True)
    args.ledger.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in ledger), encoding="utf-8")
    write_json(args.graph_json, graph)

    years = sorted({card["year"] for card in cards if card["year"]})
    cutoff = int(config.get("holdout_cutoff_year", max(years) - 2 if years else dt.date.today().year - 2))
    train = [card["bibcode"] for card in cards if card["year"] and card["year"] <= cutoff]
    holdout = [card["bibcode"] for card in cards if card["year"] and card["year"] > cutoff]
    args.holdout_md.parent.mkdir(parents=True, exist_ok=True)
    args.holdout_md.write_text(
        "# Holdout Evaluation\n\n"
        f"Default temporal cutoff: `{cutoff}`. Build a provisional lineage using papers up to this year, "
        "then compare its predicted next refinements with the held-out papers. This is a human-reviewed evaluation, not an automated score.\n\n"
        f"- Training records: {len(train)}\n- Held-out records: {len(holdout)}\n\n"
        "## Evaluation Questions\n\n"
        "1. Did the early-paper synthesis identify the later research direction?\n"
        "2. Did it predict the required new data, instrument, or validation layer?\n"
        "3. Which later developments were missed?\n"
        "4. Which predicted extensions did not appear in held-out papers?\n"
        "5. Should the active method lineage be revised?\n\n"
        "## Held-Out ADS Bibcodes\n\n"
        + "\n".join(f"- `{bibcode}`" for bibcode in holdout)
        + "\n",
        encoding="utf-8",
    )
    orcid = config.get("orcid", "")
    args.profile_md.parent.mkdir(parents=True, exist_ok=True)
    args.profile_md.write_text(
        "# Researcher Profile\n\n"
        f"- Name: {config.get('display_name', '')}\n"
        f"- ORCID: {orcid or 'not recorded'}\n"
        f"- ORCID URL: {'https://orcid.org/' + orcid if orcid else 'not recorded'}\n"
        f"- Formal manifest records: {len(manifest)}\n"
        f"- First-author records: {sum('first_author' in role or 'first_author_verified' in role for item in manifest for role in item.get('roles', []))}\n"
        f"- PDF correspondence-marker records: {sum(any('corresponding_author' in role or role == 'pdf_email_marker' for role in item.get('roles', [])) for item in manifest)}\n\n"
        "Use ORCID as an identity anchor, not as a complete publication list. ADS remains the primary astronomy bibliography.\n",
        encoding="utf-8",
    )
    args.graph_md.parent.mkdir(parents=True, exist_ok=True)
    args.graph_md.write_text(
        "# Collaboration And Citation Map\n\n"
        f"Only the first {author_limit} listed authors are tracked by default, matching the astronomy-focused distillation policy.\n\n"
        "## Frequent Top-Author Collaborators\n\n"
        + "\n".join(f"- {item['name']}: {item['paper_count']} records" for item in graph["collaborators"][:30])
        + "\n\n## Internal Citation Edges\n\n"
        + ("\n".join(f"- `{edge['source']}` cites `{edge['target']}`" for edge in citation_edges) or "- No mapped internal citation edges available.")
        + "\n",
        encoding="utf-8",
    )
    new_snapshot = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "bibcodes": sorted(item["bibcode"] for item in manifest),
        "orcid": orcid,
    }
    old_snapshot = load_json(args.snapshot, {}) or {}
    old_bibcodes = set(old_snapshot.get("bibcodes", []))
    new_bibcodes = set(new_snapshot["bibcodes"])
    write_json(args.update_report, {"added_bibcodes": sorted(new_bibcodes - old_bibcodes), "removed_bibcodes": sorted(old_bibcodes - new_bibcodes), "previous_generated_at": old_snapshot.get("generated_at"), "current_generated_at": new_snapshot["generated_at"]})
    write_json(args.snapshot, new_snapshot)
    print(json.dumps({"paper_cards": len(cards), "ledger_entries": len(ledger), "collaborators": len(graph["collaborators"]), "citation_edges": len(citation_edges), "holdout_cutoff_year": cutoff, "holdout_records": len(holdout)}, indent=2))


if __name__ == "__main__":
    main()
