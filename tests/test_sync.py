"""双方向同期（scripts/sync.py）の判定ロジックの回帰テスト。リポジトリのファイルは書き換えない。"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import sync  # noqa: E402

PLUGIN = ROOT / 'plugins/openai/nanaki11-consulting-toolkit'
CLAUDE = ROOT / 'plugins/claude'


class SyncTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.state = self.tmp / 'state.json'
        self._orig = sync.STATE_JSON
        sync.STATE_JSON = self.state

    def tearDown(self):
        sync.STATE_JSON = self._orig
        shutil.rmtree(self.tmp)

    def baseline(self, target):
        self.state.write_text(json.dumps({'targets': {target: {'files': sync.repo_hashes(target)}}}))

    def kinds(self, target, roots):
        files, warns = sync.target_files(roots)
        return {f: k for k, f in sync.classify(target, files)}, files, warns

    def test_generated_plugins_round_trip_to_sources(self):
        for target, roots in (('chatgpt', [PLUGIN]),
                              ('claude', [CLAUDE / 'consulting-agents', CLAUDE / 'consulting-pptx-skill'])):
            k, _, warns = self.kinds(target, roots)
            self.assertEqual({'same'}, set(k.values()), (target, warns))
            self.assertEqual(set(sync.scope(target)), set(k))

    def test_target_edit_is_imported_and_repo_edit_needs_reinstall(self):
        self.baseline('chatgpt')
        t = self.tmp / 'p'
        shutil.copytree(PLUGIN, t)
        (t / 'skills/kpi-design/SKILL.md').write_text('edited in ChatGPT\n')
        (t / 'skills/consulting-agent-router/references/pmo.md').write_text('edited role\n')
        k, files, _ = self.kinds('chatgpt', [t])
        self.assertEqual('target-changed', k['.agents/skills/kpi-design/SKILL.md'])
        self.assertEqual('target-changed', k['claude/plugins/consulting-agents/agents/pmo.md'])
        self.assertEqual(b'edited role\n', files['claude/plugins/consulting-agents/agents/pmo.md'])
        # リポジトリ側だけが新しい場合
        st = json.loads(self.state.read_text())
        st['targets']['chatgpt']['files']['.agents/skills/tech-selection/SKILL.md'] = 'old'
        self.state.write_text(json.dumps(st))
        (t / 'skills/tech-selection/SKILL.md').write_text('old-content\n')
        k, _, _ = self.kinds('chatgpt', [t])
        self.assertEqual('conflict', k['.agents/skills/tech-selection/SKILL.md'])

    def test_repo_newer_is_reported_as_repo_changed(self):
        self.baseline('chatgpt')
        st = json.loads(self.state.read_text())
        f = '.agents/skills/tech-selection/SKILL.md'
        t = self.tmp / 'p'
        shutil.copytree(PLUGIN, t)
        old = b'installed old version\n'
        (t / 'skills/tech-selection/SKILL.md').write_bytes(old)
        st['targets']['chatgpt']['files'][f] = sync.sha_bytes(old)
        self.state.write_text(json.dumps(st))
        k, _, _ = self.kinds('chatgpt', [t])
        self.assertEqual('repo-changed', k[f])

    def test_no_baseline_is_not_silently_imported(self):
        t = self.tmp / 'p'
        shutil.copytree(PLUGIN, t)
        (t / 'skills/kpi-design/SKILL.md').write_text('x\n')
        k, _, _ = self.kinds('chatgpt', [t])
        self.assertEqual('unknown', k['.agents/skills/kpi-design/SKILL.md'])

    def test_standard_copy_maps_back_to_common_rules(self):
        self.baseline('claude')
        t = self.tmp / 'c'
        shutil.copytree(CLAUDE / 'consulting-agents', t)
        for p in t.glob('skills/*/references/consulting-delivery-standard.md'):
            p.write_text(sync.STANDARD_HEADER + 'new standard\n')
        k, files, warns = self.kinds('claude', [t, CLAUDE / 'consulting-pptx-skill'])
        # pptx 側は旧内容のままなので、写しの不一致を警告する
        self.assertTrue(any('写し' in w for w in warns))
        self.assertIn('common/rules/consulting-delivery-standard.md', files)

    def test_zip_slip_is_rejected(self):
        import zipfile
        z = self.tmp / 'bad.zip'
        with zipfile.ZipFile(z, 'w') as zf:
            zf.writestr('../evil.txt', 'x')
        with self.assertRaises(SystemExit):
            sync.unpack([z], self.tmp / 'out')


if __name__ == '__main__':
    unittest.main()
