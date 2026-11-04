"""Regenerate canonical SDO implementations using the independent SDO CLI.

This utility never alters the Defs read-contract artifact. Pass --production to
produce internal canonical model SDO implementations in the Defs implementation artifact. Source inputs
come exclusively from schema-generated read-only DataObject interfaces.
Run with ``--check`` for a non-mutating consistency check of generated files.
"""
from __future__ import annotations

import ast
from pathlib import Path
import sys

from eu.algites.tool.codegen.sdo.impl.cli.aic_sdo_codegen_cli import main


def _read_contracts(source_root: Path) -> list[str]:
    """Find source-generated JSON read contracts, excluding non-DataObject records."""
    results: list[str] = []
    for source in sorted(source_root.glob('eu/algites/tool/codegen/defs/model/*.py')):
        module = '.'.join(source.relative_to(source_root).with_suffix('').parts)
        for declaration in ast.parse(source.read_text(encoding='utf-8')).body:
            if (isinstance(declaration, ast.ClassDef)
                    and declaration.name.startswith('AIig')
                    and any(isinstance(parent, ast.Name) and parent.id == 'AIiJsonDataObject'
                            for parent in declaration.bases)):
                results.append(f'{module}:{declaration.name}')
    if not results:
        raise ValueError('No generated DataObject contracts found; regenerate Defs schema contracts first')
    return results


def regenerate(check: bool = False, *, production: bool = False) -> int:
    """Invoke the standard native SDO CLI; do not couple it to Defs internals."""
    repository = next(folder for folder in Path(__file__).resolve().parents
                      if folder.name == 'pub.tool.General')
    read_root = 'generators/code/defscodegen/intf/src/product/python.gen'
    fixture_root = ('generators/code/defscodegen/impl/src/product/python.gen' if production
                    else 'generators/code/defscodegen/impl/src/develop/python.gen')
    profile = repository / ('generators/code/profile/algites/src/product/config/'
                            'eu/algites/tool/codegen/sdo/algites-sdocodegen-python.settings')
    arguments = [
        f'--repository-root={repository}',
        f'--technology-dointf-input-dir:python={read_root}',
        f'--technology-sdointf-output-dir:python={fixture_root}',
        f'--technology-sdoimpl-output-dir:python={fixture_root}',
        '--dointf-input-classes:python=' + ';'.join(_read_contracts(repository / read_root)),
        '--sdointf-subpackage=impl.intf',
        '--sdoclass-subpackage=impl',
    ]
    arguments.extend(line.strip() for line in profile.read_text(encoding='utf-8').splitlines()
                     if line.startswith('--'))
    if check:
        arguments.append('--check')
    return main(arguments)


if __name__ == '__main__':
    sys.exit(regenerate('--check' in sys.argv[1:], production='--production' in sys.argv[1:]))
