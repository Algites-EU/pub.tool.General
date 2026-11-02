"""Remote Maven resolution must admit dependencies of published dependency POMs.

The roots declared in the artifact descriptors cannot predict the GroupIds of
all transitively referenced Modustro artifacts. Filtering Cloudsmith to only
those direct groups causes Gradle to search Maven Central for other groups.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
BOOT = ROOT / 'devops/bootstrap'


def _remote_clause(source: str, condition: str) -> str:
    match = re.search(r'if \(' + re.escape(condition) + r'\) maven \{(.*?)\n\s*\}', source, re.DOTALL)
    assert match, f'Missing remote Maven declaration for {condition}'
    return match.group(1)


def test_staged_gradle_remote_repository_includes_transitive_groups(tmp_path):
    spec = importlib.util.spec_from_file_location('bootstrap_prepare', BOOT / 'prepare.py')
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    records = [dict(
        java=True, artifactId='test.credentials', groupId='eu.algites.lib.security',
        path='example/credentials', resourceDirs=[], dependencies=[dict(
            kind='external', coordinate='eu.algites.lib.data:pub.lib.General_data.smartdataobject.intf:1.1-SNAPSHOT',
            configuration='api', modustro=True)],
    )]
    module.stage_gradle(ROOT, tmp_path, records, '1.1-SNAPSHOT')
    script = (tmp_path / 'gradle/build.gradle').read_text(encoding='utf-8')
    assert 'bootstrapRemoteModustroGroups = ["eu.algites.lib.data"]' in script
    remote = _remote_clause(script, "bootstrapMode == 'remote'")
    assert 'MODUSTRO_BOOTSTRAP_REMOTE_MAVEN_URL' in remote
    assert 'includeGroup' not in remote
    assert 'content {' not in remote
    assert 'mavenCentral()' in script
    # Source mode keeps its explicit list of source-owned groups.
    assert 'exclusiveContent {' in script
    assert 'filter { rootProject.ext.bootstrapRemoteModustroGroups.each { includeGroup(it) } }' in script


def test_sdo_gradle_remote_repository_includes_transitive_groups():
    source = (BOOT / 'sdo-java.gradle').read_text(encoding='utf-8')
    remote = _remote_clause(source, "mode == 'remote'")
    assert 'MODUSTRO_BOOTSTRAP_REMOTE_MAVEN_URL' in remote
    assert 'includeGroup' not in remote
    assert 'content {' not in remote
    assert 'mavenCentral()' in source
