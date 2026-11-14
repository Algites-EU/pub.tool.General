#!/usr/bin/env python3
"""Plan and prepare Modustro source dependencies across sibling checkouts.

This is a standalone, temporary bootstrap resolver. The Modustro Builder will
own this behavior after the Builder migration. Dependencies are discovered from
artifact descriptors, never from hard-coded repository or artifact lists.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
import re
from pathlib import Path
import subprocess
import sys

import yaml

SKIP = frozenset({'.git', '.gradle', 'build', 'node_modules', '.venv', '__pycache__', '.pytest_cache', 'devops.orig'})


@dataclass(frozen=True)
class Artifact:
    repository: Path
    relative: Path
    identifier: str
    group: str
    version: str
    technologies: frozenset[str]
    dependencies: tuple[tuple[str, str, dict], ...]


def read(path: Path) -> dict:
    with path.open(encoding='utf-8') as stream:
        return yaml.safe_load(stream) or {}


def repository_version(document: dict) -> str:
    value = document['Version']
    kind = str(value.get('QualifierKind', 'release')).lower()
    if kind not in ('release', 'snapshot'):
        raise ValueError(f'Unsupported version qualifier {kind!r}')
    return f"{value['ReleaseLineVersion']}.{value['Revision']}" + ('-SNAPSHOT' if kind == 'snapshot' else '')


def checkouts(repository: Path) -> list[Path]:
    candidates = [repository]
    for name in ('MODUSTRO_BOOTSTRAP_SOURCE_REPOSITORIES', 'MODUSTRO_BOOTSTRAP_CODEGEN_SOURCE',
                 'MODUSTRO_BOOTSTRAP_NAMING_SOURCE', 'MODUSTRO_BOOTSTRAP_GENERAL_SOURCE_DIR'):
        value = os.environ.get(name)
        if value:
            candidates.extend(Path(part) for part in value.split(os.pathsep) if part)
    for entry in sorted(repository.parent.iterdir()):
        if entry.is_dir() and not entry.is_symlink() and entry.name not in SKIP:
            candidates.append(entry)
    results = []
    seen_ids: dict[str, Path] = {}
    for candidate in candidates:
        candidate = candidate.resolve(strict=True)
        descriptor = candidate / 'modustro-source-repository.yml'
        if not descriptor.is_file():
            continue
        identifier = str(read(descriptor)['SourceRepository']['Id'])
        previous = seen_ids.get(identifier)
        if previous is not None and previous != candidate:
            raise ValueError(f'Ambiguous checkout for {identifier}: {previous} and {candidate}')
        if candidate not in results:
            seen_ids[identifier] = candidate
            results.append(candidate)
    if repository not in results:
        raise ValueError(f'Not a Modustro source repository: {repository}')
    return results


def descriptors(repo: Path):
    """Walk only descriptor directories; exclude generated/build/cache trees."""
    for current, dirs, names in os.walk(repo, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in SKIP and not d.startswith('.')
                         and not (Path(current) / d).is_symlink())
        if 'modustro-artifact.yml' in names:
            yield Path(current) / 'modustro-artifact.yml'


def group_for(repo: Path, directory: Path, fallback: str) -> str:
    cursor = directory
    while cursor != repo:
        parent = cursor / 'modustro-artifact-set.yml'
        if parent.is_file():
            group = read(parent).get('GroupId')
            if group:
                return str(group)
        cursor = cursor.parent
    return fallback


def catalog(repositories: list[Path]) -> dict[str, Artifact]:
    found: dict[str, Artifact] = {}
    for repo in repositories:
        descriptor = read(repo / 'modustro-source-repository.yml')
        owner = str(descriptor['SourceRepository']['Id'])
        fallback_group = str(descriptor['GroupId'])
        version = repository_version(descriptor)
        for filename in descriptors(repo):
            relative = filename.parent.relative_to(repo)
            definition = read(filename)
            technologies = frozenset(definition.get('Artifact', {}).get('TechnologyKinds') or [])
            if not technologies.intersection(('java', 'python')):
                continue
            identifier = owner + '_' + '.'.join(relative.parts)
            required: list[tuple[str, str, dict]] = []
            for block in definition.get('Dependencies') or []:
                if block.get('DependencyKind') != 'modustro':
                    continue
                for item in block.get('Items') or []:
                    if not any(str(u).startswith('product_') for u in item.get('Usages') or []):
                        continue
                    requirement = item.get('VersionRequirement') or {}
                    required.append((str(item['ArtifactId']), str(item.get('GroupId') or ''), requirement))
            artifact = Artifact(repo, relative, identifier,
                                group_for(repo, filename.parent, fallback_group), version,
                                technologies, tuple(required))
            if identifier in found:
                raise ValueError(f'Duplicate source artifact {identifier}: '
                                 f'{found[identifier].repository} and {repo}')
            found[identifier] = artifact
    return found


def compatible_version(actual: str, requirements: dict) -> bool:
    """Enforce descriptor Exact/Minimum/Maximum without invoking a package manager.

    Snapshot versions sort immediately before their corresponding releases.
    Unknown version forms are rejected instead of silently skipping constraints.
    """
    if not requirements:
        return True
    def comparable(value: str) -> tuple[tuple[int, ...], int]:
        match = re.fullmatch(r'(\d+(?:\.\d+)*)(-SNAPSHOT)?', value)
        if not match:
            raise ValueError(f'Unsupported Modustro dependency version {value!r}')
        parts = tuple(map(int, match.group(1).split('.')))
        return (parts + (0,) * max(0, 5 - len(parts)), 0 if match.group(2) else 1)
    version = comparable(actual)
    if requirements.get('Exact') is not None:
        return version == comparable(str(requirements['Exact']))
    for key, default in (('Minimum', '>='), ('Maximum', '<=')):
        if requirements.get(key) is None:
            continue
        value = str(requirements[key])
        match = re.fullmatch(r'(>=|<=|>|<|==)?\s*(.+)', value)
        if not match:
            raise ValueError(f'Invalid {key} requirement: {value}')
        op, boundary = match.group(1) or default, comparable(match.group(2))
        if key == 'Maximum' and requirements.get('MaximumStrict'):
            op = '<'
        if not {'>=': version >= boundary, '<=': version <= boundary,
                '>': version > boundary, '<': version < boundary,
                '==': version == boundary}[op]:
            return False
    return True


def resolve(repository: Path, root: Path, available: dict[str, Artifact]) -> tuple[list[Artifact], set[str]]:
    roots = [item for item in available.values()
             if item.repository == repository and (root == repository or
               (item.repository / item.relative).is_relative_to(root))]
    if not roots:
        raise ValueError(f'No Java/Python source artifacts beneath {root}')
    selected = {item.identifier for item in roots}
    state: dict[str, int] = {}
    path: list[str] = []
    ordered: list[Artifact] = []
    groups: set[str] = set()

    def visit(identifier: str) -> None:
        if state.get(identifier) == 2:
            return
        if state.get(identifier) == 1:
            start = path.index(identifier)
            raise ValueError('Modustro source dependency cycle: ' + ' -> '.join(path[start:] + [identifier]))
        item = available.get(identifier)
        if item is None:
            raise ValueError('Missing source checkout/artifact for Modustro dependency '
                             + identifier + ' (source mode never falls back to published binaries)')
        state[identifier] = 1
        groups.add(item.group)
        path.append(identifier)
        for dep_id, expected_group, version_requirement in item.dependencies:
            other = available.get(dep_id)
            if other is None:
                raise ValueError(f'{item.identifier}: missing Modustro source dependency {dep_id}; '
                                 'supply the owning sibling checkout or set '
                                 'MODUSTRO_BOOTSTRAP_SOURCE_REPOSITORIES')
            if expected_group and other.group != expected_group:
                raise ValueError(f'{item.identifier} -> {dep_id}: GroupId {expected_group!r} '
                                 f'does not match source {other.group!r}')
            if not compatible_version(other.version, version_requirement):
                raise ValueError(f'{item.identifier} -> {dep_id}: required version '
                                 f'{version_requirement!r}, source checkout has {other.version!r}')
            visit(dep_id)
        path.pop()
        state[identifier] = 2
        if identifier not in selected:
            ordered.append(item)

    for item in sorted(roots, key=lambda r: r.identifier):
        visit(item.identifier)
    return ordered, groups


@dataclass(frozen=True)
class SourceCompilerBootstrap:
    """Declarative source-compiler cycle, loaded from artifact-owner policy."""
    cli: Artifact
    seed_ids: frozenset[str]
    trigger_ids: frozenset[str]
    rebuild_ids: tuple[str, ...]


def compiler_bootstraps(available: dict[str, Artifact]) -> tuple[SourceCompilerBootstrap, ...]:
    """Discover special self-hosting cycles without naming any particular repo.

    The optional bootstrap-specializations.yml resides beside the universal
    engine.  Normal repositories have no compiler cycles and need no config.
    The CLI owner declares a cycle; its temporary ABI dependencies may be in
    other source repositories, and must be present in the resolved graph.
    """
    result = []
    seen = set()
    repositories = sorted({artifact.repository for artifact in available.values()})
    for repository in repositories:
        policy = repository / 'devops/bootstrap/bootstrap-specializations.yml'
        if not policy.is_file():
            continue
        document = read(policy)
        for definition in document.get('SourceCompilerBootstraps') or ():
            if not isinstance(definition, dict):
                raise ValueError(f'{policy}: expected mapping in SourceCompilerBootstraps')
            cli_id = definition.get('CliArtifactId')
            if not isinstance(cli_id, str) or not cli_id:
                raise ValueError(f'{policy}: missing CliArtifactId')
            cli = available.get(cli_id)
            if cli is None or cli.repository != repository:
                raise ValueError(f'{policy}: compiler CLI is not owned by this repository: {cli_id}')
            if cli_id in seen:
                raise ValueError(f'{policy}: duplicate source compiler bootstrap for {cli_id}')
            seen.add(cli_id)
            ids = {}
            for key in ('SeedArtifactIds', 'TriggerArtifactIds', 'RebuildAfterCliArtifactIds'):
                raw = definition.get(key)
                if not isinstance(raw, list) or not all(isinstance(x, str) and x for x in raw):
                    raise ValueError(f'{policy}: {key} must be an artifact ID list')
                if len(raw) != len(set(raw)):
                    raise ValueError(f'{policy}: duplicate artifact in {key}')
                for artifact_id in raw:
                    if artifact_id not in available:
                        raise ValueError(f'{policy}: missing configured artifact {artifact_id}')
                ids[key] = raw
            if not ids['TriggerArtifactIds'] or not ids['SeedArtifactIds']:
                raise ValueError(f'{policy}: source compiler needs triggers and ABI seeds')
            if not set(ids['RebuildAfterCliArtifactIds']).issubset(ids['SeedArtifactIds']):
                raise ValueError(f'{policy}: rebuilt artifacts must have an ABI seed')
            result.append(SourceCompilerBootstrap(
                cli=cli,
                seed_ids=frozenset(ids['SeedArtifactIds']),
                trigger_ids=frozenset(ids['TriggerArtifactIds']),
                rebuild_ids=tuple(ids['RebuildAfterCliArtifactIds']),
            ))
    return tuple(result)


def owns_compiler_root(program: SourceCompilerBootstrap,
                       roots: set[str], available: dict[str, Artifact]) -> bool:
    """Detect a self-hosted compiler's subtree from its actual CLI artifact."""
    owner = program.cli.repository
    directory = program.cli.relative.parent
    return any(item.repository == owner and item.relative.is_relative_to(directory)
               for name in roots if (item := available.get(name)) is not None)


