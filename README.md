# 天文学家论文蒸馏通用流程

本项目将 ADS 优先的天文学家论文整理与研究方法蒸馏流程封装为 Codex skill。最终产物不是“模仿某位天文学家说话”的聊天角色，而是一个可追溯的研究方法数字人格：它把论文中的方法谱系、适用边界、验证习惯和回退策略组织成可调用的工作模型。

## 蒸馏后的数字人格可以做什么

安装某位天文学家的派生 skill 后，可以让它围绕该研究者论文中蒸馏出的研究框架工作：

- 审阅论文、proposal、观测计划、catalog paper 和数据分析流程。
- 判断目标问题关联哪些研究分支，并标记 `primary`、`supporting` 或 `not applicable`。
- 给出可用的 baseline 方法、后续 refinement、必要输入、验证方案、系统误差和 failure boundary。
- 判断你的数据或科学问题是否超出该方法的适用域，并给出 fallback 或 abstention 条件。
- 对比目标论文与谱系核心论文、外部对照候选和已知方法边界。
- 生成审稿意见、方法 checklist、验证计划、项目设计建议或刷新语料需求。

示例调用：

```text
使用 zhang-san-research review 这篇论文。
使用 li-si-research 评估这个测光校准方案。
使用 zhang-san-research 帮我设计一个 stellar label pipeline 的验证计划。
```

严禁把派生 skill 当作本人代理、私人观点模拟器或完整书目数据库。它只能在来源证据和蒸馏出的研究方法边界内给出建议。

## 交付物

- `skill/distill-astronomer-research/`：可安装的通用 skill。
- `scripts/` 逻辑位于 skill 内：初始化项目、自动写入多分支评估模板、默认限制到 ADS astronomy database 的 ADS API 记录收集、同名作者身份过滤、ADS 全文审计、带进度和长尾控制的公开 PDF 下载、文本提取、通讯作者证据扫描、正式 manifest 生成、论文索引生成、方法谱系引用校验、有界引用邻域构建和滚动时间回测模板生成。
- `assets/astronomer-config.example.json`：每位天文学家的配置模板。

## 安装

克隆仓库后，将通用 skill 目录复制到本机 Codex skills 目录：

```bash
git clone https://github.com/xs201611160102/astronomer-research-distiller.git
mkdir -p ~/.codex/skills
cp -R astronomer-research-distiller/skill/distill-astronomer-research ~/.codex/skills/
```

确认安装结果：

```bash
ls ~/.codex/skills/distill-astronomer-research/SKILL.md
```

安装后新开一个 Codex 线程，或重启 Codex，让新 skill 被重新加载。之后可直接要求 Codex：

`使用 distill-astronomer-research skill，为某位天文学家构建研究方法 skill。`

## 核心约束

