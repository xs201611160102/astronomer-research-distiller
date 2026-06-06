#!/usr/bin/env python3
"""Initialize a traceable astronomer-distillation project."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


DIRECTORIES = (
    "config",
    "metadata",
    "correspondence_audit/papers",
    "correspondence_audit/text",
    "papers",
    "text",
    "distillation",
    "skill",
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--display-name", required=True)
    parser.add_argument("--skill-name", required=True)
    parser.add_argument("--email", action="append", default=[])
    parser.add_argument("--legacy-email", action="append", default=[])
    parser.add_argument("--name-variant", action="append", default=[])
    parser.add_argument("--orcid", default="")
    args = parser.parse_args()

    for directory in DIRECTORIES:
        (args.project_dir / directory).mkdir(parents=True, exist_ok=True)
    config = {
        "display_name": args.display_name,
        "skill_name": args.skill_name,
        "emails": args.email,
        "legacy_emails": args.legacy_email,
        "name_variants": args.name_variant or [args.display_name],
        "orcid": args.orcid,
        "top_author_limit": 3,
        "explicit_name_patterns": [],
        "pdf_fallbacks": {},
        "supplemental_bibcode_tokens": ["yCat", "IAUGA", "eas..conf", "IAUS"],
        "identity_filter": {
            "min_score": 3,
            "first_author_initial_variants": [],
            "topic_keywords": [],
            "trusted_coauthors": [],
            "affiliation_keywords": [],
            "venue_keywords": [
                "The Astrophysical Journal",
                "The Astrophysical Journal Supplement Series",
                "Astronomy & Astrophysics",
                "Monthly Notices of the Royal Astronomical Society",
                "Nature",
                "Nature Astronomy",
                "Research in Astronomy and Astrophysics",
                "The Astronomical Journal",
            ],
            "reject_keywords": [],
        },
    }
    config_path = args.project_dir / "config/astronomer.json"
    if not config_path.exists():
        config_path.write_text(
            json.dumps(config, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    readme = args.project_dir / "README.md"
    if not readme.exists():
        readme.write_text(
            f"# {args.display_name} 论文蒸馏项目\n\n"
            "本目录使用 ADS 优先、全文审计、证据分级和方法谱系流程构建研究方法 skill。\n\n"
            "## 目录\n\n"
            "- `config/astronomer.json`：作者配置、邮箱和公开 PDF 回退链接。\n"
            "- `metadata/`：ADS 导出、审计报告和正式论文清单。\n"
            "- `correspondence_audit/`：通讯作者全文审计区。\n"
            "- `papers/`、`text/`：正式证据集。\n"
            "- `distillation/`：跨论文归纳。\n"
            "- `skill/`：最终可安装 skill。\n",
            encoding="utf-8",
        )
    verified = args.project_dir / "metadata/verified_first_author_bibcodes.txt"
    verified.touch(exist_ok=True)
    derived_references = args.project_dir / "skill" / args.skill_name / "references"
    derived_references.mkdir(parents=True, exist_ok=True)
    branch_protocol = derived_references / "branch-evaluation-protocol.md"
    if not branch_protocol.exists():
        template = Path(__file__).resolve().parent.parent / "references" / "branch-evaluation-protocol.md"
        shutil.copyfile(template, branch_protocol)
    print(f"Initialized {args.project_dir}")


if __name__ == "__main__":
    main()
