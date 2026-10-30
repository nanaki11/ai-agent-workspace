#!/usr/bin/env bash
# コミット前の機密情報チェック。1件でも検出したら終了コード 1。
#   1) gitleaks（あれば）  2) detect-secrets（あれば）  3) 正規表現による簡易チェック（常に実行）
set -uo pipefail
cd "$(dirname "$0")/.."
rc=0

if command -v gitleaks >/dev/null 2>&1; then
  echo "== gitleaks"
  gitleaks detect --no-git --source . --redact --no-banner -v || rc=1
else
  echo "== gitleaks: 未インストール（スキップ）"
fi

if command -v detect-secrets >/dev/null 2>&1; then
  echo "== detect-secrets"
  out=$(detect-secrets scan --all-files --exclude-files '^(\.git|dist)/' .)
  n=$(printf '%s' "$out" | python3 -c 'import json,sys;print(sum(len(v) for v in json.load(sys.stdin)["results"].values()))')
  printf '%s' "$out" | python3 -c 'import json,sys;[print(" ",f,r["type"],"line",r["line_number"]) for f,v in json.load(sys.stdin)["results"].items() for r in v]'
  echo "  検出: $n 件"; [ "$n" -eq 0 ] || rc=1
else
  echo "== detect-secrets: 未インストール（スキップ）"
fi

echo "== 正規表現チェック（APIキー・トークン・秘密鍵・個人情報の簡易検出）"
pat='(sk-[A-Za-z0-9_-]{20,}|sk-ant-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|xox[abpr]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|ya29\.[0-9A-Za-z_-]{20,}|(password|passwd|secret|api[_-]?key|access[_-]?token)\s*[:=]\s*["'\'']?[A-Za-z0-9/+_-]{8,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|0[789]0-?[0-9]{4}-?[0-9]{4})'
hits=$(grep -rInE "$pat" --exclude-dir=.git --exclude-dir=dist --exclude=scan_secrets.sh . || true)
# 許可リスト：公開URL内の文字列・コミット署名用のダミー等
allow='noreply@anthropic.com|example\.(com|org)'
hits=$(printf '%s\n' "$hits" | grep -vE "$allow" | sed '/^$/d' || true)
if [ -n "$hits" ]; then echo "$hits"; rc=1; else echo "  検出なし"; fi

[ $rc -eq 0 ] && echo "OK: 機密情報は検出されなかった" || echo "NG: 上記を確認すること"
exit $rc
