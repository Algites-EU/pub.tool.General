"""Guard the native artifact dependency metadata used by the Defs/SDO bootstrap.

The generated read-only and mutable interfaces expose types from other Modustro
artifacts.  Those providers must be *direct* product dependencies of the
owning artifact; relying on an unrelated transitive Gradle dependency can make
an otherwise valid generated source tree fail at compileJava.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import re

import pytest
import yaml

BOOTSTRAP = Path(__file__).resolve().parents[1] / 'bootstrap'
TOOL_ROOT = BOOTSTRAP.parents[1]
LIB_ROOT = Path(os.environ.get('MODUSTRO_BOOTSTRAP_LIB_REPOSITORY',
                               TOOL_ROOT.parent / 'pub.lib.General')).resolve()

spec = importlib.util.spec_from_file_location('p0_native_prepare', BOOTSTRAP / 'prepare.py')
assert spec and spec.loader
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)

# These are public contracts, not incidental details of a remote Maven POM.
REQUIRED = {
    'generators/code/sdocodegen/intf': {
        'pub.lib.General_common.util': 'product_api',
        'pub.lib.General_naming.convention.intf': 'product_api',
        'pub.lib.General_data.smartdataobject.impl.common': 'product_api',
    },
    'generators/code/defscodegen/impl': {
        'pub.lib.General_data.smartdataobject.intf': 'product_api',
        'pub.lib.General_factory.cpdiscovery.intf': 'product_api',
    },
    'generators/code/sdocodegen/impl': {
        'pub.lib.General_data.smartdataobject.intf': 'product_implementation',
        'pub.lib.General_naming.convention.intf': 'product_api',
    },
}


def _declared(descriptor: Path) -> dict[str, set[str]]:
    doc = yaml.safe_load(descriptor.read_text(encoding='utf-8'))
    return {
        str(entry['ArtifactId']): set(entry.get('Usages', []))
        for group in doc.get('Dependencies', [])
        if group.get('DependencyKind') == 'modustro'
        for entry in group.get('Items', [])
    }


def test_codegen_direct_dependencies() -> None:
    """The first published Defs/SDO contracts compile without accidental transitivity."""
    for artifact, requirements in REQUIRED.items():
        found = _declared(TOOL_ROOT / artifact / 'modustro-artifact.yml')
        for dependency, scope in requirements.items():
            assert scope in found.get(dependency, set()), (artifact, dependency, scope, found)


def test_sdo_api_descriptor_has_no_duplicate_yaml_keys() -> None:
    """Reject duplicate YAML mapping keys before publication hides configuration errors."""
    from yaml.nodes import MappingNode, SequenceNode

    descriptor = TOOL_ROOT / 'generators/code/sdocodegen/intf/modustro-artifact.yml'
    document = yaml.compose(descriptor.read_text(encoding='utf-8'))
    assert document is not None

    def check(node, path: str) -> None:
        if isinstance(node, MappingNode):
            seen: set[str] = set()
            for key, value in node.value:
                assert key.value not in seen, f'{descriptor}:{path}: duplicate {key.value}'
                seen.add(key.value)
                check(value, f'{path}/{key.value}')
        elif isinstance(node, SequenceNode):
            for index, value in enumerate(node.value):
                check(value, f'{path}/{index}')

    check(document, '$')


def test_staged_gradle_dependencies_have_api_scope(tmp_path: Path) -> None:
    """Native bootstrap translates product_api to Gradle api and preserves coordinates."""
    records = prepare.module_records(TOOL_ROOT, '1.1-SNAPSHOT', '1.1.dev20261109000000')
    prepare.stage_gradle(TOOL_ROOT, tmp_path, records, '1.1-SNAPSHOT')
    modules = json.loads((tmp_path / 'gradle/modules.json').read_text(encoding='utf-8'))
    sdo = next(m for m in modules if m['artifactId'] ==
               'pub.tool.General_generators.code.sdocodegen.intf')
    for artifact, group in (
        ('pub.lib.General_common.util', 'eu.algites.lib.common'),
        ('pub.lib.General_naming.convention.intf', 'eu.algites.lib.naming'),
        ('pub.lib.General_data.smartdataobject.impl.common', 'eu.algites.lib.data'),
    ):
        assert any(d['configuration'] == 'api' and d['kind'] == 'external' and
                   d['target'] == f'{group}:{artifact}:1.1-SNAPSHOT'
                   for d in sdo['dependencies']), (artifact, sdo['dependencies'])


def test_all_known_java_modustro_imports_have_direct_dependencies() -> None:
    """Check both product Java trees, including generated and bootstrap-seed sources.

    With only pub.tool.General checked out, the explicit Codegen fixture above
    still runs; the cross-repository inventory is enabled when pub.lib.General
    is available beside the tool repository (or at the configured location).
    """
    if not LIB_ROOT.is_dir():
        pytest.skip('pub.lib.General source tree not available for cross-repository audit')
    owners: dict[str, set[str]] = {}
    modules: list[tuple[str, Path, set[str]]] = []
    for repo in (TOOL_ROOT, LIB_ROOT):
        for descriptor in repo.rglob('modustro-artifact.yml'):
            if any(part in {'build', '.git', '__pycache__'} for part in descriptor.parts):
                continue
            artifact = descriptor.parent
            parsed = yaml.safe_load(descriptor.read_text(encoding='utf-8'))
            if 'java' not in parsed.get('Artifact', {}).get('TechnologyKinds', []):
                continue
            identifier = repo.name + '_' + '.'.join(artifact.relative_to(repo).parts)
            declared = _declared(descriptor)
            modules.append((identifier, artifact, set(declared)))
            for file in artifact.glob('src/product/java*/**/*.java'):
                match = re.search(r'^\s*package\s+([\w.]+)\s*;',
                                  file.read_text(encoding='utf-8'), re.M)
                if match:
                    owners.setdefault(match.group(1) + '.' + file.stem, set()).add(identifier)
    missing: list[str] = []
    for identifier, artifact, dependencies in modules:
        for file in artifact.glob('src/product/java*/**/*.java'):
            content = file.read_text(encoding='utf-8')
            # Comments and generated origin metadata are not Java type references.
            content = re.sub(r'/\*.*?\*/|//[^\n]*', '', content, flags=re.S)
            referenced = set(re.findall(r'\beu\.algites\.[\w.]+', content))
            for referenced_type in referenced:
                others = owners.get(referenced_type, set()) - {identifier}
                if others and not others.intersection(dependencies):
                    missing.append(f'{file}: {referenced_type} defined in '
                                   f'{sorted(others)} but not declared by {identifier}')
    assert not missing, '\n'.join(sorted(missing))


def test_all_known_python_modustro_imports_have_direct_dependencies() -> None:
    """Verify namespace imports without importing modules or invoking their side effects."""
    if not LIB_ROOT.is_dir():
        pytest.skip('pub.lib.General source tree not available for cross-repository audit')
    import ast

    owners: dict[str, set[str]] = {}
    modules: list[tuple[str, Path, set[str]]] = []
    for repo in (TOOL_ROOT, LIB_ROOT):
        for descriptor in repo.rglob('modustro-artifact.yml'):
            if any(part in {'build', '.git', '__pycache__'} for part in descriptor.parts):
                continue
            artifact = descriptor.parent
            parsed = yaml.safe_load(descriptor.read_text(encoding='utf-8'))
            if 'python' not in parsed.get('Artifact', {}).get('TechnologyKinds', []):
                continue
            identifier = repo.name + '_' + '.'.join(artifact.relative_to(repo).parts)
            modules.append((identifier, artifact, set(_declared(descriptor))))
            for file in artifact.glob('src/product/python*/**/*.py'):
                source_root = next((part for part in file.parents if part.name.startswith('python')
                                    and part.parent.name == 'product'), None)
                if source_root is not None:
                    name = '.'.join(file.relative_to(source_root).with_suffix('').parts)
                    owners.setdefault(name, set()).add(identifier)

    missing: list[str] = []
    for identifier, artifact, dependencies in modules:
        for file in artifact.glob('src/product/python*/**/*.py'):
            tree = ast.parse(file.read_text(encoding='utf-8'), filename=str(file))
            for node in ast.walk(tree):
                names: list[str] = []
                if isinstance(node, ast.Import):
                    names = [entry.name for entry in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    names = [node.module] + [node.module + '.' + entry.name
                                             for entry in node.names]
                for name in names:
                    matches = sorted((key for key in owners if name == key or
                                      name.startswith(key + '.')), key=len, reverse=True)
                    if not matches:
                        continue
                    other_owners = owners[matches[0]] - {identifier}
                    if other_owners and not other_owners.intersection(dependencies):
                        missing.append(f'{file}:{node.lineno}: {name} supplied by '
                                       f'{sorted(other_owners)}, not declared by {identifier}')
    assert not missing, '\n'.join(sorted(set(missing)))


def test_defs_cli_does_not_import_sdo_cli() -> None:
    """Independent Defs and SDO CLIs must not require each other's packages."""
    path = TOOL_ROOT / ('generators/code/defscodegen/cli/src/product/python/'
                        'eu/algites/tool/codegen/defs/impl/cli/_standard_cli.py')
    content = path.read_text(encoding='utf-8')
    assert 'from eu.algites.tool.codegen.sdo.' not in content
    assert 'from eu.algites.tool.codegen.defs.impl.standard._catalog_sources import expand_naming_catalogs' in content
    assert 'from eu.algites.tool.codegen.defs.old.' not in content