1. 优先使用 ADS 和官方个人主页。
2. 不把一次 ADS 全文邮箱搜索当作完整召回。
3. 同时记录当前和历史邮箱。
4. 区分明确通讯作者表述、PDF 首页邮箱标记和未核验元数据候选。
5. 蒸馏结果必须包含按年份组织的方法谱系：基线、扩展、输入条件、验证和回退版本。
6. 使用 ORCID 作为身份锚点，但仍以 ADS 作为天文学论文主目录。
7. 天文学场景重点追踪第一作者、通讯作者和最多前三作者，不机械推断详细贡献角色。
8. 自动生成论文卡片、证据账本、前三作者合作图、内部引用边、更新差异和时间切分验证模板。
9. 围绕谱系核心论文构建有界一至二跳引用邻域；引用边语义自动标签必须标为启发式判断，并允许人工覆盖。
10. 从引用邻域生成外部方法对照候选，并使用多个时间截止点做滚动 holdout 回测。
11. 将人工阅读全文得到的谱系论文卡片与机器骨架分开保存：方法基线、关键扩展和边界变化标为 `deep`，应用、综述、会议摘要和过渡节点标为 `context`。深读卡片的 `source_lines` 会被 `render_deep_cards.py` 渲染到 Markdown，并默认显示目标行前后各一行上下文，方便逐条回查；从本地全文抽取核心引用上下文，仅把会改变谱系的少量歧义边交给用户裁决。
12. 维护方法适用边界、版本与勘误关系、原子结论账本、刷新协议和异常日志。超出验证域且没有合理回退时明确拒绝套用；外部证据冲突时保留分歧。
13. 使用保守刷新命令重建本地资产并输出人工复核队列；默认不联网、不覆盖人工策展 JSON。
14. 每个生成型天文学家 skill 必须采用多分支评估协议：先从该研究者自己的论文和 `research-map.md` 中识别实际研究方向，标记 `primary`、`supporting` 或 `not applicable`，分别完成分支级审查后再统合。不要预设固定领域清单，也不要让最显眼的单一主线压过其他真实相关分支。
15. 每个生成型 skill 必须携带 `references/branch-evaluation-protocol.md`，使用统一覆盖矩阵和分支级报告模板，使不同天文学家的论文审查可复现、可比较。
16. 每个生成型 skill 必须携带数字人格使用说明：说明它能做论文/方案/工作流审查、方法设计、适用性 triage、谱系比较和刷新诊断；同时明确它是论文蒸馏出的研究方法操作模型，不是对天文学家本人的模拟或代言。
17. 语料收集阶段必须先用 `identity_filter` 配置和 `filter_ads_identity_candidates.py` 将 ADS raw 搜索拆成目标作者记录与同名误配记录，再合并过滤后的 ADS 来源并尝试下载全量公开 PDF；代表性论文只用于后续深读和方法谱系，不得替代全量下载。运行 `audit_corpus_completeness.py` 记录 ADS、下载、抽文本和正式 manifest 的数量差异。
18. PDF 下载器必须优先尝试 ADS identifier 暴露出的 arXiv PDF，再尝试 ADS gateway 和配置回退链接；arXiv 默认不设置总下载时间限制，下载过程应输出逐条进度，默认使用 `.part` 文件断点续传，并通过 gateway 短超时、单记录超时和单记录最大尝试数控制出版社拒绝或慢链接造成的长尾等待。
19. 通讯作者审计必须在全文抽取后运行：`verify_correspondence_markers.py` 同时记录明确通讯作者表述和 PDF 邮箱标记；已知当前或历史邮箱时，应额外做 ADS full-text 邮箱检索作为通讯作者候选召回来源，但不得绕过 PDF/出版社证据分级。
20. ADS API 采集默认追加 `database:astronomy`，减少 physics/general 库的同名污染；只有在做误配审计或目标作者确有跨库关键论文时，才显式使用 `--database all`。
21. 会议摘要、会议记录和 symposium proceedings 默认不进入 PDF 下载审计；`build_ads_audit_manifest.py` 会将它们写入 `metadata/conference_records_excluded_from_audit.json`，除非用户明确要求 `--include-conference-records`。arXiv 预印本若在 metadata 或全文中显示 proceedings 语境，`build_formal_manifest.py` 会以 `record_flags` 标记并默认降为 supplemental。
22. PDF 文本抽取应传入 `--manifest metadata/correspondence_audit_manifest.json`，只抽取当前 audit manifest 内的 PDF，避免旧下载、会议记录或其他目录残留污染 completeness audit。
23. 下载、文本抽取和通讯作者扫描报告使用统一 `{summary, records}` JSON 结构；读取脚本同时兼容旧的顶层数组报告。
24. Rolling holdout 生成必须显式使用 `--cutoffs 2017,2019,...` 或重复 `--cutoff YEAR`；脚本禁用 argparse 缩写，避免 `--cutoff` 被误读成 `--cutoffs` 并静默覆盖。
25. 深读卡片渲染默认使用 `--source-root` 解析 `source_lines.source`，并用 `--context-lines` 输出邻近全文行；如果源文件缺失则保留原始单行引用，不阻塞旧项目渲染。

## 校验

