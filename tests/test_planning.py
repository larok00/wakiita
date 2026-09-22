"""Run with: python -B -m unittest discover -s tests"""

import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'plugins/wakiita/scripts'))
from planning import plan


def component(name, requires=(), *, provides=None, when=None, overlays=()):
    return {
        'schemaVersion': 1, 'id': name, 'provides': provides or [f'{name}.ready'],
        'routes': [{'id': 'default', 'when': when or {}, 'requires': list(requires),
                    'instructions': 'AGENTS.md', 'interactive': False,
                    'overlays': list(overlays)}],
    }


def repository(*components):
    return {item['id']: item for item in components}


class PlanningTests(unittest.TestCase):
    def test_transitive_dependencies_reuse_provider(self):
        data = repository(component('app', ['base.ready', 'login.ready']),
                          component('login', ['base.ready']), component('base'))
        result = plan(data, ['app'], {})
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(result['order'], ['base', 'login', 'app'])
        self.assertEqual(len(result['nodes']), 3)
        self.assertFalse(result['nodes']['base']['requested'])
        self.assertTrue(result['nodes']['app']['requested'])

    def test_overlay_requirements_are_conditional_and_labelled(self):
        overlay = {'id': 'desktop', 'when': {'machine': 'desktop'},
                   'requires': ['network.ready', 'base.ready'], 'instructions': 'AGENTS.md'}
        data = repository(component('guest', ['base.ready'], overlays=[overlay]),
                          component('base'), component('network'))
        ordinary = plan(data, ['guest'], {'machine': None})
        desktop = plan(data, ['guest'], {'machine': 'desktop'})
        self.assertNotIn('network', ordinary['nodes'])
        self.assertEqual(desktop['nodes']['guest']['requires'], ['base.ready', 'network.ready'])
        self.assertIn({'provider': 'network', 'consumer': 'guest', 'outcome': 'network.ready',
                       'route': 'default', 'overlay': 'desktop'}, desktop['edges'])
        self.assertEqual(len([e for e in desktop['edges'] if e['outcome'] == 'base.ready']), 2)

    def test_missing_provider_explains_requirement(self):
        result = plan(repository(component('app', ['missing.ready'])), ['app'], {})
        issue = result['issues'][0]
        self.assertEqual(issue['kind'], 'missing-provider')
        self.assertEqual(issue['required_by'][0]['consumer'], 'app')
        self.assertEqual(result['order'], [])

    def test_ambiguity_and_explicit_choice(self):
        data = repository(component('app', ['browser.ready']),
                          component('one', provides=['browser.ready']),
                          component('two', provides=['browser.ready']))
        self.assertEqual(plan(data, ['app'], {})['issues'][0]['kind'], 'ambiguous-provider')
        result = plan(data, ['app'], {}, provider_choices={'browser.ready': 'two'})
        self.assertEqual(result['order'], ['two', 'app'])

    def test_invalid_provider_is_not_silently_replaced(self):
        data = repository(component('app', ['base.ready']), component('base'))
        result = plan(data, ['app'], {}, provider_choices={'base.ready': 'app'})
        self.assertEqual(result['issues'][0]['kind'], 'invalid-provider')

    def test_requested_provider_beats_external_readiness_and_alternatives(self):
        data = repository(component('app', ['browser.ready']),
                          component('one', provides=['browser.ready']),
                          component('two', provides=['browser.ready']))
        result = plan(data, ['app', 'two'], {}, external_outcomes={'browser.ready': 'verified'})
        self.assertEqual(result['bindings']['browser.ready'], {'provider': 'two'})
        self.assertEqual(result['order'], ['two', 'app'])

    def test_external_readiness_avoids_unrequested_setup(self):
        data = repository(component('app', ['base.ready']), component('base'))
        result = plan(data, ['app'], {}, external_outcomes={'base.ready': 'checked on target'})
        self.assertEqual(result['order'], ['app'])
        self.assertEqual(result['bindings']['base.ready'], {'external': 'checked on target'})
        result = plan(data, ['base'], {}, external_outcomes={'base.ready': 'checked on target'})
        self.assertEqual(result['order'], ['base'])

    def test_implicitly_added_provider_supersedes_old_evidence(self):
        data = repository(component('app', ['shared.ready']), component('other', ['extra.ready']),
                          component('base', provides=['shared.ready', 'extra.ready']))
        result = plan(data, ['app', 'other'], {}, external_outcomes={'shared.ready': 'verified'})
        self.assertEqual(result['bindings']['shared.ready'], {'provider': 'base'})
        self.assertLess(result['order'].index('base'), result['order'].index('app'))
        reversed_data = dict(reversed(list(data.items())))
        self.assertEqual(result, plan(reversed_data, ['other', 'app'], {},
                                     external_outcomes={'shared.ready': 'verified'}))

    def test_multiple_included_providers_do_not_arbitrarily_replace_evidence(self):
        data = repository(component('app', ['shared.ready', 'one.ready', 'two.ready']),
                          component('one', provides=['one.ready', 'shared.ready']),
                          component('two', provides=['two.ready', 'shared.ready']))
        result = plan(data, ['app'], {}, external_outcomes={'shared.ready': 'verified'})
        self.assertEqual(result['issues'][0]['kind'], 'ambiguous-provider')
        self.assertNotIn('shared.ready', result['bindings'])

    def test_unknown_candidate_cannot_be_eliminated(self):
        data = repository(component('app', ['browser.ready']),
                          component('one', provides=['browser.ready']),
                          component('two', provides=['browser.ready'], when={'machine': 'desktop'}))
        result = plan(data, ['app'], {})
        self.assertEqual(result['issues'][0]['kind'], 'unresolved-provider')
        self.assertEqual(result['issues'][0]['missing_facts'], ['machine'])
        self.assertEqual(plan(data, ['app'], {'machine': None})['order'], ['one', 'app'])

    def test_unsupported_provider_is_excluded(self):
        data = repository(component('app', ['base.ready']),
                          component('base', when={'os': 'windows'}))
        result = plan(data, ['app'], {'os': 'linux'})
        self.assertEqual(result['issues'][0]['kind'], 'missing-provider')

    def test_missing_unsupported_and_unresolved_requested_components(self):
        data = repository(component('windows', when={'os': 'windows'}),
                          component('profile', when={'machine': 'desktop'}))
        result = plan(data, ['missing', 'windows', 'profile'], {'os': 'linux'})
        self.assertEqual({i['kind'] for i in result['issues']},
                         {'missing', 'unsupported', 'unresolved'})
        self.assertEqual(result['order'], [])

    def test_no_route_fallback_for_missing_dependencies(self):
        app = component('app', ['missing.ready'])
        app['routes'].append({'id': 'fallback', 'when': {}, 'requires': [],
                              'interactive': False, 'instructions': 'AGENTS.md'})
        result = plan(repository(app), ['app'], {})
        self.assertEqual(result['nodes']['app']['route'], 'default')
        self.assertEqual(result['issues'][0]['kind'], 'missing-provider')

    def test_cycles_include_causes_and_no_execution_order(self):
        data = repository(component('a', ['b.ready']), component('b', ['c.ready']),
                          component('c', ['a.ready']))
        result = plan(data, ['a'], {})
        issue = result['issues'][0]
        self.assertEqual(issue['kind'], 'cycle')
        self.assertEqual(issue['chain'][0], issue['chain'][-1])
        self.assertEqual(len(issue['edges']), 3)
        for provider, consumer in zip(issue['chain'], issue['chain'][1:]):
            self.assertTrue(any(e['provider'] == provider and e['consumer'] == consumer
                                for e in issue['edges']))
        self.assertEqual(result['order'], [])

    def test_self_dependency_not_hidden_by_existing_readiness(self):
        data = repository(component('app', ['app.ready']))
        result = plan(data, ['app'], {}, external_outcomes={'app.ready': 'verified'})
        self.assertEqual(result['issues'][0]['kind'], 'cycle')
        self.assertEqual(result['issues'][0]['chain'], ['app', 'app'])

    def test_unmatched_overlay_and_unrequested_cycles_do_not_block(self):
        overlay = {'id': 'desktop', 'when': {'machine': 'desktop'},
                   'requires': ['app.ready'], 'instructions': 'AGENTS.md'}
        data = repository(component('app', overlays=[overlay]), component('other', ['other.ready']))
        self.assertEqual(plan(data, ['app'], {'machine': None})['order'], ['app'])
        self.assertEqual(plan(data, ['app'], {'machine': 'desktop'})['issues'][0]['kind'], 'cycle')

    def test_inputs_unchanged_and_result_has_no_shared_mutable_values(self):
        data = repository(component('app', ['base.ready']))
        target = {'machine': None}
        evidence = {'base.ready': {'check': ['passed']}}
        original = copy.deepcopy((data, target, evidence))
        result = plan(data, ['app'], target, external_outcomes=evidence)
        result['bindings']['base.ready']['external']['check'].append('changed')
        result['target']['machine'] = 'desktop'
        self.assertEqual((data, target, evidence), original)


if __name__ == '__main__':
    unittest.main()
