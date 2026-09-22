"""Build a read-only dependency plan from validated manifests and target facts.

``plan`` takes manifests keyed by ippin ID, requested IDs, and the same target
facts as selection.select. Optional provider_choices maps outcomes to ippin IDs;
external_outcomes maps outcomes to JSON-compatible evidence already verified by
the caller for this target. It does not inspect machines or execute instructions.
"""

from copy import deepcopy
from graphlib import CycleError, TopologicalSorter

from selection import select


def plan(manifests, requested, target, *, provider_choices=None, external_outcomes=None):
    """Return nodes, outcome bindings, labelled edges, issues, and execution order.

    Only a complete plan has an order. Complete means structurally resolved, not
    installed or verified. File validation and recipe snapshotting belong to the
    caller; this function operates only on the supplied in-memory contents.
    """
    requested = sorted(set(requested))
    choices = provider_choices or {}
    external = external_outcomes or {}
    selections = {name: select(data, target) for name, data in sorted(manifests.items())}
    providers = {}
    for name, data in sorted(manifests.items()):
        for outcome in data['provides']:
            providers.setdefault(outcome, []).append(name)

    def choose(outcome):
        candidates = providers.get(outcome, [])
        if outcome in choices:
            name = choices[outcome]
            if name not in candidates or selections[name]['status'] == 'unsupported':
                return None, {'kind': 'invalid-provider', 'provider': name}
            return {'provider': name}, None

        eligible = [name for name in candidates if selections[name]['status'] != 'unsupported']
        preferred = [name for name in eligible if name in requested]
        if not preferred and outcome in external:
            return {'external': external[outcome]}, None
        eligible = preferred or eligible
        unknown = [name for name in eligible if selections[name]['status'] == 'unresolved']
        if unknown:
            return None, {
                'kind': 'unresolved-provider', 'candidates': eligible,
                'missing_facts': sorted({fact for name in unknown
                                         for fact in selections[name]['missing_facts']}),
            }
        if len(eligible) == 1:
            return {'provider': eligible[0]}, None
        return None, {'kind': 'ambiguous-provider' if eligible else 'missing-provider',
                      'candidates': eligible}

    nodes, bindings, problems, origins = {}, {}, {}, {}
    pending = set(requested)
    while pending:
        name = min(pending)
        pending.remove(name)
        if name in nodes:
            continue
        if name not in manifests:
            nodes[name] = {'requested': True, 'status': 'missing', 'requires': []}
            continue
        selection = selections[name]
        node = nodes[name] = {**selection, 'requested': name in requested, 'requires': []}
        if selection['status'] != 'selected':
            continue
        route = next(item for item in manifests[name]['routes'] if item['id'] == selection['route'])
        node['interactive'] = route['interactive']
        parts = [(None, route)] + [(item['id'], item) for item in route.get('overlays', [])
                                  if item['id'] in selection['overlays']]
        for overlay, part in parts:
            for outcome in part.get('requires', []):
                if outcome not in node['requires']:
                    node['requires'].append(outcome)
                origins.setdefault(outcome, []).append({
                    'consumer': name, 'route': route['id'], 'overlay': overlay,
                })
                if outcome not in bindings and outcome not in problems:
                    binding, problem = choose(outcome)
                    if problem:
                        problems[outcome] = problem
                    else:
                        bindings[outcome] = binding
                provider = bindings.get(outcome, {}).get('provider')
                if provider is not None and provider not in nodes:
                    pending.add(provider)

    # An implicitly added provider may also provide an outcome previously bound
    # to existing readiness. Wait for its new verification, regardless of traversal order.
    for outcome, binding in list(bindings.items()):
        if 'external' not in binding:
            continue
        included = [name for name in providers.get(outcome, []) if name in nodes]
        if len(included) == 1:
            bindings[outcome] = {'provider': included[0]}
        elif included:
            del bindings[outcome]
            problems[outcome] = {'kind': 'ambiguous-provider', 'candidates': included}

    issues = []
    for name, node in sorted(nodes.items()):
        if node['status'] != 'selected':
            issues.append({'kind': node['status'], 'ippin': name,
                           'missing_facts': node.get('missing_facts', [])})
    for outcome, problem in sorted(problems.items()):
        issues.append({**problem, 'outcome': outcome, 'required_by': origins[outcome]})

    edges = []
    dependencies = {name: set() for name in sorted(nodes)}
    for outcome, binding in sorted(bindings.items()):
        if 'provider' not in binding:
            continue
        provider = binding['provider']
        for origin in origins[outcome]:
            edges.append({'provider': provider, 'outcome': outcome, **origin})
            dependencies[origin['consumer']].add(provider)
    try:
        order = list(TopologicalSorter({name: sorted(deps)
                                       for name, deps in dependencies.items()}).static_order())
    except CycleError as error:
        cycle = error.args[1]
        pairs = set(zip(cycle, cycle[1:]))
        issues.append({'kind': 'cycle', 'chain': cycle,
                       'edges': [edge for edge in edges
                                 if (edge['provider'], edge['consumer']) in pairs]})
        order = []

    return deepcopy({
        'status': 'unresolved' if issues else 'complete',
        'requested': requested, 'target': target,
        'nodes': dict(sorted(nodes.items())), 'bindings': dict(sorted(bindings.items())),
        'edges': edges, 'issues': issues, 'order': [] if issues else order,
    })
