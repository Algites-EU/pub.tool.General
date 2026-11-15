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


def test_defs_selfhost_selects_exactly_one_generated_source_tree(tmp_path, monkeypatch):
    """Do not compile/stage duplicate Defs FQCNs from .extgen and .gen."""
    if REPO.name != 'pub.tool.General':
        pytest.skip('Defs self-hosting is owned by pub.tool.General')
    bootstrap = _load('defs_selfhosting_source_selection', 'selfhosting.py')
    prepare = _load('defs_selfhosting_prepare', 'prepare.py')
    artifact_id = 'pub.tool.General_generators.code.defscodegen.intf'
    artifact = tmp_path / 'generators/code/defscodegen/intf'
    product = artifact / 'src/product'
    for lang, extension, read_file, sdo_intf, sdo_impl in (
            ('java', '.java', 'model/AIigType_1.java',
             'model/impl/intf/AIigdType_1.java', 'model/impl/AIcgdType_1.java'),
            ('python', '.py', 'model/aiig_type_1.py',
             'model/impl/intf/aiigd_type_1.py', 'model/impl/aicgd_type_1.py')):
        extgen_read = product / (lang + '.extgen') / read_file
        extgen_read.parent.mkdir(parents=True, exist_ok=True)
        extgen_read.write_text('seed', encoding='utf-8')
        gen_read = product / (lang + '.gen') / read_file
        gen_read.parent.mkdir(parents=True, exist_ok=True)
        gen_read.write_text('fresh', encoding='utf-8')
        selected = bootstrap.source_directories(artifact, artifact_id, lang, REPO)
        assert selected == ('src/product/' + lang, 'src/product/' + lang + '.extgen')
        for relative in (sdo_intf, sdo_impl):
            generated = product / (lang + '.gen') / relative
            generated.parent.mkdir(parents=True, exist_ok=True)
            generated.write_text('fresh', encoding='utf-8')
        selected = bootstrap.source_directories(artifact, artifact_id, lang, REPO)
        assert selected == ('src/product/' + lang, 'src/product/' + lang + '.gen')
    monkeypatch.setenv('MODUSTRO_BOOTSTRAP_SDO_ABI_SEED', '1')
    for lang in ('java', 'python'):
        assert bootstrap.source_directories(artifact, artifact_id, lang, REPO)[-1] == (
            'src/product/' + lang + '.extgen')
    monkeypatch.delenv('MODUSTRO_BOOTSTRAP_SDO_ABI_SEED', raising=False)
    records = prepare.module_records(REPO, '1.1-SNAPSHOT', '1.1.dev20261115000000')
    defs_record = next(record for record in records if record['artifactId'] == artifact_id)
    assert len(defs_record['javaGeneratedCompletionPatterns']) == 2


def test_canonical_promotion_happens_after_java_sdo_before_publication(monkeypatch):
    """New read contracts and mutable seeds must be replaced before javac sees both."""
    if REPO.name != 'pub.tool.General':
        pytest.skip('Canonical compiler seed belongs to pub.tool.General')
    build = (BOOTSTRAP / 'build.sh').read_text(encoding='utf-8')
    java_generated = build.index('"${locGradle[@]}" "${locGradleArgs[@]}" bootstrapSdoJava')
    promotion = build.index('--phase after-sdo-java')
    publication = build.index('"${locGradle[@]}" "${locGradleArgs[@]}" publishAllPublicationsToBootstrapRepository')
    assert java_generated < promotion < publication

    selfhosting = _load('modustro_post_sdo_source_refresh', 'selfhosting.py')
    calls = []
    monkeypatch.setattr(selfhosting.subprocess, 'run', lambda args, **kwargs: calls.append((args, kwargs)))
    repo = REPO.resolve()
    policy = selfhosting.policies(repo)
    snapshot = next(entry for entry in policy['Snapshots'] if
                    entry['ArtifactPath'] == 'generators/code/defscodegen/intf')
    assert snapshot['AfterSdoJava'] == '--refresh'
    assert snapshot.get('AfterBootstrap') is None

    monkeypatch.delenv('MODUSTRO_BOOTSTRAP_SDO_ABI_SEED', raising=False)
    selfhosting.run_phase(repo, repo, 'after-sdo-java')
    assert len(calls) == 1
    assert Path(calls[0][0][1]).name == 'promote-canonical-extgen.py'
    assert calls[0][0][2:] == ['--refresh']

    calls.clear()
    selfhosting.run_phase(repo, repo / 'generators/code/defscodegen/intf', 'after-sdo-java')
    assert not calls, 'Partial root may not promote the whole compiler seed'

    monkeypatch.setenv('MODUSTRO_BOOTSTRAP_SDO_ABI_SEED', '1')
    selfhosting.run_phase(repo, repo, 'after-sdo-java')
    assert not calls, 'The first compiler pass may not overwrite the seed'
