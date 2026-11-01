"""Engineering role bindings and cross-environment distribution regressions."""
import json
from pathlib import Path
import sys
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from lib_skills import load_claude_agents, load_skills, strip_namespace


class EngineeringTest(unittest.TestCase):
    def test_roles_have_five_shared_and_five_specialist_skills(self):
        agents = load_claude_agents()
        shared = {'inspect-engineering-context', 'plan-engineering-change',
                  'review-engineering-change', 'diagnose-engineering-failure',
                  'handoff-engineering-work'}
        specialized = []
        for role in ('frontend-engineer', 'backend-engineer', 'infrastructure-engineer'):
            refs = {strip_namespace(s) for s in agents[role]['meta']['skills']}
            self.assertTrue(shared <= refs)
            self.assertEqual(10, len(refs))
            specialized.extend(refs - shared)
        self.assertEqual(15, len(set(specialized)))
        for name in shared | set(specialized):
            body = load_skills()[name]['body']
            for heading in ('必要入力', '手順', '成果物', '完了条件', '連携条件', '失敗時'):
                self.assertIn('## ' + heading, body, name)

    def test_generated_codex_and_claude_keep_role_instructions(self):
        for role in ('frontend-engineer', 'backend-engineer', 'infrastructure-engineer'):
            agent = load_claude_agents()[role]
            cfg = tomllib.loads((ROOT / '.codex/agents' / (role + '.toml')).read_text())
            self.assertEqual(role, cfg['name'])
            self.assertIn(agent['body'].strip(), cfg['developer_instructions'])
            claude = ROOT / 'plugins/claude/consulting-agents/agents' / (role + '.md')
            self.assertEqual(agent['file'].read_bytes(), claude.read_bytes())

    def test_router_discovers_engineering_and_all_sources_are_traced(self):
        plugin = ROOT / 'plugins/openai/nanaki11-consulting-toolkit'
        router = (plugin / 'skills/consulting-agent-router/SKILL.md').read_text()
        inventory = json.loads((plugin / 'SOURCE_MANIFEST.json').read_text())
        for role in ('frontend-engineer', 'backend-engineer', 'infrastructure-engineer'):
            self.assertIn(role, router)
            agent = load_claude_agents()[role]
            self.assertIn(agent['file'].relative_to(ROOT).as_posix(), inventory['sha256'])
            for ref in agent['meta']['skills']:
                name = strip_namespace(ref)
                self.assertTrue((plugin / 'skills' / name / 'SKILL.md').is_file())


if __name__ == '__main__':
    unittest.main()
