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

    # Qualified option names are the stable configuration identity. Do not
    # translate them into the obsolete kind:value parser representation.
    merged: dict[str, str] = {}

    def push(token: str) -> None:
        if token in {'--check', '--clean-only', '--allow-unversioned-schemas'}:
            token += '=true'
        if not token.startswith('--') or '=' not in token:
            raise ValueError(f'Invalid settings argument: {token}')
        key, value = token.split('=', 1)
        if key == '--settings-file':
            raise ValueError('Nested settings-file is not supported')
        if value == '':
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
        if key in {'--check', '--clean-only', '--allow-unversioned-schemas'}:
            if value.lower() not in {'true', 'false'}:
                raise ValueError(f'Expected boolean for {key}: {value}')
            if value.lower() == 'true':
                expanded.append(key)
        else:
            expanded.append(f'{key}={value}')
    return expanded
