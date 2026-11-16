"""Universal bootstrap accepts compact/structured technology and schema identities."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / 'devops/bootstrap'


def load_script(name: str):
    path = BOOTSTRAP / name
    spec = importlib.util.spec_from_file_location('bootstrap_' + name.replace('.', '_').replace('-', '_'), path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('script', ['prepare.py', 'source-dependencies.py'])
def test_both_technology_kinds_forms(script):
    module = load_script(script)
    compact = {'TechnologyKinds':['java','python']}
    structured = {'TechnologyKinds':{'Items':[
        {'TechnologyKind':'java', 'BuildOutputTypes':{'Items':[{'BuildOutputType':'java_classes_jar'}]}},
        {'TechnologyKind':'python', 'BuildOutputTypes':{'Items':[{'BuildOutputType':'python_wheel'}]}},
    ]}}
    assert module.technology_kinds(compact) == frozenset({'java','python'})
    assert module.technology_kinds(structured) == module.technology_kinds(compact)
    with pytest.raises(ValueError):
        module.technology_kinds({'TechnologyKinds':{'Items':'java'}})


def test_schema_url_and_urn_are_aliases(tmp_path, monkeypatch):
    module = load_script('schema-locations.py')
    owner = tmp_path / 'artifact'
    directory = owner / 'src/product/yamldefs/eu/algites/example'
    directory.mkdir(parents=True)
    target = directory / 'example_1.yamldef.schema.json'
    target.write_text(json.dumps({'$id':'urn:algites:example:1', 'type':'object'}))
    (directory/(target.name+'.meta.yml')).write_text(
        'GlobalPublicationPathId: eu/algites/example/example_1.yamldef.schema.json\n')
    monkeypatch.setattr(module, 'selected_artifacts',
        lambda repository, root: [SimpleNamespace(repository=tmp_path, relative=Path('artifact'))])
    found = module.collect(tmp_path, tmp_path)
    assert found['urn:algites:example:1'] == target.resolve()
    assert found['https://defs.dev.algites.eu/api/yamldefs/eu/algites/example/example_1.yamldef.schema.json'] == target.resolve()
    # Inputs with unsafe property-file delimiters are rejected before mapping.
    target.write_text(json.dumps({'$id':'urn:algites:bad\nidentity', 'type':'object'}))
    with pytest.raises(ValueError, match='Unsupported schema'):
        module.collect(tmp_path, tmp_path)


def test_shared_bootstrap_script_syntax():
    for filename in ('bootstrap.sh','build.sh','generate.sh','upload-cloudsmith.sh'):
        subprocess.run(['bash','-n',str(BOOTSTRAP/filename)],check=True)


def test_repository_specific_configuration_is_optional():
    module = load_script('selfhosting.py')
    assert module.policies(ROOT) == (
        __import__('yaml').safe_load((BOOTSTRAP/'bootstrap-specializations.yml').read_text())
        if (BOOTSTRAP/'bootstrap-specializations.yml').exists() else {}
    )
