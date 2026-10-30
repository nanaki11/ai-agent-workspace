#!/usr/bin/env python3
"""claude/packages.json に従い、Claude 用の配布物を dist/claude/ に組み立てる。

- dist/claude/consulting-agents/       … Claude Code の `--plugin-dir` で読めるプラグイン
- dist/claude/consulting-agents.zip    … claude.ai（組織ライブラリ）へアップロードする zip
- dist/claude/<standalone-skill>.zip   … claude.ai の Skills にアップロードする zip

スキル本体は .agents/skills/ からコピーする（シンボリックリンクは実体化）。dist/ は .gitignore 対象。
"""
from __future__ import annotations

import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_skills import ROOT, SKILLS_DIR, load_packages  # noqa: E402

DIST = ROOT / "dist" / "claude"


def zip_dir(src: Path, dst: Path, arc_root: str) -> None:
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(src.rglob("*")):
            if f.is_file():
                z.write(f, Path(arc_root) / f.relative_to(src))


def main() -> int:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    for pkg in load_packages()["packages"]:
        if pkg["type"] == "plugin":
            out = DIST / pkg["name"]
            shutil.copytree(ROOT / pkg["source_dir"], out, symlinks=False)
            for s in pkg["skills"]:
                shutil.copytree(SKILLS_DIR / s, out / "skills" / s, symlinks=False)
            zip_dir(out, DIST / f"{pkg['name']}.zip", pkg["name"])
            print(f"plugin: {out.relative_to(ROOT)} (+ .zip) skills={len(pkg['skills'])}")
        elif pkg["type"] == "standalone-skill":
            for s in pkg["skills"]:
                zip_dir(SKILLS_DIR / s, DIST / f"{s}.zip", s)
                print(f"skill : dist/claude/{s}.zip")
    return 0


if __name__ == "__main__":
    sys.exit(main())
