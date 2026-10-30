#!/usr/bin/env python3
"""正本から派生ファイルを生成する。

  正本                                         → 生成物
  common/rules/*.md + .agents/skills/*/SKILL.md → AGENTS.md
  claude/plugins/consulting-agents/agents/*.md  → .codex/agents/*.toml

使い方:
  python3 scripts/generate.py          # 生成（上書き）
  python3 scripts/generate.py --check  # 生成物が最新か確認（差分があれば終了コード 1）
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_skills import (  # noqa: E402
    CODEX_AGENTS_DIR, ROOT, RULES_DIR, load_claude_agents, load_skills, strip_namespace,
)

GEN_NOTE = "<!-- 自動生成ファイル。直接編集しない。正本を直して `python3 scripts/generate.py` を実行する。 -->"


def build_agents_md() -> str:
    skills = load_skills()
    agents = load_claude_agents()
    rules = []
    for f in sorted(RULES_DIR.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        # 先頭の HTML コメント（出典メモ）は除く
        if text.startswith("<!--"):
            text = text.split("-->", 1)[1].lstrip()
        # 見出しレベルを1段下げる
        text = "\n".join(("#" + l) if l.startswith("#") else l for l in text.splitlines())
        rules.append(text.strip())

    lines = [
        GEN_NOTE,
        "# AGENTS.md — ai-agent-workspace",
        "",
        "このリポジトリは、Claude・OpenAI Codex・ChatGPT で共通に使うスキルとエージェント定義の正本（Single Source of Truth）である。",
        "",
        "## 1. 共通ルール（全エージェント共通）",
        "",
        *rules,
        "",
        "## 2. スキル",
        "",
        "スキル本体は `.agents/skills/<name>/SKILL.md`。Codex はこのディレクトリを自動で検出する（`$<name>` で明示呼び出し）。",
        "依頼内容がスキルの description に合うときは、作業の前にその SKILL.md を読んで手順に従う。",
        "",
        "| スキル | 用途（description の冒頭） |",
        "|---|---|",
    ]
    for name, s in skills.items():
        desc = s["meta"].get("description", "").split("。")[0]
        lines.append(f"| `{name}` | {desc} |")
    lines += [
        "",
        "### Claude 固有の記法の読み替え（Codex / ChatGPT で使うとき）",
        "",
        "| SKILL.md 内の記法 | 読み替え |",
        "|---|---|",
        "| `${CLAUDE_SKILL_DIR}` | その SKILL.md があるディレクトリ（例：`.agents/skills/drawio-diagram`） |",
        "| `${CLAUDE_PLUGIN_ROOT}/skills/<name>` | `.agents/skills/<name>` |",
        "| `consulting-agents:<name>`（名前空間付きスキル名） | `<name>`（Codex では `$<name>`） |",
        "| 「Agent ツール」「別エージェントにレビューさせる」 | Codex のサブエージェント（`.codex/agents/`）または新しいセッション |",
        "| `/mnt/user-data/outputs/` | 作業ディレクトリ配下の出力先（例：`./outputs/`） |",
        "| xlsx / pptx / docx / pdf スキル | Anthropic 提供スキル（本リポジトリ対象外）。Codex では同等のライブラリ（openpyxl・python-pptx 等）で代替 |",
        "",
        "## 3. 専門家エージェント",
        "",
        "Claude ではサブエージェント（`claude/plugins/consulting-agents/agents/`）、Codex ではカスタムエージェント（`.codex/agents/*.toml`、生成物）として定義している。",
        "ChatGPT では該当エージェントの本文をプロジェクトの指示に貼って使う。",
        "",
        "| エージェント | 役割 | 使うスキル |",
        "|---|---|---|",
    ]
    for name, a in agents.items():
        desc = a["meta"].get("description", "").split("。")[0]
        sk = ", ".join(f"`{strip_namespace(x)}`" for x in a["meta"].get("skills", []))
        lines.append(f"| `{name}` | {desc} | {sk} |")
    lines += [
        "",
        "## 4. リポジトリの運用ルール",
        "",
        "- スキルは `.agents/skills/` だけを編集する（Claude 用パッケージは `scripts/build_claude_packages.py` で組み立てる）",
        "- AGENTS.md と `.codex/agents/*.toml` は生成物。正本（`common/rules/`、`claude/plugins/consulting-agents/agents/`）を直して `python3 scripts/generate.py` を実行する",
        "- コミット前に `python3 scripts/validate.py` と `bash scripts/scan_secrets.sh` を実行する",
        "- APIキー・トークン・顧客情報・個人情報をコミットしない。MCP の認証情報は環境変数かローカル設定に置く",
        "",
    ]
    return "\n".join(lines)


def toml_literal_multiline(s: str) -> str:
    if "'''" in s:
        raise ValueError("本文に ''' が含まれるため TOML リテラル文字列にできない")
    return "'''\n" + s.rstrip() + "\n'''"


def toml_basic(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def build_codex_agents() -> dict[str, str]:
    out = {}
    for name, a in load_claude_agents().items():
        skills = [strip_namespace(x) for x in a["meta"].get("skills", [])]
        header = (
            "（このエージェント定義は claude/plugins/consulting-agents/agents/"
            f"{a['file'].name} から自動生成）\n\n"
            "## 使うスキル\n"
            "次のスキルを `.agents/skills/<name>/SKILL.md` から読み、該当する作業の前に手順に従う：\n"
            + "\n".join(f"- ${s}" for s in skills)
            + "\n\n共通ルールはリポジトリ直下の AGENTS.md に従う。本文中のスキル名は上記スキルを指す。\n\n"
        )
        body = header + a["body"].strip()
        toml = "\n".join([
            "# 自動生成ファイル。直接編集しない（scripts/generate.py）",
            f"name = {toml_basic(name)}",
            f"description = {toml_basic(a['meta'].get('description', ''))}",
            f"developer_instructions = {toml_literal_multiline(body)}",
            "",
        ])
        out[f"{name}.toml"] = toml
    return out


def main() -> int:
    check = "--check" in sys.argv
    targets = {ROOT / "AGENTS.md": build_agents_md()}
    standard = (RULES_DIR / "consulting-delivery-standard.md").read_text(encoding="utf-8")
    for skill in load_skills().values():
        targets[skill["dir"] / "references" / "consulting-delivery-standard.md"] = (
            "<!-- Generated from common/rules/consulting-delivery-standard.md; do not edit. -->\n" + standard
        )
    for fn, content in build_codex_agents().items():
        targets[CODEX_AGENTS_DIR / fn] = content
    stale = []
    for path, content in targets.items():
        cur = path.read_text(encoding="utf-8") if path.exists() else None
        if cur != content:
            stale.append(path.relative_to(ROOT))
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
    if check:
        if stale:
            print("生成物が古い:", *stale, sep="\n  ")
            return 1
        print("生成物は最新")
        return 0
    print("生成/更新:", *(stale or ["（変更なし）"]), sep="\n  ")
    return 0


if __name__ == "__main__":
    sys.exit(main())
