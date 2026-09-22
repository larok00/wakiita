# /// script
# dependencies = ["jsonschema>=4.18,<5"]
# ///
"""Validate an Oma-repository and print a read-only plan as JSON."""

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

from manifests import load_repository, load_schema
from planning import plan


def request_schema():
    definitions = load_schema()['$defs']
    target = deepcopy(definitions['when'])
    target['properties'] = {key: {'anyOf': [value, {'type': 'null'}]}
                            for key, value in target['properties'].items()}
    outcome_pattern = definitions['outcome']['pattern']
    return {
        '$defs': definitions, 'type': 'object', 'additionalProperties': False,
        'required': ['requested', 'target'],
        'properties': {
            'requested': {'type': 'array', 'minItems': 1, 'uniqueItems': True,
                          'items': {'$ref': '#/$defs/id'}},
            'target': target,
            'provider_choices': {
                'type': 'object', 'propertyNames': {'$ref': '#/$defs/outcome'},
                'patternProperties': {outcome_pattern: {'$ref': '#/$defs/id'}},
                'additionalProperties': False,
            },
            'external_outcomes': {
                'type': 'object', 'propertyNames': {'$ref': '#/$defs/outcome'},
                'patternProperties': {outcome_pattern: {'type': 'string', 'pattern': r'\S'}},
                'additionalProperties': False,
            },
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repository', type=Path, help='Path to the Oma-repository')
    parser.add_argument('request', type=Path, help='JSON file with requested ippin and target facts')
    args = parser.parse_args()
    try:
        request = json.loads(args.request.read_text())
        errors = []
        for error in Draft202012Validator(request_schema()).iter_errors(request):
            location = '/'.join(map(str, error.absolute_path)) or '<root>'
            errors.append(f'request: {location}: {error.message}')
        if not errors:
            _, manifests, errors, _ = load_repository(args.repository)
        if errors:
            result = {'status': 'invalid', 'errors': errors}
        else:
            result = plan(manifests, **request)
            result['repository'] = str(args.repository.resolve())
    except (OSError, ValueError, RuntimeError) as error:
        result = {'status': 'invalid', 'errors': [str(error)]}
    print(json.dumps(result, indent=2))
    return {'complete': 0, 'invalid': 1, 'unresolved': 2}[result['status']]


if __name__ == '__main__':
    sys.exit(main())
