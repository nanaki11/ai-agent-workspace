"""配布時の情報欠落と品質規約の同期漏れを検出する回帰テスト。"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from lib_skills import load_skills, load_claude_agents, load_packages
from build_chatgpt_package import build, portable_manifest, DIST, NAME

class DistributionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = build()
        subprocess.run([sys.executable, str(ROOT / 'scripts/build_claude_packages.py')], check=True)

    def test_chatgpt_preserves_every_source_byte(self):
        manifest = json.loads((self.out / 'SOURCE_MANIFEST.json').read_text())
        for name, skill in load_skills().items():
            for src in skill['dir'].rglob('*'):
                if src.is_file() and '__pycache__' not in src.parts and src.suffix != '.pyc':
                    dst = self.out / 'skills' / name / src.relative_to(skill['dir'])
                    self.assertEqual(src.read_bytes(), dst.read_bytes(), str(src))
                    self.assertEqual(hashlib.sha256(src.read_bytes()).hexdigest(), manifest['sha256'][src.relative_to(ROOT).as_posix()])
        self.assertEqual(21, len(load_skills()))
        self.assertEqual(22, len(list((self.out / 'skills').glob('*/SKILL.md'))))

    def test_roles_and_shared_rules_are_self_contained(self):
        for a in load_claude_agents().values():
            dst = self.out / 'skills/consulting-agent-router/references' / a['file'].name
            self.assertEqual(a['file'].read_bytes(), dst.read_bytes())
        source = (ROOT / 'common/rules/consulting-delivery-standard.md').read_text()
        for name, skill in load_skills().items():
            self.assertIn('references/consulting-delivery-standard.md', (skill['dir'] / 'SKILL.md').read_text())
            self.assertEqual(source, (skill['dir'] / 'references/consulting-delivery-standard.md').read_text().split('\n', 1)[1])

    def test_claude_packages_include_full_skills_and_references(self):
        for package in load_packages()['packages']:
            for name in package['skills']:
                archive = ROOT / 'dist/claude' / ((package['name'] if package['type'] == 'plugin' else name) + '.zip')
                prefix = package['name'] + '/skills/' + name if package['type'] == 'plugin' else name
                with zipfile.ZipFile(archive) as z:
                    for src in load_skills()[name]['dir'].rglob('*'):
                        if src.is_file() and '__pycache__' not in src.parts and src.suffix != '.pyc':
                            self.assertEqual(src.read_bytes(), z.read(prefix + '/' + src.relative_to(load_skills()[name]['dir']).as_posix()))

    def test_generated_drift_is_rejected(self):
        p = next(iter(load_skills().values()))['dir'] / 'references/consulting-delivery-standard.md'
        original = p.read_bytes()
        try:
            p.write_text('stale\n')
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/generate.py'), '--check'], capture_output=True)
            self.assertEqual(1, result.returncode)
        finally:
            p.write_bytes(original)

    def test_portable_migration_preserves_metadata_and_prompt_order(self):
        legacy = {'name': NAME, 'version': '1.0.0', 'skills': './skills/',
                  'author': {'name': 'Owner'},
                  'interface': {'displayName': 'Existing name',
                                'defaultPrompt': ['First', 'Second', 'Third'],
                                'capabilities': ['Analysis']},
                  'extensions': {'com.openai': {'requires_local_executor': False}}}
        portable = portable_manifest(legacy)
        self.assertEqual(legacy['interface'], portable['extensions']['com.openai']['interface'])
        self.assertEqual(legacy['author'], portable['author'])
        self.assertIs(False, portable['extensions']['com.openai']['requires_local_executor'])
        self.assertNotIn('skills', portable)
        self.assertEqual('https://agent-plugins.org/schemas/1.0.0/plugin.schema.json', portable['$schema'])

    def test_unknown_metadata_cannot_be_silently_dropped(self):
        with self.assertRaises(ValueError):
            portable_manifest({'name': NAME, 'unsupported': True})

    def test_archive_matches_built_files(self):
        with zipfile.ZipFile(DIST / (NAME + '.zip')) as z:
            for f in self.out.rglob('*'):
                if f.is_file():
                    self.assertEqual(f.read_bytes(), z.read(f.relative_to(DIST).as_posix()))

if __name__ == '__main__':
    unittest.main()
