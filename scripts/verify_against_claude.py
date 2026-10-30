#!/usr/bin/env python3
"""Claude の元環境（同期済みプラグイン／スキル）と、このリポジトリの内容をファイル単位で比較する。

使い方:
  python3 scripts/verify_against_claude.py [--claude-home ~/.claude]

比較対象:
  <claude-home>/plugins/synced/*/consulting-agents/{agents,skills,.claude-plugin}
  <claude-home>/skills/synced/*/<packages.json の standalone-skill>
各ファイルの SHA-256 を比べ、一致／差分／リポジトリのみ／元環境のみ を出力する。差分があれば終了コード 1。
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_skills import ROOT, SKILLS_DIR, load_packages  # noqa: E402

IGNORE = {".in_use", ".last-complete-round"}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def files(base: Path) -> dict[str, Path]:
    return {f.relative_to(base).as_posix(): f for f in base.rglob("*")
            if f.is_file() and not any(part in IGNORE for part in f.relative_to(base).parts)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--claude-home", default=str(Path.home() / ".claude"))
    a = ap.parse_args()
    home = Path(a.claude_home).expanduser()
    pairs: list[tuple[str, Path, Path]] = []  # (label, src_dir, repo_dir)
    for pkg in load_packages()["packages"]:
        if pkg["type"] == "plugin":
            srcs = sorted(home.glob(f"plugins/synced/*/{pkg['name']}"))
            if not srcs:
                print(f"元環境に {pkg['name']} が見つからない: {home}"); return 2
            src = srcs[0]
            pairs.append((f"{pkg['name']}/agents", src / "agents", ROOT / pkg["source_dir"] / "agents"))
            pairs.append((f"{pkg['name']}/.claude-plugin", src / ".claude-plugin", ROOT / pkg["source_dir"] / ".claude-plugin"))
            for s in pkg["skills"]:
                pairs.append((f"{pkg['name']}/skills/{s}", src / "skills" / s, SKILLS_DIR / s))
            extra = {d.name for d in (src / "skills").iterdir()} - set(pkg["skills"])
            for s in sorted(extra):
                print(f"ONLY_IN_CLAUDE  {pkg['name']}/skills/{s}（packages.json に未登録）")
        else:
            for s in pkg["skills"]:
                srcs = sorted(home.glob(f"skills/synced/*/{s}"))
                if not srcs:
                    print(f"元環境に {s} が見つからない"); return 2
                pairs.append((f"skills/{s}", srcs[0], SKILLS_DIR / s))
    same = diff = 0
    for label, src, dst in pairs:
        fs, fd = files(src), files(dst)
        for rel in sorted(set(fs) | set(fd)):
            if rel in fs and rel in fd:
                if sha(fs[rel]) == sha(fd[rel]):
                    same += 1
                else:
                    diff += 1; print(f"DIFF            {label}/{rel}")
            elif rel in fs:
                diff += 1; print(f"ONLY_IN_CLAUDE  {label}/{rel}")
            else:
                diff += 1; print(f"ONLY_IN_REPO    {label}/{rel}")
    print(f"\n一致 {same} ファイル / 差分 {diff} 件（比較単位 {len(pairs)}）")
    return 1 if diff else 0


if __name__ == "__main__":
    sys.exit(main())
