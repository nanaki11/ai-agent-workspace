#!/usr/bin/env python3
"""draw.io (.drawio) ファイルの構造チェック。

使い方: python validate_drawio.py diagram.drawio [more.drawio ...]

エラー（必ず直す）:
  id の重複・欠落、必須セル 0/1 の欠落、存在しない parent/source/target、
  図形の座標・サイズの不正
警告（内容を見て判断する）:
  浮いた線、兄弟図形の重なり、親子関係のない包含、文字のはみ出しの可能性

エラーが1件でもあれば終了コード 1 を返す。
"""
import base64
import math
import re
import sys
import unicodedata
import urllib.parse
import xml.etree.ElementTree as ET
import zlib


def load_pages(path):
    root = ET.parse(path).getroot()
    if root.tag == "mxGraphModel":
        return [("page-1", root)]
    pages = []
    for d in root.iter("diagram"):
        name = d.get("name") or d.get("id") or "?"
        model = d.find("mxGraphModel")
        if model is None and (d.text or "").strip():
            # 圧縮形式（base64 + deflate + URLエンコード）
            raw = zlib.decompress(base64.b64decode(d.text.strip()), -15)
            model = ET.fromstring(urllib.parse.unquote(raw.decode("utf-8")))
        if model is not None:
            pages.append((name, model))
    return pages


def parse_style(style):
    out = {}
    for part in (style or "").split(";"):
        part = part.strip()
        if not part:
            continue
        if "=" in part:
            k, v = part.split("=", 1)
            out[k] = v
        else:
            out[part] = True  # ellipse, swimlane, text など
    return out


def plain_text(value):
    s = re.sub(r"<br\s*/?>", "\n", value or "", flags=re.I)
    s = re.sub(r"</(div|p)>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    for a, b in (("&nbsp;", " "), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&amp;", "&")):
        s = s.replace(a, b)
    return s.strip()


def text_width(line, font_size):
    w = 0.0
    for ch in line:
        wide = unicodedata.east_asian_width(ch) in ("W", "F")
        w += font_size if wide else font_size * 0.6
    return w


def collect_cells(root):
    cells = list(root.findall("mxCell"))
    # UserObject / object は中に mxCell を持ち、id と label を外側に持つ
    for obj in list(root.findall("UserObject")) + list(root.findall("object")):
        c = obj.find("mxCell")
        if c is not None:
            c.set("id", obj.get("id", ""))
            c.set("value", obj.get("label", ""))
            cells.append(c)
    return cells


