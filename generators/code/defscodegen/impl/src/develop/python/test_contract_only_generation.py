"""Schemas generate annotated Java/Python contracts only; SDO has separate ownership."""
import json
from pathlib import Path
import pytest
from eu.algites.tool.codegen.defs.aic_schema_contract_bindings_generator import AIcSchemaContractBindingsGenerator


def _fixture(root):
    schemas = root / 'intf/src/product/jsondefs/example/contracts'
    schemas.mkdir(parents=True)
    (schemas / 'example_1.jsondef.schema.json').write_text(json.dumps({
        '$id': 'urn:example:contract:1', 'type':'object',
        'properties': {'Name': {'type':'string'}, 'Count': {'type':'integer'}},
        'required':['Name']}))
    manifest=root/'bindings.json'
    manifest.write_text(json.dumps({'artifact':'intf','languages':['java','python'],'bindings':[]}))
    return manifest


def test_contract_only_repository_two_technologies(tmp_path):
    manifest = _fixture(tmp_path)
    generator = AIcSchemaContractBindingsGenerator()
    outputs = generator.generate_repository(tmp_path, manifest)
    assert {o['language'] for o in outputs} == {'java','python'}
    assert len(outputs)==2
    py=(tmp_path/'intf/src/product/python.gen/example/contracts/aiig_example_1.py').read_text()
    java=(tmp_path/'intf/src/product/java.gen/example/contracts/AIigExample_1.java').read_text()
    assert 'AIcdDataObjectField' in py and 'AIcdDataObject(' in py
    assert 'AIaDataObjectField' in java and 'AIaDataObject(' in java
    assert '@abstractmethod\n    def getName' in py
    assert 'AIiDataObject' in java and 'AIiDataObject' in py
    assert not (tmp_path/'impl').exists()
    assert generator.generate_repository(tmp_path, manifest, check=True) == outputs
    (tmp_path/'intf/src/product/python.gen/example/contracts/aiig_example_1.py').unlink()
    with pytest.raises(ValueError, match='outdated'):
        generator.generate_repository(tmp_path, manifest, check=True)


def test_contract_stale_ownership(tmp_path):
    manifest=_fixture(tmp_path)
    generator=AIcSchemaContractBindingsGenerator()
    generator.generate_repository(tmp_path,manifest)
    artifact=tmp_path/'intf/src/product/python.gen/example/contracts'
    foreign=artifact/'not_ours.py';foreign.write_text('x=1\n')
    schema=tmp_path/'intf/src/product/jsondefs/example/contracts/example_1.jsondef.schema.json'
    schema.write_text(json.dumps({'type':'object','properties':{'Renamed':{'type':'string'}}}))
    generator.generate_repository(tmp_path,manifest)
    assert foreign.read_text()=='x=1\n'
    assert not (tmp_path/'impl').exists()


def test_schema_allof_creates_inherited_java_and_python_contracts(tmp_path):
    schemas = tmp_path / 'intf/src/product/jsondefs/example/contracts'
    schemas.mkdir(parents=True)
    (schemas / 'parent_1.jsondef.schema.json').write_text(json.dumps({
        '$id':'urn:example:parent:1', 'type':'object',
        'properties':{'Name':{'type':'string'}},'required':['Name']}))
    (schemas / 'child_1.jsondef.schema.json').write_text(json.dumps({
        '$id':'urn:example:child:1', 'allOf':[
            {'$ref':'parent_1.jsondef.schema.json'},
            {'type':'object','properties':{'Count':{'type':'integer'}}}]}))
    manifest=tmp_path/'bindings.json'
    manifest.write_text(json.dumps({'artifact':'intf','languages':['java','python'],'bindings':[]}))
    generator=AIcSchemaContractBindingsGenerator()
    output=generator.generate_repository(tmp_path,manifest)
    assert len(output)>=4
    java=(tmp_path/'intf/src/product/java.gen/example/contracts/AIigChild_1.java').read_text()
    python=(tmp_path/'intf/src/product/python.gen/example/contracts/aiig_child_1.py').read_text()
    assert 'extends example.contracts.AIigParent_1 {' in java
    assert 'class AIigChild_1(AIigParent_1):' in python
    assert ' count()' in java and ' name()' not in java
    assert 'def getCount' in python and 'def getName' not in python
    assert generator.generate_repository(tmp_path,manifest,check=True)==output


def test_allof_rejects_missing_parent_contract(tmp_path):
    manifest = _fixture(tmp_path)
    schemas=tmp_path/'intf/src/product/jsondefs/example/contracts'
    schema=schemas/'example_1.jsondef.schema.json'
    schema.write_text(json.dumps({'allOf':[
        {'$ref':'missing_1.jsondef.schema.json'},
        {'type':'object','properties':{'Count':{'type':'integer'}}}]}))
    with pytest.raises(ValueError,match='parent is not an emitted contract'):
        AIcSchemaContractBindingsGenerator().generate_repository(tmp_path,manifest)


def test_manifest_discovers_xsd_in_both_languages(tmp_path):
    schemas=tmp_path/'intf/src/product/xmldefs/example/contracts'
    schemas.mkdir(parents=True)
    (schemas/'example_1.xsd').write_text('''<?xml version="1.0" encoding="UTF-8"?>
    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" targetNamespace="urn:example:xsd:1" version="1">
      <xs:element name="example" type="ThingType" />
      <xs:complexType name="ThingType"><xs:sequence>
        <xs:element name="Name" type="xs:string" />
        <xs:element name="Count" type="xs:int" minOccurs="0" />
      </xs:sequence></xs:complexType>
    </xs:schema>''' )
    manifest=tmp_path/'bindings.json'
    manifest.write_text(json.dumps({'artifact':'intf','languages':['java','python'],'bindings':[]}))
    generator=AIcSchemaContractBindingsGenerator()
    result=generator.generate_repository(tmp_path,manifest)
    assert len(result)==2
    java=(tmp_path/'intf/src/product/java.gen/example/contracts/AIigExample_1.java').read_text()
    python=(tmp_path/'intf/src/product/python.gen/example/contracts/aiig_example_1.py').read_text()
    assert ' name()' in java and ' count()' in java
    assert 'def getName' in python and 'def getCount' in python
    assert 'AIaDataObjectField' in java and 'AIcdDataObjectField' in python
    assert not (tmp_path/'impl').exists()
    generator.generate_repository(tmp_path,manifest,check=True)


