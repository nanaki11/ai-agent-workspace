# エンジニアエージェント

更新日: 2026-11-01 JST / 配布版: 1.4.1

## 構成と呼び出し

既存の4役割・21スキルを維持し、3役割・20スキルを追加した。
ChatGPTでは既存のConsulting Toolkit内のconsulting-agent-routerが役割を選択する。
「フロントエンドエンジニアとして検索画面を実装して」などと依頼する。
これは役割指示であり、並列実行や独立した実行プロセスの起動を保証しない。
Claude向けにはagents/*.md、Codex向けには.codex/agents/*.tomlを生成する。
ユーザー端末の導入は従来のマーケットプレイス更新またはinstall_codex.shを使い、ホストで読み込みを確認する。

| 役割 | 所有する成果物 | 専門スキル |
|---|---|---|
| frontend-engineer | 画面・状態・API接続・操作検証 | design-frontend-architecture / implement-accessible-ui / integrate-frontend-api / test-frontend-behavior / optimize-frontend-performance |
| backend-engineer | API契約・業務処理・認可・データ・移行 | design-api-contracts / implement-domain-services / design-data-and-migrations / implement-backend-security / test-and-optimize-backend |
| infrastructure-engineer | 基盤・IaC・配備・IAM・監視・復旧 | design-infrastructure / implement-infrastructure-as-code / build-delivery-pipelines / secure-cloud-platform / operate-and-recover-services |

共通スキル: inspect-engineering-context、plan-engineering-change、review-engineering-change、diagnose-engineering-failure、handoff-engineering-work。
各スキルに必要入力、手順、成果物、完了条件、連携条件、失敗時の対応を定める。
技術スタックは対象プロジェクトに合わせ、フレームワークやクラウドを固定しない。

## 作業と連携

1. 既存規約・構成・未コミット差分・実行方法を調べる。
2. 受け入れ条件と主担当、契約、依存順、ファイル所有者を定める。
3. 主担当が該当スキルを読み、設計・実装・検証する。小さな変更は単独で進める。
4. APIはバックエンド、画面状態はフロントエンド、配備はインフラを責任者とする。
5. 対象版・成果物・成功・失敗・未実施・次の作業を引き継ぐ。

API契約は型・認証認可・エラー・互換性を含める。DB変更は旧新コードの共存と復旧可能性を確認する。
基盤の変更計画と適用、モックと実API、バックアップと復元成功を区別する。
本番操作はユーザーの既存承認範囲と実行権限を確認し、未承認の破壊的変更を進めない。

## 正本と配布

- スキル正本: .agents/skills/<name>/SKILL.md
- 役割正本: claude/plugins/consulting-agents/agents/<role>.md
- 配布定義: claude/packages.json
- 生成: python3 scripts/generate.py
- 検証: python3 scripts/validate.py / python3 -m unittest discover -s tests / bash scripts/scan_secrets.sh

生成物の手動編集は避ける。ChatGPT配布には41原本スキルと生成ルーター1件が含まれる。
GitHubへのマージとインストール済みプラグインの更新は別操作で、双方の結果を確認する。

## 参照

- OpenAPI: https://spec.openapis.org/ （API契約の表現。利用ツールに対応する版を選ぶ）
- WCAG: https://www.w3.org/TR/WCAG22/ （画面品質。自動検査だけで適合と断定しない）
- SLSA: https://slsa.dev/spec/v1.2/ （成果物来歴。採用だけで認定・準拠を主張しない）

## 1.4.1の責任分担

ITの横断設計と各engineerの領域内詳細設計を分離。PMOの全体品質・切替計画と技術実行を区別する。責任表はcommon/rules/agent-responsibilities.md/json、変更理由と検証範囲は[MECEレビュー](AGENT_MECE_REVIEW.md)を参照。
