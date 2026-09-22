"""Create and check an isolated Shokunin rehearsal; never execute its recipes."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile


def fingerprint(directory):
    return {str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(directory.rglob('*')) if p.is_file()}


def target_state(directory):
    return {str(p.relative_to(directory)): [hashlib.sha256(p.read_bytes()).hexdigest(),
                                           p.stat().st_mtime_ns]
            for p in sorted(directory.rglob('*')) if p.is_file()}


def create():
    root = Path(tempfile.mkdtemp(prefix='wakiita-rehearsal-'))
    plugin = Path(__file__).resolve().parents[1] / 'plugins/wakiita'
    shutil.copytree(plugin, root / 'plugin', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    repo, target = root / 'oma', root / 'target'
    repo.mkdir()
    target.mkdir()
    (repo / 'AGENTS.md').write_text('Configure only the requested setup in the target directory named by each recipe.\n')
    components = [
        ('base', []), ('b-good', ['base.ready']), ('z-independent', []),
        ('a-failing', ['base.ready']), ('c-dependent', ['a-failing.ready']),
        ('d-transitive', ['c-dependent.ready']), ('z-later', ['base.ready']),
    ]
    for name, requires in components:
        folder = repo / 'ippin' / name
        folder.mkdir(parents=True)
        (folder / 'README.md').write_text(f'{name}: preferences for a disposable Linux target.\n')
        expected = {'ready': True}
        overlays = []
        if name == 'b-good':
            expected['accent'] = 'green'
            overlays = [{'id': 'rehearsal', 'when': {'machine': 'rehearsal'},
                         'instructions': 'overlay.md'}]
            (folder / 'overlay.md').write_text(
                f'In {target / (name + ".json")}, set accent to green, preserving other keys. '
                'Skip writing if already green. Verify accent is green.\n')
        (folder / 'AGENTS.md').write_text(
            f'Target directory: {target}\n'
            f'Read {name}.json first. Run the manifest command only if its ready value is not true.\n'
            f'After matching overlays, verify {name}.ready only when the file contains exactly '
            f'{json.dumps(expected)}. An installer event does not prove readiness.\n')
        (folder / 'install.py').write_text(
            'import json\nfrom pathlib import Path\n'
            f'root = Path({str(target)!r})\n'
            f"with (root / 'events').open('a') as events:\n    events.write({name!r} + '\\n')\n"
            f"(root / {name + '.json'!r}).write_text(json.dumps({{'ready': {name != 'a-failing'!r}}}))\n")
        (folder / 'ippin.json').write_text(json.dumps({
            'schemaVersion': 1, 'id': name, 'provides': [name + '.ready'],
            'routes': [{'id': 'linux', 'when': {'os': 'linux'}, 'requires': requires,
                        'interactive': False, 'instructions': 'AGENTS.md',
                        'command': ['python3', 'install.py'], 'overlays': overlays}],
        }, indent=2) + '\n')
    (root / 'sources.json').write_text(json.dumps({
        'plugin': fingerprint(root / 'plugin'), 'oma': fingerprint(repo),
    }))
    return root


def check(root, phase):
    sources = json.loads((root / 'sources.json').read_text())
    for directory, expected in sources.items():
        if fingerprint(root / directory) != expected:
            raise ValueError(f'{directory} changed during rehearsal')
    target = root / 'target'
    if phase == 'plan':
        if list(target.iterdir()):
            raise ValueError('Planning modified the target')
        return

    successful = {'base', 'b-good', 'z-independent'}
    installed = successful | ({'a-failing', 'z-later'} if phase == 'failure' else set())
    events = (target / 'events').read_text().splitlines()
    if set(events) != installed or len(events) != len(installed):
        raise ValueError(f'Unexpected or repeated installations: {events}')
    for name in installed:
        expected = {'ready': name != 'a-failing'}
        if name == 'b-good':
            expected['accent'] = 'green'
        if json.loads((target / (name + '.json')).read_text()) != expected:
            raise ValueError(f'Unexpected final settings for {name}')
    if {p.name for p in target.iterdir()} != {'events', *(name + '.json' for name in installed)}:
        raise ValueError('Unexpected target files, possibly a blocked dependant was executed')
    for name in installed - {'base', 'z-independent'}:
        if events.index('base') >= events.index(name):
            raise ValueError(f'{name} ran before its prerequisite')
    if phase == 'failure' and events.index('a-failing') >= events.index('z-later'):
        raise ValueError('Independent continuation after failure was not exercised')
    if phase == 'success':
        (root / 'success-state.json').write_text(json.dumps(target_state(target)))
    if phase == 'repeat':
        if target_state(target) != json.loads((root / 'success-state.json').read_text()):
            raise ValueError('Repeat setup rewrote an already-ready target')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('create')
    checker = commands.add_parser('check')
    checker.add_argument('root', type=Path)
    checker.add_argument('phase', choices=['plan', 'success', 'repeat', 'failure'])
    args = parser.parse_args()
    if args.command == 'create':
        print(create())
        return 0
    try:
        check(args.root, args.phase)
    except (OSError, ValueError, KeyError) as error:
        print(f'FAIL: {error}')
        return 1
    print(f'PASS: {args.phase}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
