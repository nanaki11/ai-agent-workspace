# MCP 接続設定（テンプレート）

## 棚卸し結果（2026-10-30、Claude Cowork のクラウドセッションで確認）

| 区分 | 項目 | 結果 |
|---|---|---|
| ローカル設定 | `.mcp.json`（プロジェクト） | 存在しない |
| ローカル設定 | `~/.claude.json` の `mcpServers` | 空（`{}`） |
| ローカル設定 | `~/.claude/settings.json` | `{}`（MCP 設定なし） |
| claude.ai コネクタ（ユーザーが接続） | Google Drive | 接続済み（OAuth は claude.ai 側で管理。トークンはローカルに無い） |
| claude.ai コネクタ（ユーザーが接続） | Google Slides | 接続済み（同上） |
| Anthropic 提供（Claude 固有） | Claude Docs | Claude のドキュメント機能。他環境に移行不可 |
| Cowork 基盤（Claude 固有） | claude-code-remote（スケジュール実行）、widgets、visualize | Cowork の UI・基盤機能。他環境に移行不可 |

認証情報（OAuth トークン等）はすべて claude.ai 側にあり、このリポジトリには含めていない。

## テンプレート

| ファイル | 用途 |
|---|---|
| `claude.mcp.json.example` | Claude Code（CLI）でローカル MCP を使う場合の `.mcp.json` 雛形 |
| `codex.config.toml.example` | Codex の `~/.codex/config.toml` に追記する MCP 設定の雛形 |
| `.env.example` | 上記で参照する環境変数の一覧（値は空） |

- 実際の値は `.env`（`.gitignore` 対象）か OS の環境変数に置く。
- Google Drive / Slides の MCP サーバーの URL・提供元は【不明】。claude.ai のコネクタは Anthropic 経由で提供されており、同じエンドポイントを Codex から使えるかは要確認。Codex で使う場合は、Google 公式または組織で承認した MCP サーバーを選定して URL を埋める。
- ChatGPT では「コネクタ／アプリ」として UI から接続する（設定ファイルは使わない）。