def build_prerequisite(artifact: Artifact, *, seed: bool = False) -> None:
    command = ['bash', str(artifact.repository / 'devops/bootstrap/bootstrap.sh'),
               '--root', artifact.relative.as_posix(), '--prepare-only']
    env = dict(os.environ, MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE='source',
               MODUSTRO_BOOTSTRAP_SOURCE_PREREQUISITES_READY='1')
    env.pop('MODUSTRO_BOOTSTRAP_SDO_ABI_SEED', None)
    # An invocation's UUID and cleanup policy must not leak into the next
    # repository's independent self-hosting policy.
    if artifact.repository.resolve() != Path(__file__).resolve().parents[2]:
        env.pop('MODUSTRO_BOOTSTRAP_FRESH_GENERATION', None)
        env.pop('MODUSTRO_BOOTSTRAP_RUN_ID', None)
        # Never reuse a caller's generated-source cleanup setting in another
        # checkout: that checkout owns its default policy.
        env.pop('MODUSTRO_CODEGEN_CLEANUP_OUTPUT_FOLDER_BEFORE_GENERATION', None)
    if seed:
        # Artifact-local seed checking is entirely declarative. An ordinary
        # repository has no configured phase and needs no exception here.
        subprocess.run([sys.executable,
                        str(artifact.repository / 'devops/bootstrap/selfhosting.py'),
                        'phase', '--repository', str(artifact.repository),
                        '--root', str(artifact.repository / artifact.relative),
                        '--phase', 'check-seed'],
                       cwd=artifact.repository, env=env, check=True)
        env['MODUSTRO_BOOTSTRAP_SDO_ABI_SEED'] = '1'
    print(f"Building source prerequisite {artifact.identifier}" +
          (' (Defs-only compiler ABI seed)' if seed else ''), flush=True)
    subprocess.run(command, cwd=artifact.repository, env=env, check=True)


