---
name: consulting-agent-router
description: 戦略・業務改革・IT・PMO・フロントエンド・バックエンド・インフラの依頼に主担当と必要なスキルを選び、実装・検証・引き継ぎまで進める。エンジニアとして開発・修正・障害対応するときにも使用する。
---

# Consulting agent router

## 実行
1. `references/consulting-delivery-standard.md` と `references/consulting-output-rules.md` を読む。
2. `references/agent-responsibilities.md` と `references/agent-responsibilities.json` を読み、依頼を成果物単位の作業パッケージへ分ける。各パッケージにwork_typesのIDと主担当1名を付け、下の参照ファイルを読む。PMOは横断管理、ITは横断設計、各engineerは領域内詳細設計・実装と分ける。
3. 必要なスキルだけを `skills/<name>/SKILL.md`（プラグインルート基準）から読む。
4. 開発依頼では `references/development-workflow.md` を読み、inspect-engineering-context → plan-engineering-change → 該当専門スキル → review-engineering-change → handoff-engineering-workの順で進める。明示担当を優先し、指定がなければ主成果物のownerを統合主担当とする。同等の複数領域成果物ではit-architectを暫定統合主担当とし、各成果物ownerは維持する。全体進捗・全体切替計画が主成果物ならpmo。原因不明の本番障害はinfraが初動、非本番は再現領域、領域も不明ならbackendが暫定調査し、特定後に修正担当を移管する。未分類は未分類と記録して範囲を確認する。
5. 引き継ぎ記録を維持し、顧客提出用は deliverable-review で品質ゲートを確認する。開発は受け入れ条件と実行済みテスト、失敗・未実施を報告する。

## 環境互換性
- 同梱する全文を使う。GitHubへの毎回の再取得は必須にしない。SOURCE_MANIFEST.jsonで版とハッシュを確認する。
- `${CLAUDE_SKILL_DIR}` は対象スキルのディレクトリ、`${CLAUDE_PLUGIN_ROOT}` はこのプラグインのルートと読み替える。
- `consulting-agents:<name>` は同名スキルを指す。ファイル出力先・検索・文書生成は利用環境の対応手段を使う。
- ロールは役割定義であり、実際の並列実行や独立レビューを保証しない。使えないツールを使ったと報告しない。
- 外部スライドリポジトリや提供元固有の生成ツールは同梱対象外。取得・実行不可なら代替手段と未検証範囲を示す。

## 主担当
- [backend-engineer](references/backend-engineer.md): バックエンドエンジニア。API・業務ロジック・DB・マイグレーション・認証認可・サーバーテストを設計・実装する。該当する開発・修正・レビューの依頼で使用する。 適用スキル: inspect-engineering-context, plan-engineering-change, review-engineering-change, diagnose-engineering-failure, handoff-engineering-work, design-api-contracts, implement-domain-services, design-data-and-migrations, implement-backend-security, test-and-optimize-backend
- [business-consultant](references/business-consultant.md): ビジネス（業務改革）コンサルタント。業務の可視化（BPM・業務フロー）、課題分析、To-Be業務設計、Fit&Gap、KPI設計、組織・役割分担（RACI）の設計を担う。業務整理、業務フロー作成、業務改善、BPRの依頼を受けたときに使う。 適用スキル: logical-thinking, desk-research, quantitative-analysis, storyline-builder, deliverable-review, bpm-process-mapping, process-redesign, kpi-design, org-raci-design, drawio-diagram, consulting-pptx-skill
- [frontend-engineer](references/frontend-engineer.md): フロントエンドエンジニア。画面・フォーム・コンポーネント・API接続・アクセシビリティ・ブラウザテスト・表示性能を実装・改善する。該当する開発・修正・レビューの依頼で使用する。 適用スキル: inspect-engineering-context, plan-engineering-change, review-engineering-change, diagnose-engineering-failure, handoff-engineering-work, design-frontend-architecture, implement-accessible-ui, integrate-frontend-api, test-frontend-behavior, optimize-frontend-performance
- [infrastructure-engineer](references/infrastructure-engineer.md): インフラエンジニア。実行基盤・IaC・CI/CD・IAM・監視・バックアップ・復旧・費用管理を設計・実装する。該当する開発・修正・レビューの依頼で使用する。 適用スキル: inspect-engineering-context, plan-engineering-change, review-engineering-change, diagnose-engineering-failure, handoff-engineering-work, design-infrastructure, implement-infrastructure-as-code, build-delivery-pipelines, secure-cloud-platform, operate-and-recover-services
- [it-architect](references/it-architect.md): ITアーキテクト。IT戦略・システム化構想、エンタープライズアーキテクチャ（EA）設計、現行システムの調査、要件定義、アプリ・データ・クラウドを横断する原則・境界とアーキテクチャ設計、製品・ベンダー選定を担う。システム全体像や構成図（draw.io）、要件定義書、RFP、ADRの作成を依頼されたときに使う。 適用スキル: logical-thinking, desk-research, quantitative-analysis, storyline-builder, deliverable-review, drawio-diagram, ea-design, requirements-definition, tech-selection, consulting-pptx-skill, plan-engineering-change, review-engineering-change, handoff-engineering-work
- [pmo](references/pmo.md): PMO（プロジェクトマネジメントオフィス）。プロジェクトの進捗把握（EVM・RAG評価）、週次・月次報告やステアリングコミッティ資料の作成、課題・リスク・変更の管理、品質指標の分析、全体移行・切り替え計画とGo/No-Go判断材料、プロジェクトの健全性診断を担う。プロジェクトの状況分析や管理資料の作成を依頼されたときに使う。 適用スキル: logical-thinking, quantitative-analysis, storyline-builder, deliverable-review, project-status-report, risk-issue-management, quality-management, cutover-planning, consulting-pptx-skill
- [strategy-consultant](references/strategy-consultant.md): 戦略コンサルタント。経営課題の論点整理、業界・競合分析、成長戦略、新規事業、M&A、中期経営計画の策定を担う。全社戦略・事業戦略の検討や、経営層向けの資料作成を依頼されたときに使う。 適用スキル: logical-thinking, desk-research, quantitative-analysis, storyline-builder, deliverable-review, environment-analysis, growth-strategy, business-plan, consulting-pptx-skill
