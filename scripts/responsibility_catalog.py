"""Validate artifact ownership; route classified work, not raw natural language."""
from __future__ import annotations
import json
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1] / 'common/rules/agent-responsibilities.json'


def load_catalog():
    return json.loads(CATALOG.read_text(encoding='utf-8'))


def validate_catalog(catalog, agent_names, skill_names):
    errors = []
    roles = catalog.get('roles', {})
    if set(roles) != set(agent_names):
        errors.append('catalog roles must exactly match installed agent definitions')
    if not catalog.get('scope') or not catalog.get('external_responsibilities'):
        errors.append('scope and external responsibilities must be explicit')
    if {v.get('layer') for v in roles.values()} != {'direction', 'delivery', 'governance'}:
        errors.append('role layers must distinguish direction, delivery and governance')
    seen = set()
    for work in catalog.get('work_types', []):
        key = work.get('id')
        if not isinstance(key, str) or not key or key in seen:
            errors.append('work type IDs must be nonblank and unique')
        seen.add(key)
        owner = work.get('owner')
        if not isinstance(owner, str) or owner not in roles:
            errors.append(f'{key}: exactly one known artifact owner is required')
        if not work.get('output') or not work.get('skills'):
            errors.append(f'{key}: output and executable skills are required')
        for skill in work.get('skills', []):
            if skill not in skill_names:
                errors.append(f'{key}: unknown skill {skill}')
    if not seen:
        errors.append('work types cannot be empty')
    shared = catalog.get('shared_skills', [])
    classified = list(shared)
    specialists = catalog.get('specialist_skills', {})
    if set(specialists) != set(roles):
        errors.append('specialist skill groups must match roles')
    for names in specialists.values():
        classified.extend(names)
    if len(classified) != len(set(classified)) or set(classified) != set(skill_names):
        errors.append('skill management categories must cover all skills once')
    for key, role in catalog.get('routing', {}).items():
        if role not in roles:
            errors.append(f'{key}: unknown routing fallback {role}')
    for key in ('mixed_fallback', 'unknown_production', 'unknown_development'):
        if key not in catalog.get('routing', {}):
            errors.append(f'{key}: missing routing rule')
    return errors


def route_work_package(work_types, *, explicit_owner=None, primary_work_type=None, catalog=None):
    """Return one coordinator while preserving artifact owners; unknown work fails."""
    c = catalog if catalog is not None else load_catalog()
    work = {w['id']: w for w in c['work_types']}
    keys = list(dict.fromkeys(work_types))
    if not keys or any(k not in work for k in keys):
        raise ValueError('unclassified work: clarify scope before routing')
    owners = {k: work[k]['owner'] for k in keys}
    if explicit_owner is not None:
        if explicit_owner not in c['roles']:
            raise ValueError('unknown explicitly requested role')
        coordinator = explicit_owner
    elif 'unknown-production-incident' in keys:
        coordinator = c['routing']['unknown_production']
    elif primary_work_type is not None:
        if primary_work_type not in owners:
            raise ValueError('primary work type must belong to the work package')
        coordinator = owners[primary_work_type]
    elif len(set(owners.values())) == 1:
        coordinator = next(iter(owners.values()))
    else:
        coordinator = c['routing']['mixed_fallback']
    return {'coordinator': coordinator, 'artifact_owners': owners}