def test_json_yaml_xsd_merge_the_same_logical_contract(tmp_path):
    for kind, suffix in (('jsondefs', 'jsondef.schema.json'),
                         ('yamldefs', 'yamldef.schema.json')):
        path = tmp_path / 'intf/src/product' / kind / 'example/contracts'
        path.mkdir(parents=True)
        (path / f'example_1.{suffix}').write_text(json.dumps({
            '$id': 'urn:example:crossformat:1', 'type':'object',
            'properties': {'Name': {'type':'string'}, 'Alias': {'type':'string'}},
            'required':['Name']}))
    xsd = tmp_path / 'intf/src/product/xmldefs/example/contracts'
    xsd.mkdir(parents=True)
    (xsd/'example_1.xsd').write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        targetNamespace="urn:example:crossformat:1" version="1">
        <xs:element name="example" type="ExampleType"/>
        <xs:complexType name="ExampleType"><xs:sequence>
          <xs:element name="Name" type="xs:string"/>
          <xs:element name="Alias" type="xs:string" minOccurs="0"/>
        </xs:sequence></xs:complexType>
    </xs:schema>''')
    manifest = tmp_path/'bindings.json'
    manifest.write_text(json.dumps({'artifact':'intf','languages':['java','python'],'bindings':[]}))
    generator = AIcSchemaContractBindingsGenerator()
    result = generator.generate_repository(tmp_path,manifest)
    assert len(result) == 6
    java = (tmp_path/'intf/src/product/java.gen/example/contracts/AIigExample_1.java').read_text()
    python = (tmp_path/'intf/src/product/python.gen/example/contracts/aiig_example_1.py').read_text()
    assert java.count('public interface AIigExample_1') == 1
    assert 'Canonical representations:' in java and 'XMLDEFS' in java
    assert '__data_object_fields__' in python
    assert not (tmp_path/'impl').exists()
    generator.generate_repository(tmp_path,manifest,check=True)



def test_xsd_unsupported_attribute_must_not_silently_disappear(tmp_path):
    root=tmp_path/'intf/src/product/xmldefs/example/contracts'
    root.mkdir(parents=True)
    (root/'sample_1.xsd').write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" version="1">
        <xs:complexType name="Sample"><xs:sequence>
          <xs:element name="Value" type="xs:string" />
        </xs:sequence><xs:attribute name="Code" type="xs:string" use="required"/>
        </xs:complexType></xs:schema>''')
    manifest=tmp_path/'bindings.json'
    manifest.write_text(json.dumps({'artifact':'intf','languages':['java','python']}))
    with pytest.raises(ValueError, match='XSD attributes'):
        AIcSchemaContractBindingsGenerator().generate_repository(tmp_path,manifest)


def test_json_yaml_inheritance_merge_keeps_one_parent(tmp_path):
    for kind, suffix in (('jsondefs', 'jsondef.schema.json'), ('yamldefs', 'yamldef.schema.json')):
        root = tmp_path / 'intf/src/product' / kind / 'example/contracts'
        root.mkdir(parents=True)
        parent=f'parent_1.{suffix}'
        (root/parent).write_text(json.dumps({
            '$id':'urn:parent:1', 'type':'object',
            'properties':{'Name':{'type':'string'}}, 'required':['Name']}))
        (root/f'child_1.{suffix}').write_text(json.dumps({
            '$id':'urn:child:1', 'allOf':[{'$ref':parent},
                {'type':'object','properties':{'Count':{'type':'integer'}}}]}))
    manifest=tmp_path/'bindings.json'
    manifest.write_text(json.dumps({'artifact':'intf','languages':['java','python']}))
    generator=AIcSchemaContractBindingsGenerator()
    results=generator.generate_repository(tmp_path,manifest)
    assert len(results)>=8
    java=(tmp_path/'intf/src/product/java.gen/example/contracts/AIigChild_1.java').read_text()
    python=(tmp_path/'intf/src/product/python.gen/example/contracts/aiig_child_1.py').read_text()
    assert 'extends example.contracts.AIigParent_1 {' in java
    assert 'class AIigChild_1(AIigParent_1)' in python
    generator.generate_repository(tmp_path,manifest,check=True)


def test_repository_manifest_xsd_import_graph_and_enums(tmp_path):
    import shutil
    fixture = Path(__file__).resolve().parents[1] / 'xmldefs'
    target = tmp_path / 'intf/src/product/xmldefs/example/contracts'
    shutil.copytree(fixture, target)
    manifest = tmp_path/'bindings.json'
    manifest.write_text(json.dumps({'artifact':'intf','languages':['java','python']}))
    generator = AIcSchemaContractBindingsGenerator()
    result = generator.generate_repository(tmp_path,manifest)
    assert len(result) == 10
    assert {'AIigParityRoot_1','AIigParityChild_1','AIigParityLeaf_1','AIngParityStatus_1'} <= {
        row['type'] for row in result}
    assert not (tmp_path/'impl').exists()
    generator.generate_repository(tmp_path,manifest,check=True)
