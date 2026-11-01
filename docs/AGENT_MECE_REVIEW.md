# エージェント構成のMECEレビュー

基準日: 2026-11-01 JST / 修正版: 1.4.1

## 判定と前提

1.4.0は主要な能力を備えていたが、役割の分類軸・設計の粒度・横断業務の主担当に曖昧さがあった。
独立した2担当の静的レビューを親担当が原文照合し、7役割・41スキルを維持して責任境界を修正した。
共通スキルを複数職種が使うことは許容する。MECEの評価単位は、作業パッケージと成果物の責任である。

定義した対象範囲では、23の作業区分に各1名の成果物ownerを定めた。
これは自然言語の全依頼が網羅される保証ではない。未分類を明示し、対象外は人の役割・専門家へ渡す。
機械検証と限られたシナリオの結果から、全モデル・実案件での完全MECEや品質を保証しない。

## 分類軸

|区分|役割|所有する成果物|
|---|---|---|
|構想・要件|strategy-consultant|経営・事業の選択、投資理由|
|構想・要件|business-consultant|業務要求、業務ルール、組織、KPI、教育・定着、UAT案|
|構想・要件|it-architect|システム要件、領域横断原則・境界・非機能配分、技術テスト整合|
|実装・運用|frontend-engineer|情報設計、操作試作、画面詳細設計・実装・操作検証|
|実装・運用|backend-engineer|API契約、業務処理、アプリ認可、物理DB、データ移行・照合|
|実装・運用|infrastructure-engineer|基盤詳細設計、IaC、配備、基盤IAM、監視、復元実行|
|横断管理|pmo|全体進捗・品質指標・証跡・リスク・切替計画と判断材料|

PMOは他の6役割と同じ工程の分割ではなく、横断管理の役割である。
成果物の責任者、案件の統合主担当、人の承認者を区別する。

## 指摘と修正

|1.4.0の問題|1.4.1の修正|原文の正本|
|---|---|---|
|ITと3エンジニアの設計責任が重なる|ITは領域横断、各engineerは領域内詳細。原則変更時だけITへ戻す|agents/it-architect.md、各engineer、ea-design、各設計スキル|
|PMOと実装担当が品質・移行を扱うが境界が不明|全体計画・証跡と、実行コード・配備・復元・教育を分離|pmo.md、quality-management、cutover-planning、data migration|
|PMOが工程表作成を除外しながら切替時刻表を作る|全体WBS策定はPM。移行範囲の詳細タイムチャート案はPMOの対象|pmo.md、project-status-report、cutover-planning|
|混合依頼・原因不明障害の主担当が不明|主成果物を優先。同等の混合成果物はITが暫定統合。本番障害初動はinfra|共通責任規約、ルーター、plan/diagnose-engineering|
|UX探索と継続的な依存更新が薄い|businessと利用者根拠を共有しfrontendが操作試作・評価。更新通知は運用、修正は各領域owner|frontend design/UI、operations、CI/CD、backend/cloud security|
|本文で使うPPTスキルが役割メタデータにない|コンサル4役割のスキル一覧へ追記|各コンサル役割のfrontmatter|
|責任表が配布・同期で失われる可能性|共通md/jsonをChatGPTとClaudeへ同梱し、Codexの共通指示にも規約を反映。JSONを同期対象にする|build_chatgpt_package.py、sync.py、generate.py|

共通12スキルと専門29スキルは、能力の管理区分として41スキルを重複なく分類した。
専門スキルの他職種利用は制限しない。共有しても成果物ownerは変えない。

## 主担当の決定規則

- 明示された統合主担当を優先し、各成果物ownerと分けて記録する。
- 指定がなければ主成果物のownerを統合主担当とする。
- 同等の複数領域成果物ならit-architectを暫定統合主担当とし、各成果物ownerを維持する。
- 全体進捗・全体切替の判断材料が主成果物ならpmo。
- 原因不明の本番障害はinfraが影響抑制の初動。非本番は再現領域、領域も不明ならbackendが暫定調査。原因特定後に修正担当を移す。
- 未分類は未分類として扱い、対象範囲を再定義する。小さな領域内変更にIT・PMOの経由を強制しない。

ルーターが自然言語から作業区分を選ぶ。scripts/responsibility_catalog.pyは分類済みIDを検証・振り分ける補助であり、自然言語分類器ではない。
機械テストは未定義ID、owner欠落・重複、入力順依存、主成果物指定、障害初動の優先、配布・同期の保持を検査する。

## 人の権限と対象外

PMによる全体WBS・人員配置・対人調整、業務責任者によるUAT合否、経営・予算・本番Go/No-Goの最終承認を代行しない。
法務・税務・規制の最終専門判断は対象外。ML・組込み・モバイル等は個別スコープを再定義する。
既存のユーザー承認を再要求する規約ではなく、役割指示が人の権限を自動取得することを防ぐ区分である。

## 検証範囲と限界

- 独立2担当の原文レビュー。主要な設計・品質・移行・混合依頼・障害初動の指摘を修正。
- 再レビューで見つかったPMOの旧引き継ぎ文も修正。単独のplan-engineering-changeは同梱規約と本文で完結し、所在不明のJSONを必須にしない。
- 自動検証結果と6つの自然言語シナリオの記録はtests/reportsを参照。
- 実アプリの開発、実クラウドの変更、ユーザー端末のホスト読み込みは本レビューの検証対象外。

## 出典

本リポジトリの役割原文: claude/plugins/consulting-agents/agents/

スキル原文: .agents/skills/

責任表の正本: common/rules/agent-responsibilities.md、agent-responsibilities.json

配布・検証・同期: scripts/build_chatgpt_package.py、generate.py、validate.py、sync.py、responsibility_catalog.py
