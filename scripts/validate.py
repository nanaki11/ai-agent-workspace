#!/usr/bin/env python3
"""リポジトリの整合性チェック。エラーがあれば終了コード 1。

1. スキル：SKILL.md の有無、name とディレクトリ名の一致、name/description の形式（Agent Skills 仕様）
2. スキル名の重複
3. SKILL.md 内の参照パス（${CLAUDE_SKILL_DIR}/…、${CLAUDE_PLUGIN_ROOT}/…、相対 scripts/ 等）の実在
4. エージェントが参照するスキルの実在
5. claude/packages.json が全スキルを過不足なく1回ずつ含むこと
6. 生成物（AGENTS.md・.codex/agents）が最新であること
7. 禁止ファイル（.env、鍵、認証キャッシュ等）が無いこと
"""
from __future__ import annotations

import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_skills import (  # noqa: E402
    ROOT, SKILLS_DIR, load_claude_agents, load_packages, load_skills, strip_namespace,
)

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FORBIDDEN = re.compile(
    r"(^|/)(\.env(\..*)?|.*\.pem|.*\.key|id_rsa.*|id_ed25519.*|\.oauth_token|.*credentials.*\.json|"
    r"\.claude\.json|launcher-settings\.json|.*\.p12|.*\.pfx)$"
)
errors: list[str] = []
warns: list[str] = []


def err(m): errors.append(m)
def warn(m): warns.append(m)


def main() -> int:
    skills = load_skills()
    for name, s in skills.items():
        meta = s["meta"]
        if not (s["dir"] / "SKILL.md").exists():
            err(f"[skill] {name}: SKILL.md が無い"); continue
        if meta.get("name") != name:
            err(f"[skill] {name}: frontmatter name='{meta.get('name')}' がディレクトリ名と不一致")
        if not NAME_RE.match(name) or len(name) > 64:
            err(f"[skill] {name}: name の形式が不正（小文字・数字・ハイフン、64字以内）")
        d = meta.get("description", "")
        if not d:
            err(f"[skill] {name}: description が無い")
        elif len(d) > 1024:
            err(f"[skill] {name}: description が 1024 字超（{len(d)}）")
        # 参照パス
        for m in re.finditer(r"\$\{CLAUDE_SKILL_DIR\}/([\w./-]+)", s["body"]):
            if not (s["dir"] / m.group(1)).exists():
                err(f"[ref] {name}: ${{CLAUDE_SKILL_DIR}}/{m.group(1)} が存在しない")
        for m in re.finditer(r"\$\{CLAUDE_PLUGIN_ROOT\}/skills/([\w./-]+)", s["body"]):
            if not (SKILLS_DIR / m.group(1)).exists():
                err(f"[ref] {name}: ${{CLAUDE_PLUGIN_ROOT}}/skills/{m.group(1)} が存在しない")
        for m in re.finditer(r"(?<![\w$/{}.])((?:scripts|references|assets|examples)/[\w./-]+\.\w+)", s["body"]):
            if not (s["dir"] / m.group(1)).exists():
                # 外部リポジトリ（$SK/…）を指す記述は対象外
                ctx = s["body"][max(0, m.start() - 5):m.start()]
                if "$SK/" not in ctx and "SK/" not in ctx:
                    warn(f"[ref] {name}: {m.group(1)} がスキル内に無い（外部取得物なら問題なし）")
        if "${CLAUDE_" in s["body"]:
            warn(f"[codex] {name}: Claude 固有の変数を使用（AGENTS.md の読み替え表で対応）")

    dup = [n for n, c in Counter(n.lower() for n in skills).items() if c > 1]
    for n in dup:
        err(f"[skill] 名前の重複: {n}")

    for name, a in load_claude_agents().items():
        for ref in a["meta"].get("skills", []):
            if strip_namespace(ref) not in skills:
                err(f"[agent] {name}: スキル {ref} が存在しない")
        if not a["meta"].get("description"):
            err(f"[agent] {name}: description が無い")

    listed = [s for p in load_packages()["packages"] for s in p["skills"]]
    for s, c in Counter(listed).items():
        if c > 1:
            err(f"[packages] {s} が複数パッケージに重複")
        if s not in skills:
            err(f"[packages] {s} が .agents/skills に無い")
    for s in skills:
        if s not in listed:
            err(f"[packages] {s} がどのパッケージにも含まれていない")

    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "generate.py"), "--check"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        err("[generate] 生成物が古い。python3 scripts/generate.py を実行する\n" + r.stdout)

    for f in ROOT.rglob("*"):
        rel = f.relative_to(ROOT).as_posix()
        if rel.startswith((".git/", "dist/")):
            continue
        if f.is_file() and FORBIDDEN.search(rel) and not rel.endswith(".env.example"):
            err(f"[secret] 禁止ファイル: {rel}")
        if f.is_symlink() and not f.resolve().exists():
            err(f"[link] リンク切れ: {rel}")

    for w in warns:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"\nskills={len(skills)} agents={len(load_claude_agents())} errors={len(errors)} warnings={len(warns)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
