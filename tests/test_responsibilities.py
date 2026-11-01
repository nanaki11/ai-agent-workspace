"""Guard against ambiguous ownership and loss of routing contracts in distribution."""
from copy import deepcopy
from itertools import permutations
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from lib_skills import load_claude_agents, load_skills
from responsibility_catalog import load_catalog, route_work_package, validate_catalog
import sync


class ResponsibilitiesTest(unittest.TestCase):
    def test_missing_or_shared_artifact_owner_is_rejected(self):
        c = load_catalog()
        for owner in (None, [], ['it-architect', 'infrastructure-engineer'], 'missing-role'):
            bad = deepcopy(c)
            bad['work_types'][0]['owner'] = owner
            self.assertTrue(validate_catalog(bad, load_claude_agents(), load_skills()))

    def test_missing_or_duplicate_skill_management_is_rejected(self):
        c = load_catalog()
        self.assertEqual([], validate_catalog(c, load_claude_agents(), load_skills()))
        for change in ('missing', 'duplicate'):
            bad = deepcopy(c)
            if change == 'missing':
                bad['shared_skills'].pop()
            else:
                bad['shared_skills'].append(bad['specialist_skills']['it-architect'][0])
            self.assertTrue(validate_catalog(bad, load_claude_agents(), load_skills()))

    def test_mixed_work_preserves_owners_and_is_order_independent(self):
        keys = ['frontend-implementation', 'backend-contract', 'infrastructure-delivery']
        for ordered in permutations(keys):
            result = route_work_package(ordered)
            self.assertEqual('it-architect', result['coordinator'])
            self.assertEqual({'frontend-implementation': 'frontend-engineer',
                              'backend-contract': 'backend-engineer',
                              'infrastructure-delivery': 'infrastructure-engineer'}, result['artifact_owners'])

    def test_primary_output_and_explicit_coordinator_take_precedence(self):
        keys = ['cutover-coordination', 'data-migration', 'infrastructure-delivery']
        self.assertEqual('pmo', route_work_package(keys, primary_work_type='cutover-coordination')['coordinator'])
        self.assertEqual('backend-engineer', route_work_package(keys, primary_work_type='data-migration')['coordinator'])
        self.assertEqual('infrastructure-engineer', route_work_package(keys, explicit_owner='infrastructure-engineer')['coordinator'])
        self.assertEqual('frontend-engineer', route_work_package(['frontend-design'])['coordinator'])

    def test_unknown_production_incident_has_one_initial_owner(self):
        keys = ['unknown-production-incident', 'backend-verification']
        self.assertEqual('infrastructure-engineer', route_work_package(keys, primary_work_type='backend-verification')['coordinator'])
        self.assertEqual('backend-engineer', route_work_package(['unknown-development-defect'])['coordinator'])

    def test_unclassified_work_and_invalid_overrides_are_not_silently_routed(self):
        for keys, kwargs in (([], {}), (['legal-opinion'], {}),
                             (['frontend-design'], {'explicit_owner': 'nonexistent'}),
                             (['frontend-design'], {'primary_work_type': 'data-migration'})):
            with self.assertRaises(ValueError):
                route_work_package(keys, **kwargs)

    def test_contract_round_trips_through_chatgpt_and_claude(self):
        for target, root in (('chatgpt', ROOT / 'plugins/openai/nanaki11-consulting-toolkit'),
                             ('claude', ROOT / 'plugins/claude/consulting-agents')):
            files, _ = sync.target_files([root])
            for name in ('agent-responsibilities.md', 'agent-responsibilities.json'):
                key = 'common/rules/' + name
                self.assertEqual((ROOT / key).read_bytes(), files[key], target)
                self.assertIn(key, sync.scope(target))

    def test_session_hook_loads_contract_within_output_limit(self):
        root = ROOT / 'plugins/claude/consulting-agents'
        hooks = json.loads((root / 'hooks/hooks.json').read_text())
        command = hooks['hooks']['SessionStart'][0]['hooks'][0]['command']
        result = subprocess.run(['bash', '-c', command], env={**os.environ, 'CLAUDE_PLUGIN_ROOT': str(root)},
                                capture_output=True, text=True, check=True)
        self.assertIn('主担当の決め方', result.stdout)
        self.assertIn('agent-responsibilities.json', result.stdout)
        self.assertLess(len(result.stdout), 10000)


if __name__ == '__main__':
    unittest.main()
