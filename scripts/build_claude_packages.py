#!/usr/bin/env python3
"""claude/packages.json に従い、Claude 用のプラグインを組み立てる。

  python3 scripts/build_claude_packages.py            # dist/claude/ にプラグインと zip を作る
  （plugins/claude/ への出力は scripts/generate.py が行う。マーケットプレイス配布用で Git 管理対象）

- <dest>/consulting-agents/          … Claude Code の `--plugin-dir`／マーケットプレイス／PublishPlugin で使うプラグイン
- <dest>/consulting-pptx-skill/      … 単体スキルを1つだけ含むプラグイン（Claude Code 用）
- dist/claude/*.zip                  … claude.ai へ手動アップロードする zip

スキル本体は .agents/skills/ からコピーする（シンボリックリンクは実体化）。
"""
from __future__ import annotations

import json
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_skills import ROOT, SKILLS_DIR, load_packages, read_version  # noqa: E402

DIST = ROOT / "dist" / "claude"
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc")


def zip_dir(src: Path, dst: Path, arc_root: str) -> None:
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(src.rglob("*")):
            if f.is_file():
                info = zipfile.ZipInfo((Path(arc_root) / f.relative_to(src)).as_posix(), (2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (f.stat().st_mode & 0o777) << 16
                z.writestr(info, f.read_bytes())


def build(dest: Path = DIST, archive: bool = True, quiet: bool = False) -> list[Path]:
    version = read_version()
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    outs = []
    for pkg in load_packages()["packages"]:
        out = dest / pkg["name"]
        if pkg["type"] == "plugin":
            shutil.copytree(ROOT / pkg["source_dir"], out, symlinks=False, ignore=IGNORE)
        else:
            (out / ".claude-plugin").mkdir(parents=True)
            manifest = {"name": pkg["name"], "description": pkg.get("description", ""), "author": {"name": "hoshi"}}
            (out / ".claude-plugin" / "plugin.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        mf = out / ".claude-plugin" / "plugin.json"
        data = json.loads(mf.read_text(encoding="utf-8"))
        data["version"] = version
        mf.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for s in pkg["skills"]:
            shutil.copytree(SKILLS_DIR / s, out / "skills" / s, symlinks=False, ignore=IGNORE)
        outs.append(out)
        if archive:
            if pkg["type"] == "plugin":
                zip_dir(out, dest / f"{pkg['name']}.zip", pkg["name"])
            else:  # claude.ai の Skills へは「スキルフォルダ」を zip で上げる
                for s in pkg["skills"]:
                    zip_dir(SKILLS_DIR / s, dest / f"{s}.zip", s)
        if not quiet:
            print(f"{pkg['type']:16} {out.relative_to(ROOT)} skills={len(pkg['skills'])} version={version}")
    return outs


if __name__ == "__main__":
    build()
