#!/usr/bin/env python3
"""全文・資源・専門家役割を保持するChatGPT向け配布物。公開・インストールは行わない。"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_skills import ROOT, SKILLS_DIR, RULES_DIR, load_skills, load_claude_agents, strip_namespace, read_version  # noqa: E402

DIST = ROOT / 'dist' / 'chatgpt'
NAME = 'nanaki11-consulting-toolkit'


def portable_manifest(legacy):
    """Map legacy metadata without dropping interface fields or component declarations."""
    allowed = {'name', 'version', 'description', 'author', 'homepage', 'repository',
               'license', 'keywords', 'interface', 'extensions', 'skills', 'apps',
               'hooks', 'requires_local_executor', 'publicationPolicy', 'id'}
    unknown = set(legacy) - allowed
    if unknown:
        raise ValueError(f'Unsupported legacy fields: {sorted(unknown)}')
    if legacy.get('name') != NAME or legacy.get('skills', './skills/') != './skills/':
        raise ValueError('Plugin identity or custom skill path requires reconciliation')
    result = {'$schema': 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json'}
    for key in ('name', 'version', 'description', 'author', 'homepage', 'repository', 'license', 'keywords'):
        if key in legacy:
            result[key] = copy.deepcopy(legacy[key])
    result['extensions'] = copy.deepcopy(legacy.get('extensions', {}))
    ext = result['extensions'].setdefault('com.openai', {})
    for key in ('interface', 'apps', 'hooks', 'requires_local_executor', 'publicationPolicy', 'id'):
        if key in legacy:
            if key in ext and ext[key] != legacy[key]:
                raise ValueError(f'Conflicting OpenAI field: {key}')
            ext[key] = copy.deepcopy(legacy[key])
    interface = ext.get('interface', {})
    if 'default_prompt' in interface:
        value = interface['default_prompt']
        if 'defaultPrompt' in interface and interface['defaultPrompt'] != value:
            raise ValueError('Conflicting starter prompts')
        interface['defaultPrompt'] = interface.pop('default_prompt')
    return result


def build(legacy_manifest=None, dest=DIST, build_info=True, archive=True, precheck=True, quiet=False):
    """dest/NAME にプラグインを作る。build_info=False は Git 管理用（コミット等の可変情報を入れない）。"""
    if precheck:
        subprocess.run([sys.executable, str(ROOT / 'scripts/generate.py'), '--check'], check=True)
    version = read_version()
    skill_count, agent_count = len(load_skills()), len(load_claude_agents())
    out = dest / NAME
    if out.exists():
        shutil.rmtree(out)
    (out / '.codex-plugin').mkdir(parents=True)
    manifest = {
        'name': NAME, 'version': version, 'skills': './skills/',
        'description': f'{skill_count}のコンサルティング・開発スキルの全文・資源と{agent_count}つの専門家役割。GitHubを正本とする。',
        'interface': {
            'displayName': 'Consulting Toolkit (nanaki11)',
            'shortDescription': '戦略・業務改革・IT・PMO・アプリ開発と品質検証',
            'longDescription': 'スキル原本を要約せず同梱し、判断事項、根拠、引き継ぎ、品質ゲートを共通化。外部スライド資源と実行ツールは別途必要。',
            'category': 'Productivity', 'capabilities': ['Research', 'Analysis', 'Documents']}}
    if legacy_manifest is not None:
        manifest = copy.deepcopy(legacy_manifest)
        manifest['version'] = version
    portable = portable_manifest(manifest)
    # Keep older clients consistent with the effective portable interface.
    manifest['interface'] = copy.deepcopy(portable['extensions']['com.openai'].get('interface', {}))
    (out / 'plugin.json').write_text(json.dumps(portable, ensure_ascii=False, indent=2)+'\n')
    (out / '.codex-plugin/plugin.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    (out / 'README.md').write_text(
        '# Consulting Toolkit\n'
        'Source: https://github.com/nanaki11/ai-agent-workspace\n'
        f'Includes {skill_count} full skill definitions, their repository-owned resources, and {agent_count} expert roles through a router.\n'
        'External slide-generation dependencies and provider tools are not bundled. See SOURCE_MANIFEST.json for source hashes.\n')
    sources = {}
    for name, skill in load_skills().items():
        shutil.copytree(skill['dir'], out / 'skills' / name,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for f in sorted(skill['dir'].rglob('*')):
            if f.is_file() and '__pycache__' not in f.parts and f.suffix != '.pyc':
                sources[f.relative_to(ROOT).as_posix()] = hashlib.sha256(f.read_bytes()).hexdigest()
    router = out / 'skills/consulting-agent-router'
    refs = router / 'references'
    refs.mkdir(parents=True)
    for f in sorted(f for f in RULES_DIR.iterdir() if f.suffix in {'.md', '.json'}):
        shutil.copy2(f, refs / f.name)
        sources[f.relative_to(ROOT).as_posix()] = hashlib.sha256(f.read_bytes()).hexdigest()
    text = '''---
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
'''
    for name, a in load_claude_agents().items():
        shutil.copy2(a['file'], refs / a['file'].name)
        sources[a['file'].relative_to(ROOT).as_posix()] = hashlib.sha256(a['file'].read_bytes()).hexdigest()
        names = ', '.join(strip_namespace(x) for x in a['meta'].get('skills', []))
        text += f"- [{name}](references/{a['file'].name}): {a['meta']['description']} 適用スキル: {names}\n"
    (router / 'SKILL.md').write_text(text, encoding='utf-8')
    inventory = {'repository': 'https://github.com/nanaki11/ai-agent-workspace',
                 'version': version, 'sha256': sources,
                 'external_dependencies': [{'name': 'carnot-tech/consulting-pptx-skill',
                    'commit': '5d3b048e944f237c26690ed5f624d7773b302d96', 'bundled': False}]}
    dirty = None
    if build_info:
        rev = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        dirty = bool(subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=all'], cwd=ROOT, text=True).strip())
        inventory['source_commit'], inventory['working_tree_dirty'] = rev, dirty
    (out / 'SOURCE_MANIFEST.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2)+'\n')
    if not archive:
        return out
    archive_path = dest / (NAME + '.zip')
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in sorted(out.rglob('*')):
            if f.is_file():
                info = zipfile.ZipInfo(f.relative_to(dest).as_posix(), (2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, f.read_bytes())
    if not quiet:
        print(f'{archive_path.relative_to(ROOT)}: {len(load_skills())} full skills + router; version={version}; dirty={dirty}')
    return out

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--legacy-manifest', type=Path, help='Existing plugin metadata to preserve for an update (never commit private metadata)')
    args = parser.parse_args()
    build(json.loads(args.legacy_manifest.read_text()) if args.legacy_manifest else None)
