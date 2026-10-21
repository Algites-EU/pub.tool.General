from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind
"""Schemas generate annotated Java/Python contracts only; SDO has separate ownership."""
import json
from pathlib import Path
import pytest
from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import AIcSchemaContractBindingsGenerator


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
    assert 'AIiJsonDataObject' in java and 'AIiJsonDataObject' in py
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
    assert ' getCount()' in java and ' getName()' not in java
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
    assert len(result)==6  # includes XML namespace contract for each target
    java=(tmp_path/'intf/src/product/java.gen/example/contracts/AIigExample_1.java').read_text()
    python=(tmp_path/'intf/src/product/python.gen/example/contracts/aiig_example_1.py').read_text()
    assert ' getName()' in java and ' getCount()' in java
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
    assert len(result) == 10  # includes XML namespace contract for each target
    java = (tmp_path/'intf/src/product/java.gen/example/contracts/AIigExample_1.java').read_text()
    python = (tmp_path/'intf/src/product/python.gen/example/contracts/aiig_example_1.py').read_text()
    assert java.count('public interface AIigExample_1') == 1
    assert 'Canonical representations:' in java and 'XMLDEFS' in java
    assert '__data_object_fields__' in python
    assert not (tmp_path/'impl').exists()
    generator.generate_repository(tmp_path,manifest,check=True)



