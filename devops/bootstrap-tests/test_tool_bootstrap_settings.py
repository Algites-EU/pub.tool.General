"""Descriptor-driven publication and root-scoping regressions for Tool."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).resolve().parents[1] / 'bootstrap' / 'prepare.py'


def helper():
    spec = importlib.util.spec_from_file_location('native_bootstrap', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_repository_descriptor_controls_coordinates():
    module = helper()
    records = module.module_records(ROOT, '1.1-SNAPSHOT', '1.1.dev20261027000000')
    assert len(records) == 11
    assert all(record['artifactId'].startswith('pub.tool.General_') for record in records)
    common = next(record for record in records if record['path'] == 'generators/code/common')
    assert common['groupId'] == 'eu.algites.tool.codegen'
    impl = next(record for record in records if record['path'] == 'generators/code/defscodegen/impl')
    assert any(dep['kind'] == 'external'
               and ':pub.lib.General_' in dep['coordinate']
               for dep in impl['dependencies'])
    # Concrete naming profiles belong to bootstrap/build-source preparation,
    # not to the published Defs Codegen implementation.
    naming_profile = 'pub.lib.General_naming.convention.profile.algites'
    assert not any(naming_profile in dep.get('coordinate', '')
                   for dep in impl['dependencies'])
    assert not any('naming-convention-profile-algites' in dependency
                   for dependency in impl['pythonDependencies'])
    from importlib.util import spec_from_file_location, module_from_spec
    bootstrap = ROOT / 'generators/code/regenerate_sources.py'
    spec = spec_from_file_location('source_bootstrap', bootstrap)
    source = module_from_spec(spec)
    spec.loader.exec_module(source)
    assert 'eu_algites_pub_lib_general_naming_convention_profile_algites' in (
        source.BOOTSTRAP_BUILD_SOURCE_PYTHON_DISTRIBUTIONS)


def test_selection_never_builds_dependencies_outside_root():
    module = helper()
    records = module.module_records(ROOT, '1.1-SNAPSHOT', '1.1.dev20261027000000')
    selected = [r for r in records if r['path'] == 'generators/code/defscodegen/impl']
    assert len(selected) == 1
    module.restrict_to_selection(selected, '1.1-SNAPSHOT', '1.1.dev20261027000000')
    deps = selected[0]['dependencies']
    assert all(dep['kind'] == 'external' for dep in deps)
    assert any('pub.tool.General_generators.code.defscodegen.intf' in dep['coordinate'] for dep in deps)


def test_sdo_naming_engine_is_declared_at_the_consumption_sites():
    """Keep the profile-neutral naming engine on the SDO Java/Python classpath.

    The SDO service exposes the catalog in public method signatures, while the
    CLI imports it directly. Neither artifact should require a specific profile.
    """
    module = helper()
    records = module.module_records(ROOT, '1.1-SNAPSHOT', '1.1.dev20261027000000')
    by_path = {record['path']: record for record in records}
    naming = 'eu.algites.lib.naming:pub.lib.General_naming.convention.impl:1.1-SNAPSHOT'
    for path, expected_configuration in (
        ('generators/code/sdocodegen/impl', 'api'),
        ('generators/code/sdocodegen/cli', 'implementation'),
    ):
        record = by_path[path]
        assert any(dep['kind'] == 'external'
                   and dep['coordinate'] == naming
                   and dep['configuration'] == expected_configuration
                   for dep in record['dependencies'])
        assert any(
            entry.startswith('eu-algites-pub-lib-general-naming-convention-impl')
            for entry in record['pythonDependencies'])
        assert not any('pub.lib.General_naming.convention.profile.algites' in dep.get('coordinate', '')
                       for dep in record['dependencies'])
        assert not any('naming_convention_profile_algites' in dependency
                       for dependency in record['pythonDependencies'])


def test_product_java_imports_have_direct_naming_and_factory_dependencies():
    """Every artifact must declare the library types it imports directly.

    Both dependency modes use these product descriptors when constructing the
    Java compilation classpath.  A transitive dependency of a sibling module
    must not be relied on to compile a different artifact.
    """
    module = helper()
    records = module.module_records(ROOT, '1.1-SNAPSHOT', '1.1.dev20261028000000')
    by_path = {record['path']: record for record in records}
    expected = {
        'naming/validator/cli': (
            'eu.algites.lib.naming:pub.lib.General_naming.convention.impl:1.1-SNAPSHOT',
        ),
        'generators/code/sdocodegen/cli': (
            'eu.algites.lib.naming:pub.lib.General_naming.convention.impl:1.1-SNAPSHOT',
            'eu.algites.lib.data:pub.lib.General_data.dataobject.intf:1.1-SNAPSHOT',
        ),
        'generators/code/sdocodegen/impl': (
            'eu.algites.lib.naming:pub.lib.General_naming.convention.impl:1.1-SNAPSHOT',
            'eu.algites.lib.common:pub.lib.General_factory.cpdiscovery.intf:1.1-SNAPSHOT',
        ),
    }
    for path, coordinates in expected.items():
        record = by_path[path]
        dependencies = {dependency['coordinate']: dependency['configuration']
                        for dependency in record['dependencies']
                        if dependency['kind'] == 'external'}
        python_dependencies = record['pythonDependencies']
        for coordinate in coordinates:
            assert coordinate in dependencies, (path, coordinate)
            assert dependencies[coordinate] in {'implementation', 'api'}
            # This exact Modustro contract also appears in Python metadata,
            # rather than being inferred through unrelated product dependencies.
            artifact_id = coordinate.split(':')[1]
            normalized = module.python_name(artifact_id, 'eu-algites')
            assert any(value.startswith(normalized + '>=1.1.dev0,')
                       for value in python_dependencies), (path, artifact_id)
        assert not any('profile.algites' in dependency.get('coordinate', '')
                       for dependency in record['dependencies'] if dependency['kind'] == 'external' and
                       path == 'naming/validator/cli')


def test_all_product_dependency_declarations_are_unambiguous():
    """Prevent silent YAML duplicate-key overwrites and ignored dependency items."""
    import yaml
    from yaml.nodes import MappingNode, SequenceNode

    def inspect_node(node, source):
        if isinstance(node, MappingNode):
            found = set()
            for key, value in node.value:
                assert key.value not in found, (source, key.value, key.start_mark.line + 1)
                found.add(key.value)
                inspect_node(value, source)
        elif isinstance(node, SequenceNode):
            for value in node.value:
                inspect_node(value, source)

    for descriptor in ROOT.rglob('modustro-artifact.yml'):
        inspect_node(yaml.compose(descriptor.read_text(encoding='utf-8')), descriptor)
        data = yaml.safe_load(descriptor.read_text(encoding='utf-8'))
        for dependency in data.get('Dependencies') or []:
            for item in dependency.get('Items') or []:
                assert item.get('Usages'), (descriptor, item.get('ArtifactId'))
