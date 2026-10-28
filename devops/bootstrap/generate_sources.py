#!/usr/bin/env python3
"""Generate Defs contracts in every selected artifact that declares matching schema sources.

This interim build-source step is deliberately shared by all repositories: the
Algites naming profiles and build-source prerequisites are temporary constants
HERE, not in Codegen's published product dependencies or per-repository runners.
If no applicable schemas/output roots exist, generation is a successful no-op.
"""
from __future__ import annotations

import argparse
import ast
import os
from pathlib import Path
import subprocess
import sys
import shutil
import tempfile

from clean_generated import generated_directories

SOURCE_KINDS = ('jsondefs', 'yamldefs', 'xmldefs')
# Temporary fixed Algites naming profile (until build_source and tool selection
# are represented by Modustro artifact metadata). Never infer from .settings.
ALGITES_INPUT_PROFILES = {
    'jsondefs': 'algites-jsondef-schema-versioned_1',
    'yamldefs': 'algites-yamldef-schema-versioned_1',
    'xmldefs': 'algites-xmldef-schema-versioned_1',
}
ALGITES_NAMING_FILES = [f'resource:{name}' for name in (
    'standard-conventions.yml', 'algites-java-name-conventions.yml',
    'algites-python-name-conventions.yml', 'algites-jsondef-name-conventions.yml',
    'algites-yamldef-name-conventions.yml', 'algites-xmldef-name-conventions.yml',
    'algites-java-codegen-method-conventions.yml',
    'algites-python-codegen-method-conventions.yml',
)]
# Temporary bootstrap-only build-source prerequisites. All repositories share
# this list until Modustro supports a declared build_source dependency usage.
BOOTSTRAP_BUILD_SOURCE_PYTHON_DISTRIBUTIONS = (
    'eu_algites_pub_tool_general_generators_code_defscodegen_impl',
    'eu_algites_pub_tool_general_generators_code_defscodegen_cli',
    'eu_algites_pub_lib_general_naming_convention_impl',
    'eu_algites_pub_lib_general_naming_convention_profile_algites',
    'eu_algites_pub_lib_general_data_dataobject_intf',
)
# The second generator is loaded only if SDO-eligible sources were found.
_BOOTSTRAP_SDO_PYTHON_DISTRIBUTIONS = (
    'eu_algites_pub_tool_general_generators_code_sdocodegen_intf',
    'eu_algites_pub_tool_general_generators_code_sdocodegen_impl',
    'eu_algites_pub_tool_general_generators_code_sdocodegen_cli',
    'eu_algites_pub_lib_general_data_smartdataobject_impl',
)
# These are *Python module identities*, not checkout/repository paths. A source
# checkout can place the module in any artifact exposing src/product/python.
_CODEGEN_MODULE = Path('eu/algites/tool/codegen/defs/impl/standard/'
                       'aic_schema_contract_bindings_generator.py')
_SDO_MODULE = Path('eu/algites/tool/codegen/sdo/impl/cli/aic_sdo_codegen_cli.py')
_NAMING_MODULE = Path('eu/algites/lib/naming/convention/impl/standard/'
                      'aic_name_convention_catalog.py')
_NAMING_PROFILE_RESOURCE = 'algites-java-name-conventions.yml'
_SKIPPED = frozenset({'.git', 'build', '.gradle', 'node_modules', '.venv', '__pycache__'})


def _schema_files(directory: Path, kind: str) -> bool:
    """Check real schema files, excluding metadata companions and empty roots."""
    extensions = {
        'jsondefs': ('.json',),
        'yamldefs': ('.json', '.yaml', '.yml'),
        'xmldefs': ('.xsd',),
    }[kind]
    return any(file.is_file() and not file.is_symlink()
               and not file.name.endswith('.meta.yml')
               and not file.name.endswith('.meta.yaml')
               and file.name.endswith(extensions)
               for file in directory.rglob('*'))


