#!/usr/bin/env python3
"""正本から派生ファイルを生成する。

  正本                                         → 生成物
  common/rules/*.md + .agents/skills/*/SKILL.md → AGENTS.md
  claude/plugins/consulting-agents/agents/*.md  → .codex/agents/*.toml
  common/rules/consulting-delivery-standard.md  → .agents/skills/*/references/（写し）
  上記すべて＋VERSION                           → plugins/claude/*、plugins/openai/*（配布用プラグイン）
                                                 .claude-plugin/marketplace.json、.agents/plugins/marketplace.json

使い方:
  python3 scripts/generate.py          # 生成（上書き）
  python3 scripts/generate.py --check  # 生成物が最新か確認（差分があれば終了コード 1）
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_skills import (  # noqa: E402
    CODEX_AGENTS_DIR, PLUGINS_DIR, ROOT, RULES_DIR, STANDARD_HEADER, STANDARD_NAME, iter_files,
    load_claude_agents, load_packages, load_skills, read_version, strip_namespace,
)

OPENAI_NAME = "nanaki11-consulting-toolkit"

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
        text = "\n".join(("##" + l) if l.startswith("#") else l for l in text.splitlines())
        rules.append(text.strip() + "\n")

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
        "ChatGPT／Codex のプラグイン（`plugins/openai/`）では `consulting-agent-router` スキルが4役割を振り分ける。",
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
        "- 人が編集するのは正本だけ：`.agents/skills/`、`claude/plugins/consulting-agents/agents/`、`common/rules/`、`claude/packages.json`、`VERSION`",
        "- それ以外（AGENTS.md、`.codex/agents/`、各スキルの `references/consulting-delivery-standard.md`、`plugins/`、マーケットプレイス定義）は生成物。`python3 scripts/generate.py` で更新する",
        "- 各環境で編集されたスキルは `python3 scripts/sync.py import` で正本に取り込む（直接 `plugins/` を直さない）",
        "- 配布内容を変えたら `VERSION` を上げる。コミット前に `validate.py`・`scan_secrets.sh`・`unittest` を実行する",
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


MARKET_NAME = "nanaki11-ai-agent-workspace"


def build_marketplaces() -> dict[Path, str]:
    """Claude Code 用と Codex／ChatGPT 用のマーケットプレイス定義（リポジトリを配布元にする）。"""
    pk = load_packages()["packages"]
    v = read_version()
    claude = {
        "name": MARKET_NAME,
        "owner": {"name": "hoshi"},
        "plugins": [{"name": x["name"], "source": f"./plugins/claude/{x['name']}",
                     "description": x.get("description", ""), "version": v} for x in pk],
    }
    for e, x in zip(claude["plugins"], pk):
        if not e["description"]:
            e["description"] = json.loads((ROOT / x["source_dir"] / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))["description"]
    openai = {
        "name": MARKET_NAME,
        "interface": {"displayName": "ai-agent-workspace (nanaki11)"},
        "plugins": [{"name": OPENAI_NAME,
                     "source": {"source": "local", "path": f"./plugins/openai/{OPENAI_NAME}"},
                     "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                     "category": "Productivity"}],
    }
    dump = lambda o: json.dumps(o, ensure_ascii=False, indent=2) + "\n"  # noqa: E731
    return {ROOT / ".claude-plugin/marketplace.json": dump(claude),
            ROOT / ".agents/plugins/marketplace.json": dump(openai)}


def tree(base: Path) -> dict[str, bytes]:
    return {f.relative_to(base).as_posix(): f.read_bytes() for f in iter_files(base)} if base.exists() else {}


def build_plugin_tree(tmp: Path) -> None:
    """plugins/ に置く配布用プラグインを tmp に組み立てる（可変情報なし＝再現可能）。"""
    import build_chatgpt_package
    import build_claude_packages
    build_claude_packages.build(tmp / "claude", archive=False, quiet=True)
    build_chatgpt_package.build(dest=tmp / "openai", build_info=False, archive=False, precheck=False, quiet=True)


def main() -> int:
    check = "--check" in sys.argv
    targets = {ROOT / "AGENTS.md": build_agents_md()}
    standard = (RULES_DIR / STANDARD_NAME).read_text(encoding="utf-8")
    for skill in load_skills().values():
        targets[skill["dir"] / "references" / STANDARD_NAME] = STANDARD_HEADER + standard
    for fn, content in build_codex_agents().items():
        targets[CODEX_AGENTS_DIR / fn] = content
    targets.update(build_marketplaces())
    stale = []
    for path, content in targets.items():
        cur = path.read_text(encoding="utf-8") if path.exists() else None
        if cur != content:
            stale.append(path.relative_to(ROOT))
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
    # 配布用プラグイン（plugins/）。check 時は現在の正本から作った結果と比較する
    if check and stale:
        stale.append(Path("plugins/（上記の生成物が古いため未比較）"))
    else:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            build_plugin_tree(tmp)
            if tree(tmp) != tree(PLUGINS_DIR):
                stale.append(PLUGINS_DIR.relative_to(ROOT))
                if not check:
                    if PLUGINS_DIR.exists():
                        shutil.rmtree(PLUGINS_DIR)
                    shutil.copytree(tmp, PLUGINS_DIR)
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