def check_page(name, model):
    errors, warns = [], []
    p = f"[{name}]"
    root = model.find("root")
    if root is None:
        return [f"{p} <root> がありません"], warns, (0, 0)

    ids = {}
    for c in collect_cells(root):
        cid = c.get("id")
        if not cid:
            errors.append(f"{p} id のない mxCell があります")
            continue
        if cid in ids:
            errors.append(f"{p} id が重複しています: {cid}")
        ids[cid] = c
    for must in ("0", "1"):
        if must not in ids:
            errors.append(f'{p} 必須セル id="{must}" がありません')

    edge_ids = {cid for cid, c in ids.items() if c.get("edge") == "1"}
    boxes = {}  # cid -> (parent, x, y, w, h, style)
    n_vertex = 0

    for cid, c in ids.items():
        parent = c.get("parent")
        if cid != "0" and parent not in ids:
            errors.append(f"{p} {cid}: parent '{parent}' が存在しません")

        if c.get("edge") == "1":
            for end in ("source", "target"):
                ref = c.get(end)
                if not ref:
                    warns.append(f"{p} 線 {cid}: {end} が未指定です（浮いた線）")
                elif ref not in ids:
                    errors.append(f"{p} 線 {cid}: {end} '{ref}' が存在しません")
            continue

        if c.get("vertex") != "1":
            continue
        n_vertex += 1
        g = c.find("mxGeometry")
        if g is None:
            errors.append(f"{p} 図形 {cid}: mxGeometry がありません")
            continue
        if parent in edge_ids or g.get("relative") == "1":
            continue  # 線のラベルなど、相対座標の図形は対象外
        try:
            x, y = float(g.get("x", 0)), float(g.get("y", 0))
            w, h = float(g.get("width", 0)), float(g.get("height", 0))
        except ValueError:
            errors.append(f"{p} 図形 {cid}: 座標・サイズが数値ではありません")
            continue
        if w <= 0 or h <= 0:
            errors.append(f"{p} 図形 {cid}: 幅または高さが 0 です")
            continue

        st = parse_style(c.get("style"))
        boxes[cid] = (parent, x, y, w, h, st)

        # 文字のはみ出しの目安
        label = plain_text(c.get("value"))
        if not label or st.get("verticalLabelPosition") == "bottom" or "swimlane" in st:
            continue
        font = float(st.get("fontSize", 12))
        inner_w = max(w - 10, 1)
        wrap = st.get("whiteSpace") == "wrap"
        lines = 0
        for line in label.split("\n"):
            tw = text_width(line, font)
            if wrap:
                lines += max(1, math.ceil(tw / inner_w))
            else:
                lines += 1
                if tw > w:
                    warns.append(f"{p} 図形 {cid}: 文字が横にはみ出す可能性があります（whiteSpace=wrap なし）")
        if lines * font * 1.25 > h + 2:
            warns.append(f"{p} 図形 {cid}: 文字が縦にはみ出す可能性があります（約{lines}行、高さ{int(h)}px）")

    # 同じ親を持つ図形どうしの重なり
    by_parent = {}
    for cid, b in boxes.items():
        if "text" in b[5]:
            continue
        by_parent.setdefault(b[0], []).append((cid, b))
    for siblings in by_parent.values():
        for i in range(len(siblings)):
            a_id, (_, ax, ay, aw, ah, _) = siblings[i]
            for j in range(i + 1, len(siblings)):
                b_id, (_, bx, by, bw, bh, _) = siblings[j]
                ox = min(ax + aw, bx + bw) - max(ax, bx)
                oy = min(ay + ah, by + bh) - max(ay, by)
                if ox <= 4 or oy <= 4:
                    continue
                if ax <= bx and ay <= by and ax + aw >= bx + bw and ay + ah >= by + bh:
                    warns.append(f"{p} {a_id} が {b_id} を囲んでいますが親子関係がありません（背景枠なら無視可。コンテナなら parent を設定）")
                elif bx <= ax and by <= ay and bx + bw >= ax + aw and by + bh >= ay + ah:
                    warns.append(f"{p} {b_id} が {a_id} を囲んでいますが親子関係がありません（背景枠なら無視可。コンテナなら parent を設定）")
                else:
                    warns.append(f"{p} 図形が重なっています: {a_id} と {b_id}")

    return errors, warns, (n_vertex, len(edge_ids))


def main(paths):
    if not paths:
        print(__doc__)
        return 2
    failed = False
    for path in paths:
        try:
            pages = load_pages(path)
        except (ET.ParseError, OSError, zlib.error, ValueError) as e:
            print(f"[NG] {path}: 読み込めません: {e}")
            failed = True
            continue
        if not pages:
            print(f"[NG] {path}: ページ（diagram）がありません")
            failed = True
            continue
        total_err = 0
        for name, model in pages:
            errors, warns, (nv, ne) = check_page(name, model)
            total_err += len(errors)
            print(f"--- {path} / ページ「{name}」: 図形 {nv} 個、線 {ne} 本")
            for e in errors:
                print(f"  [ERROR] {e}")
            for w in warns:
                print(f"  [WARN]  {w}")
        if total_err:
            failed = True
            print(f"[NG] {path}: エラー {total_err} 件")
        else:
            print(f"[OK] {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
