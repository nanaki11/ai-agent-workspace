# 移行レポート（2026-10-30）

対象：Claude（Cowork）環境 → GitHub `nanaki11/ai-agent-workspace`（main）
コミット ID はこのファイル自身に書けないため、`git log` を参照する。

## 1. 件数

| 種別 | 件数 | 内訳 |
|---|---|---|
| スキル | 21 | consulting-agents プラグイン 20 ＋ consulting-pptx-skill 1 |
| エージェント | 4 | business-consultant、it-architect、pmo、strategy-consultant |
| MCP（ローカル設定） | 0 | claude.ai コネクタ（Google Drive、Google Slides）のみ。詳細は `mcp/README.md` |
| Hooks（ユーザー設定） | 0 | 基盤の Stop フック1件は除外 |
| Commands | 0 | — |

## 2. 互換性の評価

| 機能 | Claude | Codex | ChatGPT | 対応 |
|---|---|---|---|---|
| スキル 18件（下記以外） | そのまま | そのまま（`.agents/skills/`） | スキル登録で利用可（要確認） | 変換不要 |
| drawio-diagram | そのまま | 動作可。`${CLAUDE_SKILL_DIR}` は AGENTS.md の読み替え表で解決 | スクリプト実行環境が必要 | 読み替えのみ |
| ea-design | そのまま | `${CLAUDE_PLUGIN_ROOT}` を読み替え | 同左 | 読み替えのみ |
| consulting-pptx-skill | そのまま | 動作は要検証（git・Node・playwright が必要。Agent ツール・`/mnt/user-data/outputs/` は読み替え） | 実行環境の制約で【不明】 | 要検証 |
| エージェント 4件 | そのまま（プラグイン） | `.codex/agents/*.toml` に変換済み（生成物） | 本文をプロジェクト指示に貼る | 変換済み |
| エージェントの `skills:` 事前読み込み | 対応 | 非対応（Codex はスキルを親から継承）。指示文に「使うスキル」一覧を埋め込んで代替 | 非対応 | 代替実装 |
| 名前空間付きスキル名 `consulting-agents:<name>` | 対応 | 非対応 → `$<name>` に読み替え | 非対応 | 読み替え |
| 共通ルール（Personal preferences） | claude.ai 設定 | AGENTS.md | カスタム指示 | 生成済み |
| MCP（Google Drive / Slides） | claude.ai コネクタ | `config.toml` に別途設定（サーバー選定が必要） | ChatGPT のコネクタで接続 | 再設定が必要 |

## 3. Claude 固有で移行できない機能

- Claude Docs、Artifact、widgets、visualize、スケジュール実行（claude-code-remote）など Cowork 基盤の機能
- Anthropic 提供スキル（docx / pptx / xlsx / pdf 等。ライセンス上も再配布不可）
- claude.ai の組織ライブラリによるプラグイン配布

## 4. 未解決の問題

| # | 内容 | 推奨対応 |
|---|---|---|
| 1 | ユーザー PC 上の `~/.claude`（ローカルの Claude Code 設定）は未調査 | PC を接続したセッションで `verify_against_claude.py` と棚卸しを再実行 |
| 2 | Codex での実動作（スキル検出、カスタムエージェントの読み込み）は未検証（Codex CLI の認証がこの環境に無い） | Codex で `/skills` と各エージェントの起動を確認 |
| 3 | Google Drive / Slides の MCP を Codex で使うためのサーバー URL・認証方式が【不明】 | 組織で MCP サーバーを選定し `mcp/` のテンプレートに反映 |
| 4 | 共通ルール原文は「以下のラベル」に【推論】【不明】の2つのみで、【事実】ラベルが無い（原文どおり転記） | 意図どおりか確認し、必要なら `common/rules/` を修正して `generate.py` |
| 5 | consulting-pptx-skill は外部リポジトリ（固定コミット）に依存。リポジトリ消失時に動かない | 必要なら MIT ライセンス表記を付けてフォークを保持 |
| 6 | claude.ai 上のプラグインと GitHub の同期は手動（zip の再アップロード） | 更新時は `build_claude_packages.py` → アップロード → `verify_against_claude.py` |
