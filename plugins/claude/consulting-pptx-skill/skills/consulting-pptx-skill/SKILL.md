---
name: "consulting-pptx-skill"
description: "コンサル品質・経営会議品質のスライド（HTML 16:9→PDF）を、約110項目の設計規約・62型パーツ集・機械チェックで作る。「コンサル品質のスライドを作って」「規約に沿ったデッキで」「型カタログから選んで」で使う。"
---

# コンサル型スライド作成スキル（carnot-tech/consulting-pptx-skill, MIT）

## 実行契約
作業前に [実行・品質規約](references/consulting-delivery-standard.md) を読む。単独利用時も同じ規約を適用し、作業モードに応じて記録と検証を絞る。
このファイルが同梱されていない環境（claude.ai の単体スキル等）では、deliverable-review スキルの `references/consulting-delivery-standard.md` を読む。

本体（規約・パーツ集・スクリプト・カタログPDF）は GitHub リポジトリにある。このスキルはそれを取得して、リポジトリの SKILL.md の手順どおりに作る。**ただし「タイトルとリード文」だけは、下の「★ タイトル＋リード文方式」がリポジトリの規約（タイトル＝結論文）より優先する。**

## 0. ブートストラップ（毎回最初に）

```bash
SK="$PWD/consulting-pptx-skill"
SK_REV="5d3b048e944f237c26690ed5f624d7773b302d96"
if [ ! -d "$SK" ]; then
  git clone https://github.com/carnot-tech/consulting-pptx-skill.git "$SK" || exit 1
  git -C "$SK" checkout -q "$SK_REV" || exit 1
fi
# 既存の取得物も検証する。異なる版を無断で上書きしない。
test "$(git -C "$SK" rev-parse HEAD)" = "$SK_REV" || exit 1
test -z "$(git -C "$SK" status --porcelain)" || exit 1
```

取得・版確認に失敗したら、この外部ツールの実行を止める。利用可能な別の生成手段に切り替え、適用できない検証を明記する。別版を採用する場合はコミットと検証結果を記録する。

その後、必ず次を Read する:

1. `$SK/SKILL.md` — 手順の正本。以降はこれに従う（タイトルとリード文の扱いを除く）
2. `$SK/references/slide-rules.md` — **作成前に全文必読**（規約の正典。§2・§3 のうちタイトル／リード文に関する項は下の★で上書き）
3. 必要に応じて `$SK/references/archetype-catalog.md`（62型一覧）、`$SK/references/ai-smell-lexicon.md`（文章仕上げ）、`$SK/references/content-review-prompt.md`（レビュー指示文）

スクリプトは `$SK/scripts/` から実行する（`python3 $SK/scripts/new_deck.py --list` など）。成果物の HTML/PDF は作業ディレクトリに出力する。

## ★ タイトル＋リード文方式（リポジトリ規約より優先）

リポジトリ既定の「タイトル＝結論文（メッセージライン）」「タイトル直下の説明行は禁止」は使わない。**タイトルはシンプルな見出し、キーメッセージはタイトル直下のリード文で伝える**（アクセンチュア型）。storyline-builder の骨子でタイトルが結論文になっている場合は、ここで「タイトル（名詞句）」と「リード文」に分け直す。

### タイトル

- そのページの**論点・対象を示す短い名詞句**にする（例:「市場規模の推移」「競合比較」「To-Be業務フロー」「推進体制」「投資対効果」）
- 全角20字以内・1行が目安。主張・評価・数値の結論は入れない
- 「〜について」「〜の件」は付けない。「現状と課題：〜」のようなラベル＋コロン＋文も不可
- 同じデッキで同じタイトルを重複させない（同じ論点が続くなら「（1）」「（2）」や対象名で区別する）
- 表紙・章扉・裏表紙はリポジトリ規約どおり

### リード文（キーメッセージ）

- タイトルの直下・本文の上に、**そのページのキーメッセージを1〜2文**で書く。全角40〜90字、最大2行
- だ・である調／体言止めの言い切り（です・ます不可）。主語・対象を省かず、リード文だけを切り出して初見で意味が取れること
- リポジトリ規約でタイトルに課していた要件は**すべてリード文に移す**: 結論を書く（§2.1）、普通の文として読める（§2.3）、個数を書かない（§2.4）、So what を載せる（§2.10）、数を書いたら本文と一致（§2.9）、同じ文型を並べない（§2.8）、「この」「その」で他ページを参照しない
- **縦の論理はリード文の通し読みで確認する**（§2.6 の「タイトル通し読み」はリード文通し読みに読み替える）。エグゼクティブサマリーの各行はリード文と対応させる
- 1ページ1メッセージ。リード文に論点が2つ入ったらページを分ける
- 「〜の現状を示す」「〜を整理した」のような説明文にしない（言い切りのメッセージにする）
- 図のページの右カラムは「読み方・補足」を担い、リード文と同じことを繰り返さない

### HTML 実装

