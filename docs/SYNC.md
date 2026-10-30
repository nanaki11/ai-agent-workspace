# 双方向同期の運用手順

## 1. 考え方

- 正本は GitHub（このリポジトリ）。各環境（Claude・ChatGPT・Codex）はその写しをインストールして使う。
- 環境側でスキルを直してもよい（claude.ai のスキル編集、ChatGPT／Codex 上での修正など）。その変更は `sync.py import` で正本に取り込み、他の環境へ配る。
- どちらが新しいかを判定するため、各環境に「いつの版をインストールしたか」を `sync/state.json` に記録する（`sync.py mark`）。

| 状態 | 意味 | すること |
|---|---|---|
| `same` | 一致 | なし |
| `target-changed` | 環境側で編集された | `import --apply` で取り込む |
| `repo-changed` | GitHub 側が新しい | その環境へ再インストール → `mark` |
| `conflict` | 両方で編集された | 内容を見比べ、`--prefer target` で環境側を採るか、GitHub 側を採って再インストール。両方を活かす場合は手で統合 |
| `unknown` | 基準（前回同期の記録）が無い | 内容を確認して `--prefer` で決め、以後は `mark` で基準を残す |
| `target-deleted` | 環境側でファイルが消えた | 自動では削除しない。必要なら手で削除 |

## 2. 環境ごとの場所

| target | 既定で読む場所 | 補足 |
|---|---|---|
| `claude` | `~/.claude/plugins/synced/*/consulting-agents`、`~/.claude/skills/synced/*/consulting-pptx-skill`（claude.ai／Cowork）。無ければ `~/.claude/plugins/cache/*/…`（Claude Code） | Cowork のクラウドセッションで実行すると claude.ai 上の最新版と比較できる |
| `chatgpt` | `~/.codex/plugins/cache/*/nanaki11-consulting-toolkit/*` | ChatGPT デスクトップと Codex で共通。ChatGPT からファイルを取り出せない場合は、スキルフォルダや zip を `--path` で渡す |
| `codex` | `~/.agents/skills` | `install_codex.sh` のリンク方式なら常に正本と一致 |

`--path` は複数指定でき、フォルダでも zip でもよい（zip の不正パスは拒否する）。

## 3. 定期同期（週1回の目安）

1. `git pull`（他の環境・人の変更を受け取る）
2. 環境ごとに確認：`python3 scripts/sync.py status --target <claude|chatgpt|codex>`
3. 環境側の変更を取り込む：`python3 scripts/sync.py import --target <t> [--path …] --apply`
   - 競合・基準なしは自動で取り込まない。中身を確認してから `--prefer target` を付ける
   - 生成物（各スキルの `references/consulting-delivery-standard.md`）の変更は `common/rules/` の正本に戻して取り込む
4. 生成と検証：`python3 scripts/generate.py && python3 scripts/validate.py && python3 -m unittest discover -s tests && bash scripts/scan_secrets.sh`
5. `VERSION` を上げる（例：1.2.0 → 1.2.1。スキルの追加・削除は 1.3.0）→ `generate.py` を再実行 → commit・push（force push 禁止）
6. 各環境へ再インストール（README の表）
7. `python3 scripts/sync.py mark --target <t>` → `sync/state.json` を commit・push

Cowork のスケジュール機能で 1〜3 の確認だけを定期実行し、差分があれば通知する運用もできる（取り込みと再インストールは人が確認してから行う）。

## 4. 注意

- 環境側で新しく作ったスキルは自動では取り込まない（WARN に出る）。`.agents/skills/` に置き、`claude/packages.json` のどのパッケージに入れるかを決める。
- Anthropic 提供スキル（docx・pptx・xlsx・pdf 等）は同期対象外。
- `plugins/` は生成物。環境から取り出したファイルを `plugins/` に直接上書きしない（`generate.py --check` で検出される）。
- 取り込む差分に顧客情報や認証情報が混ざっていないか、commit 前に必ず確認する。
