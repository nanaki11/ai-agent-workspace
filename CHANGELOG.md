# 変更履歴

## 1.2.0（2026-10-31）

- 目的を「Claude → GitHub → ChatGPT の一方向移行」から「GitHub を正本とした双方向の定期同期」に変更（README、docs/SYNC.md）
- `scripts/sync.py` を追加：環境ごとの前回同期時点（`sync/state.json`）と比べ、取り込み・再インストール・競合を判定
- 配布用プラグインを `plugins/` に生成して Git 管理し、Claude Code（`.claude-plugin/marketplace.json`）と ChatGPT／Codex（`.agents/plugins/marketplace.json`）のマーケットプレイスとして GitHub から直接インストール・更新できるようにした
- 配布版の番号を `VERSION` に一元化（ChatGPT 用の版番号 1.1.0 の固定記述と、Claude 用 plugin.json の 0.1.0 を置き換え）
- 修正：`scan_secrets.sh` が固定コミット ID と SHA-256 一覧を秘密情報と誤検知して常に失敗していた
- 修正：スクリプトの実行権限（755）の欠落
- 修正：AGENTS.md の見出しレベルの重複と、ルール間の改行抜け
- 修正：consulting-pptx-skill を claude.ai の単体スキルとして使うと参照先の規約ファイルが無い問題に代替の参照先を追記。冒頭の優先順位の文の崩れ（「他のテンプレートの」）を修正
- テスト追加（tests/test_sync.py）：取り込み・再インストール判定・基準なし・規約の写しの逆変換・zip の不正パス

## 1.1.0（2026-10-30〜31、PR #1）

- 21スキルに実行契約と実務での追加検証を追加、共通の実行・品質規約を追加（docs/CONSULTING_QUALITY_UPDATE.md）
- ChatGPT 向け配布スクリプトを追加

## 1.0.0（2026-10-30）

- Claude 環境のスキル21件・エージェント4件を GitHub に移行（docs/MIGRATION_REPORT.md）