运行 `bash tests/run_smoke_test.sh` 可验证初始化、ADS 审计 manifest、历史邮箱扫描、明确通讯作者识别、正式 manifest、论文索引与方法谱系引用检查。

# Astronomer Research Distiller

This repository packages an ADS-first workflow for collecting an astronomer's papers and distilling their research methods into a reusable Codex skill. The output is not a chatbot that imitates the astronomer; it is a traceable research-method digital persona built from papers, method lineage, evidence boundaries, validation habits, and fallback rules.

## What A Distilled Persona Can Do

After installing a derived astronomer skill, you can use it to:

- review manuscripts, proposals, observing plans, catalog papers, and analysis workflows;
- identify relevant research branches and classify them as `primary`, `supporting`, or `not applicable`;
- recommend baseline methods, refinements, required inputs, validation checks, systematics, failure boundaries, and fallbacks;
- decide whether a method applies to your data or should abstain outside its validated domain;
- compare a target paper against lineage-defining papers, external comparison candidates, and known method boundaries;
- draft review notes, method checklists, validation plans, project designs, or corpus-refresh requests.

Example prompts:

```text
Use zhang-san-research to review this paper.
Use li-si-research to evaluate this photometric calibration workflow.
Use zhang-san-research to design a validation plan for a stellar-label pipeline.
```

Derived skills must not be used as personal representatives, private-opinion simulators, or complete bibliography databases. They should stay inside the source-backed research-method boundaries.

## Deliverables

- `skill/distill-astronomer-research/`: the installable general-purpose skill.
- Scripts inside the skill: project initialization, branch-aware review templates, ADS API record collection scoped to the ADS astronomy database by default, same-name identity filtering, ADS audit manifests, public PDF download with progress and long-tail controls, text extraction, corresponding-author evidence scans, formal manifest generation, paper-index generation, method-lineage reference validation, bounded citation-neighborhood construction, and rolling holdout templates.
- `assets/astronomer-config.example.json`: a configuration template for each target astronomer.

## Installation

Clone this repository, then copy the skill directory into your local Codex skills directory:

```bash
git clone https://github.com/xs201611160102/astronomer-research-distiller.git
mkdir -p ~/.codex/skills
cp -R astronomer-research-distiller/skill/distill-astronomer-research ~/.codex/skills/
```

Check that the skill was installed:

```bash
ls ~/.codex/skills/distill-astronomer-research/SKILL.md
```

Open a new Codex thread, or restart Codex, so the new skill is loaded. You can then ask Codex:

`Use the distill-astronomer-research skill to build a research-method skill for an astronomer.`

## Core Rules

