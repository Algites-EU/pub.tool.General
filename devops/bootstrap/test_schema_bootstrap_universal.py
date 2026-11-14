"""Source-schema closure and descriptor-driven self-hosting regressions.

Does not require Gradle, network access, generated CLI packages or Cloudsmith.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

REPO = Path(__file__).resolve().parents[2]
BOOTSTRAP = REPO / 'devops/bootstrap'


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, BOOTSTRAP / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_schema_only_development_dependency_is_mapped_without_runtime_dep(tmp_path):
    lib = REPO if REPO.name == 'pub.lib.General' else REPO.parent / 'pub.lib.General'
    if not lib.is_dir():
        pytest.skip('Sibling pub.lib.General checkout is required for integration test')
    mapper = _load('modustro_schema_mapping_closure', 'schema-locations.py')
    identity = ('https://defs.dev.algites.eu/api/xmldefs/eu/algites/lib/'
                'common/documentation/algites-documentation_1.xsd')
    for target in ('naming/convention/intf', 'naming/convention/sourcecode'):
        mapping = mapper.collect(lib, lib / target)
        assert identity in mapping, target
        assert mapping[identity] == (lib / 'documentation/intf/src/product/xmldefs/eu/'
                                     'algites/lib/common/documentation/algites-documentation_1.xsd').resolve()
    staging = _load('modustro_prepare_no_runtime_dependency', 'prepare.py')
    record = next(item for item in staging.module_records(lib, '1.1-SNAPSHOT', '1.1.dev20261113000000')
                  if item['artifactId'] == 'pub.lib.General_naming.convention.intf')
    assert not any('documentation' in name for name in record['pythonDependencies'])
    assert len(record['javaGeneratedCompletionPatterns']) == 2


def test_shared_bootstrap_uses_configuration_only(tmp_path):
    lib = REPO if REPO.name == 'pub.lib.General' else REPO.parent / 'pub.lib.General'
    tool = REPO if REPO.name == 'pub.tool.General' else REPO.parent / 'pub.tool.General'
    if not lib.is_dir() or not tool.is_dir():
        pytest.skip('Both source checkouts are needed for universal bootstrap check')
    for filename in ('bootstrap.sh', 'build.sh', 'generate.sh', 'prepare.py',
                     'schema-locations.py', 'source-dependencies.py',
                     'generate_sources.py', 'sdo-java.gradle', 'selfhosting.py'):
        assert (lib / 'devops/bootstrap' / filename).read_bytes() == (
            tool / 'devops/bootstrap' / filename).read_bytes(), filename
    config = _load('modustro_selfhosting_config', 'selfhosting.py')
    assert config.policies(lib)['CleanGeneratedDefault'] is False
    assert config.policies(tool)['CleanGeneratedDefault'] is True
    assert config.policies(tool)['RequireFreshGenerated'] is True
    resolver = _load('modustro_owning_compiler_policies', 'source-dependencies.py')
    graph = resolver.catalog(resolver.checkouts(lib))
    programs = resolver.compiler_bootstraps(graph)
    assert len(programs) == 1
    assert programs[0].cli.repository == tool
    assert 'pub.lib.General_naming.convention.intf' in programs[0].seed_ids
    assert 'pub.tool.General_generators.code.sdocodegen.intf' in programs[0].rebuild_ids
    assert 'NAMING_ABI_SEED' not in (lib / 'devops/bootstrap/source-dependencies.py').read_text()


def test_seed_and_generated_python_never_merge(tmp_path, monkeypatch):
    sh = _load('modustro_source_selection', 'selfhosting.py')
    policy = {
        'GeneratedSourceSelection': [{
            'ArtifactId': 'test-module',
            'PythonCompletionPatterns': ['**/impl/intf/aiigd*.py', '**/impl/aicgd*.py'],
        }],
    }
    monkeypatch.setattr(sh, 'policies', lambda _: policy)
    artifact = tmp_path / 'module'
    assert sh.source_directories(artifact, 'test-module', 'python', tmp_path)[-1] == 'src/product/python.extgen'
    for path in ('eu/impl/intf/aiigd_name.py', 'eu/impl/aicgd_name.py'):
        file = artifact / 'src/product/python.gen' / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text('generated')
    assert sh.source_directories(artifact, 'test-module', 'python', tmp_path)[-1] == 'src/product/python.gen'
    monkeypatch.setenv('MODUSTRO_BOOTSTRAP_SDO_ABI_SEED', '1')
    assert sh.source_directories(artifact, 'test-module', 'python', tmp_path)[-1] == 'src/product/python.extgen'
