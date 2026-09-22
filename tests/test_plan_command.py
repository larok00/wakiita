"""Integration tests; requires jsonschema (see the planning command reference)."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

PLUGIN = Path(__file__).resolve().parents[1] / 'plugins/wakiita'


class PlanCommandTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'oma'
        self.component = self.repo / 'ippin/editor'
        self.component.mkdir(parents=True)
        (self.component / 'AGENTS.md').write_text('Verify the editor works.\n')
        self.manifest = {
            'schemaVersion': 1, 'id': 'editor', 'provides': ['editor.ready'],
            'routes': [{'id': 'linux', 'when': {'os': 'linux'}, 'requires': [],
                        'interactive': False, 'instructions': 'AGENTS.md',
                        'command': [sys.executable, '-c',
                                    f"from pathlib import Path; Path({str(self.root / 'executed')!r}).touch()"]}],
        }
        self.save_manifest()
        self.request = {'requested': ['editor'], 'target': {'os': 'linux', 'machine': None}}

    def save_manifest(self):
        (self.component / 'ippin.json').write_text(json.dumps(self.manifest))

    def run_command(self, plugin=PLUGIN, raw_request=None):
        request = self.root / 'request.json'
        request.write_text(json.dumps(self.request) if raw_request is None else raw_request)
        process = subprocess.run(
            [sys.executable, '-B', str(plugin / 'scripts/plan.py'), str(self.repo), str(request)],
            cwd=self.root, capture_output=True, text=True,
        )
        self.assertEqual(process.stderr, '')
        return process.returncode, json.loads(process.stdout)

    def test_complete_without_executing_or_changing_repository(self):
        before = {str(p.relative_to(self.repo)): p.read_bytes()
                  for p in self.repo.rglob('*') if p.is_file()}
        code, result = self.run_command()
        self.assertEqual(code, 0)
        self.assertEqual(result['order'], ['editor'])
        self.assertFalse((self.root / 'executed').exists())
        self.assertEqual(before, {str(p.relative_to(self.repo)): p.read_bytes()
                                for p in self.repo.rglob('*') if p.is_file()})

    def test_unknown_target_is_unresolved(self):
        self.request['target'] = {}
        code, result = self.run_command()
        self.assertEqual(code, 2)
        self.assertEqual(result['issues'][0]['missing_facts'], ['os'])

    def test_request_typos_and_bad_values_are_invalid(self):
        for request in [
            {'requested': ['editor'], 'target': {'enviroment': 'omarchy'}},
            {'requested': ['editor'], 'target': {'os': 'Linux'}},
            {'requested': [], 'target': {}},
            {'requested': 'editor', 'target': {}},
            {'requested': ['editor'], 'target': {}, 'extra': True},
            {'requested': ['editor'], 'target': {}, 'external_outcomes': {'base.ready': ''}},
            {'requested': ['editor'], 'target': {}, 'provider_choices': {'invalid': 'editor'}},
        ]:
            with self.subTest(request=request):
                self.request = request
                code, result = self.run_command()
                self.assertEqual((code, result['status']), (1, 'invalid'))

    def test_malformed_json(self):
        code, result = self.run_command(raw_request='{')
        self.assertEqual((code, result['status']), (1, 'invalid'))

    def test_invalid_manifest_and_missing_instructions(self):
        self.manifest['extra'] = True
        self.save_manifest()
        self.assertEqual(self.run_command()[0], 1)
        del self.manifest['extra']
        self.save_manifest()
        (self.component / 'AGENTS.md').unlink()
        code, result = self.run_command()
        self.assertEqual(code, 1)
        self.assertIn('instructions', result['errors'][0])

    def test_external_instruction_symlink_is_rejected(self):
        outside = self.root / 'outside.md'
        outside.write_text('Outside the ippin')
        instruction = self.component / 'AGENTS.md'
        instruction.unlink()
        instruction.symlink_to(outside)
        self.assertEqual(self.run_command()[0], 1)

    def test_duplicate_route_ids_are_rejected(self):
        self.manifest['routes'].append(dict(self.manifest['routes'][0]))
        self.save_manifest()
        code, result = self.run_command()
        self.assertEqual(code, 1)
        self.assertTrue(any('duplicate route' in e for e in result['errors']))

    def test_missing_prerequisite_and_evidence(self):
        self.manifest['routes'][0]['requires'] = ['base.ready']
        self.save_manifest()
        self.assertEqual(self.run_command()[0], 2)
        self.request['external_outcomes'] = {'base.ready': 'Verified on this target'}
        code, result = self.run_command()
        self.assertEqual(code, 0)
        self.assertEqual(result['bindings']['base.ready']['external'], 'Verified on this target')

    def test_packaged_command_works_outside_checkout(self):
        copied = self.root / 'plugin'
        shutil.copytree(PLUGIN, copied)
        self.assertEqual(self.run_command(copied)[0], 0)

    def test_existing_validator_still_reports_success_and_failure(self):
        command = [sys.executable, '-B', str(PLUGIN / 'scripts/validate-manifests.py'), str(self.repo)]
        good = subprocess.run(command, cwd=self.root, capture_output=True, text=True)
        self.assertEqual(good.returncode, 0)
        self.assertIn('PASS: 1 manifests', good.stdout)
        (self.component / 'AGENTS.md').unlink()
        bad = subprocess.run(command, cwd=self.root, capture_output=True, text=True)
        self.assertEqual(bad.returncode, 1)
        self.assertIn('FAIL:', bad.stderr)


if __name__ == '__main__':
    unittest.main()
