# ai-agent-workspace

Claude・OpenAI Codex・ChatGPT で共通に使うスキルとエージェント定義の正本（Single Source of Truth）。

## 構成

```
.
├── AGENTS.md                     # Codex／ChatGPT 向けの共通指示（生成物）
├── .agents/skills/<name>/        # ★スキルの正本（21件）。Codex がそのまま検出する
├── .codex/agents/*.toml          # Codex のカスタムエージェント（生成物）
├── claude/
│   ├── packages.json             # Claude 側の配布単位（どのスキルをどのプラグインに入れるか）
│   └── plugins/consulting-agents/
│       ├── .claude-plugin/plugin.json
│       └── agents/*.md           # ★エージェントの正本（Claude 形式、4件）
├── common/rules/                 # ★共通ルールの正本（AGENTS.md の生成元）
├── mcp/                          # MCP 設定のテンプレート（秘密情報なし）
├── scripts/                      # 生成・ビルド・検証・導入スクリプト
└── docs/                         # 棚卸し・移行レポート
```

★が人が編集する正本。それ以外は正本から生成する。

## 使い方

### Claude

| 環境 | 手順 |
|---|---|
| claude.ai／Cowork | `python3 scripts/build_claude_packages.py` → `dist/claude/consulting-agents.zip` を組織ライブラリのプラグインとして、`dist/claude/consulting-pptx-skill.zip` をスキルとして更新アップロード |
| Claude Code（CLI） | `python3 scripts/build_claude_packages.py` → `claude --plugin-dir dist/claude/consulting-agents`。consulting-pptx-skill は `~/.claude/skills/` に配置 |

### Codex

- このリポジトリ内で起動すれば、`AGENTS.md`・`.agents/skills/`・`.codex/agents/` が自動で読まれる。
- 他のプロジェクトでも使う場合：`bash scripts/install_codex.sh`（`~/.agents/skills/` と `~/.codex/agents/` にシンボリックリンク）。
- スキルの明示呼び出しは `$drawio-diagram` のように書く。`/skills` で一覧を確認する。

### ChatGPT

- 共通ルール：`common/rules/consulting-output-rules.md` をカスタム指示またはプロジェクトの指示に貼る。
- エージェント：`claude/plugins/consulting-agents/agents/<name>.md` の本文をプロジェクトの指示に貼る。
- 配布物：`python3 scripts/build_chatgpt_package.py` で `dist/chatgpt/nanaki11-consulting-toolkit.zip` を生成する。21スキルの全文・添付資源と、4専門家定義を持つルーターを同梱する。
- 既存プラグインの更新時は `--legacy-manifest /path/to/current-plugin.json` を指定し、表示名・著者・スタータープロンプト等を保持する。認証情報や非公開のメタデータをリポジトリへ追加しない。
- `SOURCE_MANIFEST.json` に原本コミット、未コミット変更の有無、各ファイルのSHA-256を記録する。配布用はコミット後に再ビルドし、`working_tree_dirty: false` を確認する。
- GitHubの更新だけではインストール済みChatGPTプラグインは更新されない。生成ZIPを、利用環境が提供するプラグイン更新操作で別途反映する。本スクリプトは公開・インストールを行わない。
- 外部のスライド生成リポジトリ・提供元固有ツールは同梱しない。依存関係はマニフェストに明記する。

## 更新の流れ

```bash
# 1. 正本を編集（.agents/skills/ ・ claude/plugins/consulting-agents/agents/ ・ common/rules/）
# 2. 生成物を更新
python3 scripts/generate.py
# 3. 検証
python3 scripts/validate.py
bash scripts/scan_secrets.sh
python3 -m unittest discover -s tests -v
# 4. Claude 環境との差分確認（Claude の環境で実行）
python3 scripts/verify_against_claude.py --claude-home ~/.claude
# 5. commit・push（force push 禁止）
```

## スクリプト

| スクリプト | 役割 |
|---|---|
| `scripts/generate.py` | AGENTS.md と `.codex/agents/*.toml` を正本から生成（`--check` で最新か確認） |
| `scripts/build_chatgpt_package.py` | ChatGPT向けに全文・資源・役割・ソース情報を同梱。インストールは別操作 |
| `scripts/build_claude_packages.py` | Claude 用のプラグイン／スキル zip を `dist/claude/` に組み立て |
| `scripts/validate.py` | frontmatter、参照パス、スキル名の重複、エージェントの参照、生成物の鮮度、禁止ファイルをチェック |
| `scripts/scan_secrets.sh` | gitleaks・detect-secrets・正規表現で機密情報を検査 |
| `scripts/verify_against_claude.py` | Claude の元環境とファイル単位（SHA-256）で比較 |
| `scripts/install_codex.sh` | Codex にユーザー単位でリンク導入（`--dry-run` あり） |

## セキュリティ

- APIキー・トークン・パスワード・`.env`・顧客情報・個人情報はコミットしない（Private リポジトリでも同じ）。
- MCP の認証情報は環境変数かローカル設定に置く（`mcp/.env.example` 参照）。
- コミット前に `bash scripts/scan_secrets.sh` を実行する。

詳細：[docs/INVENTORY.md](docs/INVENTORY.md)、[docs/MIGRATION_REPORT.md](docs/MIGRATION_REPORT.md)

## プロ向け実行契約

共通の判断基準は `common/rules/consulting-delivery-standard.md` を編集する。
`generate.py` が各スキルの `references/consulting-delivery-standard.md` に複製し、単独配布でも参照できるようにする。参照ファイルを直接編集しない。
簡易相談・分析ドラフト・顧客提出用を分け、顧客提出用は「提出可／要修正／未検証」を明記する。
変更点・検証範囲は [docs/CONSULTING_QUALITY_UPDATE.md](docs/CONSULTING_QUALITY_UPDATE.md) を参照。
