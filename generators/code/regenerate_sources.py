#!/usr/bin/env python3
"""Clean or regenerate native Defs contracts for the standalone Codegen bootstrap.

Generated trees are disposable. Each build must remove their contents and
produce contracts from the currently checked-out schema sources, never retain
previous generated files or run an incremental upgrade against them.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

SOURCE_KINDS = ('jsondefs', 'yamldefs', 'xmldefs')
NAMING_PROFILES = {
    'jsondefs': 'algites-jsondef-schema-versioned_1',
    'yamldefs': 'algites-yamldef-schema-versioned_1',
    'xmldefs': 'algites-xmldef-schema-versioned_1',
}
NAMING_FILES = [f'resource:{name}' for name in (
    'standard-conventions.yml', 'algites-java-name-conventions.yml',
    'algites-python-name-conventions.yml', 'algites-jsondef-name-conventions.yml',
    'algites-yamldef-name-conventions.yml', 'algites-xmldef-name-conventions.yml',
    'algites-java-codegen-method-conventions.yml',
    'algites-python-codegen-method-conventions.yml',
)]
# Temporary bootstrap/build-source prerequisites until the Modustro
# build_source usage exists. Do not add these to Defs Codegen product metadata.
BOOTSTRAP_BUILD_SOURCE_PYTHON_DISTRIBUTIONS = (
    'eu_algites_pub_lib_general_naming_convention_impl',
    'eu_algites_pub_lib_general_naming_convention_profile_algites',
    'eu_algites_pub_lib_general_data_dataobject_intf',
)
SKIPPED = {'.git', '.gradle', 'build', '.venv', 'node_modules', '__pycache__', '.pytest_cache'}


def generated_roots(repository: Path, selected: Path | None = None) -> list[Path]:
    """Locate existing generated source roots without following symlinks."""
    result = []
    if selected is None:
        selected = repository
    if not selected.is_relative_to(repository):
        raise ValueError(f"Selected root escapes repository: {selected}")
    for current, dirs, _ in os.walk(selected, followlinks=False):
        folder = Path(current)
        if folder.name == 'src':
            for branch in folder.iterdir():
                if not branch.is_dir() or branch.is_symlink():
                    continue
                for name in ('java.gen', 'python.gen'):
                    target = branch / name
                    if target.is_symlink():
                        raise ValueError(f'Refusing symlinked generated directory: {target}')
                    if target.is_dir():
                        if not target.resolve().is_relative_to(repository):
                            raise ValueError(f'Generated output escapes repository: {target}')
                        result.append(target)
        dirs[:] = [name for name in dirs if name not in SKIPPED
                   and not (folder / name).is_symlink()]
    return sorted(set(result))


def artifact_outputs(repository: Path, selected: Path | None = None) -> dict[Path, list[str]]:
    result: dict[Path, list[str]] = {}
    for target in generated_roots(repository, selected):
        artifact = target.parent.parent.parent
        if not (artifact / 'modustro-artifact.yml').is_file():
            raise ValueError(f'Generated root has no declared artifact: {target}')
        result.setdefault(artifact, []).append(target.name.removesuffix('.gen'))
    return result


def clean(repository: Path, selected: Path | None = None) -> None:
    for target in generated_roots(repository, selected):
        for child in target.iterdir():
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()
        print(f'Cleaned generated source root: {target.relative_to(repository)}', flush=True)


def add_checkout_paths(checkout: Path) -> None:
    """Expose current source Python and naming-resource roots to the generator."""
    for path in sorted(checkout.rglob('src/product/python')):
        if 'build' not in path.relative_to(checkout).parts:
            sys.path.insert(0, str(path))
    for path in sorted(checkout.rglob('src/product/config')):
        if 'build' not in path.relative_to(checkout).parts:
            sys.path.insert(0, str(path))


def load_dependencies(repository: Path, source_general: Path | None, output: Path) -> None:
    if source_general is not None:
        source_general = source_general.resolve(strict=True)
        required = source_general / 'naming/convention/impl/src/product/python'
        profile = source_general / 'naming/convention/profile/algites/src/product/config'
        if not required.is_dir() or not profile.is_dir():
            raise ValueError(f'Missing bootstrap/build-source naming prerequisites in {source_general}')
        add_checkout_paths(source_general)
    else:
        home = Path(os.environ.get('MODUSTRO_HOME', str(Path.home() / '.modustro')))
        wheels = sorted((home / 'artifact-repos/python/packages').glob('eu_algites_*.whl'))
        selection = {}
        for wheel in wheels:
            package, sep, version = wheel.name.partition('-')
            if sep and version.startswith('1.1.dev'):
                if package not in selection or wheel.name > selection[package].name:
                    selection[package] = wheel
        if not all(key in selection for key in BOOTSTRAP_BUILD_SOURCE_PYTHON_DISTRIBUTIONS):
            raise RuntimeError('Current pub.lib.General sources or pinned 1.1 local Python '
                               'wheels are needed to regenerate Codegen contracts. '
                               'Set MODUSTRO_BOOTSTRAP_GENERAL_SOURCE_DIR or bootstrap '
                               'pub.lib.General first.')
        target = output / 'naming-python'
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check',
                        '--no-input', '--no-deps', '--target', str(target),
                        *[str(wheel) for wheel in selection.values()]], check=True)
        sys.path.insert(0, str(target))
    add_checkout_paths(repository)


def manifest(repository: Path, artifact: Path, languages: list[str]) -> dict:
    root = artifact / 'src/product'
    schemas = [{'kind': kind, 'directory': (root / kind).relative_to(repository).as_posix()}
               for kind in SOURCE_KINDS if (root / kind).is_dir()]
    if not schemas:
        raise ValueError(f'No schema source for generated artifact: {artifact}')
    return {
        'artifact': artifact.relative_to(repository).as_posix(),
        'languages': languages,
        'schema_inputs': schemas,
        'schema_input_naming_conventions': NAMING_PROFILES,
        'technology_outputs': {
            language: (root / (language + '.gen')).relative_to(repository).as_posix()
            for language in languages},
        'technology_output_naming_conventions': {
            language: {
                'common': f'algites-{language}-gen-intf-versioned_1',
                'jsondefs': f'algites-{language}-gen-json-intf-versioned_1',
                'yamldefs': f'algites-{language}-gen-yaml-intf-versioned_1',
                'xmldefs_type': f'algites-{language}-gen-xml-type-intf-versioned_1',
                'xmldefs_element': f'algites-{language}-gen-xml-element-intf-versioned_1',
                'xmldefs_namespace': f'algites-{language}-gen-xml-namespace-intf_1',
            } for language in languages
        },
        'technology_enum_output_naming_conventions': {
            language: f'algites-{language}-gen-enum-versioned_1' for language in languages
        },
        'generated_dataobject_method_naming_conventions': {
            language: f'algites-{language}-codegen-standard_1' for language in languages
        },
        'naming_convention_files': NAMING_FILES,
    }


def generate(repository: Path, source_general: Path | None, output: Path,
             selected: Path | None = None) -> None:
    modules = artifact_outputs(repository, selected)
    if not modules:
        print('No declared generated-source roots; nothing to regenerate.', flush=True)
        return
    output.mkdir(parents=True, exist_ok=True)
    load_dependencies(repository, source_general, output)
    from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import (
        AIcSchemaContractBindingsGenerator,
    )
    count = 0
    for artifact, languages in sorted(modules.items()):
        sources = AIcSchemaContractBindingsGenerator().generate_manifest(
            repository, manifest(repository, artifact, sorted(languages)))
        if not sources:
            raise RuntimeError(f'No code was generated for {artifact}')
        count += len(sources)
        for language in languages:
            target = artifact / 'src/product' / (language + '.gen')
            if not list(target.rglob('*.java' if language == 'java' else '*.py')):
                raise RuntimeError(f'Empty generated {language} source tree: {artifact}')
    print(f'Regenerated {count} Defs contracts in {len(modules)} Codegen artifacts', flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('clean', 'generate', 'list'))
    parser.add_argument('--repository', required=True, type=Path)
    parser.add_argument('--root', type=Path, default=Path('.'),
                        help='Repository-relative or absolute subtree to generate')
    parser.add_argument('--source-general', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    repo = args.repository.resolve(strict=True)
    selected = (repo / args.root).resolve(strict=True)
    if not selected.is_dir() or not selected.is_relative_to(repo):
        parser.error(f'Bootstrap root must remain inside repository: {selected}')
    if args.action == 'list':
        for item in generated_roots(repo, selected):
            print(item.relative_to(repo))
    elif args.action == 'clean':
        clean(repo, selected)
    else:
        if args.output is None:
            parser.error('generate requires --output')
        generate(repo, args.source_general, args.output.resolve(), selected)


if __name__ == '__main__':
    main()