def prepare_compiler(program: SourceCompilerBootstrap,
                     available: dict[str, Artifact]) -> None:
    """Build one self-hosted CLI from seed contracts and regenerate its own API.

    Bootstrap seed selection comes exclusively from the owning repository's
    declarative policy. All real compilation is still delegated to the same
    universal bootstrap entry point; no alternate generator is involved.
    """
    cli = program.cli
    prerequisites, _ = resolve(cli.repository, cli.repository / cli.relative, available)
    for artifact in prerequisites:
        build_prerequisite(artifact, seed=artifact.identifier in program.seed_ids)
    build_prerequisite(cli)
    # Once the new generator CLI exists, replace explicitly declared ABI-only
    # publications with their complete freshly generated interface artifacts.
    required = {artifact.identifier for artifact in prerequisites}
    for identifier in program.rebuild_ids:
        if identifier in required:
            build_prerequisite(available[identifier])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('plan', 'prepare', 'groups', 'identifiers'))
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    repository = args.repository.resolve(strict=True)
    root = args.root.resolve(strict=True)
    if not root.is_relative_to(repository):
        raise ValueError(f'Source root must be inside its repository: {root}')
    available = catalog(checkouts(repository))
    todo, groups = resolve(repository, root, available)
    if args.action == 'groups':
        print(','.join(sorted(groups)))
        return
    if args.action == 'identifiers':
        selected = [item.identifier for item in available.values()
                    if item.repository == repository and (root == repository or
                        (item.repository / item.relative).is_relative_to(root))]
        print(','.join(sorted(set(selected) | {item.identifier for item in todo})))
        return
    print(f'Source prerequisites: {len(todo)} artifact(s) for {root.relative_to(repository)}', flush=True)
    for artifact in todo:
        print(f'  {artifact.identifier} [{artifact.group}:{artifact.version}] '
              f'from {artifact.repository.name}/{artifact.relative}', flush=True)
    if args.action == 'prepare':
        identifiers = {item.identifier for item in todo}
        roots = {item.identifier for item in available.values()
                 if item.repository == repository and (root == repository or
                     (item.repository / item.relative).is_relative_to(root))}
        programs = compiler_bootstraps(available)
        seeded_for_this_root: set[str] = set()
        for program in programs:
            generator_root = owns_compiler_root(program, roots, available)
            if not generator_root and program.trigger_ids.intersection(identifiers | roots):
                # Build the source compiler before generating its consumers.
                prepare_compiler(program, available)
                # A selected API interface already received its complete
                # publication after the compiler came online.
                if any(identifier in roots for identifier in program.rebuild_ids):
                    return
            if generator_root:
                seeded_for_this_root.update(program.seed_ids)
        for artifact in todo:
            build_prerequisite(artifact, seed=artifact.identifier in seeded_for_this_root)



if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f'Source dependency resolution failed: {exc}', file=sys.stderr)
        raise SystemExit(2) from exc
