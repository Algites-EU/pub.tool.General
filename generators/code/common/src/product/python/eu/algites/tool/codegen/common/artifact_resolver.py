"""Technology-neutral, explicit artifact selector used by both code generators.

The resolver does not execute builds, contact remote repositories, or silently
substitute a different published snapshot. It resolves local artifacts only.
The bootstrap is responsible for preparing source dependencies in advance.
"""
from __future__ import annotations

from eu.algites.tool.codegen.common.aix_codegen_validation_exception import AIxCodegenValidationException
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
        raise AIxCodegenValidationException(f'Unsupported technology: {technology}', 'Check the selected artifact coordinates, version and selected technology. For Modustro use artifactId@version; for Maven use groupId:artifactId:version; for Python use a PEP 508 distribution requirement. Separate artifacts with semicolons.')
    from packaging.requirements import Requirement
    result = []
    for raw in value.split(';'):
        entry = raw.strip()
        if not entry:
            raise AIxCodegenValidationException(f'Empty artifact selector in {value!r}', 'Check the selected artifact coordinates, version and selected technology. For Modustro use artifactId@version; for Maven use groupId:artifactId:version; for Python use a PEP 508 distribution requirement. Separate artifacts with semicolons.')
        prefix, sep, rest = entry.partition(':')
        kind = prefix if sep and prefix in {'modustro', 'maven', 'pypi'} else ''
        if kind:
            entry = rest
        if kind == 'modustro' or (not kind and '@' in entry):
            name, marker, version = entry.rpartition('@')
            if not marker or not name or not version:
                raise AIxCodegenValidationException(f'Invalid Modustro artifact: {raw}', 'Check the selected artifact coordinates, version and selected technology. For Modustro use artifactId@version; for Maven use groupId:artifactId:version; for Python use a PEP 508 distribution requirement. Separate artifacts with semicolons.')
            result.append(ArtifactSpec('modustro', name, version))
        elif kind == 'maven' or (not kind and technology == 'java'):
            if technology != 'java':
                raise AIxCodegenValidationException('Maven coordinates are only valid for Java inputs', 'Check the selected artifact coordinates, version and selected technology. For Modustro use artifactId@version; for Maven use groupId:artifactId:version; for Python use a PEP 508 distribution requirement. Separate artifacts with semicolons.')
            pieces = entry.split(':')
            if len(pieces) != 3 or any(not part for part in pieces):
                raise AIxCodegenValidationException(f'Expected groupId:artifactId:version: {raw}', 'Check the selected artifact coordinates, version and selected technology. For Modustro use artifactId@version; for Maven use groupId:artifactId:version; for Python use a PEP 508 distribution requirement. Separate artifacts with semicolons.')
            result.append(ArtifactSpec('maven', pieces[1], pieces[2], pieces[0]))
        else:
            if technology != 'python':
                raise AIxCodegenValidationException('Python requirements are only valid for Python inputs', 'Check the selected artifact coordinates, version and selected technology. For Modustro use artifactId@version; for Maven use groupId:artifactId:version; for Python use a PEP 508 distribution requirement. Separate artifacts with semicolons.')
            requirement = Requirement(entry)
            if requirement.marker is not None or requirement.url is not None or requirement.extras:
                raise AIxCodegenValidationException(f'Environment markers, URLs and extras are unsupported: {raw}', 'Check the selected artifact coordinates, version and selected technology. For Modustro use artifactId@version; for Maven use groupId:artifactId:version; for Python use a PEP 508 distribution requirement. Separate artifacts with semicolons.')
            if not requirement.specifier:
                raise AIxCodegenValidationException(f'Python distribution requires a version selector: {raw}', 'Check the selected artifact coordinates, version and selected technology. For Modustro use artifactId@version; for Maven use groupId:artifactId:version; for Python use a PEP 508 distribution requirement. Separate artifacts with semicolons.')
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
                raise AIxCodegenValidationException(f'Source input {spec.name} is not declared in the '
                                 'prepared Modustro dependency graph; add it to '
                                 'the artifact build-time dependencies', 'Declare this source artifact as a build-time dependency in the current Modustro artifact and prepare the dependency graph before running Codegen in source mode.')
        if technology == 'java':
            if spec.kind == 'pypi':
                raise AIxCodegenValidationException(f'Python requirement cannot select a Java artifact: {spec.name}', 'Check the selected artifact coordinates, version and selected technology. For Modustro use artifactId@version; for Maven use groupId:artifactId:version; for Python use a PEP 508 distribution requirement. Separate artifacts with semicolons.')
            if spec.kind == 'maven':
                candidate = (home / 'java/maven' / spec.group.replace('.', '/') /
                             spec.name / spec.version / f'{spec.name}-{spec.version}.jar')
                matches = [candidate] if candidate.is_file() else []
            else:
                matches = list((home / 'java/maven').glob(
                    f'**/{spec.name}/{spec.version}/{spec.name}-{spec.version}.jar'))
            if len(matches) != 1:
                raise AIxCodegenValidationException(f'Expected one local Java artifact for {spec}, found {matches}', 'Prepare the selected Maven/Modustro JAR in the local artifact repository and check its group, artifact ID and version.')
            paths.append(matches[0].resolve())
        else:
            if spec.kind == 'maven':
                raise AIxCodegenValidationException(f'Maven coordinates cannot select a Python distribution: {spec.name}', 'Check the selected artifact coordinates, version and selected technology. For Modustro use artifactId@version; for Maven use groupId:artifactId:version; for Python use a PEP 508 distribution requirement. Separate artifacts with semicolons.')
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
                raise AIxCodegenValidationException(f'No local Python wheel satisfies {spec}', 'Prepare a wheel matching this Python distribution and version requirement, or adjust the selected input artifact requirement.')
            if spec.kind == 'modustro':
                # A logical Modustro identity maps to a distribution with its
                # organizational prefix (see bootstrap/prepare.py:python_name).
                # Multiple different distributions with this suffix are ambiguous.
                names = {p.name.rsplit('-', 4)[0] for _, p in candidates}
                if len(names) != 1:
                    raise AIxCodegenValidationException(f'Ambiguous Modustro Python distribution {spec.name}: {sorted(names)}', 'Use a more specific distribution identity so that exactly one matching Modustro artifact can be resolved.')
            chosen = max(candidates, key=lambda pair: pair[0])[1]
            paths.append(chosen.resolve())
    if len(set(paths)) != len(paths):
        raise AIxCodegenValidationException('Duplicate resolved artifact in input list', 'Remove repeated artifact coordinates from the semicolon-separated input list; each resolved artifact must occur only once.')
    return tuple(paths)