- `<h1>` には短いタイトルだけを書き、直後に `<p class="lead">キーメッセージ</p>` を置く
- CSS の目安（パーツ集の変数を使う）:
  ```css
  .lead{margin:2.5mm 0 3mm 0;font-size:14pt;line-height:1.5;font-weight:600;color:var(--navy)}
  ```
  h1（22pt）より小さく本文より大きく。色分け・枠・塗りは付けない
- リード文が入る分だけ本文領域が減るので、本文の下端・出典行・フッターとの重なりを `check_layout.mjs` と PDF 目視で確認する

### 機械チェックの読み替え

- `check_deck.py` の「`.lead` ×N — コンテンツスライドのタイトル直下なら禁止」の WARN は、この方式では**想定どおりなので許容**する
- 出力されるタイトル一覧は「見出しの重複・表記ゆれ」の確認に使い、ストーリーの通し読みは HTML からリード文を抽出して行う:
  ```bash
  python3 -c "import re,sys;h=open(sys.argv[1]).read();[print(i,re.sub(r'<[^>]+>','',t).strip()) for i,t in enumerate(re.findall(r'<p class=\"lead\"[^>]*>(.*?)</p>',h,re.S),1)]" mydeck.html
  ```
- 別エージェントにレビューさせるとき（手順8）は、「タイトルは名詞句の見出し、キーメッセージはリード文で書く方式」であることを指示文に添える（タイトルが結論文でないことを指摘させない）

## 手順の要約（詳細は $SK/SKILL.md）

1. 目的・成果物・スコープ IN/OUT を3〜5行で先に合意する（不明ならユーザーに確認）
2. ストーリーラインを書く。**1枚1行で「タイトル（名詞句）｜リード文（キーメッセージ）｜見せ方」**を並べ、リード文だけを通し読みしてストーリーが通ることを確認する。推移・構成比・分布・相関は必ず図
3. `python3 $SK/scripts/new_deck.py --parts b01,b02,...,b10 --title "資料名" -o mydeck.html` でたたき台を生成し、プレースホルダー（`Text N` / `ラベル N` / `YYYY` / `00`）を差し替え、各コンテンツスライドの h1 直下に `.lead` を入れる
4. グラフは表パーツに流し込まず自分で描く
5. 規約の範囲で調整（型に合わせず、ストーリーに型を合わせる）
6. `python3 $SK/scripts/check_deck.py mydeck.html` → FAIL 0（`.lead` の WARN は許容）。リード文一覧を抽出して通し読みする
7. `node $SK/scripts/check_layout.mjs mydeck.html` → OK
8. `content-review-prompt.md` の指示文（★方式の注記を追加）で、作り方を伏せた別エージェント（Agent ツール）にレビューさせ、採否表を作って採用分だけ直し、6・7を再実行
9. PDF 化して全ページを目視（Read で PDF を確認）

## この環境での読み替え

- **playwright**: `npm run setup` は不要なことが多い。まず `npm i -g playwright` 済みか確認し、無ければ `cd $SK && npm install`（`playwright install` は実行しない。Chromium は `/opt/pw-browsers` にある）。モジュールの場所が違えば `PLAYWRIGHT_MODULE_DIR` で指す
- **PDF 化**: Mac の Chrome パスではなく、playwright の Chromium で印刷する:
  ```bash
  node -e "const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage();await p.goto('file://'+require('path').resolve('mydeck.html'));await p.pdf({path:'mydeck.pdf',preferCSSPageSize:true,printBackground:true});await b.close();})()"
  ```
  （`require('playwright')` が解決しなければ `NODE_PATH=$SK/node_modules` を付ける）
- 日本語フォントが無く文字化けする場合は `fc-list :lang=ja` で確認し、無ければ `apt-get install -y fonts-noto-cjk` を試す
- 完成した PDF / HTML は `/mnt/user-data/outputs/` に置いて渡す

## PowerPoint（.pptx）が要るとき

HTML→編集可能PPTXの変換は含まない。編集可能PPTXの依頼には利用可能なpptx生成手段で応える。見本が必要なら `$SK/assets/SuperTemplate_62type.pptx`（62型の見本帳）を案内するか、pptx スキルで別途作る。pptx で作る場合も★方式（短いタイトル＋タイトル直下のリード文テキストボックス）に従う。

## 注釈

裏表紙（b10）左下に「本資料は consulting-pptx-skill（github.com/carnot-tech/consulting-pptx-skill）で作成」が既定で入る。他ページには入れない。

## 実務での追加検証
- 編集可能PPTXを求められたら利用可能なプレゼン生成スキル・ツールで直接作る。PDFへの置換を既定にせず、困難な場合は制約を示す。
- 全ページをレンダリングし、文字切れ・重なり・図の欠落・数値と出典・編集可能性を確認する。未実施の検査は未検証とする。
- 外部依存は取得元と実際のコミットを確認する。固定版の取得失敗を無視して別版を実行しない。外部の追加インストール・コード実行は環境の権限内で行う。
