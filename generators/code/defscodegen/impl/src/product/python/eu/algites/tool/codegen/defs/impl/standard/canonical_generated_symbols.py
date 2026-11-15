"""Resolve generated canonical model classes by *schema identity*, not names.

Generated DataObject metadata carries canonical ``schema_id`` and generated
Python enum documentation records the canonical definition identity.  Those
identities survive changes in the selected naming profile; generated Python
module/class names do not.  Resolve the former to the latter from the actual
output of the naming catalog, without assuming format-specific class prefixes.

Only generated source files are indexed.  No unrelated Python code is executed
while discovering symbols.  Imports happen after an unambiguous identity match.
"""
from __future__ import annotations

import ast
from functools import lru_cache
from importlib import import_module, util
from pathlib import Path
import re
from typing import NamedTuple


class GeneratedSymbol(NamedTuple):
    """One unambiguously resolved generated Python symbol."""

    module: str
    typename: str

    def load(self):
        """Import the exact symbol written by the selected naming convention."""
        return getattr(import_module(self.module), self.typename)


_ENUM_ID = re.compile(r'(?:Generated from canonical definition\s+(\S+?)/\d+\.|Canonical identity:\s+(\S+?);\s+version:)')


def _literal_schema_id(declaration: ast.ClassDef) -> str | None:
    """Extract a source-format schema identity from an annotated generated type."""
    for statement in declaration.body:
        if not isinstance(statement, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id in
                   ('__json_schema__', '__yaml_schema__')
                   for target in statement.targets):
            continue
        if isinstance(statement.value, ast.Call):
            for keyword in statement.value.keywords:
                if keyword.arg == 'schema_id' and isinstance(keyword.value, ast.Constant):
                    if isinstance(keyword.value.value, str):
                        return keyword.value.value
    return None


@lru_cache(maxsize=4)
def _index(package: str) -> tuple[dict[tuple[str, str], GeneratedSymbol],
                                  dict[str, GeneratedSymbol]]:
    """Index generated source in a Python package, excluding handwritten code.

    The second mapping resolves dataclass choice records by the type of their
    annotated ``value`` member.  Neither mapping uses any naming prefix.
    """
    spec = util.find_spec(package)
    if spec is None or not spec.submodule_search_locations:
        raise ModuleNotFoundError(
            f'Generated canonical model package {package!r} is missing. '
            'The generated Defs contracts and SDO implementations must be '
            'available before the native Defs CLI is imported.')
    symbols: dict[tuple[str, str], GeneratedSymbol] = {}
    selected: dict[str, GeneratedSymbol] = {}
    bootstrap_implementations: list[tuple[GeneratedSymbol, str]] = []
    for root_string in spec.submodule_search_locations:
        root = Path(root_string)
        for source in sorted(root.rglob('*.py')):
            if source.name == '__init__.py' or '__pycache__' in source.parts:
                continue
            module = package + '.' + '.'.join(source.relative_to(root).with_suffix('').parts)
            # Do not import modules to inspect them; AST contains all metadata.
            tree = ast.parse(source.read_text(encoding='utf-8'), filename=str(source))
            module_description = ast.get_docstring(tree) or ''
            # Compiler seeds can predate the fully annotated SDO implementation.
            # Their generated module header links them to the read-only contract.
            module_owner = re.search(r'Generated SmartDataObject implementation for (\w+)\.',
                                     module_description)
            for declaration in tree.body:
                if not isinstance(declaration, ast.ClassDef):
                    continue
                # Accept only the canonical naming family's generated symbols.
                # In particular, a wire-format alias must not be indexed as a
                # second logical contract beside the common read interface.
                if not re.match(r'^(?:AIig|AIigd|AIcgd|AIng)[A-Z]', declaration.name):
                    continue
                symbol = GeneratedSymbol(module, declaration.name)
                if (module_owner is not None and 'impl' in source.relative_to(root).parts
                        and declaration.name.startswith('AIcgd')):
                    bootstrap_implementations.append((symbol, module_owner.group(1)))
                schema_id = _literal_schema_id(declaration)
                if schema_id:
                    parts = source.relative_to(root).parts
                    if 'impl' in parts and 'intf' in parts:
                        continue  # mutable SDO interface is not a read-only contract
                    role = 'implementation' if 'impl' in parts else 'contract'
                    key = (role, schema_id)
                    previous = symbols.get(key)
                    if previous is not None and previous != symbol:
                        raise ValueError(f'Ambiguous generated canonical {key}: '
                                         f'{previous} and {symbol}')
                    symbols[key] = symbol
                description = ast.get_docstring(declaration) or ''
                match = _ENUM_ID.search(description)
                if match and any(isinstance(base, ast.Name) and base.id == 'Enum'
                                 for base in declaration.bases):
                    key = ('enum', match.group(1) or match.group(2))
                    previous = symbols.get(key)
                    if previous is not None and previous != symbol:
                        raise ValueError(f'Ambiguous generated enum {key}: '
                                         f'{previous} and {symbol}')
                    symbols[key] = symbol
                # Source-generated sealed-choice selections are frozen dataclasses
                # with an explicit `value: <variant-interface>` contract.
                if any(isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name)
                       and dec.func.id == 'dataclass' for dec in declaration.decorator_list):
                    for member in declaration.body:
                        if (isinstance(member, ast.AnnAssign)
                                and isinstance(member.target, ast.Name)
                                and member.target.id == 'value'
                                and isinstance(member.annotation, ast.Name)):
                            annotation = member.annotation.id
                            previous = selected.get(annotation)
                            if previous is not None and previous != symbol:
                                raise ValueError(f'Ambiguous selected variant {annotation}: '
                                                 f'{previous} and {symbol}')
                            selected[annotation] = symbol
    # The first-stage ABI seed is generated before the general-purpose SDO
    # metadata annotations are available. Link its implementations to their
    # annotated, unified read-only contracts by the generator's own provenance.
    by_name = {symbol.typename: schema_id for (role, schema_id), symbol
               in symbols.items() if role == 'contract'}
    for symbol, owner in bootstrap_implementations:
        schema_id = by_name.get(owner)
        if schema_id is None:
            continue
        key = ('implementation', schema_id)
        previous = symbols.get(key)
        if previous is not None and previous != symbol:
            raise ValueError(f'Ambiguous generated canonical {key}: {previous} and {symbol}')
        symbols[key] = symbol
    return symbols, selected


