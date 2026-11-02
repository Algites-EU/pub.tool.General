"""Regressions for shared artifact selection in both code generators."""
from pathlib import Path
from zipfile import ZipFile
import pytest

from eu.algites.tool.codegen.common.artifact_resolver import (
    parse_artifacts, resolve_artifacts,
)


def test_maven_and_modustro_use_same_resolved_jar(tmp_path):
    jar = (tmp_path / 'java/maven/eu/algites/lib/contract/1.1-SNAPSHOT/'
           'contract-1.1-SNAPSHOT.jar')
    jar.parent.mkdir(parents=True)
    with ZipFile(jar, 'w') as archive:
        archive.writestr('example/Person.class', b'fixture')
    one = parse_artifacts('eu.algites.lib:contract:1.1-SNAPSHOT', 'java')
    two = parse_artifacts('contract@1.1-SNAPSHOT', 'java')
    assert resolve_artifacts(one, 'java', tmp_path) == (jar,)
    assert resolve_artifacts(two, 'java', tmp_path) == (jar,)


def test_python_specifiers_and_modustro_snapshot(tmp_path):
    directory = tmp_path / 'python/wheels'
    directory.mkdir(parents=True)
    for version in ('1.1.dev20261031', '1.1.dev20261101'):
        with ZipFile(directory / f'contract-{version}-py3-none-any.whl', 'w') as wheel:
            wheel.writestr('contract/__init__.py', '')
    selected = parse_artifacts('contract>=1.1.dev0,<1.1a0', 'python')
    assert '1.1.dev20261101' in str(resolve_artifacts(selected, 'python', tmp_path)[0])
    modustro = parse_artifacts('contract@1.1-SNAPSHOT', 'python')
    assert resolve_artifacts(modustro, 'python', tmp_path) == resolve_artifacts(selected, 'python', tmp_path)


def test_prefixed_modustro_python_distribution(tmp_path):
    directory = tmp_path / 'python/wheels'
    directory.mkdir(parents=True)
    wheel = directory / 'eu_algites_pub_lib_general_example_defsintf-1.1.dev20261101-py3-none-any.whl'
    with ZipFile(wheel, 'w') as archive:
        archive.writestr('example/__init__.py', '')
    spec = parse_artifacts('pub.lib.General_example.defsintf@1.1-SNAPSHOT', 'python')
    assert resolve_artifacts(spec, 'python', tmp_path) == (wheel,)


def test_semicolon_is_list_delimiter_but_python_commas_stay_in_version():
    specs = parse_artifacts('first>=1.1.dev0,<1.1a0;second==2.0', 'python')
    assert len(specs) == 2
    assert specs[0].name == 'first'
    assert specs[1].name == 'second'
    with pytest.raises(ValueError):
        parse_artifacts('maven:group:artifact:1.0', 'python')
    with pytest.raises(ValueError):
        parse_artifacts('first>=1.0;python_version>="3.12"', 'python')
    with pytest.raises(ValueError):
        parse_artifacts('a:b:1.0;;c:d:2.0', 'java')
