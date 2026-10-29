"""Cross-repository Modustro source-resolution regression tests.

The tests use real descriptors and a no-op child builder so they require no
Gradle installation, network, Cloudsmith account, or published dependencies.
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
import yaml

BOOTSTRAP = Path(__file__).resolve().parents[1] / 'bootstrap'


def make_repo(root: Path, owner: str, *, version: str = '1.1-SNAPSHOT') -> Path:
    repo = root / owner
    repo.mkdir()
    (repo / 'modustro-source-repository.yml').write_text(yaml.safe_dump({
        'SourceRepository': {'Id': owner}, 'GroupId': 'eu.algites.lib.common',
        'Version': {'ReleaseLineVersion': '1', 'Revision': int(version.split('.')[1].split('-')[0]),
                    'QualifierKind': 'snapshot' if version.endswith('-SNAPSHOT') else 'release'},
    }), encoding='utf-8')
    return repo


def make_artifact(repo: Path, relative: str, deps=(), *, group: str = 'eu.algites.lib.common') -> str:
    path = repo / relative
    path.mkdir(parents=True)
    # Artifact sets use the same group used in the source dependency declaration.
    (path / 'modustro-artifact-set.yml').write_text('GroupId: ' + group + '\n')
    (path / 'modustro-artifact.yml').write_text(yaml.safe_dump({
        'Artifact': {'Name': relative, 'TechnologyKinds': ['java', 'python']},
        'Dependencies': [{'DependencyKind': 'modustro', 'Items': [
            {'ArtifactId': item, 'GroupId': group, 'Usages': ['product_api'],
             'VersionRequirement': {'Exact': '1.1-SNAPSHOT'}}
            for item in deps]}] if deps else [],
    }), encoding='utf-8')
    return repo.name + '_' + '.'.join(Path(relative).parts)


def invoke(repo: Path, root: str, *actions: str, extra_env=None) -> subprocess.CompletedProcess:
    env = {**os.environ, 'MODUSTRO_BOOTSTRAP_SOURCE_REPOSITORIES': str(repo.parent / 'pub.lib.General')
           + os.pathsep + str(repo.parent / 'pub.tool.General'), **(extra_env or {})}
    return subprocess.run([sys.executable, str(BOOTSTRAP / 'source-dependencies.py'), *actions,
                           '--repository', str(repo), '--root', str(repo / root)],
                          capture_output=True, text=True, env=env, timeout=30)


def test_source_plan_resolves_transitive_dependencies_in_order(tmp_path):
    lib = make_repo(tmp_path, 'pub.lib.General')
    tool = make_repo(tmp_path, 'pub.tool.General')
    base = make_artifact(lib, 'common')
    api = make_artifact(lib, 'naming/intf', [base])
    tool_dep = make_artifact(tool, 'generators/common', [api])
    root = make_artifact(tool, 'generators/impl', [tool_dep])
    result = invoke(tool, 'generators/impl', 'plan')
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert '3 artifact(s)' in lines[0]
    assert [next(i for i, line in enumerate(lines) if artifact in line)
            for artifact in (base, api, tool_dep)] == [1, 2, 3]
    assert root not in result.stdout


def test_selected_artifact_dependencies_not_rebuilt(tmp_path):
    lib = make_repo(tmp_path, 'pub.lib.General')
    tool = make_repo(tmp_path, 'pub.tool.General')
    lib_id = make_artifact(lib, 'common')
    api = make_artifact(tool, 'generators/intf', [lib_id])
    make_artifact(tool, 'generators/impl', [api])
    result = invoke(tool, 'generators', 'plan')
    assert result.returncode == 0, result.stderr
    assert '1 artifact(s)' in result.stdout
    assert lib_id in result.stdout
    assert api not in result.stdout


def test_source_fails_if_checkout_missing(tmp_path):
    lib = make_repo(tmp_path, 'pub.lib.General')
    tool = make_repo(tmp_path, 'pub.tool.General')
    make_artifact(tool, 'generators/impl', ['pub.lib.General_missing'])
    result = invoke(tool, 'generators/impl', 'plan')
    assert result.returncode == 2
    assert 'missing Modustro source dependency pub.lib.General_missing' in result.stderr


def test_version_mismatch_fails_before_build(tmp_path):
    lib = make_repo(tmp_path, 'pub.lib.General', version='1.2-SNAPSHOT')
    tool = make_repo(tmp_path, 'pub.tool.General')
    base = make_artifact(lib, 'common')
    make_artifact(tool, 'generators/impl', [base])
    result = invoke(tool, 'generators/impl', 'plan')
    assert result.returncode == 2
    assert 'required version' in result.stderr


def test_group_mismatch_fails(tmp_path):
    lib = make_repo(tmp_path, 'pub.lib.General')
    tool = make_repo(tmp_path, 'pub.tool.General')
    base = make_artifact(lib, 'common', group='eu.algites.other')
    make_artifact(tool, 'generators/impl', [base])
    result = invoke(tool, 'generators/impl', 'plan')
    assert result.returncode == 2
    assert 'GroupId' in result.stderr


def test_cycle_reports_chain(tmp_path):
    lib = make_repo(tmp_path, 'pub.lib.General')
    tool = make_repo(tmp_path, 'pub.tool.General')
    a = 'pub.lib.General_common.util'
    b = 'pub.tool.General_generators.impl'
    make_artifact(lib, 'common', [b])
    make_artifact(tool, 'generators/impl', [a])
    result = invoke(tool, 'generators/impl', 'plan')
    assert result.returncode == 2
    assert 'dependency cycle:' in result.stderr
    assert a in result.stderr and b in result.stderr


def test_prepare_invokes_only_prerequisites_in_dependency_order(tmp_path):
    lib = make_repo(tmp_path, 'pub.lib.General')
    tool = make_repo(tmp_path, 'pub.tool.General')
    base = make_artifact(lib, 'common')
    make_artifact(lib, 'naming/intf', [base])
    make_artifact(tool, 'generators/impl', ['pub.lib.General_naming.intf'])
    script = lib / 'devops/bootstrap/bootstrap.sh'
    script.parent.mkdir(parents=True)
    script.write_text('#!/usr/bin/env bash\nprintf "%s:%s:%s\\n" "$MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE" "$MODUSTRO_BOOTSTRAP_SOURCE_PREREQUISITES_READY" "$2" >> "$SOURCE_TEST_LOG"\n')
    log = tmp_path / 'sources.log'
    result = invoke(tool, 'generators/impl', 'prepare', extra_env={'SOURCE_TEST_LOG': str(log)})
    assert result.returncode == 0, result.stderr
    assert log.read_text().splitlines() == ['source:1:common', 'source:1:naming/intf']


def test_duplicate_repository_id_is_rejected(tmp_path):
    lib = make_repo(tmp_path, 'pub.lib.General')
    tool = make_repo(tmp_path, 'pub.tool.General')
    make_artifact(tool, 'generators/impl')
    clone = tmp_path / 'cloned'
    shutil.copytree(lib, clone)
    result = invoke(tool, 'generators/impl', 'plan', extra_env={
        'MODUSTRO_BOOTSTRAP_SOURCE_REPOSITORIES': os.pathsep.join([str(clone), str(lib), str(tool)])
    })
    assert result.returncode == 2
    assert 'Ambiguous checkout' in result.stderr


def test_bootstrap_plan_only_reports_sources_without_cleaning(tmp_path):
    lib = make_repo(tmp_path, 'pub.lib.General')
    tool = make_repo(tmp_path, 'pub.tool.General')
    base = make_artifact(lib, 'common')
    make_artifact(tool, 'generators/impl', [base])
    for filename in ('bootstrap.sh', 'clean_generated.py', 'bootstrap-config.py',
                     'modustro-bootstrap.yml', 'source-dependencies.py'):
        directory = tool / 'devops/bootstrap'
        directory.mkdir(parents=True, exist_ok=True)
        shutil.copy2(BOOTSTRAP / filename, directory / filename)
    (tool / 'devops/bootstrap/build.sh').write_text('#!/usr/bin/env bash\necho "root-build:$1"\n')
    (tool / 'generators/impl/src/product/java.gen').mkdir(parents=True)
    generated = tool / 'generators/impl/src/product/java.gen/keep.java'
    generated.write_text('keep')
    result = subprocess.run(['bash', str(tool / 'devops/bootstrap/bootstrap.sh'),
                             '--root', 'generators/impl', '--plan-only'],
                            capture_output=True, text=True, env={
                                **os.environ,
                                'MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE': 'source',
                                'MODUSTRO_BOOTSTRAP_SOURCE_REPOSITORIES': str(lib),
                            }, timeout=30)
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert 'Source prerequisites: 1 artifact(s)' in result.stdout
    assert 'root-build:--plan-only' in result.stdout
    assert generated.read_text() == 'keep'


def test_source_gradle_restricts_transitive_modustro_groups(tmp_path):
    lib = make_repo(tmp_path, 'pub.lib.General')
    tool = make_repo(tmp_path, 'pub.tool.General')
    base = make_artifact(lib, 'common')
    make_artifact(tool, 'generators/impl', [base])
    out = tmp_path / 'build'
    result = subprocess.run([sys.executable, str(BOOTSTRAP / 'prepare.py'), 'plan',
                             '--repository', str(tool), '--root', str(tool / 'generators/impl'),
                             '--output', str(out), '--version', '1.1-SNAPSHOT'],
                            capture_output=True, text=True, env={
                                **os.environ, 'MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE': 'source',
                                'MODUSTRO_BOOTSTRAP_SOURCE_GROUPS': 'eu.algites.lib.common,eu.algites.lib.data',
                            }, timeout=30)
    assert result.returncode == 0, result.stderr
    gradle = (out / 'gradle/build.gradle').read_text()
    assert 'exclusiveContent' in gradle
    assert 'modustro-sources-only' in gradle
    assert 'eu.algites.lib.data' in gradle
    assert 'eu.algites.lib.common' in gradle
