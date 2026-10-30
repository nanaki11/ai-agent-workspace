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
from lib_skills import ROOT, SKILLS_DIR, RULES_DIR, load_skills, load_claude_agents, strip_namespace

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


def build(legacy_manifest=None):
    subprocess.run([sys.executable, str(ROOT / 'scripts/generate.py'), '--check'], check=True)
    out = DIST / NAME
    if out.exists():
        shutil.rmtree(out)
    (out / '.codex-plugin').mkdir(parents=True)
    manifest = {
        'name': NAME, 'version': '1.1.0', 'skills': './skills/',
        'description': '21のコンサルティングスキルの全文・資源と4つの専門家役割。GitHubを正本とする。',
        'interface': {
            'displayName': 'Consulting Toolkit (nanaki11)',
            'shortDescription': '戦略・業務改革・IT・PMOの分析と提出前検証',
            'longDescription': 'スキル原本を要約せず同梱し、判断事項、根拠、引き継ぎ、品質ゲートを共通化。外部スライド資源と実行ツールは別途必要。',
            'category': 'Productivity', 'capabilities': ['Research', 'Analysis', 'Documents']}}
    if legacy_manifest is not None:
        manifest = copy.deepcopy(legacy_manifest)
        manifest['version'] = '1.1.0'
    portable = portable_manifest(manifest)
    # Keep older clients consistent with the effective portable interface.
    manifest['interface'] = copy.deepcopy(portable['extensions']['com.openai'].get('interface', {}))
    (out / 'plugin.json').write_text(json.dumps(portable, ensure_ascii=False, indent=2)+'\n')
    (out / '.codex-plugin/plugin.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    (out / 'README.md').write_text(
        '# Consulting Toolkit\n'
        'Source: https://github.com/nanaki11/ai-agent-workspace\n'
        'Includes 21 full skill definitions, their repository-owned resources, and four expert roles through a router.\n'
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
    for f in sorted(RULES_DIR.glob('*.md')):
        shutil.copy2(f, refs / f.name)
        sources[f.relative_to(ROOT).as_posix()] = hashlib.sha256(f.read_bytes()).hexdigest()
    text = '''---
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
'''
    for name, a in load_claude_agents().items():
        shutil.copy2(a['file'], refs / a['file'].name)
        sources[a['file'].relative_to(ROOT).as_posix()] = hashlib.sha256(a['file'].read_bytes()).hexdigest()
        names = ', '.join(strip_namespace(x) for x in a['meta'].get('skills', []))
        text += f"- [{name}](references/{a['file'].name}): {a['meta']['description']} 適用スキル: {names}\n"
    (router / 'SKILL.md').write_text(text)
    rev = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=all'], cwd=ROOT, text=True).strip())
    inventory = {'repository': 'https://github.com/nanaki11/ai-agent-workspace',
                 'source_commit': rev, 'working_tree_dirty': dirty,
                 'sha256': sources,
                 'external_dependencies': [{'name': 'carnot-tech/consulting-pptx-skill',
                    'commit': '5d3b048e944f237c26690ed5f624d7773b302d96', 'bundled': False}]}
    (out / 'SOURCE_MANIFEST.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2)+'\n')
    archive = DIST / (NAME + '.zip')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in sorted(out.rglob('*')):
            if f.is_file():
                info = zipfile.ZipInfo(f.relative_to(DIST).as_posix(), (2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, f.read_bytes())
    print(f'{archive.relative_to(ROOT)}: {len(load_skills())} full skills + router; dirty={dirty}')
    return out

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--legacy-manifest', type=Path, help='Existing plugin metadata to preserve for an update (never commit private metadata)')
    args = parser.parse_args()
    build(json.loads(args.legacy_manifest.read_text()) if args.legacy_manifest else None)