def _applicable_artifacts(repository: Path, root: Path) -> dict[tuple[Path, str], tuple[list[str], list[str]]]:
    """Discover generated target technologies together with source schema types."""
    outputs: dict[tuple[Path, str], set[str]] = {}
    for target in generated_directories(repository, root):
        artifact = target.parent.parent.parent
        if not (artifact / 'modustro-artifact.yml').is_file():
            raise ValueError(f'Undeclared generated source root: {target}')
        branch = target.parent.name
        outputs.setdefault((artifact, branch), set()).add(target.name.removesuffix('.gen'))
    result = {}
    for (artifact, branch), languages in sorted(outputs.items()):
        source = artifact / 'src' / branch
        kinds = []
        for kind in SOURCE_KINDS:
            directory = source / kind
            if directory.is_symlink():
                raise ValueError(f'Refusing symlinked schema input: {directory}')
            if directory.is_dir() and _schema_files(directory, kind):
                kinds.append(kind)
        if kinds:
            result[(artifact, branch)] = sorted(languages), kinds
    return result


def _manifest(repository: Path, artifact: Path, languages: list[str], kinds: list[str],
              branch: str = 'product') -> dict:
    source = artifact / 'src' / branch
    return {
        'artifact': artifact.relative_to(repository).as_posix(),
        'languages': languages,
        'schema_inputs': [
            {'kind': kind, 'directory': (source / kind).relative_to(repository).as_posix()}
            for kind in kinds
        ],
        'schema_input_naming_conventions': ALGITES_INPUT_PROFILES,
        'technology_outputs': {
            language: (source / (language + '.gen')).relative_to(repository).as_posix()
            for language in languages
        },
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
            language: f'algites-{language}-gen-enum-versioned_1'
            for language in languages
        },
        'generated_dataobject_method_naming_conventions': {
            language: f'algites-{language}-codegen-standard_1'
            for language in languages
        },
        'naming_convention_files': ALGITES_NAMING_FILES,
    }


def _source_checkouts(repository: Path) -> list[Path]:
    """Discover build sources by capabilities, never by repository names."""
    candidates = [repository]
    for key in ('MODUSTRO_BOOTSTRAP_CODEGEN_SOURCE',
                'MODUSTRO_BOOTSTRAP_NAMING_SOURCE',
                'MODUSTRO_BOOTSTRAP_GENERAL_SOURCE_DIR'):
        value = os.environ.get(key)
        if value:
            candidates.append(Path(value))
    # Look for sibling source checkouts only when generation is necessary.
    for item in sorted(repository.parent.iterdir()):
        if item.is_dir() and not item.is_symlink() and item.name not in _SKIPPED:
            candidates.append(item)
    unique = []
    for candidate in candidates:
        resolved = candidate.resolve(strict=True)
        if resolved not in unique:
            unique.append(resolved)
    return unique


def _has_python_module(checkout: Path, module: Path) -> bool:
    """Discover a module by its package-relative name, not by artifact layout."""
    for directory in checkout.rglob('src/product/python'):
        if not any(name in _SKIPPED for name in directory.relative_to(checkout).parts):
            if (directory / module).is_file():
                return True
    return False


def _has_algites_catalog(checkout: Path) -> bool:
    """The fixed bootstrap Algites profile must supply its catalog resources."""
    for directory in checkout.rglob('src/product/config'):
        if not any(name in _SKIPPED for name in directory.relative_to(checkout).parts):
            if any(file.is_file() for file in directory.rglob(_NAMING_PROFILE_RESOURCE)):
                return True
    return False


def _add_source_paths(checkout: Path) -> None:
    """Add available Python sources and bundled naming catalog resources."""
    for directory in sorted(checkout.rglob('src/product/python')):
        if not any(name in _SKIPPED for name in directory.relative_to(checkout).parts):
            sys.path.insert(0, str(directory))
    for directory in sorted(checkout.rglob('src/product/config')):
        if not any(name in _SKIPPED for name in directory.relative_to(checkout).parts):
            sys.path.insert(0, str(directory))