def test_xsd_root_attribute_becomes_canonical_field(tmp_path):
    root=tmp_path/'intf/src/product/xmldefs/example/contracts'
    root.mkdir(parents=True)
    (root/'sample_1.xsd').write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" version="1">
        <xs:complexType name="Sample"><xs:sequence>
          <xs:element name="Value" type="xs:string" />
        </xs:sequence><xs:attribute name="Code" type="xs:string" use="required"/>
        </xs:complexType></xs:schema>''')
    manifest=tmp_path/'bindings.json'
    manifest.write_text(json.dumps({'artifact':'intf','languages':['java','python']}))
    generated = AIcSchemaContractBindingsGenerator().generate_repository(tmp_path, manifest)
    assert generated
    java = (tmp_path/'intf/src/product/java.gen/example/contracts/AIigSample_1.java').read_text()
    python = (tmp_path/'intf/src/product/python.gen/example/contracts/aiig_sample_1.py').read_text()
    assert 'getCode()' in java
    assert 'getCode' in python
    from eu.algites.tool.codegen.defs.impl.standard.aic_xml_defs_frontend import AIcXmlDefsFrontend
    from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
    from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
    from eu.algites.lib.naming.convention.impl.algites.aic_algites_naming_profiles_1 import AIcAlgitesNamingProfiles_1
    path = root/'sample_1.xsd'
    contract = AIcXmlDefsFrontend().load(AIcdDefinitionLoadRequest(path, AInDefinitionSourceKind.XMLDEFS,
        AIcAlgitesNamingProfiles_1.python_profile()))
    assert [(p.source_name, (p.presence is AInFieldPresenceKind.REQUIRED)) for p in contract.data_type.properties] == [('Value', True), ('Code', True)]


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
    # The fixture intentionally reuses the local element name Value across
    # independent XML namespaces. Put these separate declarations under unique
    # names when flattening all source files into one business Java package.
    for xsd in sorted(target.glob('*.xsd')):
        unique = 'Value' + ''.join(part.title() for part in xsd.stem.replace('_1', '').split('-'))
        text = xsd.read_text(encoding='utf-8')
        text = text.replace('<xs:element name="Value" type=',
                            f'<xs:element name="{unique}" type=', 1)
        xsd.write_text(text, encoding='utf-8')
    manifest = tmp_path/'bindings.json'
    manifest.write_text(json.dumps({'artifact':'intf','languages':['java','python']}))
    generator = AIcSchemaContractBindingsGenerator()
    result = generator.generate_repository(tmp_path,manifest)
    # Additional named XSD simple types are now emitted independently, not discarded.
    assert len(result) == 32  # includes one XML namespace per distinct URI and language
    assert {'AIigParityRoot_1','AIigParityChild_1','AIigParityLeaf_1',
            'AIngParityStatus_1', 'AIngNotationValue_1'} <= {
        row['type'] for row in result}
    assert not (tmp_path/'impl').exists()
    generator.generate_repository(tmp_path,manifest,check=True)


def test_two_allof_contract_parents_preserve_both_inheritance_paths(tmp_path):
    """Cross-resource metadata and local content remain two independent parents."""
    base = tmp_path / 'intf/src/product/yamldefs/example/contracts'
    base.mkdir(parents=True)
    (base / 'metadata_1.yamldef.schema.json').write_text(json.dumps({
        '$id': 'https://example.org/metadata_1.yamldef.schema.json',
        'type': 'object', 'properties': {'SchemaId': {'type': 'string'}},
        'required': ['SchemaId']}))
    (base / 'document_1.yamldef.schema.json').write_text(json.dumps({
        '$id': 'urn:example:document:1',
        '$defs': {'DocumentContent': {'type': 'object',
            'properties': {'Name': {'type': 'string'}}, 'required': ['Name']}},
        'allOf': [
            {'$ref': 'https://example.org/metadata_1.yamldef.schema.json'},
            {'$ref': '#/$defs/DocumentContent'}
        ]
    }))
    manifest = tmp_path / 'bindings.json'
    manifest.write_text(json.dumps({'artifact': 'intf', 'languages': ['java', 'python'], 'bindings': []}))
    result = AIcSchemaContractBindingsGenerator().generate_repository(tmp_path, manifest)
    assert result
    java = (tmp_path / 'intf/src/product/java.gen/example/contracts/AIigDocument_1.java').read_text()
    python = (tmp_path / 'intf/src/product/python.gen/example/contracts/aiig_document_1.py').read_text()
    assert 'extends example.contracts.AIigMetadata_1, example.contracts.AIigDocumentDefinitionDocumentContent_1' in java
    assert 'class AIigDocument_1(AIigMetadata_1, AIigDocumentDefinitionDocumentContent_1):' in python
    assert 'getSchemaId()' not in java and 'getName()' not in java
    assert 'def getSchemaId' not in python and 'def getName' not in python
    AIcSchemaContractBindingsGenerator().generate_repository(tmp_path, manifest, check=True)


def test_user_defined_getter_composition_reaches_generated_java_and_python(tmp_path, monkeypatch):
    """Both languages must render a custom getter prefix from the chosen YAML role."""
    from copy import deepcopy
    from eu.algites.lib.naming.convention.impl.algites.aic_name_convention_catalog_1 import AIcNameConventionCatalog_1

    standard = AIcNameConventionCatalog_1.standard
    def custom_catalog(language):
        source = standard(language)
        config = deepcopy(source._config)
        if language in ('java', 'python'):
            config['NameCompositions'][f'{language}-getter-method-name_1']['Segments'][0]['Value'] = 'read'
        return AIcNameConventionCatalog_1(config)

    monkeypatch.setattr(AIcNameConventionCatalog_1, 'standard', staticmethod(custom_catalog))
    manifest = _fixture(tmp_path)
    AIcSchemaContractBindingsGenerator().generate_repository(tmp_path, manifest)
    java = (tmp_path / 'intf/src/product/java.gen/example/contracts/AIigExample_1.java').read_text()
    python = (tmp_path / 'intf/src/product/python.gen/example/contracts/aiig_example_1.py').read_text()
    assert 'readName()' in java and 'readCount()' in java
    assert 'getName()' not in java and 'getCount()' not in java
    assert 'def readName(self)' in python and 'def readCount(self)' in python
    assert "getter_name='readName'" in python
    assert 'def getName(self)' not in python


def test_accessor_names_preserve_input_field_word_boundaries_without_fixed_output_syntax():
    """Schema camel/snake/kebab source names retain their meaning through configured profiles."""
    from eu.algites.lib.naming.convention.impl.algites.aic_algites_naming_profiles_1 import AIcAlgitesNamingProfiles_1
    from eu.algites.tool.codegen.defs.impl.standard.aic_generation_names import AIcGenerationNames

    names = AIcGenerationNames()
    profiles = AIcAlgitesNamingProfiles_1.python_profile()
    for source in ('customerId', 'CustomerId', 'customer_id', 'customer-id'):
        assert names.getter_name(source, profiles) == 'getCustomerId'
        assert names.setter_name(source, profiles) == 'setCustomerId'
