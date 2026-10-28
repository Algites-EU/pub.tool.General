"""Regression tests for class-based and schema-only Maven Java publications."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import zipfile

import pytest


_SCRIPT = Path(__file__).resolve().parents[1] / 'bootstrap' / 'prepare.py'


def _helper():
    spec = importlib.util.spec_from_file_location('bootstrap_resource_verifier', _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_jar(jar: Path, files: dict[str, bytes]) -> None:
    jar.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(jar, 'w') as archive:
        archive.writestr('META-INF/MANIFEST.MF', b'Manifest-Version: 1.0\n')
        for name, contents in files.items():
            archive.writestr(name, contents)


def _publish(tmp_path: Path, resources: dict[str, tuple[str, bytes]],
             included: dict[str, bytes], java: bool = False,
             snapshot: bool = False) -> tuple[Path, Path, list[dict]]:
    """Construct Maven publications with the same resource-root layout as Gradle."""
    root = tmp_path / 'repo'
    artifact = root / 'generators/code/common'
    for source, (folder, content) in resources.items():
        file = artifact / 'src/product' / folder / source
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(content)
    if java:
        source = artifact / 'src/product/java/example/Marker.java'
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text('package example; public class Marker {}', encoding='utf-8')
    work = tmp_path / 'work'
    release, group, artifact_id = '1.1-SNAPSHOT', 'eu.algites.tool.codegen', 'pub.tool.General_generators.code.common'
    publication = work / 'maven-repository' / group.replace('.', '/') / artifact_id / release
    publication.mkdir(parents=True)
    published_version = '1.1-20261028.082452-1' if snapshot else release
    stem = artifact_id + '-' + published_version
    _write_jar(publication / (stem + '.jar'), included)
    _write_jar(publication / (stem + '-sources.jar'), {'META-INF/SOURCES': b'present'})
    (publication / (stem + '.pom')).write_text(f'''<project>
      <groupId>{group}</groupId>
      <artifactId>{artifact_id}</artifactId>
      <version>{release}</version>
    </project>''', encoding='utf-8')
    (publication / (stem + '.module')).write_text('{"module":"present"}', encoding='utf-8')
    if snapshot:
        (publication / 'maven-metadata.xml').write_text(f'''<metadata>
          <groupId>{group}</groupId><artifactId>{artifact_id}</artifactId><version>{release}</version>
          <versioning><snapshot><timestamp>20261028.082452</timestamp><buildNumber>1</buildNumber></snapshot>
          </versioning>
        </metadata>''', encoding='utf-8')
    records = [{'path': 'generators/code/common', 'artifactId': artifact_id,
                'groupId': group, 'java': True}]
    return root, work, records


def test_schema_only_artifact_passes_and_generates_publication_manifest(tmp_path: Path):
    """No .class needed when JSONDEFS, YAMLDEFS and XMLDEFS ship intact."""
    contents = {
        'eu/algites/schema/sample.json': ('jsondefs', b'{"type":"object"}'),
        'eu/algites/schema/sample.yml': ('yamldefs', b'type: object\n'),
        'eu/algites/schema/sample.xsd': ('xmldefs', b'<xs:schema/>'),
    }
    archive_files = {path: data for path, (_, data) in contents.items()}
    root, work, records = _publish(tmp_path, contents, archive_files, snapshot=True)
    _helper().verify_maven(root, work, records, '1.1-SNAPSHOT')
    manifest = (work / 'packages.tsv').read_text(encoding='utf-8')
    assert '20261028.082452-1.jar' in manifest
    assert '20261028.082452-1-sources.jar' in manifest


def test_profile_only_artifact_passes_without_classes(tmp_path: Path):
    contents = {'eu/algites/lib/naming/example.yml': ('config', b'roles: {}\n')}
    root, work, records = _publish(tmp_path, contents,
                                   {path: data for path, (_, data) in contents.items()})
    _helper().verify_maven(root, work, records, '1.1-SNAPSHOT')
    assert (work / 'packages.tsv').is_file()


def test_empty_jar_is_not_accepted_as_product(tmp_path: Path):
    root, work, records = _publish(tmp_path, {}, {})
    with pytest.raises(ValueError, match='neither compiled classes nor product resources'):
        _helper().verify_maven(root, work, records, '1.1-SNAPSHOT')
    assert not (work / 'packages.tsv').exists()


def test_missing_product_resource_is_rejected(tmp_path: Path):
    contents = {'schema.json': ('jsondefs', b'{"version":1}')}
    root, work, records = _publish(tmp_path, contents, {})
    with pytest.raises(ValueError, match='missing product resource schema.json'):
        _helper().verify_maven(root, work, records, '1.1-SNAPSHOT')
    assert not (work / 'packages.tsv').exists()


def test_stale_product_resource_is_rejected(tmp_path: Path):
    contents = {'schema.json': ('jsondefs', b'{"version":1}')}
    root, work, records = _publish(tmp_path, contents, {'schema.json': b'{"version":0}'})
    with pytest.raises(ValueError, match='outdated or modified product resource schema.json'):
        _helper().verify_maven(root, work, records, '1.1-SNAPSHOT')


def test_java_product_requires_compiled_classes_even_if_it_has_resources(tmp_path: Path):
    contents = {'profile.settings': ('config', b'profile=default\n')}
    root, work, records = _publish(tmp_path, contents, {'profile.settings': b'profile=default\n'}, java=True)
    with pytest.raises(ValueError, match='missing compiled Java classes'):
        _helper().verify_maven(root, work, records, '1.1-SNAPSHOT')


def test_java_product_with_classes_passes(tmp_path: Path):
    root, work, records = _publish(tmp_path, {}, {'example/Marker.class': b'compiled'}, java=True)
    _helper().verify_maven(root, work, records, '1.1-SNAPSHOT')


def test_gradle_and_verifier_use_identical_resource_roots(tmp_path: Path):
    module = _helper()
    root = tmp_path / 'repo'
    root.mkdir()
    artifact = root / 'example'
    artifact.mkdir()
    custom = artifact / 'src/product/tomldefs'
    custom.mkdir(parents=True)
    (custom / 'schema.toml').write_text('value = 1')
    resource_dirs = module.product_resource_dirs(artifact)
    module.stage_gradle(root, tmp_path / 'build', [{
        'path': 'example', 'artifactId': 'example', 'groupId': 'example',
        'java': True, 'dependencies': [], 'resourceDirs': resource_dirs,
    }], '1.1-SNAPSHOT')
    build = (tmp_path / 'build/gradle/build.gradle').read_text(encoding='utf-8')
    manifest = __import__('json').loads((tmp_path / 'build/gradle/modules.json').read_text())
    assert manifest[0]['resourceDirs'] == ['src/product/tomldefs']
    assert 'resources.srcDirs = config.resourceDirs' in build
    assert module.expected_java_resources(artifact)['schema.toml'] == custom / 'schema.toml'


def test_real_common_artifact_is_valid_as_resource_only_jar(tmp_path: Path):
    """The actual Codegen common has schema products but no Java sources."""
    module = _helper()
    repository = Path(__file__).resolve().parents[2]
    source = repository / 'generators/code/common'
    resources = module.expected_java_resources(source)
    assert len(resources) == 12
    assert {path.suffix for path in resources.values()} == {'.json', '.yml', '.xsd'}
    assert not list((source / 'src/product/java').rglob('*.java'))
    jar = tmp_path / 'common.jar'
    _write_jar(jar, {entry: path.read_bytes() for entry, path in resources.items()})
    module.verify_java_jar(jar, source)
