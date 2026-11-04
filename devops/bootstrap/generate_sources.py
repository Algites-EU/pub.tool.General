#!/usr/bin/env python3
"""Generate Defs contracts in every selected artifact that declares matching schema sources.

This interim build-source step is deliberately shared by all repositories: the
Algites naming profiles and build-source prerequisites are temporary constants
HERE, not in Codegen's published product dependencies or per-repository runners.
If no applicable schemas/output roots exist, generation is a successful no-op.
"""
from __future__ import annotations

import argparse
from email.parser import BytesParser
import zipfile
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
    'algites-java-common-codegen-conventions.yml',
    'algites-python-common-codegen-conventions.yml',
    'algites-java-defs-codegen-conventions.yml',
    'algites-python-defs-codegen-conventions.yml',
    'algites-java-sdo-codegen-conventions.yml',
    'algites-python-sdo-codegen-conventions.yml',
)]
# Temporary bootstrap-only build-source prerequisites. All repositories share
# this list until Modustro supports a declared build_source dependency usage.
BOOTSTRAP_BUILD_SOURCE_PYTHON_DISTRIBUTIONS = (
    'eu_algites_pub_tool_general_generators_code_common',
    'eu_algites_pub_tool_general_generators_code_defscodegen_intf',
    'eu_algites_pub_tool_general_generators_code_defscodegen_impl',
    'eu_algites_pub_tool_general_generators_code_defscodegen_cli',
    'eu_algites_pub_lib_general_naming_convention_impl',
    'eu_algites_pub_lib_general_naming_convention_profile_algites',
    'eu_algites_pub_tool_general_generators_code_profile_algites',
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
_CODEGEN_MODULE = Path('eu/algites/tool/codegen/defs/old/impl/cli/'
                       'aic_defs_codegen_cli.py')
_SDO_MODULE = Path('eu/algites/tool/codegen/sdo/old/impl/cli/aic_sdo_codegen_cli.py')
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
        'common_codegen_naming_conventions': {
            language: f'algites-{language}-codegen-common_1'
            for language in languages
        },
        'defs_codegen_naming_conventions': {
            language: f'algites-{language}-defscodegen-standard_1'
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
    # pip --no-deps is intentional: never query a remote index during local
    # bootstrap. Resolve Modustro runtime dependencies from wheel metadata
    # first, including dependencies introduced after the fixed seed list.
    from packaging.requirements import Requirement
    from packaging.utils import canonicalize_name
    from packaging.version import Version

    pending = list(found.values())
    constraints = []
    while pending:
        wheel = pending.pop()
        with zipfile.ZipFile(wheel) as archive:
            metadata = [name for name in archive.namelist()
                        if name.endswith('.dist-info/METADATA')]
            if len(metadata) != 1:
                raise RuntimeError(f'Expected one wheel METADATA file: {wheel}')
            message = BytesParser().parsebytes(archive.read(metadata[0]))
        for value in message.get_all('Requires-Dist', []):
            requirement = Requirement(value)
            if requirement.marker and not requirement.marker.evaluate():
                continue
            name = canonicalize_name(requirement.name).replace('-', '_')
            if not name.startswith('eu_algites_'):
                continue  # External runtime libraries belong to the bootstrap host.
            constraints.append((wheel, name, requirement))
            if name in found:
                continue
            candidates = [candidate for candidate in package_dir.glob(name + '-*.whl')
                          if candidate.name.split('-')[1].startswith('1.1.dev')]
            if not candidates:
                raise RuntimeError(f'{wheel.name}: missing local bootstrap dependency '
                                   f'{requirement}; prepare its artifact first')
            selected = max(candidates, key=lambda item: Version(item.name.split('-')[1]))
            found[name] = selected
            pending.append(selected)
    for owner, name, requirement in constraints:
        version = Version(found[name].name.split('-')[1])
        if requirement.url or version not in requirement.specifier:
            raise RuntimeError(f'{owner.name}: local bootstrap dependency '
                               f'{requirement} is incompatible with {found[name].name}')
    target = output / 'codegen-python' 
    target.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check',
                    '--no-input', '--no-deps', '--upgrade', '--target', str(target),
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
        # Prefer current generator sources even when naming must use local wheels.
        for checkout in checkouts:
            if checkout == repository or _has_python_module(checkout, module):
                _add_source_paths(checkout)
    if module == _SDO_MODULE:
        try:
            from eu.algites.tool.codegen.sdo.old.impl.cli.aic_sdo_codegen_cli import main as sdo_main
        except ImportError as error:
            raise RuntimeError('Cannot import the bootstrap SDO Codegen implementation') from error
        return sdo_main
    try:
        from eu.algites.tool.codegen.defs.old.impl.cli.aic_defs_codegen_cli import (
            AIcDefsCodegenCli,
        )
    except ImportError as error:
        raise RuntimeError('Cannot import the bootstrap Defs Codegen CLI') from error
    return AIcDefsCodegenCli.main


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
        if _validation_policy() == 'false':
            # Leave malformed sources for the SDO CLI validation collector.
            # Discovery must not hide later errors by failing first.
            return True
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
                '--codegen-validate-one-input-at-a-time-only=' + _validation_policy(),
                f'--technology-dointf-input-dir:python={staging}',
                f'--technology-sdointf-output-dir:python={destination}',
                f'--technology-sdoimpl-output-dir:python={destination}',
                '--sdointf-subpackage=impl.intf', '--sdoclass-subpackage=impl',
                '--common-codegen-naming-convention:python=algites-python-codegen-common_1',
                '--sdo-codegen-naming-convention:python=algites-python-sdocodegen-standard_1',
            ]
            arguments += [f'--naming-conventions-file:catalog-{index}={value}'
                          for index, value in enumerate(ALGITES_NAMING_FILES)]
            arguments += [
                '--naming-conventions-file:codegen_common=classpath:algites-python-common-codegen-conventions.yml',
                '--naming-conventions-file:codegen_sdo=classpath:algites-python-sdo-codegen-conventions.yml',
            ]
            for role, suffix in _SDO_ROLES.items():
                arguments.extend((
                    f'--input-technology-naming-convention:python:{role}:defsintf=algites-python-gen{suffix}-intf-versioned_1',
                    f'--output-technology-naming-convention:python:{role}:sdointf=algites-python-gen-data{suffix}-intf-versioned_1',
                    f'--output-technology-naming-convention:python:{role}:sdoclass=algites-python-gen-data{suffix}-class-versioned_1',
                ))
            old_modules = set(destination.rglob('*.py'))
            outcome = cli(arguments)
            if outcome not in (0, None):
                raise RuntimeError(f'SDO Python generation failed for {artifact}: {outcome}')
            new_modules = set(destination.rglob('*.py')) - old_modules
            total += len(new_modules)
    print(f'SDO Python: generated {total} new files in {len(modules)} artifacts', flush=True)
    return total


def _defs_cli_arguments(repository: Path, manifest: dict) -> list[str]:
    """Translate one generic artifact selection into Defs' public qualified CLI.

    The bootstrap owns neither Defs' internal manifest format nor its parser.
    All naming, root and output options are therefore passed through the same
    settings/CLI boundary that is used by a manual invocation.
    """
    arguments = [f'--repository-root={repository}']
    selected_kinds = {item['kind'] for item in manifest['schema_inputs']}
    # Packaged CLI defaults select all format directories; remove unselected
    # defaults so --root restricts the artifact's real input scope.
    for kind in SOURCE_KINDS:
        if kind not in selected_kinds:
            arguments.append(f'--schema-input-dir:{kind}=')
    for item in manifest['schema_inputs']:
        arguments.append(f"--schema-input-dir:{item['kind']}={item['directory']}")
    for kind, profile in manifest['schema_input_naming_conventions'].items():
        arguments.append(f'--input-schema-naming-convention:{kind}={profile}')
    # Neutral native CLI defaults may select Python even when only Java
    # output was declared. Empty overrides remove every unselected output role.
    for tech in ('java', 'python'):
        if tech not in manifest['languages']:
            arguments.extend([
                f'--technology-dointf-output-dir:{tech}=',
                f'--output-enum-technology-naming-convention:{tech}=',
                f'--common-codegen-naming-convention:{tech}=',
                f'--defs-codegen-naming-convention:{tech}=',
            ])
            for role in ('common', 'xmldefs_type', 'xmldefs_element',
                         'xmldefs_namespace', 'yamldefs', 'jsondefs'):
                arguments.append(f'--output-interface-technology-naming-convention:{tech}:{role}:defsintf=')
    for tech, directory in manifest['technology_outputs'].items():
        arguments.append(f'--technology-dointf-output-dir:{tech}={directory}')
    for tech, roles in manifest['technology_output_naming_conventions'].items():
        for role, profile in roles.items():
            arguments.append(f'--output-interface-technology-naming-convention:{tech}:{role}:defsintf={profile}')
    for tech, profile in manifest['technology_enum_output_naming_conventions'].items():
        arguments.append(f'--output-enum-technology-naming-convention:{tech}={profile}')
    for tech, profile in manifest['common_codegen_naming_conventions'].items():
        arguments.append(f'--common-codegen-naming-convention:{tech}={profile}')
    for tech, profile in manifest['defs_codegen_naming_conventions'].items():
        arguments.append(f'--defs-codegen-naming-convention:{tech}={profile}')
    for index, catalog in enumerate(manifest['naming_convention_files']):
        arguments.append(f'--naming-conventions-file:bootstrap_{index}={catalog}')
    for tech in manifest['languages']:
        arguments.extend([
            f'--naming-conventions-file:codegen_common=classpath:algites-{tech}-common-codegen-conventions.yml',
            f'--naming-conventions-file:codegen_defs=classpath:algites-{tech}-defs-codegen-conventions.yml',
        ])
    arguments.append('--codegen-validate-one-input-at-a-time-only=' + _validation_policy())
    return arguments


def _validation_policy() -> str:
    """Strictly validate the inherited, shared policy before either generator runs."""
    value = os.environ.get('MODUSTRO_CODEGEN_VALIDATE_ONE_INPUT_AT_A_TIME_ONLY', 'true')
    if value not in ('true', 'false'):
        raise ValueError('MODUSTRO_CODEGEN_VALIDATE_ONE_INPUT_AT_A_TIME_ONLY must be true or false')
    return value


def generate(repository: Path, root: Path, output: Path) -> int:
    """Invoke the standalone Defs CLI, not its private manifest implementation."""
    modules = _applicable_artifacts(repository, root)
    if not modules:
        print('No applicable Defs schemas below the selected root; nothing generated.', flush=True)
        return 0
    cli = _load_codegen(repository, output)
    produced = 0
    for (artifact, branch), (languages, kinds) in modules.items():
        manifest = _manifest(repository, artifact, languages, kinds, branch)
        outcome = cli(_defs_cli_arguments(repository, manifest))
        if outcome not in (None, 0):
            raise RuntimeError(f'Defs CLI generation failed for {artifact}: exit code {outcome}')
        for language in languages:
            directory = artifact / 'src' / branch / (language + '.gen')
            suffix = '.java' if language == 'java' else '.py'
            count = sum(path.is_file() for path in directory.rglob('*' + suffix))
            if not count:
                raise RuntimeError(f'Incomplete {language} Defs CLI generation: {artifact}')
            produced += count
    print(f'Regenerated {produced} Defs source files via CLI in {len(modules)} artifacts', flush=True)
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
    try:
        generate(repository, root, args.output.resolve())
        generate_sdo_python(repository, root, args.output.resolve())
    except Exception as failure:
        # Both generators use their public CLI entrypoints. Import diagnostics
        # at the failure boundary: source mode may only then expose Codegen paths.
        # the Codegen module paths inside _load_codegen.
        try:
            from eu.algites.tool.codegen.common.diagnostics import report_exception
        except ImportError:
            raise failure  # Report the generation failure, not a diagnostics import.
        if report_exception(failure, generator='Bootstrap Codegen'):
            raise SystemExit(2) from None
        raise


if __name__ == '__main__':
    main()
