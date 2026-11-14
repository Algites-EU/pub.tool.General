"""Read the existing Defs CLI settings as bootstrap naming policy.

The bootstrap never reconstructs generated type prefixes or convention IDs.
Settings files select the naming profile; the selected source-code catalog
selects the actual symbol and filename compositions.
"""
from __future__ import annotations

from pathlib import Path
from typing import Mapping
import yaml


def defs_settings(repository: Path, language: str, profile: str = 'algites') -> dict[str, str]:
    """Read one published Defs CLI settings resource without applying defaults."""
    path = (repository / 'generators/code/profile' / profile / 'src/product/config'
            / 'eu/algites/tool/codegen/defs' / f'defscodegen-{language}.settings')
    if not path.is_file():
        raise FileNotFoundError(f'Missing Defs CLI naming settings: {path}')
    options: dict[str, str] = {}
    for line_number, raw in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if not line.startswith('--') or '=' not in line:
            raise ValueError(f'Invalid codegen setting {path}:{line_number}: {line}')
        key, value = line[2:].split('=', 1)
        if not value or key in options:
            raise ValueError(f'Duplicate or empty codegen setting {path}:{line_number}: {key}')
        options[key] = value
    return options


def setting(options: Mapping[str, str], name: str) -> str:
    """Require an explicitly selected naming convention ID."""
    if not options.get(name):
        raise ValueError(f'Missing mandatory Defs CLI naming setting --{name}=...')
    return options[name]


def filename_composition(catalog_file: Path, selected_convention: str) -> str:
    """Resolve a unique named profile and file-stem rule from the XSD-shaped catalog."""
    contents = yaml.safe_load(catalog_file.read_text(encoding='utf-8'))
    location = f'{catalog_file}: SourceStructureNameConventions/NameConventions/NameConvention'
    try:
        conventions = contents['SourceStructureNameConventions']['NameConventions']['NameConvention']
    except (KeyError, TypeError) as exc:
        raise ValueError(f'{location}: expected named profile list') from exc
    if not isinstance(conventions, list):
        raise ValueError(f'{location}: expected array')
    names = set()
    selected = None
    for number, entry in enumerate(conventions):
        if not isinstance(entry, dict) or not isinstance(entry.get('name'), str) or not entry['name']:
            raise ValueError(f'{location}[{number}]: missing nonempty name')
        if entry['name'] in names:
            raise ValueError(f'{location}[{number}]: duplicate name {entry["name"]!r}')
        names.add(entry['name'])
        if entry['name'] == selected_convention:
            selected = entry
    if selected is None:
        raise ValueError(f'{location}: missing convention {selected_convention!r}')
    location += f'/{selected_convention}/StructureNaming/Rule'
    try:
        rules = selected['StructureNaming']['Rule']
    except (KeyError, TypeError) as exc:
        raise ValueError(f'{location}: expected named rules') from exc
    if not isinstance(rules, list):
        raise ValueError(f'{location}: expected array')
    seen = set()
    stem = None
    for number, rule in enumerate(rules):
        if not isinstance(rule, dict) or not isinstance(rule.get('kind'), str) or not rule['kind']:
            raise ValueError(f'{location}[{number}]: missing nonempty kind')
        if rule['kind'] in seen:
            raise ValueError(f'{location}[{number}]: duplicate kind {rule["kind"]!r}')
        seen.add(rule['kind'])
        if rule['kind'] == 'file_name_stem':
            stem = rule.get('Value')
    if not isinstance(stem, str) or not stem:
        raise ValueError(f'{location}: missing nonempty file_name_stem')
    return stem