@lru_cache(maxsize=128)
def choice_variant_identity(package: str, *, schema_prefix: str,
                            field_name: str) -> str:
    """Resolve a closed-choice branch by its schema field, not a stored ordinal.

    The parser's source schema determines both the branch's canonical identity
    and its DataObject field. Both are preserved in generated model contracts.
    """
    spec = util.find_spec(package)
    if spec is None or not spec.submodule_search_locations:
        raise ModuleNotFoundError('Generated model contracts missing: ' + package)
    found = []
    for root_string in spec.submodule_search_locations:
        root = Path(root_string)
        for file in sorted(root.glob('*.py')):
            if file.name == '__init__.py':
                continue
            tree = ast.parse(file.read_text(encoding='utf-8'), filename=str(file))
            for declaration in tree.body:
                if not isinstance(declaration, ast.ClassDef):
                    continue
                schema_id = _literal_schema_id(declaration)
                if not schema_id or not schema_id.startswith(schema_prefix):
                    continue
                fields = []
                for statement in declaration.body:
                    if not isinstance(statement, ast.AnnAssign):
                        continue
                    if (isinstance(statement.target, ast.Name)
                            and statement.target.id.startswith('SCHEMA_FIELD_NAME__')
                            and isinstance(statement.value, ast.Constant)
                            and isinstance(statement.value.value, str)):
                        fields.append(statement.value.value)
                if field_name in fields:
                    found.append(schema_id)
    if len(set(found)) != 1:
        raise ValueError(f'Expected exactly one generated variant with field '
                         f'{field_name!r} under {schema_prefix!r}, got {found}')
    return found[0]


def generated_type(package: str, *, role: str, schema_id: str):
    """Return a generated enum, read-only contract, or SDO implementation."""
    symbols, _ = _index(package)
    symbol = symbols.get((role, schema_id))
    if symbol is None:
        raise ImportError(f'No generated {role} for canonical schema {schema_id!r} '
                          f'in {package!r}; regenerate and validate model contracts')
    return symbol.load()


def generated_selected_type(package: str, *, variant_schema_id: str):
    """Find a selected sealed-choice record through its actual variant contract."""
    symbols, choices = _index(package)
    variant = symbols.get(('contract', variant_schema_id))
    if variant is None:
        raise ImportError(f'Missing generated choice variant {variant_schema_id!r}')
    record = choices.get(variant.typename)
    if record is None:
        raise ImportError(f'Missing generated selected-choice record for {variant_schema_id!r}')
    return record.load()
