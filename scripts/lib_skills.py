"""共通ユーティリティ：SKILL.md / agent .md のフロントマター読み込み（外部ライブラリ不要）。"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / ".agents" / "skills"
CLAUDE_DIR = ROOT / "claude"
PACKAGES_JSON = CLAUDE_DIR / "packages.json"
CLAUDE_AGENTS_DIR = CLAUDE_DIR / "plugins" / "consulting-agents" / "agents"
CODEX_AGENTS_DIR = ROOT / ".codex" / "agents"
RULES_DIR = ROOT / "common" / "rules"
PLUGINS_DIR = ROOT / "plugins"          # 生成物（マーケットプレイス配布用。Git 管理）
STATE_JSON = ROOT / "sync" / "state.json"
VERSION_FILE = ROOT / "VERSION"
STANDARD_NAME = "consulting-delivery-standard.md"
STANDARD_HEADER = "<!-- Generated from common/rules/consulting-delivery-standard.md; do not edit. -->\n"
EXCLUDE_PARTS = {"__pycache__", ".DS_Store"}


def read_version() -> str:
    return VERSION_FILE.read_text(encoding="utf-8").strip()


def iter_files(base: Path):
    """base 以下の通常ファイル（キャッシュ類を除く）を返す。"""
    for f in sorted(base.rglob("*")):
        if f.is_file() and not (set(f.relative_to(base).parts) & EXCLUDE_PARTS) and f.suffix != ".pyc":
            yield f

_FM = re.compile(r"\A---\n(.*?)\n---\n?(.*)\Z", re.S)


def _unquote(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """シンプルな YAML サブセット（key: value / key: + '- item' のリスト）を読む。"""
    m = _FM.match(text)
    if not m:
        return {}, text
    meta: dict = {}
    key = None
    for line in m.group(1).splitlines():
        if not line.strip():
            continue
        if line.lstrip().startswith("- ") and key:
            meta.setdefault(key, [])
            if isinstance(meta[key], list):
                meta[key].append(_unquote(line.lstrip()[2:]))
            continue
        if ":" in line and not line.startswith(" "):
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            meta[key] = _unquote(val) if val else []
    return meta, m.group(2)


def load_skills() -> dict[str, dict]:
    out = {}
    for d in sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir()):
        f = d / "SKILL.md"
        meta, body = parse_frontmatter(f.read_text(encoding="utf-8")) if f.exists() else ({}, "")
        out[d.name] = {"dir": d, "meta": meta, "body": body}
    return out


def load_claude_agents() -> dict[str, dict]:
    out = {}
    for f in sorted(CLAUDE_AGENTS_DIR.glob("*.md")):
        meta, body = parse_frontmatter(f.read_text(encoding="utf-8"))
        out[meta.get("name", f.stem)] = {"file": f, "meta": meta, "body": body}
    return out


def load_packages() -> dict:
    return json.loads(PACKAGES_JSON.read_text(encoding="utf-8"))


def strip_namespace(skill_ref: str) -> str:
    """'consulting-agents:logical-thinking' -> 'logical-thinking'"""
    return skill_ref.split(":", 1)[1] if ":" in skill_ref else skill_ref
