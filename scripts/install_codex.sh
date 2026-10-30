#!/usr/bin/env bash
# Codex にユーザー単位でスキルとカスタムエージェントを導入する（シンボリックリンク方式＝二重管理しない）。
# リポジトリ内で Codex を起動する場合は不要（.agents/skills と .codex/agents が自動で読まれる）。
#   bash scripts/install_codex.sh            # ~/.agents/skills と ~/.codex/agents にリンク
#   bash scripts/install_codex.sh --dry-run  # 実行内容の表示のみ
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
DRY=0; [ "${1:-}" = "--dry-run" ] && DRY=1
run(){ if [ $DRY -eq 1 ]; then echo "+ $*"; else "$@"; fi; }

link(){ # src dst : 既存の実ファイルは上書きしない
  local src="$1" dst="$2"
  if [ -L "$dst" ]; then run ln -sfn "$src" "$dst"
  elif [ -e "$dst" ]; then echo "SKIP（既存の実体あり。手動で確認）: $dst"
  else run ln -s "$src" "$dst"; fi
}

run mkdir -p "$HOME/.agents/skills" "$HOME/.codex/agents"
for d in "$REPO"/.agents/skills/*/; do
  n=$(basename "$d"); link "${d%/}" "$HOME/.agents/skills/$n"
done
for f in "$REPO"/.codex/agents/*.toml; do
  link "$f" "$HOME/.codex/agents/$(basename "$f")"
done
echo "完了。Codex で /skills を実行して読み込みを確認する。"
