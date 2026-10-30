---
name: drawio-diagram
description: draw.io（diagrams.net）形式の図を作るスキル。.drawio（mxGraph XML）を直接書いて、EA図、システム全体構成図、クラウド構成図（AWS/Azure）、データフロー、業務フロー（スイムレーン）、組織図、C4モデルを作り、構造チェックと PNG/SVG/PDF への書き出しまで行う。「構成図を書いて」「draw.ioで」「図にして」「アーキテクチャ図」「フロー図」の依頼で使う。
---

# draw.io 作図

.drawio ファイル（圧縮していない mxGraph XML）を直接書く。draw.io デスクトップ版、diagrams.net、VS Code の Draw.io Integration 拡張機能でそのまま開いて編集できる。

## 手順
1. **図の目的を決める**：読み手、伝えたいこと、抽象度（全体像か詳細か）。1枚に詰め込まず、抽象度ごとにページを分ける
2. **XMLの前に、要素と関係を表にする**
   - 要素表：ID／種類／ラベル／所属（グループ・レーン）／状態（既存・新規・改修・廃止）
   - 関係表：接続元／接続先／ラベル（データ・方式）／線の種類
3. **配置を決める**：要素をグリッドの行と列に割り当てる（「レイアウトの規則」と「図ごとの型」を見る）
4. **XMLを書く**（「ファイル構造」「スタイル辞書」）
5. **チェックする**：`python "${CLAUDE_SKILL_DIR}/scripts/validate_drawio.py" <ファイル>.drawio`。エラーは必ず直す。警告は内容を見て判断する
6. **書き出して目で見る**：PNGに書き出して画像を開き、重なり・文字のはみ出し・線の交差を確認して直す
7. 凡例・タイトル・版を入れて完成

見本：`${CLAUDE_SKILL_DIR}/examples/sample-system-overview.drawio`（層ごとのレーンを使ったシステム全体構成図）

## ファイル構造
```xml
<mxfile host="Claude" type="device">
  <diagram id="page-1" name="全体構成">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1654" pageHeight="1169" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <!-- ここに図形と線を書く -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```
- id="0" と id="1" は必須。図形の parent は通常 "1"
- ページを増やすときは `<diagram>` を並べる（例：L0全体像／L1詳細／凡例）
- ページサイズ（px）：A3横＝1654×1169、A4横＝1169×827

### 図形（vertex）
```xml
<mxCell id="app-crm" value="CRM&lt;br&gt;(SaaS)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#DAE8FC;strokeColor=#6C8EBF;" vertex="1" parent="1">
  <mxGeometry x="200" y="120" width="160" height="60" as="geometry"/>
</mxCell>
```

### 線（edge）
```xml
<mxCell id="e-crm-erp" value="受注データ(API)" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=1;" edge="1" parent="1" source="app-crm" target="app-erp">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

### グループ（コンテナ）
子要素の parent にはコンテナの ID を指定し、座標はコンテナの左上からの相対値で書く。
```xml
<mxCell id="grp-aws" value="AWS" style="swimlane;whiteSpace=wrap;html=1;startSize=26;fillColor=none;" vertex="1" parent="1">
  <mxGeometry x="40" y="40" width="600" height="300" as="geometry"/>
</mxCell>
<mxCell id="svc-api" value="API" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="grp-aws">
  <mxGeometry x="20" y="50" width="160" height="60" as="geometry"/>
</mxCell>
```

## XMLの規則
- id はすべて一意で、意味のある名前にする（`app-erp`、`e-erp-dwh`）
- value 内の `& < > "` はエスケープする（`&amp; &lt; &gt; &quot;`）。改行は `html=1` のとき `&lt;br&gt;`
- 図形のスタイルには必ず `whiteSpace=wrap;html=1;` を入れる
- 線には source と target を必ず指定する（座標だけで浮いている線は作らない）
- 圧縮形式（base64）では書かない

## レイアウトの規則
- グリッドは10px。座標とサイズは10の倍数にする
- 標準サイズ：箱 160×60、小さい箱 120×50、アイコン 48×48（ラベルはアイコンの下）
- 間隔：横 60〜80px、縦 40〜60px。コンテナの内側の余白 20px、タイトル帯 26〜40px
- 流れの向きは、左→右か上→下のどちらかにそろえる
- 箱160pxのラベルは全角10字×2行程度まで。それ以上なら箱を広げる
- 線は `edgeStyle=orthogonalEdgeStyle` を基本にする。線の交差が少なくなるよう、先に配置を直す
- 1ページの要素は30個程度まで。それ以上ならページを分ける
- 凡例は右下か下に置く
- 背景の枠（層の帯など）の上に箱を置くときは、枠をコンテナ（swimlane）にして、箱を子要素にする

