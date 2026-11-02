"""Technology-neutral, explicit artifact selector used by both code generators.

The resolver does not execute builds, contact remote repositories, or silently
substitute a different published snapshot. It resolves local artifacts only.
The bootstrap is responsible for preparing source dependencies in advance.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import os


@dataclass(frozen=True)
class ArtifactSpec:
    """One typed and validated selector from a semicolon-delimited setting."""
    kind: str
    name: str
    version: str
    group: str = ''


def parse_artifacts(value: str, technology: str) -> tuple[ArtifactSpec, ...]:
    """Parse Modustro, Maven or PEP 508 entries; preserve their source order.

    A semicolon separates entries. PEP 508 environment markers are not accepted
    in inline lists because a marker also uses the semicolon character.
    """
    if technology not in {'java', 'python'}:
        raise ValueError(f'Unsupported technology: {technology}')
    from packaging.requirements import Requirement
    result = []
    for raw in value.split(';'):
        entry = raw.strip()
        if not entry:
            raise ValueError(f'Empty artifact selector in {value!r}')
        prefix, sep, rest = entry.partition(':')
        kind = prefix if sep and prefix in {'modustro', 'maven', 'pypi'} else ''
        if kind:
            entry = rest
        if kind == 'modustro' or (not kind and '@' in entry):
            name, marker, version = entry.rpartition('@')
            if not marker or not name or not version:
                raise ValueError(f'Invalid Modustro artifact: {raw}')
            result.append(ArtifactSpec('modustro', name, version))
        elif kind == 'maven' or (not kind and technology == 'java'):
            if technology != 'java':
                raise ValueError('Maven coordinates are only valid for Java inputs')
            pieces = entry.split(':')
            if len(pieces) != 3 or any(not part for part in pieces):
                raise ValueError(f'Expected groupId:artifactId:version: {raw}')
            result.append(ArtifactSpec('maven', pieces[1], pieces[2], pieces[0]))
        else:
            if technology != 'python':
                raise ValueError('Python requirements are only valid for Python inputs')
            requirement = Requirement(entry)
            if requirement.marker is not None or requirement.url is not None or requirement.extras:
                raise ValueError(f'Environment markers, URLs and extras are unsupported: {raw}')
            if not requirement.specifier:
                raise ValueError(f'Python distribution requires a version selector: {raw}')
            result.append(ArtifactSpec('pypi', requirement.name, str(requirement.specifier)))
    return tuple(result)


def _python_candidates(repo: Path, name: str, modustro: bool = False) -> list[tuple[Version, Path]]:
    from packaging.version import Version
    normalized = re.sub(r'[-_.]+', '-', name).lower()
    candidates = []
    for path in (repo / 'python').rglob('*.whl') if (repo / 'python').is_dir() else ():
        stem = path.name[:-4].split('-')
        if len(stem) < 5:
            continue
        candidate_name = re.sub(r'[-_.]+', '-', stem[0]).lower()
        if candidate_name != normalized and not (modustro and candidate_name.endswith('-' + normalized)):
            continue
        try:
            candidates.append((Version(stem[1]), path))
        except ValueError:
            continue
    return candidates


def resolve_artifacts(specs: tuple[ArtifactSpec, ...], technology: str,
                      repository: Path | None = None) -> tuple[Path, ...]:
    """Resolve selected JARs or wheels from the local Modustro artifact store.

    Fails closed on missing or ambiguous artifacts. Does not rely on arbitrary
    Maven transitive dependencies as additional generation inputs.
    """
    from packaging.requirements import Requirement
    home = (repository or Path.home() / '.modustro/artifact-repos').expanduser().resolve()
    paths = []
    for spec in specs:
        if os.environ.get('MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE') == 'source' and (
                spec.kind == 'modustro' or spec.name.startswith('pub.')):
            prepared = set(filter(None, os.environ.get(
                'MODUSTRO_BOOTSTRAP_PREPARED_ARTIFACTS', '').split(',')))
            if spec.name not in prepared:
                raise ValueError(f'Source input {spec.name} is not declared in the '
                                 'prepared Modustro dependency graph; add it to '
                                 'the artifact build-time dependencies')
        if technology == 'java':
            if spec.kind == 'pypi':
                raise ValueError(f'Python requirement cannot select a Java artifact: {spec.name}')
            if spec.kind == 'maven':
                candidate = (home / 'java/maven' / spec.group.replace('.', '/') /
                             spec.name / spec.version / f'{spec.name}-{spec.version}.jar')
                matches = [candidate] if candidate.is_file() else []
            else:
                matches = list((home / 'java/maven').glob(
                    f'**/{spec.name}/{spec.version}/{spec.name}-{spec.version}.jar'))
            if len(matches) != 1:
                raise FileNotFoundError(f'Expected one local Java artifact for {spec}, found {matches}')
            paths.append(matches[0].resolve())
        else:
            if spec.kind == 'maven':
                raise ValueError(f'Maven coordinates cannot select a Python distribution: {spec.name}')
            candidates = _python_candidates(home, spec.name, spec.kind == 'modustro')
            if spec.kind == 'modustro':
                if spec.version.endswith('-SNAPSHOT'):
                    base = spec.version.removesuffix('-SNAPSHOT')
                    candidates = [(v,p) for v,p in candidates if str(v).startswith(base + '.dev')]
                else:
                    candidates = [(v,p) for v,p in candidates if str(v) == spec.version]
            else:
                requirement = Requirement(spec.name + spec.version)
                candidates = [(v,p) for v,p in candidates if v in requirement.specifier]
            if not candidates:
                raise FileNotFoundError(f'No local Python wheel satisfies {spec}')
            if spec.kind == 'modustro':
                # A logical Modustro identity maps to a distribution with its
                # organizational prefix (see bootstrap/prepare.py:python_name).
                # Multiple different distributions with this suffix are ambiguous.
                names = {p.name.rsplit('-', 4)[0] for _, p in candidates}
                if len(names) != 1:
                    raise ValueError(f'Ambiguous Modustro Python distribution {spec.name}: {sorted(names)}')
            chosen = max(candidates, key=lambda pair: pair[0])[1]
            paths.append(chosen.resolve())
    if len(set(paths)) != len(paths):
        raise ValueError('Duplicate resolved artifact in input list')
    return tuple(paths)
