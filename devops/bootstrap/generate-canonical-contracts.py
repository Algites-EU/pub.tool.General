#!/usr/bin/env python3
"""Regenerate the canonical read-only contracts using the *current* Defs CLI.

This optional self-hosting helper is NOT an alternative generator. It selects
only ``canonical-model_1.jsondef.schema.json`` and forwards the published
qualified Defs options and naming profiles to the same CLI used by
``generate_sources.py``. In particular it must never call ``defs.old``.

Output files remain in the selected artifact's normal ``*.gen`` directories;
private staging and generator ownership state remain under ``build/``.
Neither this helper nor ``--check`` modifies ``*.extgen`` snapshots.

@author linhart1
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Bootstrap imports must not produce bytecode under src/product.
if __name__ == '__main__':
    sys.dont_write_bytecode = True

from generate_sources import (_load_codegen, _native_settings_owner,
                              _qualified_defs_arguments)


CANONICAL_SCHEMA = Path(
    'generators/code/defscodegen/intf/src/product/jsondefs/'
    'eu/algites/tool/codegen/defs/model/canonical-model_1.jsondef.schema.json')


def canonical_arguments(root: Path, *, check: bool = False) -> list[str]:
    """Build standard public CLI options for exactly the canonical schema.

    :param root: Repository root containing the canonical schema and settings.
    :param check: Compare expected files without rewriting generated sources.
    :return: Fully qualified Defs CLI arguments in Java/Python symmetry.
    :raises FileNotFoundError: If the canonical schema is absent.
    """
    schema = root / CANONICAL_SCHEMA
    if not schema.is_file():
        raise FileNotFoundError(f'Canonical model schema is missing: {schema}')
    artifact = root / 'generators/code/defscodegen/intf'
    args = _qualified_defs_arguments(root, artifact, 'product',
                                     ['java', 'python'], ['jsondefs'],
                                     _native_settings_owner(root))
    relative = CANONICAL_SCHEMA.as_posix()
    input_count = 0
    for index, argument in enumerate(args):
        if argument.startswith(('--defs-input-paths:java=', '--defs-input-paths:python=')):
            args[index] = argument.split('=', 1)[0] + '=' + relative
            input_count += 1
    if input_count != 2:
        raise ValueError('Expected both Java and Python canonical Defs input selections')
    # A source archive contains *.gen but not build manifests. Publishing only
    # files emitted by this invocation is deliberately the default; do not
    # clean other Defs or SDO outputs in shared directories.
    if check:
        args.append('--check')
    return args


def main(argv: list[str] | None = None) -> int:
    """Run the standard Defs CLI for the canonical read-only model contracts.

    :param argv: Optional command-line arguments, otherwise process argv.
    :return: CLI process status, zero on successful generation or verification.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true',
                        help='Compare generated contracts without changing the source tree')
    parser.add_argument('--source-dependencies', action='store_true',
                        help='Require sibling source repositories rather than relying on wheels')
    options = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    if options.source_dependencies and not (root.parent / 'pub.lib.General').is_dir():
        parser.error('Missing sibling pub.lib.General for --source-dependencies')
    cli = _load_codegen(root, root / 'build/run/canonical-contracts')
    return cli(canonical_arguments(root, check=options.check)) or 0


if __name__ == '__main__':
    sys.exit(main())