def _install_local_build_source(output: Path, module: Path) -> None:
    """Use versioned, already prepared local wheels without altering user site-packages."""
    required = set(BOOTSTRAP_BUILD_SOURCE_PYTHON_DISTRIBUTIONS)
    if module == _SDO_MODULE:
        required.update(_BOOTSTRAP_SDO_PYTHON_DISTRIBUTIONS)
    home = Path(os.environ.get('MODUSTRO_HOME', str(Path.home() / '.modustro')))
    package_dir = home / 'artifact-repos/python/packages'
    found: dict[str, Path] = {}
    for wheel in sorted(package_dir.glob('*.whl')):
        name, separator, version = wheel.name.partition('-')
        if separator and version.startswith('1.1.dev') and name in required:
            if name not in found or wheel.name > found[name].name:
                found[name] = wheel
    missing = required - set(found)
    if missing:
        raise RuntimeError('Missing bootstrap-only Algites build-source dependencies: '
                           + ', '.join(sorted(missing))
                           + '. Bootstrap the libraries first, or supply source checkouts.')
    target = output / 'codegen-python'
    target.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check',
                    '--no-input', '--no-deps', '--target', str(target),
                    *(str(found[name]) for name in sorted(found))], check=True)
    sys.path.insert(0, str(target))


def _load_codegen(repository: Path, output: Path, module: Path = _CODEGEN_MODULE):
    checkouts = _source_checkouts(repository)
    has_codegen = any(_has_python_module(checkout, module) for checkout in checkouts)
    has_naming = any(_has_python_module(checkout, _NAMING_MODULE)
                     and _has_algites_catalog(checkout) for checkout in checkouts)
    if has_codegen and has_naming:
        for checkout in checkouts:
            if (_has_python_module(checkout, module)
                    or (_has_python_module(checkout, _NAMING_MODULE)
                        and _has_algites_catalog(checkout))
                    or checkout == repository):
                _add_source_paths(checkout)
    else:
        _install_local_build_source(output, module)
        _add_source_paths(repository)
    if module == _SDO_MODULE:
        try:
            from eu.algites.tool.codegen.sdo.impl.cli.aic_sdo_codegen_cli import main as sdo_main
        except ImportError as error:
            raise RuntimeError('Cannot import the bootstrap SDO Codegen implementation') from error
        return sdo_main
    try:
        from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import (
            AIcSchemaContractBindingsGenerator,
        )
    except ImportError as error:
        raise RuntimeError('Cannot import the bootstrap Defs Codegen implementation') from error
    return AIcSchemaContractBindingsGenerator()


# Temporary bootstrap-level Algites SDO convention selection (not Codegen runtime
# dependencies). Explicit source and output profiles are common to all repositories.
_SDO_ROLES = {
    'common': '', 'xmldefs_type': '-xml-type', 'xmldefs_element': '-xml-element',
    'yamldefs': '-yaml', 'jsondefs': '-json',
}


def _python_contract_source(path: Path) -> bool:
    """Recognize source contracts without importing arbitrary application modules."""
    if path.is_symlink() or not path.is_file() or path.suffix != '.py':
        return False
    # Never recursively treat SDO outputs as fresh DataObject inputs.
    if path.name.startswith(('aiigd', 'aicgd', 'test_')) or path.name.endswith('_test.py'):
        return False
    try:
        tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    except (SyntaxError, UnicodeError) as exc:
        raise ValueError(f'Invalid Python source while discovering DataObjects: {path}') from exc
    for item in tree.body:
        if not isinstance(item, ast.ClassDef):
            continue
        if any(isinstance(node, (ast.Assign, ast.AnnAssign)) and (
                any(isinstance(target, ast.Name) and target.id == '__data_object__'
                    for target in node.targets) if isinstance(node, ast.Assign)
                else isinstance(node.target, ast.Name) and node.target.id == '__data_object__')
                for node in item.body):
            return True
    return False


def _sdo_python_artifacts(repository: Path, root: Path) -> list[tuple[Path, str]]:
    """Find DataObject sources even if their .gen output directory is absent."""
    found = []
    for declaration in sorted(root.rglob('modustro-artifact.yml')):
        if any(part in _SKIPPED for part in declaration.relative_to(root).parts):
            continue
        artifact = declaration.parent
        for branch in ('product', 'develop'):
            source = artifact / 'src' / branch
            generated = source / 'python.gen'
            handwritten = source / 'python'
            if any(_python_contract_source(path) for base in (handwritten, generated)
                   if base.is_dir() and not base.is_symlink()
                   for path in base.rglob('*.py')):
                if generated.is_symlink():
                    raise ValueError(f'Refusing symlinked generated root: {generated}')
                found.append((artifact, branch))
    return sorted(set(found))


