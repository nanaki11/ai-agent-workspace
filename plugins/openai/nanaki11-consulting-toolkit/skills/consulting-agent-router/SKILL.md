---
name: consulting-agent-router
description: 戦略・業務改革・IT・PMOの依頼に主担当と必要なスキルを選び、判断と根拠を引き継いで品質を検証する。
---

# Consulting agent router

## 実行
1. `references/consulting-delivery-standard.md` と `references/consulting-output-rules.md` を読む。
2. 目的・判断事項・作業モードを定め、下の主担当の参照ファイルを読む。
3. 必要なスキルだけを `skills/<name>/SKILL.md`（プラグインルート基準）から読む。
4. 引き継ぎ記録を維持し、顧客提出用は deliverable-review で品質ゲートを確認する。

## 環境互換性
- 同梱する全文を使う。GitHubへの毎回の再取得は必須にしない。SOURCE_MANIFEST.jsonで版とハッシュを確認する。
- `${CLAUDE_SKILL_DIR}` は対象スキルのディレクトリ、`${CLAUDE_PLUGIN_ROOT}` はこのプラグインのルートと読み替える。
- `consulting-agents:<name>` は同名スキルを指す。ファイル出力先・検索・文書生成は利用環境の対応手段を使う。
- ロールは役割定義であり、実際の並列実行や独立レビューを保証しない。使えないツールを使ったと報告しない。
- 外部スライドリポジトリや提供元固有の生成ツールは同梱対象外。取得・実行不可なら代替手段と未検証範囲を示す。

## 主担当
- [business-consultant](references/business-consultant.md): ビジネス（業務改革）コンサルタント。業務の可視化（BPM・業務フロー）、課題分析、To-Be業務設計、Fit&Gap、KPI設計、組織・役割分担（RACI）の設計を担う。業務整理、業務フロー作成、業務改善、BPRの依頼を受けたときに使う。 適用スキル: logical-thinking, desk-research, quantitative-analysis, storyline-builder, deliverable-review, bpm-process-mapping, process-redesign, kpi-design, org-raci-design, drawio-diagram
- [it-architect](references/it-architect.md): ITアーキテクト。IT戦略・システム化構想、エンタープライズアーキテクチャ（EA）設計、現行システムの調査、要件定義、アプリ・データ・クラウドのアーキテクチャ設計、製品・ベンダー選定を担う。システム全体像や構成図（draw.io）、要件定義書、RFP、ADRの作成を依頼されたときに使う。 適用スキル: logical-thinking, desk-research, quantitative-analysis, storyline-builder, deliverable-review, drawio-diagram, ea-design, requirements-definition, tech-selection
- [pmo](references/pmo.md): PMO（プロジェクトマネジメントオフィス）。プロジェクトの進捗把握（EVM・RAG評価）、週次・月次報告やステアリングコミッティ資料の作成、課題・リスク・変更の管理、品質指標の分析、移行・切り替え計画とGo/No-Go判定、プロジェクトの健全性診断を担う。プロジェクトの状況分析や管理資料の作成を依頼されたときに使う。 適用スキル: logical-thinking, quantitative-analysis, storyline-builder, deliverable-review, project-status-report, risk-issue-management, quality-management, cutover-planning
- [strategy-consultant](references/strategy-consultant.md): 戦略コンサルタント。経営課題の論点整理、業界・競合分析、成長戦略、新規事業、M&A、中期経営計画の策定を担う。全社戦略・事業戦略の検討や、経営層向けの資料作成を依頼されたときに使う。 適用スキル: logical-thinking, desk-research, quantitative-analysis, storyline-builder, deliverable-review, environment-analysis, growth-strategy, business-plan
