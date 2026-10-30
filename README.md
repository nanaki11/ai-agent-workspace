# ai-agent-workspace

Claude・ChatGPT・Codex で使うコンサルティング用スキル（21件）とエージェント（4件）を、GitHub を正本として**双方向に同期**するためのリポジトリ。

- どの環境で改善したスキルも、GitHub に取り込んで他の環境へ再インストールできる。
- 変更の向き（どちらが新しいか）は `scripts/sync.py` が前回同期時点の記録（`sync/state.json`）と比べて判定する。
- 運用手順の詳細は [docs/SYNC.md](docs/SYNC.md)。

```
        ┌──────── import（環境で直したスキルを取り込む）────────┐
        ▼                                                      │
  GitHub（正本） ── generate / build ──▶ plugins/ ── install ──▶ Claude ／ ChatGPT ／ Codex
        ▲                                                      │
        └──────────── mark（インストール済みの版を記録）─────────┘
```

## 構成

```
.
├── VERSION                         # ★配布版の番号（配布内容を変えたら上げる）
├── .agents/skills/<name>/          # ★スキルの正本（21件）。Codex はこのまま検出する
├── claude/
│   ├── packages.json               # ★Claude 側の配布単位
│   └── plugins/consulting-agents/
│       ├── .claude-plugin/plugin.json
│       └── agents/*.md             # ★エージェントの正本（4件）
├── common/rules/                   # ★共通ルールの正本
├── sync/state.json                 # 環境ごとの「前回同期時点」のハッシュ（sync.py が更新）
├── plugins/                        # 生成物：配布用プラグイン（Git 管理＝GitHub から直接インストール可）
│   ├── claude/consulting-agents/   #   Claude（20スキル＋4エージェント）
│   ├── claude/consulting-pptx-skill/
│   └── openai/nanaki11-consulting-toolkit/  # ChatGPT／Codex（21スキル＋役割ルーター）
├── .claude-plugin/marketplace.json # 生成物：Claude Code のマーケットプレイス定義
├── .agents/plugins/marketplace.json# 生成物：ChatGPT／Codex のマーケットプレイス定義
├── AGENTS.md, .codex/agents/       # 生成物：Codex 用の共通指示とカスタムエージェント
├── mcp/                            # MCP 設定のテンプレート（秘密情報なし）
├── scripts/  tests/  docs/
```

★が人が編集する正本。それ以外は `python3 scripts/generate.py` で作る（手で直さない）。

## インストール／再インストール

| 環境 | 初回 | 更新時 |
|---|---|---|
| claude.ai／Cowork | 組織ライブラリに `plugins/claude/consulting-agents` を公開（Cowork で「プラグインを公開して」と依頼するか、`dist/claude/consulting-agents.zip` をアップロード）。consulting-pptx-skill は個人スキルとして更新 | 同じ操作で置き換え |
| Claude Code（CLI） | `/plugin marketplace add nanaki11/ai-agent-workspace` → `/plugin install consulting-agents@nanaki11-ai-agent-workspace` | `/plugin marketplace update nanaki11-ai-agent-workspace` |
| ChatGPT（デスクトップ）／Codex | `codex plugin marketplace add nanaki11/ai-agent-workspace --ref main` → ChatGPT の Plugins Directory で `nanaki11-consulting-toolkit` をインストール | `codex plugin marketplace upgrade nanaki11-ai-agent-workspace` → ChatGPT を再起動 |
| Codex（スキルだけ使う） | リポジトリ内で起動（自動検出）、または `bash scripts/install_codex.sh` | `git pull` |
| ChatGPT（zip 配布） | `python3 scripts/build_chatgpt_package.py` → `dist/chatgpt/*.zip` を利用環境のプラグイン更新操作で反映 | 同じ |

- Private リポジトリをマーケットプレイスにする場合は、その PC の Git から GitHub に認証できる必要がある。
- インストールしたら、その環境の版を記録する：`python3 scripts/sync.py mark --target claude|chatgpt|codex`

## 定期同期（推奨：週1回）

```bash
git pull
python3 scripts/sync.py status --target claude     # 各環境と GitHub の差分を確認
python3 scripts/sync.py import --target claude --apply   # 環境で直した分を取り込む（競合は --prefer）
python3 scripts/generate.py && python3 scripts/validate.py && python3 -m unittest discover -s tests && bash scripts/scan_secrets.sh
# VERSION を上げて commit・push（force push 禁止）→ 各環境へ再インストール → sync.py mark
```

詳細・競合時の扱い：[docs/SYNC.md](docs/SYNC.md)

## スクリプト

| スクリプト | 役割 |
|---|---|
| `scripts/sync.py` | 環境との3者比較（`status`）、取り込み（`import`）、同期時点の記録（`mark`） |
| `scripts/generate.py` | 生成物（AGENTS.md、Codex エージェント、規約の写し、`plugins/`、マーケットプレイス定義）を作る。`--check` で鮮度確認 |
| `scripts/build_claude_packages.py` | Claude 用プラグインと zip を `dist/claude/` に作る |
| `scripts/build_chatgpt_package.py` | ChatGPT 用プラグインと zip を `dist/chatgpt/` に作る（`--legacy-manifest` で既存の表示名等を保持） |
| `scripts/validate.py` | frontmatter、参照パス、重複、エージェントの参照、生成物の鮮度、VERSION、禁止ファイルを検査 |
| `scripts/scan_secrets.sh` | gitleaks・detect-secrets・正規表現で機密情報を検査 |
| `scripts/verify_against_claude.py` | Claude 環境とファイル単位で全件比較（`sync.py status` の詳細版） |
| `scripts/install_codex.sh` | Codex にユーザー単位でリンク導入 |

## 共通の実行・品質規約

判断基準の正本は `common/rules/consulting-delivery-standard.md`。`generate.py` が各スキルの `references/` に写す（写しは直接編集しない）。
簡易相談・分析ドラフト・顧客提出用を分け、顧客提出用は「提出可／要修正／未検証」を明記する。変更履歴は [docs/CONSULTING_QUALITY_UPDATE.md](docs/CONSULTING_QUALITY_UPDATE.md)。

## セキュリティ

- APIキー・トークン・パスワード・`.env`・顧客情報・個人情報はコミットしない（Private リポジトリでも同じ）。
- 環境から取り込むときも、取り込む差分に機密情報が無いかを `scan_secrets.sh` で確認する。
- MCP の認証情報は環境変数かローカル設定に置く（`mcp/.env.example`）。

参考：[docs/INVENTORY.md](docs/INVENTORY.md)（初回の棚卸し）、[docs/MIGRATION_REPORT.md](docs/MIGRATION_REPORT.md)
