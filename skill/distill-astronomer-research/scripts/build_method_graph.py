#!/usr/bin/env python3
"""Build a bounded OpenAlex method graph around lineage-defining papers."""

from __future__ import annotations

import argparse
import html
import json
import re
import time
import urllib.parse
import urllib.request
from urllib.error import HTTPError, URLError
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


def openalex_id(value: str) -> str:
    return (value or "").rsplit("/", 1)[-1]


def parse_lineage(path: Path) -> dict[str, list[dict]]:
    branch = ""
    stage = ""
    result: dict[str, list[dict]] = {}
    pending_refs = []
    pending_description = ""

    def flush() -> None:
        nonlocal pending_refs, pending_description
        for bibcode in pending_refs:
            result.setdefault(bibcode, []).append(
                {"branch": branch, "stage": stage, "description": pending_description.strip()}
            )
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


def fetch_json(url: str, cache_path: Path, delay: float) -> dict:
    if cache_path.exists():
        return load_json(cache_path, {}) or {}
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "astronomer-skill-distiller/1.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                payload = json.load(response)
            write_json(cache_path, payload)
            time.sleep(delay)
            return payload
        except HTTPError as error:
            if error.code == 404:
                write_json(cache_path, {})
                return {}
            if error.code not in {429, 500, 502, 503, 504} or attempt == 2:
                raise
        except URLError:
            if attempt == 2:
                raise
        time.sleep(max(delay, 0.5) * (attempt + 1))
    return {}


def fetch_work(work_id: str, cache_dir: Path, delay: float) -> dict:
    short_id = openalex_id(work_id)
    return fetch_json(
        f"https://api.openalex.org/works/{urllib.parse.quote(short_id)}",
        cache_dir / "works" / f"{short_id}.json",
        delay,
    )


def fetch_citing(work_id: str, cache_dir: Path, per_page: int, delay: float) -> list[dict]:
    short_id = openalex_id(work_id)
    query = urllib.parse.urlencode(
        {"filter": f"cites:{short_id}", "sort": "cited_by_count:desc", "per-page": per_page}
    )
    payload = fetch_json(
        f"https://api.openalex.org/works?{query}",
        cache_dir / "citing" / f"{short_id}.json",
        delay,
    )
    return payload.get("results", [])


def fetch_title_search(title: str, cache_dir: Path, per_page: int, delay: float) -> list[dict]:
    normalized = normalize_title(title)
    if not normalized:
        return []
    query = urllib.parse.urlencode({"search": title, "per-page": per_page})
    payload = fetch_json(
        f"https://api.openalex.org/works?{query}",
        cache_dir / "title_search" / f"{normalized[:80]}.json",
        delay,
    )
    return payload.get("results", [])


def best_title_match(title: str, candidates: list[dict]) -> tuple[Optional[dict], str]:
    target = normalize_title(title)
    if not target:
        return None, "no title"
    for work in candidates:
        if normalize_title(work.get("title", "")) == target:
            return work, "exact_normalized_title"
    target_words = set(re.findall(r"[a-z0-9]+", html.unescape(title or "").lower()))
    best = None
    best_score = 0.0
    for work in candidates:
        words = set(re.findall(r"[a-z0-9]+", html.unescape(work.get("title", "") or "").lower()))
        if not words:
            continue
        score = len(target_words & words) / max(1, len(target_words | words))
        if score > best_score:
            best = work
            best_score = score
    if best and best_score >= 0.72:
        return best, f"fuzzy_title_jaccard_{best_score:.2f}"
    return None, "no confident title match"


def summarize_work(work: dict) -> dict:
    return {
        "openalex_id": work.get("id", ""),
        "title": work.get("title", ""),
        "year": work.get("publication_year"),
        "doi": work.get("doi"),
        "cited_by_count": work.get("cited_by_count", 0),
        "authors": [
            authorship.get("author", {}).get("display_name", "")
            for authorship in work.get("authorships", [])[:3]
        ],
        "referenced_works": work.get("referenced_works", []),
    }


def title_suggests_transfer(title: str) -> bool:
    return bool(
        re.search(
            r"j-plus|s-plus|pan-starrs|csst|cmos|sages|gaia|landolt|standard star|mini-jpas",
            title,
            re.I,
        )
    )


