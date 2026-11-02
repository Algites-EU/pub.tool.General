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


# The naming definition module owns the read-only contracts consumed by the
# SDO generator's own naming implementation. Bootstrap it in two stages:
# first publish its Defs-only ABI, then compile the generator from source,
# and finally regenerate/publish the complete naming artifact. This seed is
# strictly confined to the generator's dependency graph.
NAMING_ABI_SEED = 'pub.lib.General_naming.convention.intf'
SDO_CLI = 'pub.tool.General_generators.code.sdocodegen.cli'


def build_prerequisite(artifact: Artifact, *, seed: bool = False) -> None:
    command = ['bash', str(artifact.repository / 'devops/bootstrap/bootstrap.sh'),
               '--root', artifact.relative.as_posix(), '--prepare-only']
    env = dict(os.environ, MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE='source',
               MODUSTRO_BOOTSTRAP_SOURCE_PREREQUISITES_READY='1')
    env.pop('MODUSTRO_BOOTSTRAP_SDO_ABI_SEED', None)
    if seed:
        if artifact.identifier != NAMING_ABI_SEED:
            raise ValueError(f'ABI seed is forbidden for {artifact.identifier}')
        env['MODUSTRO_BOOTSTRAP_SDO_ABI_SEED'] = '1'
    print(f"Building source prerequisite {artifact.identifier}" +
          (' (Defs-only naming ABI seed)' if seed else ''), flush=True)
    subprocess.run(command, cwd=artifact.repository, env=env, check=True)


def prepare_sdo_generator(repository: Path, available: dict[str, Artifact]) -> None:
    """Build the CLI and its source prerequisites, seeding the naming ABI.

    This must not silently reuse a previously published CLI. The generator
    itself is prepared with its complete normal dependency graph, except for
    the one ABI-only naming seed required to break the bootstrap cycle.
    """
    cli = available.get(SDO_CLI)
    if cli is None:
        raise ValueError('Source mode requires the SDO CLI checkout: ' + SDO_CLI)
    prerequisites, _ = resolve(cli.repository, cli.repository / cli.relative, available)
    for artifact in prerequisites:
        build_prerequisite(artifact, seed=artifact.identifier == NAMING_ABI_SEED)
    build_prerequisite(cli)


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
        generator_root = SDO_CLI in roots or any(item.startswith(
            'pub.tool.General_generators.code.sdocodegen.') for item in roots)
        if (NAMING_ABI_SEED in identifiers or NAMING_ABI_SEED in roots) and not generator_root:
            # The target depends on generated naming contracts. Build the
            # generator *first*, without accepting an old cached CLI binary.
            # The generator's own bootstrap uses the Defs-only naming seed.
            prepare_sdo_generator(repository, available)
        for artifact in todo:
            build_prerequisite(artifact, seed=(generator_root and
                               artifact.identifier == NAMING_ABI_SEED))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f'Source dependency resolution failed: {exc}', file=sys.stderr)
        raise SystemExit(2) from exc
