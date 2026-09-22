"""Create and check an isolated Ryōribon capture-and-restore rehearsal."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from rehearsal import fingerprint, target_state


TOKEN = 'SESSION_FIXTURE_DO_NOT_CAPTURE_73'


def create():
    root = Path(tempfile.mkdtemp(prefix='wakiita-generation-'))
    plugin = Path(__file__).resolve().parents[1] / 'plugins/wakiita'
    shutil.copytree(plugin, root / 'plugin', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    source = root / 'source-home'
    config = source / '.config/palette'
    config.mkdir(parents=True)
    (config / 'settings.json').write_text(json.dumps({
        'theme': 'dark', 'font_size': 14, 'display': 'eDP-1',
        'session_token': TOKEN, 'last_opened': '/source-only/recent.txt',
    }))
    distribution = root / 'distribution'
    distribution.mkdir()
    application = '''#!/usr/bin/env python3
import argparse, json
parser = argparse.ArgumentParser()
parser.add_argument('--config', required=True)
args = parser.parse_args()
with open(args.config) as source:
    settings = json.load(source)
assert settings.get('theme') in ['light', 'dark']
assert isinstance(settings.get('font_size'), int)
print(json.dumps({key: settings[key] for key in ['theme', 'font_size', 'display'] if key in settings}))
'''
    (distribution / 'palette.py').write_text(application)
    (distribution / 'README.md').write_text(
        'Palette is a synthetic utility for this rehearsal. Its Python source is redistributable '
        'and should be bundled in the recipe. It needs Python 3, no third-party packages. '
        'Install it as an executable at the target home\'s .local/bin/palette. Preferences are '
        'JSON in .config/palette/settings.json. Run palette --config <settings-file> to read '
        'supported preferences. theme and font_size are shared; display is a machine-specific '
        'connector. session_token and last_opened are generated runtime state. Defaults are '
        'light theme, font size 12, and no display restriction. Preserve unrelated settings.\n')
    executable = source / '.local/bin/palette'
    executable.parent.mkdir(parents=True)
    executable.write_text(application)
    executable.chmod(0o755)
    for home in ['travel-home', 'generic-home']:
        config = root / home / '.config/palette'
        config.mkdir(parents=True)
        (config / 'settings.json').write_text(json.dumps({'unrelated': 'keep'}))
    (root / 'sources.json').write_text(json.dumps({
        name: fingerprint(root / name) for name in ['plugin', 'source-home', 'distribution']
    }))
    (root / 'targets-before.json').write_text(json.dumps({
        name: target_state(root / name) for name in ['travel-home', 'generic-home']
    }))
    return root


def check(root, phase):
    for name, expected in json.loads((root / 'sources.json').read_text()).items():
        if fingerprint(root / name) != expected:
            raise ValueError(f'{name} changed')
    repo = root / 'oma-rehearsal'
    if phase == 'capture':
        for relative in ['README.md', 'AGENTS.md', 'docs/ippin.schema.json', 'docs/ippin-spec.md',
                         'ippin/palette/ippin.json', 'ippin/palette/README.md', 'ippin/palette/AGENTS.md']:
            if not (repo / relative).is_file():
                raise ValueError(f'Missing {relative}')
        for path in repo.rglob('*'):
            if path.is_file():
                content = path.read_bytes()
                forbidden = [TOKEN, '/source-only/recent.txt', str(root / 'source-home'),
                             str(root / 'distribution')]
                if any(value.encode() in content for value in forbidden):
                    raise ValueError(f'Captured runtime state or source dependency in {path.relative_to(repo)}')
        for name, expected in json.loads((root / 'targets-before.json').read_text()).items():
            if target_state(root / name) != expected:
                raise ValueError('Capture modified a restore target')
        (root / 'recipe-snapshot.json').write_text(json.dumps(fingerprint(repo)))
        return
    if fingerprint(repo) != json.loads((root / 'recipe-snapshot.json').read_text()):
        raise ValueError('Restore modified the generated recipe')
    for home, display in [('travel-home', 'eDP-1'), ('generic-home', None)]:
        expected = {'unrelated': 'keep', 'theme': 'dark', 'font_size': 14}
        if display:
            expected['display'] = display
        config = root / home / '.config/palette/settings.json'
        if json.loads(config.read_text()) != expected:
            raise ValueError(f'Incorrect preferences or lost unrelated setting in {home}')
        binary = root / home / '.local/bin/palette'
        if binary.read_bytes() != (root / 'distribution/palette.py').read_bytes() or not os.access(binary, os.X_OK):
            raise ValueError(f'Application missing, changed or not executable in {home}')
        result = subprocess.run([str(binary), '--config', str(config)], check=True,
                                capture_output=True, text=True, timeout=10)
        expected.pop('unrelated')
        if json.loads(result.stdout) != expected:
            raise ValueError(f'Application did not read the restored preferences in {home}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('create')
    checker = commands.add_parser('check')
    checker.add_argument('root', type=Path)
    checker.add_argument('phase', choices=['capture', 'restore'])
    args = parser.parse_args()
    if args.command == 'create':
        print(create())
        return 0
    try:
        check(args.root, args.phase)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f'FAIL: {error}')
        return 1
    print(f'PASS: {args.phase}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