def classify_edge(source: dict, target: dict, source_lineage: list[dict], target_lineage: list[dict]) -> tuple[str, str]:
    source_title = source.get("title", "")
    if source_lineage and target_lineage:
        source_branches = {item["branch"] for item in source_lineage}
        target_branches = {item["branch"] for item in target_lineage}
        if source_branches & target_branches:
            if re.search(r"validation|check|correction|recalibration|erratum", source_title, re.I):
                return "validates_method", "heuristic: same lineage branch and validation-like source title"
            if title_suggests_transfer(source_title):
                return "applies_method_to_new_survey", "heuristic: same lineage branch and survey/instrument transfer title"
            return "extends_method", "heuristic: later paper cites an earlier paper in the same lineage branch"
    return "background_only", "heuristic: citation is not mapped to the same method-lineage branch"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("metadata/paper_manifest.json"))
    parser.add_argument("--lineage", type=Path, required=True)
    parser.add_argument("--openalex-works", type=Path, default=Path("metadata/openalex_works.json"))
    parser.add_argument("--config", type=Path, default=Path("config/astronomer.json"))
    parser.add_argument("--cache-dir", type=Path, default=Path("metadata/openalex_graph_cache"))
    parser.add_argument("--output", type=Path, default=Path("metadata/method-graph.json"))
    parser.add_argument("--comparison-output", type=Path, default=Path("metadata/external-comparison-candidates.json"))
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--citing-per-core", type=int, default=12)
    parser.add_argument("--upstream-per-core", type=int, default=12)
    parser.add_argument("--second-hop-per-neighbor", type=int, default=4)
    parser.add_argument("--second-hop-neighbor-limit", type=int, default=60)
    parser.add_argument("--comparison-limit", type=int, default=30)
    parser.add_argument("--title-search-per-core", type=int, default=5)
    parser.add_argument(
        "--no-title-search",
        action="store_true",
        help="Disable OpenAlex title-search matching for lineage papers missing from the local OpenAlex file.",
    )
    parser.add_argument("--delay", type=float, default=0.08)
    args = parser.parse_args()

    config = load_json(args.config, {}) or {}
    overrides = config.get("semantic_edge_overrides", {})
    manifest = load_json(args.manifest, []) or []
    lineage = parse_lineage(args.lineage)
    formal_by_title = {normalize_title(item["title"]): item["bibcode"] for item in manifest}
    local_payload = load_json(args.openalex_works, {}) or {}
    local_works = local_payload.get("results", []) if isinstance(local_payload, dict) else (local_payload if isinstance(local_payload, list) else [])
    local_by_title = {normalize_title(work.get("title", "")): work for work in local_works}
    core_works = {}
    missing_core = []
    match_basis = {}
    for bibcode in sorted(lineage):
        formal = next((item for item in manifest if item["bibcode"] == bibcode), None)
        title = formal.get("title", "") if formal else ""
        work = local_by_title.get(normalize_title(title))
        if work:
            core_works[bibcode] = work
            match_basis[bibcode] = "local_openalex_title"
        else:
            searched_work = None
            basis = "not searched"
            if formal and not args.no_title_search:
                searched_work, basis = best_title_match(
                    title,
                    fetch_title_search(title, args.cache_dir, args.title_search_per_core, args.delay),
                )
            if searched_work:
                core_works[bibcode] = searched_work
                match_basis[bibcode] = basis
            else:
                missing_core.append({"bibcode": bibcode, "title": title, "reason": basis})

    nodes: dict[str, dict] = {}
    raw_edges = set()

    def add_node(work: dict, role: str) -> str:
        work_id = work.get("id", "")
        if not work_id:
            return ""
        summary = summarize_work(work)
        existing = nodes.setdefault(work_id, {**summary, "roles": []})
        existing["roles"] = sorted(set(existing["roles"] + [role]))
        return work_id

    for bibcode, work in core_works.items():
        core_id = add_node(work, "lineage_core")
        references = work.get("referenced_works", [])[: args.upstream_per_core]
        for ref_id in references:
            ref_work = fetch_work(ref_id, args.cache_dir, args.delay)
            neighbor_id = add_node(ref_work, "upstream_1hop")
            if neighbor_id:
                raw_edges.add((core_id, neighbor_id))
        for citing_work in fetch_citing(core_id, args.cache_dir, args.citing_per_core, args.delay):
            citing_id = add_node(citing_work, "downstream_1hop")
            raw_edges.add((citing_id, core_id))

    first_hop_ids = [
        work_id
        for work_id, node in nodes.items()
        if "lineage_core" not in node["roles"] and node["roles"]
    ]
    first_hop_ids = sorted(
        first_hop_ids,
        key=lambda work_id: nodes[work_id].get("cited_by_count", 0),
        reverse=True,
    )[: args.second_hop_neighbor_limit]
    for first_hop_id in first_hop_ids:
        work = fetch_work(first_hop_id, args.cache_dir, args.delay)
        for ref_id in work.get("referenced_works", [])[: args.second_hop_per_neighbor]:
            ref_work = fetch_work(ref_id, args.cache_dir, args.delay)
            second_id = add_node(ref_work, "upstream_2hop")
            if second_id:
                raw_edges.add((first_hop_id, second_id))

    id_to_bibcode = {}
    for work_id, node in nodes.items():
        bibcode = formal_by_title.get(normalize_title(node.get("title", "")))
        if bibcode:
            id_to_bibcode[work_id] = bibcode
    semantic_edges = []
    for source_id, target_id in sorted(raw_edges):
        source = nodes[source_id]
        target = nodes[target_id]
        source_bibcode = id_to_bibcode.get(source_id, "")
        target_bibcode = id_to_bibcode.get(target_id, "")
        relation, basis = classify_edge(
            source,
            target,
            lineage.get(source_bibcode, []),
            lineage.get(target_bibcode, []),
        )
        override_key = f"{source_bibcode}->{target_bibcode}" if source_bibcode and target_bibcode else ""
        if override_key in overrides:
            relation = overrides[override_key]
            basis = "manual override from config"
        semantic_edges.append(
            {
                "source_openalex_id": source_id,
                "source_bibcode": source_bibcode,
                "target_openalex_id": target_id,
                "target_bibcode": target_bibcode,
                "relation": relation,
                "classification_basis": basis,
                "requires_manual_review": basis != "manual override from config",
            }
        )

    external_scores = Counter()
    external_reasons: dict[str, Counter] = {}
    for edge in semantic_edges:
        source_id = edge["source_openalex_id"]
        target_id = edge["target_openalex_id"]
        source_external = source_id not in id_to_bibcode
        target_external = target_id not in id_to_bibcode
        if source_external and target_id in id_to_bibcode:
            external_scores[source_id] += 2
            external_reasons.setdefault(source_id, Counter())["cites_lineage_core_or_formal"] += 1
        if target_external and source_id in id_to_bibcode:
            external_scores[target_id] += 1
            external_reasons.setdefault(target_id, Counter())["cited_by_lineage_core_or_formal"] += 1
    candidates = []
    for work_id, score in external_scores.most_common(args.comparison_limit):
        candidates.append(
            {
                **nodes[work_id],
                "comparison_score": score,
                "comparison_reasons": dict(external_reasons[work_id]),
                "review_status": "candidate_needs_manual_review",
            }
        )
    output = {
        "graph_scope": {
            "lineage_bibcodes": len(lineage),
            "openalex_matched_lineage_bibcodes": len(core_works),
            "missing_lineage_bibcodes": missing_core,
            "lineage_match_basis": match_basis,
            "upstream_per_core": args.upstream_per_core,
            "citing_per_core": args.citing_per_core,
            "second_hop_per_neighbor": args.second_hop_per_neighbor,
            "second_hop_neighbor_limit": args.second_hop_neighbor_limit,
        },
        "nodes": sorted(nodes.values(), key=lambda item: (item.get("year") or 0, item.get("title", ""))),
        "edges": semantic_edges,
    }
    write_json(args.output, output)
    write_json(args.comparison_output, candidates)
    relation_counts = Counter(edge["relation"] for edge in semantic_edges)
    manual_override_count = sum(
        edge["classification_basis"] == "manual override from config" for edge in semantic_edges
    )
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(
        "# Method Graph\n\n"
        "This graph is bounded around lineage-defining papers. Semantic edge labels are heuristic unless explicitly overridden in project configuration.\n\n"
        f"- Lineage papers: {len(lineage)}\n"
        f"- OpenAlex-matched lineage papers: {len(core_works)}\n"
        f"- Missing lineage papers: {len(missing_core)}\n"
        f"- Graph nodes: {len(nodes)}\n"
        f"- Graph edges: {len(semantic_edges)}\n"
        f"- External comparison candidates: {len(candidates)}\n\n"
        f"- Upstream references per core paper: {args.upstream_per_core}\n"
        f"- Downstream citing papers per core paper: {args.citing_per_core}\n"
        f"- Second-hop neighbors expanded: at most {args.second_hop_neighbor_limit}\n"
        f"- Second-hop references per expanded neighbor: {args.second_hop_per_neighbor}\n"
        f"- Manual semantic-edge overrides matched: {manual_override_count}\n\n"
        + (
            "## OpenAlex Matching Diagnostics\n\n"
            + "\n".join(
                f"- `{item['bibcode']}`: {item.get('reason', 'unmatched')} - {item.get('title', '')}"
                for item in missing_core
            )
            + "\n\n"
            if missing_core else ""
        )
        + "## Semantic Edge Counts\n\n"
        + "\n".join(f"- `{relation}`: {count}" for relation, count in sorted(relation_counts.items()))
        + "\n\n## External Comparison Candidates\n\n"
        + "\n".join(
            f"- {item.get('year')}: {item.get('title')} (score={item['comparison_score']}, cited_by={item.get('cited_by_count', 0)})"
            for item in candidates
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "lineage_bibcodes": len(lineage),
                "matched_lineage_bibcodes": len(core_works),
                "missing_lineage_bibcodes": len(missing_core),
                "nodes": len(nodes),
                "edges": len(semantic_edges),
                "relations": dict(relation_counts),
                "comparison_candidates": len(candidates),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
