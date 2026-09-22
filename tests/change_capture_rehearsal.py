"""Continue a successful generation rehearsal with change capture and restoration."""

import argparse
import json
import re
from pathlib import Path
import shutil
import subprocess
import tempfile

import generation_rehearsal
from rehearsal import fingerprint, target_state


TOKEN = 'CHANGE_CAPTURE_SESSION_FIXTURE_91'


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def create(previous):
    generation_rehearsal.check(previous, 'restore')
    root = Path(tempfile.mkdtemp(prefix='wakiita-change-'))
    shutil.copytree(previous / 'oma-rehearsal', root / 'oma')
    shutil.copytree(previous / 'travel-home', root / 'source-home')
    plugin = Path(__file__).resolve().parents[1] / 'plugins/wakiita'
    shutil.copytree(plugin, root / 'plugin', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    repo = root / 'oma'
    # Find the shared preference payload without fixing the generated route layout.
    candidates = []
    for path in (repo / 'ippin/palette').rglob('settings.json'):
        data = json.loads(path.read_text())
        if data.get('font_size') == 14 and data.get('theme') == 'dark':
            candidates.append(path)
    if len(candidates) != 1:
        raise ValueError('Expected one shared Palette settings payload')
    shared = candidates[0]
    data = json.loads(shared.read_text())
    data['theme'] = 'light'  # Unrelated repository edit, not deployed to source.
    write_json(shared, data)
    # Keep existing readiness documentation consistent with that prior edit.
    for path in repo.rglob('*.md'):
        text = path.read_text()
        path.write_text(re.sub(r'\bdark\b', 'light', text))
    source = root / 'source-home/.config/palette/settings.json'
    data = json.loads(source.read_text())
    data.update(font_size=16, session_token=TOKEN, last_opened='/temporary/recent.txt')
    write_json(source, data)
    for name in ['travel-home', 'generic-home']:
        config = root / name / '.config/palette/settings.json'
        config.parent.mkdir(parents=True)
        write_json(config, {'unrelated': 'keep'})
    write_json(root / 'before.json', {
        'shared': str(shared.relative_to(repo)),
        'repo': fingerprint(repo),
        'shared_data': json.loads(shared.read_text()),
        'sources': {name: fingerprint(root / name) for name in ['plugin', 'source-home']},
        'targets': {name: target_state(root / name) for name in ['travel-home', 'generic-home']},
    })
    return root


def check(root, phase):
    before = json.loads((root / 'before.json').read_text())
    for name, state in before['sources'].items():
        if fingerprint(root / name) != state:
            raise ValueError(f'{name} changed')
    repo = root / 'oma'
    if phase == 'capture':
        expected = dict(before['shared_data'], font_size=16)
        if json.loads((repo / before['shared']).read_text()) != expected:
            raise ValueError('Shared preference change lost or unrelated repository edit overwritten')
        current = fingerprint(repo)
        if current.keys() != before['repo'].keys():
            raise ValueError('Unexpected recipe files added or removed')
        for name, digest in before['repo'].items():
            # Component prose may need updated readiness values; review its diff manually.
            if name == before['shared'] or name.endswith('.md'):
                continue
            if current[name] != digest:
                raise ValueError(f'Unrelated recipe file changed: {name}')
        for path in repo.rglob('*'):
            if path.is_file() and any(value.encode() in path.read_bytes() for value in [TOKEN, '/temporary/recent.txt', str(root / 'source-home')]):
                raise ValueError(f'Captured runtime state or source path in {path.relative_to(repo)}')
        for name, state in before['targets'].items():
            if target_state(root / name) != state:
                raise ValueError(f'Capture modified {name}')
        write_json(root / 'captured.json', current)
        return
    if fingerprint(repo) != json.loads((root / 'captured.json').read_text()):
        raise ValueError('Restore changed the recipe')
    for home, display in [('travel-home', 'eDP-1'), ('generic-home', None)]:
        expected = {'unrelated': 'keep', 'theme': 'light', 'font_size': 16}
        if display:
            expected['display'] = display
        config = root / home / '.config/palette/settings.json'
        if json.loads(config.read_text()) != expected:
            raise ValueError(f'Incorrect restored settings in {home}')
        binary = root / home / '.local/bin/palette'
        if binary.read_bytes() != (root / 'source-home/.local/bin/palette').read_bytes():
            raise ValueError(f'Installed application changed in {home}')
        result = subprocess.run([str(binary), '--config', str(config)], check=True,
                                capture_output=True, text=True, timeout=10)
        expected.pop('unrelated')
        if json.loads(result.stdout) != expected:
            raise ValueError(f'Application did not read updated preferences in {home}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    creator = commands.add_parser('create')
    creator.add_argument('previous', type=Path)
    checker = commands.add_parser('check')
    checker.add_argument('root', type=Path)
    checker.add_argument('phase', choices=['capture', 'restore'])
    args = parser.parse_args()
    try:
        if args.command == 'create':
            print(create(args.previous.resolve()))
        else:
            check(args.root.resolve(), args.phase)
            print(f'PASS: {args.phase}')
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f'FAIL: {error}')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