## スタイル辞書
| 用途 | style |
|---|---|
| 標準の箱 | `rounded=1;whiteSpace=wrap;html=1;arcSize=10;` |
| 角の箱 | `rounded=0;whiteSpace=wrap;html=1;` |
| DB | `shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;size=10;` |
| 人・アクター | `shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;`（30×60） |
| 書類・ファイル | `shape=document;whiteSpace=wrap;html=1;boundedLbl=1;size=0.2;` |
| 外部システム | `rounded=0;whiteSpace=wrap;html=1;dashed=1;fillColor=#F5F5F5;strokeColor=#666666;` |
| 開始・終了 | `ellipse;whiteSpace=wrap;html=1;aspect=fixed;`（40×40） |
| 分岐 | `rhombus;whiteSpace=wrap;html=1;`（80×60） |
| グループ枠 | `swimlane;whiteSpace=wrap;html=1;startSize=26;fillColor=none;dashed=1;` |
| 横向きレーン | `swimlane;horizontal=0;whiteSpace=wrap;html=1;startSize=40;` |
| 文字だけ | `text;html=1;align=left;verticalAlign=middle;whiteSpace=wrap;` |
| 注記 | `shape=note;whiteSpace=wrap;html=1;size=14;fillColor=#FFF9C4;strokeColor=#B3A000;` |
| 線：同期（API等） | `edgeStyle=orthogonalEdgeStyle;html=1;endArrow=block;endFill=1;` |
| 線：非同期・ファイル | 上に `dashed=1;` を足す |
| 線：双方向 | 上に `startArrow=block;startFill=1;` を足す |

### 色（EAの層）
| 区分 | fillColor | strokeColor |
|---|---|---|
| ビジネス層 | #FFF2CC | #D6B656 |
| アプリケーション層 | #DAE8FC | #6C8EBF |
| データ層 | #E1D5E7 | #9673A6 |
| テクノロジー層 | #D5E8D4 | #82B366 |
| 外部・社外 | #F5F5F5 | #666666 |
| 強調・課題 | #F8CECC | #B85450 |

### 状態（層の色とぶつからないよう、線で表す）
| 状態 | 足すstyle |
|---|---|
| 既存（変更なし） | なし |
| 新規 | `strokeWidth=3;` |
| 改修 | `strokeWidth=2;strokeColor=#D79B00;` |
| 廃止 | `dashed=1;opacity=50;` |

### クラウドのアイコン
draw.io 標準ライブラリの図形名を使う。**名前が分からないアイコンは推測で書かず、標準の箱にラベル（例：「Amazon S3」）を付ける。** 書き出した PNG でアイコンが表示されていなければ、箱に置き換える。
- AWS（aws4）
  - `sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#ED7100;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.lambda;`
  - resIcon の例：`ec2`、`lambda`、`s3`、`rds`、`dynamodb`、`api_gateway`、`cloudfront`
  - fillColor はカテゴリの色：コンピュート #ED7100／ストレージ #7AA116／DB #C925D1／ネットワーク #8C4FFF／アプリ統合 #E7157B
  - AWS Cloud の枠：`shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_aws_cloud_alt;strokeColor=#232F3E;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#232F3E;dashed=0;html=1;`
- Azure（azure2）
  - `image;aspect=fixed;html=1;points=[];align=center;image=img/lib/azure2/compute/Function_Apps.svg;`
  - 例：`img/lib/azure2/compute/Virtual_Machine.svg`、`img/lib/azure2/databases/SQL_Database.svg`、`img/lib/azure2/storage/Storage_Accounts.svg`

## 図ごとの型
| 図 | 配置の型 |
|---|---|
| システム全体構成図 | 層を横の帯（レーン）にする。上から：チャネル → 業務アプリ → 連携基盤 → データ基盤。社外システムは右端の列 |
| クラウド構成図 | 外から内へ入れ子にする：クラウド → リージョン → VPC → サブネット。利用者は左、外部連携は右 |
| 業務フロー | 横のレーン＝部署・役割・システム。時間は左→右 |
| C4 Context | 中央に対象システム、周りに利用者と外部システム |
| C4 Container | 対象システムの枠の中に、アプリ・DB・バッチを置く |
| データフロー | 左に発生源、中央に処理・連携、右に利用先 |
| 組織図・ツリー | 上→下。同じ階層は同じ y 座標 |
| ER図（概念レベル） | 主要なエンティティを中心に配置し、属性は value に `&lt;br&gt;` で並べる |

## 書き出し（PNG／SVG／PDF）
draw.io デスクトップ版のコマンドラインを使う。
```powershell
# Windows（標準のインストール先）
& "C:\Program Files\draw.io\draw.io.exe" -x -f png -s 2 -b 20 -o out.png diagram.drawio
# 全ページを PDF に
& "C:\Program Files\draw.io\draw.io.exe" -x -f pdf -a -o out.pdf diagram.drawio
# 指定したページだけ（0から数える）
& "C:\Program Files\draw.io\draw.io.exe" -x -f png -p 1 -o page2.png diagram.drawio
```
- macOS：`/Applications/draw.io.app/Contents/MacOS/draw.io`　Linux：`drawio`
- `-e` を付けると PNG に図のデータが埋め込まれ、その PNG を draw.io で再編集できる
- draw.io が入っていなければ書き出しは省き、「.drawio ファイルは draw.io または VS Code の Draw.io Integration 拡張機能で開けます」と伝える

## 仕上げのチェック
- [ ] validate_drawio.py でエラーがない
- [ ] PNG で、重なり・文字のはみ出し・線の交差がない
- [ ] 凡例がある（色・線の種類・状態の意味）
- [ ] タイトル・作成日・版がある
- [ ] 同じ種類のものは同じ形・同じ色になっている
- [ ] 一覧表（システム一覧、IF一覧など）と図の要素が一致している