1. Prefer ADS and official personal or institutional pages.
2. Do not treat a single ADS full-text email search as complete recall.
3. Record both current and historical email addresses.
4. Keep explicit corresponding-author statements, PDF front-page email markers, and unverified metadata candidates separate.
5. The distilled output must include a year-ordered method lineage: baselines, extensions, input conditions, validation, and fallback versions.
6. Use ORCID as an identity anchor, while keeping ADS as the primary astronomy paper index.
7. In astronomy use cases, track first-author, corresponding-author, and top-three-author papers; do not mechanically infer detailed contribution roles.
8. Generate paper cards, an evidence ledger, top-three-author collaboration graphs, internal citation edges, update diffs, and time-split validation templates.
9. Build a bounded one-to-two-hop citation neighborhood around core lineage papers. Automatically assigned citation-edge semantics must be marked as heuristic and remain manually overrideable.
10. Generate external method-comparison candidates from the citation neighborhood and use multiple cutoff years for rolling holdout checks.
11. Keep manually read lineage paper cards separate from machine-generated skeletons. Mark method baselines, key extensions, and boundary changes as `deep`; mark applications, reviews, conference abstracts, and transition nodes as `context`. `render_deep_cards.py` renders curated `source_lines` into Markdown with one neighboring full-text line on each side by default, so claims can be checked line by line. Extract core citation contexts from local full text and send only the small number of lineage-changing ambiguous edges to the user for judgment.
12. Maintain method boundaries, version and erratum relations, an atomic-claim ledger, refresh protocols, and exception logs. Refuse to apply a method beyond its validated domain when there is no reasonable fallback. Preserve disagreements when external evidence conflicts.
13. Use conservative refresh commands to rebuild local assets and output a manual-review queue. By default, do not use the network and do not overwrite manually curated JSON.
14. Every generated astronomer skill must use a branch-aware evaluation protocol: first identify the researcher's actual research branches from their papers and `research-map.md`, classify each as `primary`, `supporting`, or `not applicable`, review relevant branches separately, and synthesize only after branch-level review is complete. Do not assume a fixed list of fields, and do not let the most obvious single thread dominate other genuinely relevant branches.
15. Every generated skill must include `references/branch-evaluation-protocol.md`, using a shared coverage matrix and branch-level report template so reviews of different astronomers remain reproducible and comparable.
16. Every generated skill must include a digital-persona operating guide: state that it can review papers, proposals, and workflows, design validation plans, triage applicability, compare against the lineage, and diagnose refresh needs; also state that it is a research-method operating model, not an impersonation or representative of the astronomer.
17. Corpus collection must first use the `identity_filter` config and `filter_ads_identity_candidates.py` to split raw ADS searches into target-author records and same-name rejects, then merge the filtered ADS source and attempt to download every publicly accessible PDF. Representative papers are only for later deep reading and method-lineage synthesis; they cannot replace full-corpus download. Run `audit_corpus_completeness.py` to record ADS, download, text-extraction, and formal-manifest counts.
18. Run `check_ads_access.py` before ADS collection. If `ADS_DEV_KEY`, `ADS_TOKEN`, or keychain service `ads-api-token` is missing, ask the user to provide an ADS token and label any fallback corpus as incomplete.
19. The PDF downloader must try arXiv PDFs exposed by ADS identifiers before ADS gateway and configured fallback links. ArXiv downloads have no total-time cap by default; `.part` files are resumed with `curl -C -` by default, and gateway, per-record, and max-attempt controls prevent refused or slow publisher links from stalling the corpus.
20. Corresponding-author auditing is required after text extraction. `verify_correspondence_markers.py` keeps explicit corresponding-author wording separate from PDF email markers; known current or historical emails should also drive ADS full-text searches for candidate recall, but final roles still follow the evidence policy.
21. ADS API collection appends `database:astronomy` by default to reduce same-name pollution from physics/general records. Use `--database all` only for spillover audits or important cross-database target publications.
22. Meeting abstracts, conference records, and symposium proceedings are excluded from PDF download audits by default. `build_ads_audit_manifest.py` writes them to `metadata/conference_records_excluded_from_audit.json`; include them only with an explicit `--include-conference-records` request. If an arXiv eprint carries proceedings context in metadata or extracted text, `build_formal_manifest.py` marks it with `record_flags` and tiers it as supplemental by default.
23. PDF text extraction should pass `--manifest metadata/correspondence_audit_manifest.json` so only PDFs in the active audit manifest are extracted; this keeps stale downloads, conference records, and other directory leftovers out of completeness audits.
24. Download, text-extraction, and correspondence reports use a common `{summary, records}` JSON shape. Readers remain backward-compatible with older top-level array reports.
25. Rolling holdout generation requires explicit `--cutoffs 2017,2019,...` or repeated `--cutoff YEAR`; argparse abbreviation is disabled so misspelled cutoff options fail instead of silently changing the split set.
26. Deep-card rendering resolves `source_lines.source` relative to `--source-root` and writes neighboring full-text context with `--context-lines`; missing source files fall back to the original curated single-line citation.

## Validation

Run `bash tests/run_smoke_test.sh` to verify project initialization, ADS access preflight reporting, same-name identity filtering, merged ADS audit manifest generation, corpus completeness reporting, historical email scanning, explicit corresponding-author detection, formal manifest generation, paper-index generation, and method-lineage reference checks.
