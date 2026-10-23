"""Locate naming catalogs through Python package resources and sys.path.

The main Codegen path accumulates all matching classpath catalogs rather than
selecting a single winner. The legacy single-source resolver is retained for
callers that explicitly require one location.
"""
from __future__ import annotations

import importlib.resources
from pathlib import Path
import re
import sys


_RESOURCE_PREFIXES = ('classpath:', 'resource:')
_PROVIDERS = (
    ('eu.algites.lib.naming.convention', ()),
    ('algites.pub.lib.general.naming.convention.algites',
     ('eu', 'algites', 'lib', 'naming', 'convention')),
)


def resolve_naming_catalog(source: str) -> str:
    """Return a filesystem override or the existing naming-library resource URI.

    The override is deliberately limited to a file directly beneath each
    ``sys.path`` root; a non-direct descendant is a package resource and must
    be obtained through the package-resource provider. When a filesystem
    override is selected, the naming library reads referenced sibling YAML
    files from the same directory.
    """
    if not source.startswith(_RESOURCE_PREFIXES):
        return source
    name = source.partition(':')[2]
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*\.yml', name):
        raise ValueError(f'Invalid classpath naming catalog filename: {name!r}')

    packaged = False
    for package, subpath in _PROVIDERS:
        try:
            candidate = importlib.resources.files(package).joinpath(*subpath, name)
            if candidate.is_file():
                packaged = True
                break
        except (ModuleNotFoundError, TypeError, FileNotFoundError):
            continue

    for item in sys.path:
        # The empty sys.path entry denotes the current working directory.
        candidate = Path(item or '.').joinpath(name)
        if candidate.is_file():
            return str(candidate.resolve())
    if packaged:
        return 'resource:' + name
    raise FileNotFoundError(
        f'Naming catalog {name!r} not found in importlib.resources '
        'or as a direct file in any sys.path directory')


from contextlib import contextmanager
from tempfile import TemporaryDirectory


@contextmanager
def expand_naming_catalogs(sources):
    """Collect every classpath naming resource into one ordered catalog set.

    Package resources are enumerated first, followed by direct sys.path roots
    (in reverse order for standard Python import precedence). Every resource is
    materialized with its referenced StandardConventionsFile sibling, including
    ZIP-backed Traversables. Identical physical locations are deduplicated.
    Distinct conflicting naming IDs remain errors in the naming library.
    """
    resolved = []
    physical_seen = set()
    with TemporaryDirectory(prefix='algites-naming-classpath-') as temp:
        staging = Path(temp)
        index = 0

        def add_packaged(candidate, name, provider_root):
            nonlocal index
            if not candidate.is_file():
                return
            if isinstance(candidate, Path):
                absolute = candidate.resolve()
                if absolute in physical_seen:
                    return
                physical_seen.add(absolute)
            index += 1
            folder = staging / str(index)
            folder.mkdir(parents=True)
            text = candidate.read_text(encoding='utf-8')
            (folder / name).write_text(text, encoding='utf-8')
            standard = re.search(
                r'(?m)^\s*StandardConventionsFile:\s*[\"\']?([A-Za-z0-9][A-Za-z0-9_.-]*\.yml)',
                text)
            if standard:
                sibling = provider_root.joinpath(standard.group(1))
                if not sibling.is_file():
                    raise FileNotFoundError(
                        f'Missing StandardConventionsFile {standard.group(1)!r} next to {name!r}')
                (folder / standard.group(1)).write_bytes(sibling.read_bytes())
            resolved.append(str(folder / name))

        for source in sources:
            if not source.startswith(_RESOURCE_PREFIXES):
                resolved.append(source)
                continue
            name = source.partition(':')[2]
            if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*\.yml', name):
                raise ValueError(f'Invalid classpath naming catalog filename: {name!r}')
            matched = False
            for package, subpath in _PROVIDERS:
                try:
                    provider_root = importlib.resources.files(package).joinpath(*subpath)
                    candidate = provider_root.joinpath(name)
                    if candidate.is_file():
                        matched = True
                    add_packaged(candidate, name, provider_root)
                except (ModuleNotFoundError, TypeError, FileNotFoundError) as exc:
                    if isinstance(exc, FileNotFoundError) and 'StandardConventionsFile' in str(exc):
                        raise
                    continue
            for entry in reversed(sys.path):
                directory = Path(entry or '.')
                for candidate in (directory / 'eu/algites/lib/naming/convention' / name,
                                  directory / name):
                    if candidate.is_file():
                        matched = True
                        absolute = candidate.resolve()
                        if absolute not in physical_seen:
                            physical_seen.add(absolute)
                            resolved.append(str(absolute))
            if not matched:
                raise FileNotFoundError(f'Naming catalog {name!r} not found on package or sys.path')
        yield resolved
