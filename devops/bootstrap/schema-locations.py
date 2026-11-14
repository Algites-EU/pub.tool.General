#!/usr/bin/env python3
"""Create a deterministic source-dependency schema URL -> local path index.

The URL is schema identity, not a transport requirement.  Only product schemas
owned by the selected artifact(s) or their transitive Modustro dependencies are
included.  A bootstrap-generated map is strict; ambiguous declarations are errors.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
import json

import yaml

TECHNOLOGIES = {
    'xmldefs': '.xsd',
    'jsondefs': '.jsondef.schema.json',
    'yamldefs': '.yamldef.schema.json',
}
BASE = 'https://defs.dev.algites.eu/api/'


def load_dependencies_script(repository: Path):
    """Reuse the existing build dependency graph; do not invent another graph."""
    filename = repository / 'devops/bootstrap/source-dependencies.py'
    spec = importlib.util.spec_from_file_location('modustro_bootstrap_source_dependencies', filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def selected_artifacts(repository: Path, root: Path):
    """Return selected and transitively required Modustro artifact descriptors."""
    graph = load_dependencies_script(repository)
    available = graph.catalog(graph.checkouts(repository))
    prerequisites, _ = graph.resolve(repository, root, available)
    own = [artifact for artifact in available.values() if artifact.repository == repository and
           (root == repository or (artifact.repository / artifact.relative).is_relative_to(root))]
    # The product dependency graph covers compiled/runtime APIs.  Some schema
    # imports are needed only while generating code (e.g. XML annotation
    # vocabularies) and therefore have develop_* rather than product_* usage.
    # Follow those explicitly declared edges without turning a Java-only
    # schema vocabulary into a Python runtime distribution dependency.
    selected = {}
    pending = [*prerequisites, *own]
    while pending:
        artifact = pending.pop()
        if artifact.identifier in selected:
            continue
        selected[artifact.identifier] = artifact
        descriptor = graph.read(artifact.repository / artifact.relative / 'modustro-artifact.yml')
        for block in descriptor.get('Dependencies') or ():
            if block.get('DependencyKind') != 'modustro':
                continue
            for dependency in block.get('Items') or ():
                usages = dependency.get('Usages') or ()
                if not any(str(usage).startswith('develop_') for usage in usages):
                    continue
                identifier = str(dependency['ArtifactId'])
                target = available.get(identifier)
                if target is None:
                    raise ValueError(f'{artifact.identifier}: missing source checkout for '
                                     f'schema/build dependency {identifier}')
                expected_group = str(dependency.get('GroupId') or '')
                if expected_group and target.group != expected_group:
                    raise ValueError(f'{artifact.identifier} -> {identifier}: '
                                     f'GroupId {expected_group!r} != {target.group!r}')
                requirement = dependency.get('VersionRequirement') or {}
                if not graph.compatible_version(target.version, requirement):
                    raise ValueError(f'{artifact.identifier} -> {identifier}: incompatible '
                                     f'source version {target.version!r}')
                # The schema-only prerequisite may itself import schemas
                # belonging to its ordinary product dependencies.
                required, _ = graph.resolve(target.repository,
                                            target.repository / target.relative, available)
                pending.extend([*required, target])
    return sorted(selected.values(), key=lambda artifact: artifact.identifier)


def identity(path: Path, kind: str) -> str:
    """Read public publication identity from the schema's companion metadata."""
    meta = path.with_name(path.name + '.meta.yml')
    if not meta.is_file() or meta.is_symlink():
        raise ValueError(f'Missing safe schema publication metadata: {meta}')
    data = yaml.safe_load(meta.read_text(encoding='utf-8')) or {}
    publication = data.get('GlobalPublicationPathId')
    if not isinstance(publication, str) or not publication.strip() or publication.startswith('/'):
        raise ValueError(f'Missing GlobalPublicationPathId in {meta}')
    if '..' in Path(publication).parts or '\\' in publication or '?' in publication or '#' in publication:
        raise ValueError(f'Invalid schema publication path {publication!r} in {meta}')
    if not publication.endswith(TECHNOLOGIES[kind]):
        raise ValueError(f'Wrong schema technology in {meta}: {publication}')
    uri = BASE + kind + '/' + publication.lstrip('/')
    parsed = urlsplit(uri)
    if parsed.scheme != 'https' or not parsed.hostname:
        raise ValueError(f'Invalid public schema URL: {uri}')
    if kind != 'xmldefs':
        content = json.loads(path.read_text(encoding='utf-8'))
        declared = content.get('$id')
        if declared and declared != uri:
            raise ValueError(f'Schema $id differs from GlobalPublicationPathId: {path}: {declared} != {uri}')
    else:
        # XML namespaces can differ from publication URLs.  An XSD without
        # a target namespace still has an identity supplied by its metadata.
        element = ET.parse(path).getroot()
        if element.tag != '{http://www.w3.org/2001/XMLSchema}schema':
            raise ValueError(f'Expected XML Schema: {path}')
    return uri


def collect(repository: Path, root: Path) -> dict[str, Path]:
    mapping: dict[str, Path] = {}
    for artifact in selected_artifacts(repository, root):
        owner = artifact.repository / artifact.relative / 'src/product'
        for kind, suffix in TECHNOLOGIES.items():
            folder = owner / kind
            if not folder.is_dir():
                continue
            if folder.is_symlink():
                raise ValueError(f'Symlinked schema directory: {folder}')
            for file in sorted(folder.rglob('*')):
                if not file.name.endswith(suffix) or not file.is_file():
                    continue
                if file.is_symlink():
                    raise ValueError(f'Symlinked schema: {file}')
                uri = identity(file, kind)
                existing = mapping.get(uri)
                if existing is not None:
                    if existing.read_bytes() != file.read_bytes():
                        raise ValueError(f'Conflicting source schema URL {uri}: {existing} and {file}')
                    continue
                mapping[uri] = file.resolve(strict=True)
    return mapping


def save(repository: Path, root: Path, output: Path) -> int:
    mapping = collect(repository, root)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.is_symlink():
        raise ValueError(f'Refusing symlinked schema map: {output}')
    lines = ['# Schema identities mapped to local source-dependency files.',
             '# Generated by Modustro bootstrap; URLs are NOT downloaded.',
             *(f'{url}={filename}' for url, filename in sorted(mapping.items()))]
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=output.parent,
                                     prefix='.schema-locations-', delete=False) as stream:
        temporary = Path(stream.name)
        stream.write('\n'.join(lines) + '\n')
    os.replace(temporary, output)
    print(f'Schema locations: {len(mapping)} schema(s) from selected artifacts and dependencies: {output}',
          flush=True)
    return len(mapping)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    repository = args.repository.resolve(strict=True)
    root = args.root.resolve(strict=True)
    if not root.is_relative_to(repository):
        parser.error(f'Root {root} must be inside {repository}')
    save(repository, root, args.output.resolve())


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, ET.ParseError, yaml.YAMLError, json.JSONDecodeError) as error:
        print(f'Schema location pre-resolution failed: {error}', file=sys.stderr)
        raise SystemExit(2) from error
