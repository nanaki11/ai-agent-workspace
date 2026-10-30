# Claude 環境の棚卸し（2026-10-30）

調査対象：Claude（Cowork）のクラウドセッション環境（`~/.claude`、`~/.claude.json`、作業ディレクトリ）。
ユーザーの PC 上の `~/.claude` は、このセッションが PC に接続されていないため調査していない（【不明】）。

## 1. 対象ごとの結果

| 対象 | 結果 | 扱い |
|---|---|---|
| プロジェクトの `CLAUDE.md` | 存在しない | — |
| ユーザーの `~/.claude/CLAUDE.md` | 存在しない | — |
| claude.ai の Personal preferences（共通ルール相当） | あり | `common/rules/consulting-output-rules.md` に転記し、AGENTS.md の生成元にした |
| `.claude/skills/`（プロジェクト） | 存在しない | — |
| `~/.claude/skills/` | `session-start-hook`（Claude Code 組み込み）＋ `synced/`（claude.ai から同期した10スキル） | ユーザー作成の1件のみ保存（下表） |
| `.claude/agents/`、`~/.claude/agents/` | 存在しない | エージェントはプラグイン `consulting-agents` 内に4件 |
| `.claude/settings.json` | 存在しない | — |
| `~/.claude/settings.json` | `{}`（空） | — |
| `.mcp.json`／`~/.claude.json` の `mcpServers` | 存在しない／空 | MCP は claude.ai コネクタのみ（`mcp/README.md`） |
| Hooks | `launcher-settings.json` に Stop フック1件（Cowork 基盤が配置） | 基盤管理のため除外 |
| Commands（`commands/`） | 存在しない | — |
| Plugins | `consulting-agents`（組織ライブラリ、作者 hoshi）、`consulting-pptx-skill` の裏付けプラグイン、組み込み `cc-plugin-agents-md_builtin` | ユーザー作成の2件を保存 |

## 2. 保存したもの（ユーザー作成）

| 種別 | 名前 | 元の場所 | 保存先 |
|---|---|---|---|
| プラグイン定義 | consulting-agents | `~/.claude/plugins/synced/<id>/consulting-agents/.claude-plugin/plugin.json` | `claude/plugins/consulting-agents/.claude-plugin/` |
| エージェント×4 | business-consultant, it-architect, pmo, strategy-consultant | 同 `agents/` | `claude/plugins/consulting-agents/agents/` |
| スキル×20 | 同プラグインの `skills/` | 同 `skills/` | `.agents/skills/` |
| スキル×1 | consulting-pptx-skill | `~/.claude/skills/synced/<id>/consulting-pptx-skill/` | `.agents/skills/` |
| 依存ファイル | `drawio-diagram/scripts/validate_drawio.py`、`drawio-diagram/examples/sample-system-overview.drawio` | 同スキル内 | 同スキル内 |

## 3. 依存関係

| スキル／エージェント | 依存先 | 種類 | 状態 |
|---|---|---|---|
| drawio-diagram | `scripts/validate_drawio.py`（Python 標準ライブラリのみ） | 同梱 | OK |
| drawio-diagram | `examples/sample-system-overview.drawio` | 同梱 | OK |
| drawio-diagram | draw.io デスクトップ CLI（PNG/SVG/PDF 書き出し） | 外部ツール（任意） | 無ければ書き出しを省く記述あり |
| ea-design | `${CLAUDE_PLUGIN_ROOT}/skills/drawio-diagram/examples/...` | スキル間参照 | OK（Codex は AGENTS.md の読み替え表で解決） |
| consulting-pptx-skill | `github.com/carnot-tech/consulting-pptx-skill`（MIT、commit `5d3b048e…` に固定） | 実行時に git clone | 未同梱（実行時取得の設計どおり） |
| consulting-pptx-skill | Node.js・playwright・Chromium、日本語フォント | 外部ツール | 環境依存 |
| consulting-pptx-skill、storyline-builder 等 | Anthropic の pptx / xlsx / docx スキル | 外部スキル | 本リポジトリ対象外 |
| エージェント×4 | `consulting-agents:<skill>`（frontmatter の `skills:`） | スキル参照 | 全件実在（`scripts/validate.py`） |
| deliverable-review 等の「別エージェント」手順 | Claude の Agent ツール | Claude 固有機能 | Codex はサブエージェントで代替 |

同名スキルの重複：なし（ユーザー作成21件の中で重複なし。Anthropic 提供スキルとも名前は重ならない）。

## 4. 除外したもの

| 対象 | 理由 |
|---|---|
| docx / pptx / xlsx / pdf スキル | Anthropic 提供。LICENSE が「All rights reserved」で再配布不可 |
| skill-creator | Anthropic 提供（Apache-2.0）。ユーザー作成物でなく、Codex にも同名のシステムスキルがあるため二重管理を避けた |
| docs / morning / import-memory / google-workspace | Anthropic 提供（anthropic-example）。Claude 固有ツール前提 |
| session-start-hook、その他の組み込みスキル（dataviz、artifact-* 等） | Claude Code／Cowork の組み込み |
| `stop-hook-git-check.sh`、`user-prompt-submit-reply-reminder.py`、`launcher-settings.json` | Cowork 基盤が配置・管理する設定（ユーザー設定ではない） |
| `~/.claude.json` | アカウント情報・キャッシュを含む |
| `~/.claude/remote/.oauth_token`、`.session_ingress_token` | 認証トークン（内容は読んでいない） |
| `policy-limits*.json`、`sessions/`、`projects/`（会話ログ）、`backups/`、`shell-snapshots/` | 基盤の状態・会話履歴 |
| `plugins/store/cc-plugin-agents-md_builtin-*.json` | 組み込みプラグインの利用記録 |
| consulting-pptx-skill の外部リポジトリ本体 | 第三者リポジトリ。実行時に固定コミットを取得する設計のため同梱しない |