def generate_sdo_python(repository: Path, root: Path, output: Path) -> int:
    """Run SDO after Defs, in the same output tree; preserve all Defs contracts."""
    output.mkdir(parents=True, exist_ok=True)
    modules = _sdo_python_artifacts(repository, root)
    if not modules:
        print('SDO Python: no DataObject contracts; nothing generated.', flush=True)
        return 0
    cli = _load_codegen(repository, output, _SDO_MODULE)
    total = 0
    for artifact, branch in modules:
        source = artifact / 'src' / branch
        destination = source / 'python.gen'
        destination.mkdir(parents=True, exist_ok=True)
        # One merged invocation per artifact is vital: the native CLI cleans only
        # SDO output families, but two separate CLI invocations would erase the
        # previous SDO output from the same artifact.
        with tempfile.TemporaryDirectory(prefix='algites-sdo-', dir=output) as temp:
            staging = Path(temp) / 'inputs'
            for base in (source / 'python', destination):
                if not base.is_dir():
                    continue
                for item in sorted(base.rglob('*.py')):
                    if item.name.startswith(('aiigd', 'aicgd', 'test_')) or item.name.endswith('_test.py'):
                        continue
                    if item.is_symlink():
                        raise ValueError(f'Refusing symlinked SDO input: {item}')
                    relative = item.relative_to(base)
                    target = staging / relative
                    if target.is_file() and target.read_bytes() != item.read_bytes():
                        raise ValueError(f'Conflicting manual/generated DataObject module: {relative}')
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(item, target)
            arguments = [
                f'--repository-root={repository}',
                f'--technology-dointf-input-dir=python:{staging}',
                f'--technology-sdointf-output-dir=python:{destination}',
                f'--technology-sdoimpl-output-dir=python:{destination}',
                '--sdointf-subpackage=impl.intf', '--sdoclass-subpackage=impl',
                '--generated-dataobject-method-naming-convention=python:algites-python-codegen-standard_1',
            ]
            arguments += [f'--naming-conventions-file={value}' for value in ALGITES_NAMING_FILES]
            for role, suffix in _SDO_ROLES.items():
                arguments.extend((
                    f'--input-technology-naming-convention=python:{role}:defsintf=algites-python-gen{suffix}-intf-versioned_1',
                    f'--output-technology-naming-convention=python:{role}:sdointf=algites-python-gen-data{suffix}-intf-versioned_1,sdoclass=algites-python-gen-data{suffix}-class-versioned_1',
                ))
            old_modules = set(destination.rglob('*.py'))
            outcome = cli(arguments)
            if outcome not in (0, None):
                raise RuntimeError(f'SDO Python generation failed for {artifact}: {outcome}')
            new_modules = set(destination.rglob('*.py')) - old_modules
            total += len(new_modules)
    print(f'SDO Python: generated {total} new files in {len(modules)} artifacts', flush=True)
    return total


def generate(repository: Path, root: Path, output: Path) -> int:
    modules = _applicable_artifacts(repository, root)
    if not modules:
        print('No applicable Defs schemas below the selected root; nothing generated.', flush=True)
        return 0
    codegen = _load_codegen(repository, output)
    produced = 0
    for (artifact, branch), (languages, kinds) in modules.items():
        sources = codegen.generate_manifest(
            repository, _manifest(repository, artifact, languages, kinds, branch))
        if not sources:
            raise RuntimeError(f'Defs Codegen produced no contracts for {artifact}')
        produced += len(sources)
        for language in languages:
            directory = artifact / 'src' / branch / (language + '.gen')
            suffix = '.java' if language == 'java' else '.py'
            if not any(path.is_file() for path in directory.rglob('*' + suffix)):
                raise RuntimeError(f'Incomplete {language} generation: {artifact}')
    print(f'Regenerated {produced} Defs contracts in {len(modules)} artifacts', flush=True)
    return produced


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', required=True, type=Path)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    repository = args.repository.resolve(strict=True)
    root = args.root.resolve(strict=True)
    if not root.is_relative_to(repository):
        parser.error(f'Root must remain inside repository: {root}')
    generate(repository, root, args.output.resolve())
    generate_sdo_python(repository, root, args.output.resolve())


if __name__ == '__main__':
    main()
