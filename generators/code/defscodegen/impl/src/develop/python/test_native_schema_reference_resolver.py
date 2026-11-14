"""Offline-first HTTPS reference and external inheritance integration regressions."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

TOOL = next(p for p in Path(__file__).resolve().parents if p.name == 'pub.tool.General')
for location in ('generators/code/common/src/product/python',
                 'generators/code/defscodegen/intf/src/product/python',
                 'generators/code/defscodegen/impl/src/product/python',
                 'generators/code/defscodegen/cli/src/product/python'):
    sys.path.insert(0, str(TOOL / location))

from eu.algites.tool.codegen.defs.impl.standard.schema_reference_resolver import (
    SchemaReferenceResolver)
from eu.algites.tool.codegen.defs.impl.cli.canonical_defs_codegen_cli import prepare
from test_canonical_native_cli import _manifest

PARENT = 'https://defs.dev.algites.eu/api/jsondefs/eu/algites/lib/naming/convention/common-naming-conventions_1.jsondef.schema.json'


def test_local_schema_takes_precedence_over_https_and_preserves_public_id(tmp_path):
    source = tmp_path / 'pub.lib.General/naming/intf/src/product/jsondefs/demo'
    source.mkdir(parents=True)
    local = source / 'common-naming-conventions_1.jsondef.schema.json'
    local.write_text(json.dumps({'$id': PARENT, 'type': 'object'}), encoding='utf-8')
    called = []
    resolver = SchemaReferenceResolver((tmp_path / 'pub.lib.General',), tmp_path / 'cache',
                                       fetch=lambda url, timeout: called.append(url))
    result = resolver.resolve(PARENT)
    assert result.uri == PARENT
    assert result.origin == str(local)
    assert not called


def test_remote_schema_is_verified_cached_and_not_refetched(tmp_path):
    called = []
    def fake_https(uri, timeout):
        called.append(uri)
        return json.dumps({'$id': uri, 'type': 'object'}).encode('utf-8')
    resolver = SchemaReferenceResolver((), tmp_path / 'cache', fetch=fake_https)
    assert resolver.resolve(PARENT).origin == PARENT
    assert resolver.resolve(PARENT).origin != PARENT
    assert called == [PARENT]


def test_remote_schema_must_have_matching_identity(tmp_path):
    resolver = SchemaReferenceResolver((), tmp_path / 'cache', attempts=1,
        fetch=lambda uri, timeout: b'{"$id":"https://other.invalid/nope"}')
    with pytest.raises(ValueError, match='mismatch'):
        resolver.resolve(PARENT)
    assert not list((tmp_path / 'cache').iterdir())


def test_xsd_import_checks_namespace_and_disallows_doctype(tmp_path):
    uri = 'https://defs.dev.algites.eu/api/xmldefs/demo/example_1.xsd'
    text = b'<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" targetNamespace="urn:example"/>'
    resolver = SchemaReferenceResolver((), tmp_path / 'cache', fetch=lambda u, t: text)
    with pytest.raises(ValueError, match='targetNamespace'):
        resolver.resolve(uri, namespace='urn:wrong')
    assert resolver.resolve(uri, namespace='urn:example').content == text
    evil = SchemaReferenceResolver((), tmp_path / 'evil', fetch=lambda u, t:
        b'<!DOCTYPE xs:schema [<!ENTITY attack SYSTEM "file:///etc/passwd">]><xs:schema/>')
    with pytest.raises(ValueError, match='DTD'):
        evil.resolve(uri)


def test_external_parent_uses_existing_interfaces_without_duplicate_output(tmp_path):
    manifest, root = _manifest(tmp_path)
    model = json.loads(manifest.read_text())
    # The parent schema is a reference-only input with an existing published
    # Java and Python contract. It must not become a second output declaration.
    parent_root = tmp_path / 'library'
    schema = parent_root / 'src/product/jsondefs/eu/algites/lib/naming/convention/common-naming-conventions_1.jsondef.schema.json'
    schema.parent.mkdir(parents=True)
    schema.write_text(json.dumps({'$id': PARENT, 'type': 'object', 'properties': {
        'Shared': {'type': 'string'}}}), encoding='utf-8')
    java = parent_root / 'src/product/java.gen/eu/algites/lib/naming/convention/AIigCommonNamingConventions_1.java'
    java.parent.mkdir(parents=True)
    java.write_text('package eu.algites.lib.naming.convention;\n'
                    '@AIaDataObject()\n'
                    f'@AIaDataObjectJsonSchema(schemaId = "urn:parent", schemaUrl = "{PARENT}")\n'
                    'public interface AIigCommonNamingConventions_1 {}\n')
    python = parent_root / 'src/product/python.gen/eu/algites/lib/naming/convention/aiig_common_naming_conventions_1.py'
    python.parent.mkdir(parents=True)
    python.write_text('class AIigCommonNamingConventions_1(object):\n'
                      '    __data_object__ = AIcdDataObject()\n'
                      f'    __json_schema__ = AIaDataObjectJsonSchema(schema_id="urn:parent", schema_url={PARENT!r})\n')
    child_path = root / model['inputs'][0]['path']
    child_path.write_text(json.dumps({'$id': 'urn:child', 'type': 'object',
        'allOf': [{'$ref': PARENT}], 'x-algites-defscodegen-extends': [PARENT],
        'properties': {'Name': {'type': 'string'}}}))
    model['reference_roots'] = [str(parent_root)]
    manifest.write_text(json.dumps(model))
    _, outputs = prepare(manifest)
    java_files = [v for k, v in outputs.items() if k.endswith('.java')]
    python_files = [v for k, v in outputs.items() if k.endswith('.py')]
    assert len(java_files) == 1 and len(python_files) == 1
    assert any('eu.algites.lib.naming.convention.AIigCommonNamingConventions_1'
               in source.partition('public interface ')[2].partition('{')[0]
               for source in java_files)
    assert any('from eu.algites.lib.naming.convention.aiig_common_naming_conventions_1 import AIigCommonNamingConventions_1'
               in source for source in python_files)
    assert all('class AIig' in source for source in python_files)


def test_external_xsd_extension_uses_existing_contract_and_local_import(tmp_path):
    """Imported XSD parent is linked, never emitted; local enum import remains typed."""
    manifest, root = _manifest(tmp_path)
    setting = json.loads(manifest.read_text())
    parent_root = tmp_path / 'external-xsd-library'
    uri = 'https://defs.dev.algites.eu/api/xmldefs/eu/algites/lib/naming/convention/common-naming-conventions_1.xsd'
    parent = parent_root / 'src/product/xmldefs/eu/algites/lib/naming/convention/common-naming-conventions_1.xsd'
    parent.parent.mkdir(parents=True)
    parent.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
      targetNamespace="''' + uri + '''">
      <xs:complexType name="CommonNamingConventions">
        <xs:sequence><xs:element name="Inherited" type="xs:string"/></xs:sequence>
      </xs:complexType>
    </xs:schema>''')
    java = parent_root / 'src/product/java.gen/eu/algites/lib/naming/convention/AIigCommonNamingConventions_1.java'
    java.parent.mkdir(parents=True)
    java.write_text('package eu.algites.lib.naming.convention;\n'
                    '@AIaDataObject()\n'
                    f'@AIaDataObjectXmlSchema(definitionKind = AInXmlObjectDefinitionKind.TYPE, namespace = "{uri}", namespaceLocalName = "CommonNamingConventions")\n'
                    'public interface AIigCommonNamingConventions_1 {}\n')
    python = parent_root / 'src/product/python.gen/eu/algites/lib/naming/convention/aiig_common_naming_conventions_1.py'
    python.parent.mkdir(parents=True)
    python.write_text('class AIigCommonNamingConventions_1(object):\n'
                      '    __data_object__ = AIcdDataObject()\n'
                      f'    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace={uri!r}, namespace_local_name="CommonNamingConventions")\n')
    original = root / setting['inputs'][0]['path']
    original.unlink()
    local = root / 'intf/src/product/xmldefs/example/aux_1.xsd'
    local.parent.mkdir(parents=True)
    local.write_text('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
       targetNamespace="urn:aux"><xs:simpleType name="Kind">
       <xs:restriction base="xs:string"><xs:enumeration value="some"/></xs:restriction>
       </xs:simpleType></xs:schema>''')
    source = local.parent / 'child_1.xsd'
    source.write_text(f'''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        xmlns:common="{uri}" xmlns:aux="urn:aux" targetNamespace="urn:child">
       <xs:import namespace="{uri}" schemaLocation="{uri}"/>
       <xs:import namespace="urn:aux" schemaLocation="aux_1.xsd"/>
       <xs:complexType name="Child"><xs:complexContent>
         <xs:extension base="common:CommonNamingConventions"><xs:sequence>
           <xs:element name="Type" type="aux:Kind"/>
         </xs:sequence></xs:extension>
       </xs:complexContent></xs:complexType>
     </xs:schema>''')
    setting['inputs'] = [
        {'kind': 'xmldefs', 'path': local.relative_to(root).as_posix()},
        {'kind': 'xmldefs', 'path': source.relative_to(root).as_posix()}]
    setting['reference_roots'] = [str(parent_root)]
    manifest.write_text(json.dumps(setting))
    _, outputs = prepare(manifest)
    assert len([path for path in outputs if path.endswith('AIigCommonNamingConventions_1.java')]) == 0
    assert any('eu.algites.lib.naming.convention.AIigCommonNamingConventions_1'
               in source.partition('public interface ')[2].partition('{')[0]
               for path, source in outputs.items() if path.endswith('.java'))


def test_external_xsd_prefers_readonly_derived_contract_over_common_and_sdo(tmp_path):
    """Real output hierarchy: generic Defs, XML Defs, and writable SDO share IDs."""
    from eu.algites.tool.codegen.defs.impl.cli.canonical_defs_codegen_cli import (
        _existing_contracts,
    )
    uri = 'https://example.org/contracts/common_1.xsd'
    key = '{' + uri + '}SharedType'
    java = tmp_path / 'project/src/product/java.gen/example/contracts'
    python = tmp_path / 'project/src/product/python.gen/example/contracts'
    java.mkdir(parents=True)
    python.mkdir(parents=True)
    for classname, extends in (
        ('GenericContract', 'eu.algites.lib.data.dataobject.AIiDataObject'),
        ('XmlDerivedContract', 'example.contracts.GenericContract'),
    ):
        (java / (classname + '.java')).write_text(
            'package example.contracts;\n'
            '@AIaDataObject()\n'
            f'@AIaXmlDataObject(definitionKind = AInXmlObjectDefinitionKind.TYPE, '
            f'namespace = "{uri}", namespaceLocalName = "SharedType")\n'
            f'public interface {classname} extends {extends} {{}}\n', encoding='utf-8')
    (java / 'WritableJavaContract.java').write_text(
        'package example.contracts;\n'
        '@AIaDataObject()\n'
        f'@AIaXmlDataObject(definitionKind = AInXmlObjectDefinitionKind.TYPE, '
        f'namespace = "{uri}", namespaceLocalName = "SharedType")\n'
        'public interface WritableJavaContract extends example.contracts.XmlDerivedContract, '
        'example.contracts.AIiSmartDataObject {\n'
        '    void setField(Object value);\n}\n', encoding='utf-8')
    (python / 'generic_contract.py').write_text(
        'class GenericContract(object):\n'
        '    __data_object__ = Metadata()\n'
        f'    __xml_data_object__ = AIaXmlDataObject(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace={uri!r}, namespace_local_name="SharedType")\n',
        encoding='utf-8')
    (python / 'xml_derived_contract.py').write_text(
        'from example.contracts.generic_contract import GenericContract\n'
        'class XmlDerivedContract(GenericContract):\n'
        '    __data_object__ = Metadata()\n'
        f'    __xml_data_object__ = AIaXmlDataObject(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace={uri!r}, namespace_local_name="SharedType")\n',
        encoding='utf-8')
    writable = python / 'impl/intf/mutable.py'
    writable.parent.mkdir(parents=True)
    writable.write_text(
        'from example.contracts.xml_derived_contract import XmlDerivedContract\n'
        'class WritableLayer(XmlDerivedContract):\n'
        '    """Generated mutable contract for XmlDerivedContract."""\n'
        f'    __data_object__ = Metadata(schema_id={uri!r}, schema_url="")\n'
        '    __xml_data_object__ = AIaXmlDataObject(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace_local_name="SharedType")\n'
        '    def setField(self, value): ...\n', encoding='utf-8')
    assert _existing_contracts((tmp_path,))[key] == {
        'java': 'example.contracts.XmlDerivedContract',
        'python_module': 'example.contracts.xml_derived_contract',
        'python_type': 'XmlDerivedContract',
    }


def test_external_xsd_unrelated_same_identity_still_errors(tmp_path):
    """Never silently pick between unrelated declarations for one XSD type."""
    from eu.algites.tool.codegen.defs.impl.cli.canonical_defs_codegen_cli import (
        _existing_contracts,
    )
    uri = 'https://example.org/contracts/common_1.xsd'
    java = tmp_path / 'src/product/java.gen/example/contracts'
    java.mkdir(parents=True)
    for classname in ('FirstContract', 'SecondContract'):
        (java / (classname + '.java')).write_text(
            'package example.contracts;\n'
            '@AIaDataObject()\n'
            f'@AIaXmlDataObject(definitionKind = AInXmlObjectDefinitionKind.TYPE, '
            f'namespace = "{uri}", namespaceLocalName = "SharedType")\n'
            f'public interface {classname} {{}}\n', encoding='utf-8')
    with pytest.raises(ValueError, match='unrelated candidates'):
        _existing_contracts((tmp_path,))


def test_unreferenced_security_duplicate_does_not_block_xsd_contract_index(tmp_path):
    """Only actually imported parent QNames are candidates for ambiguity checks."""
    from eu.algites.tool.codegen.defs.impl.cli.canonical_defs_codegen_cli import (
        _existing_contracts, _required_external_contract_ids,
    )
    from eu.algites.tool.codegen.defs.impl.standard.canonical_pipeline import (
        AIcdDefsCodegenSourceDocument,
    )
    from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
        AIngSourceInputKind_1,
    )
    java = tmp_path / 'security/src/product/java.gen/example/security'
    java.mkdir(parents=True)
    security_url = 'https://example.org/security/credential-profiles_1.xsd'
    for name in ('GeneralType', 'XmlType'):
        (java / f'{name}.java').write_text(
            'package example.security;\n'
            '@AIaDataObject()\n'
            f'@AIaXmlDataObject(definitionKind=K.TYPE, namespace="{security_url}", namespaceLocalName="ConfigurationNameType")\n'
            f'public interface {name} {{}}\n')
    parent_url = 'https://example.org/naming/common_1.xsd'
    (java / 'NamingParent.java').write_text(
        'package example.security;\n'
        '@AIaDataObject()\n'
        f'@AIaXmlDataObject(definitionKind=K.TYPE, namespace="{parent_url}", namespaceLocalName="CommonNamingConventions")\n'
        'public interface NamingParent {}\n')
    source = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
        xmlns:common="https://example.org/naming/common_1.xsd"
        targetNamespace="urn:child"><xs:import
        namespace="https://example.org/naming/common_1.xsd"
        schemaLocation="https://example.org/naming/common_1.xsd"/>
        <xs:complexType name="Child"><xs:complexContent>
        <xs:extension base="common:CommonNamingConventions"/>
        </xs:complexContent></xs:complexType></xs:schema>'''
    needed = _required_external_contract_ids((
        AIcdDefsCodegenSourceDocument(AIngSourceInputKind_1.XMLDEFS,
                                      'child.xsd', source),))
    assert needed == frozenset({'{' + parent_url + '}CommonNamingConventions'})
    resolved = _existing_contracts((tmp_path,), needed)
    assert list(resolved) == ['{' + parent_url + '}CommonNamingConventions']
    with pytest.raises(ValueError, match='unrelated candidates'):
        _existing_contracts((tmp_path,), frozenset(
            {'{' + security_url + '}ConfigurationNameType'}))


def test_packaged_schema_resources_resolve_offline_without_source_tree(tmp_path):
    """Installed JAR/wheel schemas lack src/product yet keep their public IDs."""
    packed = tmp_path / 'unpacked-jar/eu/example/contracts'
    packed.mkdir(parents=True)
    json_uri = 'https://example.org/jsondefs/eu/example/contracts/base_1.jsondef.schema.json'
    xml_uri = 'https://example.org/xmldefs/eu/example/contracts/base_1.xsd'
    (packed / 'base_1.jsondef.schema.json').write_text(json.dumps({
        '$id': json_uri, 'type': 'object'}), encoding='utf-8')
    (packed / 'base_1.xsd').write_text(
        '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" '
        f'targetNamespace="{xml_uri}"/>', encoding='utf-8')
    requested = []
    resolver = SchemaReferenceResolver((tmp_path / 'unpacked-jar',), tmp_path / 'cache',
        fetch=lambda url, timeout: requested.append(url))
    assert resolver.resolve(json_uri).origin == str(packed / 'base_1.jsondef.schema.json')
    assert resolver.resolve(xml_uri, namespace=xml_uri).origin == str(packed / 'base_1.xsd')
    assert requested == []


def test_compiled_java_dependency_classes_indexed_without_sources(tmp_path):
    """JAR-resolved .class annotations provide external QName/API linkage."""
    import shutil
    import subprocess
    from eu.algites.tool.codegen.defs.impl.cli.canonical_defs_codegen_cli import (
        _existing_contracts,
    )
    if not shutil.which('javac'):
        pytest.skip('A Java compiler is required for class-file contract fixture')
    src = tmp_path / 'src'
    classes = tmp_path / 'classes'
    texts = {
        'eu/algites/lib/data/dataobject/AIaDataObject.java': '''package eu.algites.lib.data.dataobject;
            import java.lang.annotation.*;
            @Retention(RetentionPolicy.RUNTIME)
            public @interface AIaDataObject { }''',
        'eu/algites/lib/data/dataobject/xmldefs/AIaXmlDataObject.java': '''package eu.algites.lib.data.dataobject.xmldefs;
            import java.lang.annotation.*;
            @Retention(RetentionPolicy.RUNTIME)
            public @interface AIaXmlDataObject {
                DefinitionKind definitionKind() default DefinitionKind.TYPE;
                String namespace() default "";
                String namespaceLocalName() default "";
            }''',
        'eu/algites/lib/data/dataobject/xmldefs/DefinitionKind.java': '''package eu.algites.lib.data.dataobject.xmldefs;
            public enum DefinitionKind { TYPE, ELEMENT }''',
        'example/contracts/Generic.java': '''package example.contracts;
            @eu.algites.lib.data.dataobject.AIaDataObject()
            public interface Generic { }''',
        'example/contracts/XmlSpecific.java': '''package example.contracts;
            @eu.algites.lib.data.dataobject.AIaDataObject()
            @eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObject(
               definitionKind=eu.algites.lib.data.dataobject.xmldefs.DefinitionKind.TYPE,
               namespace="urn:contracts", namespaceLocalName="SomeType")
            public interface XmlSpecific extends Generic { }''',
        'example/contracts/Writable.java': '''package example.contracts;
            @eu.algites.lib.data.dataobject.AIaDataObject()
            @eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObject(
               namespace="urn:contracts", namespaceLocalName="SomeType")
            public interface Writable extends XmlSpecific {
                void setField(Object value);
            }''',
    }
    for name, content in texts.items():
        path = src / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
    subprocess.run(['javac', '-d', str(classes), *(str(p) for p in src.rglob('*.java'))],
                   check=True, capture_output=True, text=True)
    # Deliberately do NOT expose the Java sources to the indexer.
    assert _existing_contracts((classes,), frozenset({'{urn:contracts}SomeType'})) == {
        '{urn:contracts}SomeType': {'java': 'example.contracts.XmlSpecific'}}


def test_wheel_module_index_without_python_gen_layout(tmp_path):
    """Published wheel module paths participate in the external contract index."""
    from eu.algites.tool.codegen.defs.impl.cli.canonical_defs_codegen_cli import (
        _existing_contracts,
    )
    root = tmp_path / 'unpacked-wheel'
    module = root / 'eu/algites/lib/naming/convention/aiig_source_1.py'
    module.parent.mkdir(parents=True)
    module.write_text('''from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.jsondefs.aia_json_data_object import AIaJsonDataObject
class AIigSource_1(object):
    __data_object__ = AIcdDataObject()
    __json_data_object__ = AIaJsonDataObject(schema_id="source", schema_url="https://example.org/source_1.jsondef.schema.json")
''')
    assert _existing_contracts((root,), frozenset({
        'https://example.org/source_1.jsondef.schema.json'})) == {
        'https://example.org/source_1.jsondef.schema.json': {
            'python_module': 'eu.algites.lib.naming.convention.aiig_source_1',
            'python_type': 'AIigSource_1'}}


def test_duplicate_of_unreferenced_contract_does_not_block_index(tmp_path):
    """Only external identities used by this batch may produce conflicts."""
    from eu.algites.tool.codegen.defs.impl.cli.canonical_defs_codegen_cli import _existing_contracts
    unrelated = '{urn:unrelated}FieldBindingType'
    needed = '{urn:needed}ParentType'
    for slot, parent in [('a', 'FirstParent'), ('b', 'SecondParent')]:
        directory = tmp_path / slot / 'src/product/java.gen/example/contracts'
        directory.mkdir(parents=True)
        (directory / 'AIigFieldBindingType_1.java').write_text(
            'package example.contracts;\n@AIaDataObject()\n'
            '@AIaXmlDataObject(definitionKind=K.TYPE, namespace="urn:unrelated", '
            'namespaceLocalName="FieldBindingType")\n'
            f'public interface AIigFieldBindingType_1 extends {parent} {{}}\n')
    needed_dir = tmp_path / 'needed/src/product/java.gen/example/contracts'
    needed_dir.mkdir(parents=True)
    (needed_dir / 'Parent.java').write_text(
        'package example.contracts;\n@AIaDataObject()\n'
        '@AIaXmlDataObject(definitionKind=K.TYPE, namespace="urn:needed", '
        'namespaceLocalName="ParentType")\n'
        'public interface Parent {}\n')
    assert _existing_contracts((tmp_path,), frozenset()) == {}
    assert _existing_contracts((tmp_path,), frozenset({needed})) == {
        needed: {'java': 'example.contracts.Parent'}}
    with pytest.raises(ValueError, match='Conflicting generated contract definitions') as error:
        _existing_contracts((tmp_path,), frozenset({unrelated}))
    assert 'FirstParent' in str(error.value) and 'SecondParent' in str(error.value)
    assert 'AIigFieldBindingType_1.java' in str(error.value)
    assert 'src/product/java.gen' in str(error.value)


def test_java_source_and_class_imports_resolve_to_same_contract(tmp_path):
    """Matching published .class and source .java must use fully qualified bases."""
    import shutil
    import subprocess
    from eu.algites.tool.codegen.defs.impl.cli.canonical_defs_codegen_cli import _existing_contracts
    if not shutil.which('javac'):
        pytest.skip('javac required')
    root = tmp_path / 'src'
    classes = tmp_path / 'binary'
    source_units = {
        'annotations/AIaDataObject.java': '''package annotations;
          import java.lang.annotation.*;
          @Retention(RetentionPolicy.RUNTIME) public @interface AIaDataObject {}''',
        'annotations/AIaXmlDataObject.java': '''package annotations;
          import java.lang.annotation.*;
          @Retention(RetentionPolicy.RUNTIME) public @interface AIaXmlDataObject {
            Kind definitionKind(); String namespace(); String namespaceLocalName(); }''',
        'annotations/Kind.java': 'package annotations; public enum Kind {TYPE, ELEMENT}',
        'example/base/AIiXmlDataObject.java': 'package example.base; public interface AIiXmlDataObject {}',
        'example/contracts/AIigFieldBindingType_1.java':
            'package example.contracts; public interface AIigFieldBindingType_1 {}',
        'example/contracts/AIigFieldBindingType_1.java': '''package example.contracts;
          import annotations.AIaDataObject;
          import annotations.AIaXmlDataObject;
          import annotations.Kind;
          import example.base.AIiXmlDataObject;
          @AIaDataObject()
          @AIaXmlDataObject(definitionKind=Kind.TYPE, namespace="urn:fields",
            namespaceLocalName="FieldBindingType")
          public interface AIigFieldBindingType_1 extends
            AIigFieldBindingType_1, AIiXmlDataObject {}''',
    }
    for name, content in source_units.items():
        source = root / 'project/src/product/java.gen' / name
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(content)
    subprocess.run(['javac', '-d', str(classes), *map(str, root.rglob('*.java'))],
                   check=True, capture_output=True, text=True)
    key = '{urn:fields}FieldBindingType'
    assert _existing_contracts((root, classes), frozenset({key})) == {
        key: {'java': 'example.contracts.AIigFieldBindingType_1'}}


def test_migrated_schema_metadata_indexed_without_generic_annotation(tmp_path):
    """New JSON/YAML and XML metadata live only on technology interfaces.

    The companion common interface owns __data_object__ / AIaDataObject, but
    dependency discovery must identify the format-specific child instead.
    """
    from eu.algites.tool.codegen.defs.impl.cli.canonical_defs_codegen_cli import _existing_contracts
    root = tmp_path / 'dependency'
    java = root / 'src/product/java.gen/demo'
    python = root / 'src/product/python.gen/demo'
    java.mkdir(parents=True)
    python.mkdir(parents=True)
    url = 'https://example.org/jsondefs/common_1.jsondef.schema.json'
    xml_id = '{urn:algites:test}Common'
    (java / 'Common.java').write_text(
        'package demo; @eu.algites.lib.data.dataobject.AIaDataObject() '
        'public interface Common {}')
    (java / 'JsonSpecific.java').write_text(
        'package demo;\n'
        '@eu.algites.lib.data.dataobject.jsonschema.AIaDataObjectJsonSchema('
        'schemaId="common", schemaVersion=1, schemaUrl="' + url + '")\n'
        'public interface JsonSpecific extends Common {}')
    (java / 'XmlSpecific.java').write_text(
        'package demo;\n'
        '@eu.algites.lib.data.dataobject.xmlschema.AIaDataObjectXmlSchema('
        'definitionKind=Kind.TYPE, namespace="urn:algites:test", namespaceLocalName="Common")\n'
        'public interface XmlSpecific extends Common {}')
    (python / 'common.py').write_text(
        'class Common:\n    __data_object__ = AIcdDataObject()\n')
    (python / 'json_specific.py').write_text(
        'from demo.common import Common\n'
        'class JsonSpecific(Common):\n'
        '    __json_schema__ = AIaDataObjectJsonSchema('
        'schema_id="common", schema_version=1, schema_url="' + url + '")\n')
    (python / 'xml_specific.py').write_text(
        'from demo.common import Common\n'
        'class XmlSpecific(Common):\n'
        '    __xml_schema__ = AIaDataObjectXmlSchema('
        'definition_kind=K.TYPE, namespace="urn:algites:test", namespace_local_name="Common")\n')
    result = _existing_contracts((root,), frozenset({url, xml_id}))
    assert result[url] == {
        'java': 'demo.JsonSpecific',
        'python_module': 'demo.json_specific', 'python_type': 'JsonSpecific'}
    assert result[xml_id] == {
        'java': 'demo.XmlSpecific',
        'python_module': 'demo.xml_specific', 'python_type': 'XmlSpecific'}


def test_new_annotation_class_reader_without_generic_marker(tmp_path):
    """Compiled Java contract metadata can be indexed without AIaDataObject."""
    import shutil
    import subprocess
    from eu.algites.tool.codegen.defs.impl.cli.canonical_defs_codegen_cli import _existing_contracts
    if not shutil.which('javac'):
        pytest.skip('javac required for Java/Python parity')
    src, classes = tmp_path/'source', tmp_path/'classes'
    src.mkdir(); classes.mkdir()
    units = {
        'demo/AIaDataObjectJsonSchema.java':
            'package demo; import java.lang.annotation.*; @Retention(RetentionPolicy.RUNTIME) '
            'public @interface AIaDataObjectJsonSchema { String schemaId(); String schemaUrl(); }',
        'demo/AIaDataObjectXmlSchema.java':
            'package demo; import java.lang.annotation.*; @Retention(RetentionPolicy.RUNTIME) '
            'public @interface AIaDataObjectXmlSchema { Kind definitionKind(); '
            'String namespace(); String namespaceLocalName(); }',
        'demo/Kind.java': 'package demo; public enum Kind { TYPE, ELEMENT }',
        'demo/ReadOnly.java': 'package demo; public interface ReadOnly {}',
        'demo/JsonSpecific.java':
            'package demo; @AIaDataObjectJsonSchema(schemaId="common", '
            'schemaUrl="https://example.org/common_1.json") '
            'public interface JsonSpecific extends ReadOnly {}',
        'demo/XmlSpecific.java':
            'package demo; @AIaDataObjectXmlSchema(definitionKind=Kind.TYPE, namespace="urn:test", '
            'namespaceLocalName="Common") public interface XmlSpecific extends ReadOnly {}',
    }
    for name, content in units.items():
        file = src/name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content)
    subprocess.run(['javac', '-d', str(classes), *map(str, src.rglob('*.java'))],
                   check=True, capture_output=True, text=True)
    result = _existing_contracts((classes,), frozenset({
        '{urn:test}Common', 'https://example.org/common_1.json'}))
    assert result['{urn:test}Common']['java'] == 'demo.XmlSpecific'
    assert result['https://example.org/common_1.json']['java'] == 'demo.JsonSpecific'


def test_live_python_contract_beats_stale_packaging_copy(tmp_path):
    """Source profiles change without stale setuptools build/lib becoming parents."""
    from eu.algites.tool.codegen.defs.impl.cli.canonical_defs_codegen_cli import _existing_contracts
    uri = 'https://defs.dev.algites.eu/api/xmldefs/eu/algites/lib/naming/convention/common-naming-conventions_1.xsd'
    live = (tmp_path / 'naming/convention/intf/src/product/python.gen'
            / 'eu/algites/lib/naming/convention/aiig_common_naming_conventions_1.py')
    stale = (tmp_path / 'build/run/bootstrap/python-projects'
             / 'pub-lib-General_naming-convention-intf/build/lib'
             / 'eu/algites/lib/naming/convention/aiig_common_naming_conventions_1.py')
    for path, name in ((live, 'AIigCommonNamingConventions_1'),
                       (stale, 'AIigCommonNamingConventions_1')):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('class ' + name + ':\n'
                        '    __xml_schema__ = AIaDataObjectXmlSchema('
                        'definition_kind=K.TYPE, namespace="' + uri + '", '
                        'namespace_local_name="CommonNamingConventions")\n',
                        encoding='utf-8')
    key = '{' + uri + '}CommonNamingConventions'
    assert _existing_contracts((tmp_path,), frozenset({key}))[key] == {
        'python_module': 'eu.algites.lib.naming.convention.aiig_common_naming_conventions_1',
        'python_type': 'AIigCommonNamingConventions_1'}
    # A packaged dependency alone remains a valid external reference.
    assert _existing_contracts((tmp_path / 'build/run/bootstrap/python-projects/pub-lib-General_naming-convention-intf/build/lib',), frozenset({key}))[key]['python_type'] == 'AIigCommonNamingConventions_1'



def test_prior_bootstrap_run_staging_is_not_external_contract_source(tmp_path):
    """A dependency checkout must not index old releases from other run UUIDs.

    Unlike a separately supplied wheel, the checkout's build/run workspace is
    never an API contract source, even when the live product contract is absent.
    """
    from eu.algites.tool.codegen.defs.impl.cli.canonical_defs_codegen_cli import _existing_contracts

    url = ('https://defs.dev.algites.eu/api/jsondefs/eu/algites/lib/naming/'
           'convention/common-naming-conventions_1.jsondef.schema.json')
    checkout = tmp_path / 'pub.lib.General'
    old_bases = [
        checkout / 'build/run/bootstrap/old-run-uuid/python-projects/'
                   'pub-lib-General_naming-convention-intf/build/lib',
        checkout / 'build/run/bootstrap/other-run-uuid/python-projects/'
                   'pub-lib-General_naming-convention-intf/build/lib',
    ]
    for base, typename, module_name in [
        (old_bases[0], 'AIigCommonNamingConventions_1',
         'aiig_common_naming_conventions_1'),
        (old_bases[1], 'AIigCommonNamingConventions_1',
         'aiig_common_naming_conventions_1'),
    ]:
        source = base / 'eu/algites/lib/naming/convention' / (module_name + '.py')
        source.parent.mkdir(parents=True)
        source.write_text(f'class {typename}:\n'
                          '    __json_schema__ = AIaDataObjectJsonSchema('
                          f'schema_id="common", schema_url="{url}")\n')

    # Staging must not become an external contract when the source is absent.
    assert _existing_contracts((checkout,), frozenset({url})) == {}

    current = (checkout / 'naming/convention/intf/src/product/python.gen'
               / 'eu/algites/lib/naming/convention/aiig_common_naming_conventions_1.py')
    current.parent.mkdir(parents=True)
    current.write_text(
        'class AIigCommonNamingConventions_1:\n'
        '    __json_schema__ = AIaDataObjectJsonSchema('
        f'schema_id="common", schema_url="{url}")\n')
    assert _existing_contracts((checkout,), frozenset({url})) == {
        url: {'python_module':
              'eu.algites.lib.naming.convention.aiig_common_naming_conventions_1',
              'python_type': 'AIigCommonNamingConventions_1'}}
    # A package explicitly selected as a dependency (not its source checkout)
    # still provides its published contract metadata.
    assert _existing_contracts((old_bases[0],), frozenset({url}))[url][
        'python_type'] == 'AIigCommonNamingConventions_1'


def test_checkout_build_class_files_are_not_implicit_external_dependencies(tmp_path):
    """Untrusted .class bytes from an old Gradle build cannot taint discovery."""
    from eu.algites.tool.codegen.defs.impl.cli.canonical_defs_codegen_cli import _existing_contracts
    checkout = tmp_path / 'pub.lib.General'
    stale = checkout / 'build/run/bootstrap/old-run/gradle-build/classes/Bad.class'
    stale.parent.mkdir(parents=True)
    stale.write_bytes(b'not a valid Java class file')
    assert _existing_contracts((checkout,), frozenset({'{urn:demo}Example'})) == {}

def test_real_live_python_contract_ambiguity_is_not_hidden(tmp_path):
    """Two unrelated checked-out source contracts still cause an error."""
    from eu.algites.tool.codegen.defs.impl.cli.canonical_defs_codegen_cli import _existing_contracts
    key = '{urn:test}Shared'
    for name in ('first', 'second'):
        path = tmp_path / name / 'src/product/python.gen/demo' / (name + '.py')
        path.parent.mkdir(parents=True)
        path.write_text('class ' + name.title() + ':\n'
                        '    __xml_schema__ = AIaDataObjectXmlSchema('
                        'definition_kind=K.TYPE, namespace="urn:test", '
                        'namespace_local_name="Shared")\n')
    with pytest.raises(ValueError, match='unrelated candidates'):
        _existing_contracts((tmp_path,), frozenset({key}))
