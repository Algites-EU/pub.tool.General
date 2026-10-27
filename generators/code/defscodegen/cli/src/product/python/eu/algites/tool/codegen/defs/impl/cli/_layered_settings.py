"""Deterministically layer packaged, classpath and invocation settings for one Codegen."""
from __future__ import annotations
import importlib.resources
from pathlib import Path
import sys


def expand(arguments: list[str], generator: str, technology: str, package: str) -> list[str]:
    """Merge effective settings by the complete qualified option name before parsing values."""
    file_options = [value.partition('=')[2] for value in arguments if value.startswith('--settings-file=')]
    if len(file_options) > 1:
        raise ValueError('Only one --settings-file is permitted')
    remainder = [value for value in arguments if not value.startswith('--settings-file=')]
    name = f'{generator}-{technology}-default.settings'
    base = Path(f'generators/code/{generator}/intf/src/product/config/eu/algites/tool/codegen/{package}')
    def resource_text(name: str, required: bool) -> str | None:
        resource_path = Path('eu/algites/tool/codegen') / package / name
        try:
            candidate = importlib.resources.files(f'eu.algites.tool.codegen.{package}').joinpath(name)
            if candidate.is_file():
                return candidate.read_text(encoding='utf-8')
        except (ModuleNotFoundError, FileNotFoundError, TypeError):
            pass
        for prefix in sys.path:
            candidate = Path(prefix) / resource_path
            if candidate.is_file():
                return candidate.read_text(encoding='utf-8')
        candidate = base / name
        if candidate.is_file():
            return candidate.read_text(encoding='utf-8')
        if required:
            raise FileNotFoundError(f'Missing packaged Codegen defaults: {name}')
        return None

    sources: list[tuple[str, str]] = [(name, resource_text(name, True) or '')]
    override_name = f'{generator}-{technology}.settings'
    override_path = Path('eu/algites/tool/codegen') / package / override_name
    seen_files: set[Path] = set()
    overrides: list[tuple[str, str]] = []

    def append_file(candidate: Path, *, package_resource: bool = False) -> None:
        if candidate.is_file():
            resolved = candidate.resolve()
            if package_resource or resolved not in seen_files:
                if not package_resource:
                    seen_files.add(resolved)
                overrides.append((str(resolved), candidate.read_text(encoding='utf-8')))

    try:
        packaged = importlib.resources.files(f'eu.algites.tool.codegen.{package}').joinpath(override_name)
        if packaged.is_file():
            # Importlib can use non-filesystem Traversables (e.g. ZIP resources).
            # A physical sys.path copy of the same file must only be read once.
            try:
                append_file(Path(packaged), package_resource=True)
            except TypeError:
                overrides.append((f'importlib.resources:{override_name}',
                                  packaged.read_text(encoding='utf-8')))
    except (ModuleNotFoundError, FileNotFoundError, TypeError):
        pass
    append_file(base / override_name)
    # sys.path[0] has the highest import precedence. Apply its files last,
    # so every discovered file contributes without losing that priority.
    for prefix in reversed(sys.path):
        directory = Path(prefix or '.')
        append_file(directory / override_path)
        append_file(directory / override_name)
    sources.extend(overrides)
    if file_options:
        path = Path(file_options[0])
        sources.append((str(path), path.read_text(encoding='utf-8')))

    merged: dict[str, str] = {}
    legacy_counters: dict[str, int] = {}

    def push(token: str) -> None:
        if token in {'--check', '--clean-only', '--allow-unversioned-schemas'}:
            token += '=true'
        if not token.startswith('--') or '=' not in token:
            raise ValueError(f'Invalid settings argument: {token}')
        key, value = token.split('=', 1)
        if key == '--settings-file':
            raise ValueError('Nested settings-file is not supported')
        # Accept older unqualified arguments to keep existing build clients working.
        if ':' not in key:
            if key in {'--naming-conventions-file', '--dointf-classpath', '--dointf-input-artifact', '--dointf-input-class'}:
                legacy_counters[key] = legacy_counters.get(key, 0) + 1
                key += f':legacy-{legacy_counters[key]:08d}'
            elif key in {'--schema-input-dir', '--input-schema-naming-convention',
                         '--technology-dointf-output-dir', '--technology-dointf-input-dir',
                         '--technology-sdointf-output-dir', '--technology-sdoimpl-output-dir',
                         '--output-enum-technology-naming-convention'}:
                sub, sep, actual = value.partition(':')
                if sep:
                    key, value = f'{key}:{sub}', actual
            elif key in {'--output-interface-technology-naming-convention',
                         '--input-technology-naming-convention', '--output-technology-naming-convention'}:
                fields = value.split(':', 2)
                if len(fields) == 3:
                    kind, role, fields_value = fields
                    for part in fields_value.split(','):
                        sub, sep, actual = part.partition('=')
                        if not sep:
                            raise ValueError(f'Malformed naming assignment: {token}')
                        push(f'{key}:{kind}:{role}:{sub}={actual}')
                    return
        if not value:
            merged.pop(key, None)
        else:
            merged[key] = value

    for source, content in sources:
        for no, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            if any(ch.isspace() for ch in stripped):
                raise ValueError(f'Malformed settings at {source}:{no}: {line}')
            push(stripped)
    for arg in remainder:
        push(arg)

    expanded: list[str] = []
    for key, value in merged.items():
        base_key, sep, qualifier = key.partition(':')
        if base_key in {'--check', '--clean-only', '--allow-unversioned-schemas'}:
            if value.lower() not in {'true', 'false'}:
                raise ValueError(f'Expected boolean for {base_key}: {value}')
            if value.lower() == 'true':
                expanded.append(base_key)
        elif not sep or base_key in {'--naming-conventions-file', '--dointf-classpath',
                                    '--dointf-input-artifact', '--dointf-input-class'}:
            expanded.append(f'{base_key}={value}')
        elif base_key in {'--output-interface-technology-naming-convention',
                          '--input-technology-naming-convention', '--output-technology-naming-convention'}:
            pieces = qualifier.rsplit(':', 1)
            if len(pieces) != 2:
                raise ValueError(f'Invalid qualified naming option: {key}')
            expanded.append(f'{base_key}={pieces[0]}:{pieces[1]}={value}')
        else:
            expanded.append(f'{base_key}={qualifier}:{value}')
    return expanded
