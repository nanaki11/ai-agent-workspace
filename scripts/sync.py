#!/usr/bin/env python3
"""GitHub（このリポジトリ）と各環境にインストールしたスキル・エージェントを双方向に同期する。

各環境の「前回同期時点」のハッシュを sync/state.json に記録し、3者比較で変更の向きを判定する。

  リポジトリ＝前回、環境≠前回  → 環境側で編集された      → import で取り込む
  環境＝前回、リポジトリ≠前回  → リポジトリ側が新しい    → 再インストールが必要
  3者とも異なる                → 競合                    → --prefer で解決
  前回の記録が無く両者が異なる → 判定不能（競合扱い）

使い方:
  python3 scripts/sync.py status  --target claude  [--path <インストール先 or zip>]
  python3 scripts/sync.py import  --target chatgpt --path ~/Downloads/plugin.zip [--apply] [--prefer target|repo]
  python3 scripts/sync.py mark    --target claude  [--from-commit <rev>]   # 再インストール後に基準を記録

target:
  claude  … claude.ai／Cowork（~/.claude/plugins/synced, ~/.claude/skills/synced）または Claude Code の
            プラグインキャッシュ（~/.claude/plugins/cache）。--path でフォルダか zip を指定してもよい
  chatgpt … ChatGPT／Codex のプラグイン（~/.codex/plugins/cache/*/nanaki11-consulting-toolkit/*）または zip
  codex   … ~/.agents/skills（install_codex.sh でリンクした場合はリポジトリそのものなので常に一致）
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_skills import (  # noqa: E402
    CLAUDE_AGENTS_DIR, ROOT, RULES_DIR, SKILLS_DIR, STANDARD_HEADER, STANDARD_NAME, STATE_JSON,
    iter_files, load_packages, read_version,
)

ROUTER = "consulting-agent-router"
OPENAI_NAME = "nanaki11-consulting-toolkit"
HOME = Path.home()


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


# ---------- 管理対象（正本ファイル）の範囲 ----------

def scope(target: str) -> list[str]:
    """その環境に配布している正本ファイルの一覧（リポジトリ相対パス）。生成物は除く。"""
    pk = load_packages()["packages"]
    skills = [s for p in pk for s in p["skills"]]
    files = []
    for s in skills:
        for f in iter_files(SKILLS_DIR / s):
            if f.name == STANDARD_NAME and f.parent.name == "references":
                continue
            files.append(rel(f))
    if target == "codex":  # ~/.agents/skills にはスキルだけが入る
        return files
    files += [rel(f) for f in sorted(CLAUDE_AGENTS_DIR.glob("*.md"))]
    files += [rel(f) for f in sorted(RULES_DIR.glob("*.md"))]
    if target == "claude":  # Claude には共通ルールのうち実行規約（写し）だけが入る
        files = [f for f in files if not f.startswith("common/rules/") or f.endswith(STANDARD_NAME)]
    return files


def repo_hashes(target: str) -> dict[str, str]:
    return {f: sha_bytes((ROOT / f).read_bytes()) for f in scope(target)}


def commit_hashes(target: str, rev: str) -> dict[str, str]:
    out = {}
    for f in scope(target):
        r = subprocess.run(["git", "show", f"{rev}:{f}"], cwd=ROOT, capture_output=True)
        if r.returncode == 0:
            out[f] = sha_bytes(r.stdout)
    return out


# ---------- 環境側の読み取り（インストール済みファイル → 正本パスへの対応付け） ----------

def default_paths(target: str) -> list[Path]:
    if target == "claude":
        c = HOME / ".claude"
        found = sorted(c.glob("plugins/synced/*/consulting-agents")) + sorted(c.glob("skills/synced/*/consulting-pptx-skill"))
        if not found:
            found = sorted(c.glob("plugins/cache/*/consulting-agents/*")) + sorted(c.glob("plugins/cache/*/consulting-pptx-skill/*"))
        return found
    if target == "chatgpt":
        return sorted(HOME.glob(f".codex/plugins/cache/*/{OPENAI_NAME}/*"))[-1:]
    if target == "codex":
        return [HOME / ".agents" / "skills"]
    raise SystemExit(f"不明な target: {target}")


def unpack(paths: list[Path], tmp: Path) -> list[Path]:
    out = []
    for i, p in enumerate(paths):
        p = p.expanduser()
        if p.is_file() and p.suffix == ".zip":
            d = tmp / f"z{i}"
            with zipfile.ZipFile(p) as z:
                for n in z.namelist():  # zip slip 対策
                    if n.startswith("/") or ".." in Path(n).parts:
                        raise SystemExit(f"不正なパスを含む zip: {n}")
                z.extractall(d)
            out.append(d)
        elif p.exists():
            out.append(p)
        else:
            raise SystemExit(f"見つからない: {p}")
    return out


def target_files(roots: list[Path]) -> tuple[dict[str, bytes], list[str]]:
    """環境側のファイルを正本パスに対応付ける。戻り値：({正本パス: 内容}, 警告)"""
    mapped: dict[str, bytes] = {}
    warns: list[str] = []
    std_copies: dict[str, bytes] = {}
    for root in roots:
        for skill_md in sorted(root.rglob("SKILL.md")):
            sdir = skill_md.parent
            name = sdir.name
            if ROUTER == name:
                for f in sorted((sdir / "references").glob("*.md")):
                    if (CLAUDE_AGENTS_DIR / f.name).exists():
                        mapped[rel(CLAUDE_AGENTS_DIR / f.name)] = f.read_bytes()
                    elif (RULES_DIR / f.name).exists():
                        mapped[rel(RULES_DIR / f.name)] = f.read_bytes()
                    else:
                        warns.append(f"対応先不明（無視）: {f}")
                continue
            if not (SKILLS_DIR / name).exists():
                warns.append(f"リポジトリに無いスキル（新規の可能性。手動で追加を検討）: {name}")
                continue
            for f in iter_files(sdir):
                r = f.relative_to(sdir).as_posix()
                if r == f"references/{STANDARD_NAME}":
                    std_copies[f"{name}"] = f.read_bytes()
                    continue
                mapped[f"{rel(SKILLS_DIR / name)}/{r}"] = f.read_bytes()
        for agents_dir in [d for d in root.rglob("agents") if (d.parent / ".claude-plugin").is_dir()]:
            for f in sorted(agents_dir.glob("*.md")):
                mapped[rel(CLAUDE_AGENTS_DIR / f.name)] = f.read_bytes()
    # 実行規約の写し → common/rules の正本に戻す（ヘッダーを外す）
    bodies = {}
    for name, b in std_copies.items():
        t = b.decode("utf-8")
        bodies[name] = t[len(STANDARD_HEADER):] if t.startswith(STANDARD_HEADER) else t
    if bodies:
        uniq = set(bodies.values())
        if len(uniq) > 1:
            warns.append("実行規約の写しがスキルごとに異なる（どれが正しいか手動で確認）: "
                         + ", ".join(sorted(bodies)))
        mapped[rel(RULES_DIR / STANDARD_NAME)] = sorted(uniq, key=lambda t: -list(bodies.values()).count(t))[0].encode("utf-8")
    return mapped, warns


# ---------- 状態 ----------

def load_state() -> dict:
    return json.loads(STATE_JSON.read_text(encoding="utf-8")) if STATE_JSON.exists() else {"targets": {}}


def save_state(st: dict) -> None:
    STATE_JSON.parent.mkdir(parents=True, exist_ok=True)
    STATE_JSON.write_text(json.dumps(st, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def classify(target: str, tfiles: dict[str, bytes]) -> list[tuple[str, str]]:
    base = load_state()["targets"].get(target, {}).get("files", {})
    repo = repo_hashes(target)
    tgt = {k: sha_bytes(v) for k, v in tfiles.items()}
    rows = []
    for f in sorted(set(repo) | set(tgt)):
        r, t, b = repo.get(f), tgt.get(f), base.get(f)
        if r == t:
            kind = "same"
        elif not base:
            kind = "unknown"          # 基準が無い
        elif r == b:
            kind = "target-changed" if t is not None else "target-deleted"
        elif t == b:
            kind = "repo-changed"
        else:
            kind = "conflict"
        rows.append((kind, f))
    return rows


LABEL = {
    "target-changed": "環境で変更 → import で取り込み可",
    "target-deleted": "環境で削除 → 手動で判断（自動削除しない）",
    "repo-changed": "リポジトリが新しい → 再インストールが必要",
    "conflict": "競合（両方で変更）→ --prefer で解決",
    "unknown": "差分あり・基準なし → 内容を確認して --prefer で解決",
}


def report(rows) -> dict[str, int]:
    counts: dict[str, int] = {}
    for kind, f in rows:
        counts[kind] = counts.get(kind, 0) + 1
        if kind != "same":
            print(f"{kind:15} {f}")
    print("\n集計:", ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    for k in counts:
        if k in LABEL:
            print(f"  {k}: {LABEL[k]}")
    return counts


# ---------- コマンド ----------

def cmd_status(a) -> int:
    with tempfile.TemporaryDirectory() as td:
        roots = unpack(a.path or default_paths(a.target), Path(td))
        if not roots:
            print(f"{a.target}: インストール先が見つからない。--path で指定する"); return 2
        print("比較対象:", *roots, sep="\n  ")
        tfiles, warns = target_files(roots)
    for w in warns:
        print("WARN", w)
    c = report(classify(a.target, tfiles))
    return 0 if set(c) <= {"same"} else 1


def cmd_import(a) -> int:
    with tempfile.TemporaryDirectory() as td:
        roots = unpack(a.path or default_paths(a.target), Path(td))
        tfiles, warns = target_files(roots)
    for w in warns:
        print("WARN", w)
    rows = classify(a.target, tfiles)
    report(rows)
    take = [f for k, f in rows if k == "target-changed" or (k in ("conflict", "unknown") and a.prefer == "target")]
    take = [f for f in take if f in tfiles]
    if not take:
        print("\n取り込む変更はない"); return 0
    print("\n取り込み対象:", *take, sep="\n  ")
    if not a.apply:
        print("\n（確認のみ。書き込むには --apply）"); return 0
    for f in take:
        p = ROOT / f
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(tfiles[f])
    print(f"\n{len(take)} ファイルを取り込んだ。次に: python3 scripts/generate.py && python3 scripts/validate.py "
          "&& python3 -m unittest discover -s tests → VERSION を上げて commit → 各環境へ再インストール → sync.py mark")
    return 0


def cmd_mark(a) -> int:
    st = load_state()
    if a.from_commit:
        files = commit_hashes(a.target, a.from_commit)
        rev = subprocess.check_output(["git", "rev-parse", a.from_commit], cwd=ROOT, text=True).strip()
        ver = None
    else:
        dirty = subprocess.check_output(["git", "status", "--porcelain", "--", ".agents", "claude", "common"],
                                        cwd=ROOT, text=True).strip()
        if dirty:
            print("正本に未コミットの変更がある。commit してから mark する"); return 1
        files = repo_hashes(a.target)
        rev = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        ver = read_version()
    st["targets"][a.target] = {"commit": rev, "version": ver, "files": files,
                               "marked_at": dt.date.today().isoformat(), "note": a.note or ""}
    save_state(st)
    print(f"{a.target}: 基準を記録（commit {rev[:7]}, {len(files)} ファイル）→ sync/state.json を commit する")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("status", "import", "mark"):
        p = sub.add_parser(name)
        p.add_argument("--target", required=True, choices=["claude", "chatgpt", "codex"])
        if name != "mark":
            p.add_argument("--path", type=Path, action="append", help="インストール先フォルダか zip（複数可）")
        if name == "import":
            p.add_argument("--apply", action="store_true")
            p.add_argument("--prefer", choices=["target", "repo"], default="repo")
        if name == "mark":
            p.add_argument("--from-commit", help="その時点の内容がインストール済みとして記録する")
            p.add_argument("--note")
    a = ap.parse_args()
    return {"status": cmd_status, "import": cmd_import, "mark": cmd_mark}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
