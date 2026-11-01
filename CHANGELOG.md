# 1.4.1 (2026-11-01 JST)

- 独立2担当のMECEレビューを反映し、7役割・41スキルを維持して成果物責任を明確化。
- IT全体設計／領域詳細設計、PMO統合管理／技術実行、人の最終承認を分離。
- 23作業区分・単一ownerの責任表と混合依頼・障害初動の振り分けを追加。
- PMOの工程表除外と切替タイムチャートの矛盾、PPTスキルの役割メタデータ漏れを修正。
- UX探索と依存更新の責任を既存スキルへ補完。共通規約の配布・同期を検証。
- 詳細: docs/AGENT_MECE_REVIEW.md。

# 1.4.0 (2026-11-01 JST)

- エンジニア3役割と専門15・共通5スキルを追加。
- Claude・Codex・ChatGPT配布と既存ルーターに反映。
- 固定件数の配布説明を動的化し、役割結線・指示保持・配布追跡の回帰テストを追加。
- 設計: docs/ENGINEERING_AGENTS.md。既存21スキル・4役割を維持。

# 変更履歴

## 1.3.0（2026-11-01）

- `consulting-agents` プラグインに開発の共通ルール（`rules/development-workflow.md`）と SessionStart フック（`hooks/hooks.json`）を同梱。プラグインを入れた全 PC で、セッション開始時にルールが読み込まれる（各 PC の `~/.claude/CLAUDE.md` は不要）
- `claude/packages.json` に `rules` を追加し、`build_claude_packages.py` が共通ルールをプラグインに写すようにした。`validate.py` で実在を検査、回帰テストを追加
- README に、組織の管理設定で全 PC のマーケットプレイス登録と自動更新を行う設定例を追加

## 1.2.1（2026-11-01）

- 開発の共通ルール `common/rules/development-workflow.md` を追加：日本語出力、推奨フォルダ構成（docs/・tests/reports/・deploy/history.md）、単体テストの記録、設計書の最新化、ローカルで手動確認してからデプロイ。AGENTS.md に取り込み、Claude Code は `~/.claude/CLAUDE.md` にコピーして使う（README）

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
