"""Exercise public Defs CLI against JAR-compiled XML interface + wheel parent."""
from pathlib import Path
import subprocess
from zipfile import ZipFile
import sys

TOOL = next(p for p in Path(__file__).resolve().parents if p.name == "pub.tool.General")
LIB = TOOL.parent / "pub.lib.General"
sys.path.insert(0, str(LIB / "naming/convention/impl/src/product/python"))
sys.path.insert(0, str(LIB / "naming/convention/intf/src/product/python"))
sys.path.insert(0, str(LIB / "naming/convention/intf/src/product/config"))
for branch in ("generators/code/common/src/product/python",
               "generators/code/defscodegen/intf/src/product/python",
               "generators/code/defscodegen/impl/src/product/python",
               "generators/code/defscodegen/cli/src/product/python"):
    sys.path.insert(0, str(TOOL / branch))

from eu.algites.tool.codegen.defs.impl.cli.canonical_defs_codegen_cli import main

uri = 'https://example.org/contracts/base_1.xsd'
xsd = f'''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" targetNamespace="{uri}">
<xs:complexType name="BaseType"><xs:sequence><xs:element name="Inherited" type="xs:string"/></xs:sequence></xs:complexType></xs:schema>'''
def test_public_defs_cli_resolves_xsd_and_binary_interfaces_from_jar_and_wheel(tmp_path):
    """Dependency archives supply source definitions and already compiled contracts, but are not generated."""
    dirname = str(tmp_path)
    t=Path(dirname); root=t/'repo'; artifact=root/'sample'/'intf'
    artifact.mkdir(parents=True); (artifact/'modustro-artifact.yml').write_text('identifier: test\n')
    child=artifact/'src/product/xmldefs/example/contracts/child_1.xsd'
    child.parent.mkdir(parents=True)
    child.write_text(f'''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:base="{uri}" targetNamespace="urn:child">
      <xs:import namespace="{uri}" schemaLocation="{uri}"/>
      <xs:complexType name="ChildType"><xs:complexContent><xs:extension base="base:BaseType">
      <xs:sequence><xs:element name="ChildField" type="xs:string"/></xs:sequence>
      </xs:extension></xs:complexContent></xs:complexType></xs:schema>''')
    java=t/'java-src'; classes=t/'classes'; classes.mkdir()
    sources={
        'annotations/AIaDataObject.java': '''package annotations; import java.lang.annotation.*; @Retention(RetentionPolicy.RUNTIME) public @interface AIaDataObject {}''',
        'annotations/Kind.java': '''package annotations; public enum Kind { TYPE, ELEMENT }''',
        'annotations/AIaXmlDataObject.java': '''package annotations; import java.lang.annotation.*; @Retention(RetentionPolicy.RUNTIME) public @interface AIaXmlDataObject { Kind definitionKind(); String namespace(); String namespaceLocalName(); }''',
        'example/contracts/Parent.java': f'''package example.contracts;
            @annotations.AIaDataObject()
            @annotations.AIaXmlDataObject(definitionKind=annotations.Kind.TYPE, namespace="{uri}", namespaceLocalName="BaseType")
            public interface Parent {{ String getInherited(); }}''',
    }
    for name, value in sources.items():
        source=java/name; source.parent.mkdir(parents=True,exist_ok=True); source.write_text(value)
    subprocess.run(['javac','-d',str(classes),*(str(p) for p in java.rglob('*.java'))],check=True)
    jar=t/'dependency.jar'
    with ZipFile(jar,'w') as z:
        for file in classes.rglob('*.class'):
            z.write(file, file.relative_to(classes).as_posix())
        z.writestr('eu/example/contracts/base_1.xsd', xsd)
    wheel=t/'dependency-1.0-py3-none-any.whl'
    with ZipFile(wheel,'w') as z:
        z.writestr('eu/algites/lib/naming/convention/base_type.py',f'''class BaseType(object):
    __data_object__ = Metadata()
    __xml_data_object__ = AIaXmlDataObject(definition_kind=Kind.TYPE, namespace={uri!r}, namespace_local_name="BaseType")
''')
    args=[f'--repository-root={root}',
          '--defs-input-paths:python=sample/intf/src/product/xmldefs/example/contracts/child_1.xsd',
          f'--defs-dependency-paths:java={jar}',f'--defs-dependency-paths:python={wheel}',
          '--technology-dointf-output-dir:python=sample/intf/src/product/python.gen',
          '--common-codegen-naming-convention:python=algites-python-codegen-common_1',
          '--defs-codegen-naming-convention:python=algites-python-defscodegen-standard_1']
    assert main(args) == 0
    out=artifact/'src/product/python.gen/example/contracts'
    generated = sorted(out.glob('*.py'))
    assert {p.name for p in generated} == {'aiig_child_type_1.py', 'aiig_child_type_1.py'}
    specialized = (out / 'aiig_child_type_1.py').read_text(encoding='utf-8')
    assert 'from eu.algites.lib.naming.convention.base_type import BaseType' in specialized
    assert 'class AIigChildType_1(AIigChildType_1, BaseType, AIiXmlDataObject):' in specialized
    assert 'class AIigChildType_1(AIiDataObject):' in (out / 'aiig_child_type_1.py').read_text()
    # Neither the imported parent XML model nor its annotated contracts are
    # generation inputs: do not create duplicate inherited interfaces.
    assert not any('base_type' in file.name for file in generated)
    assert not list(out.glob('*.java'))
    # Dry-run mode must succeed with identical JAR/wheel dependency resolution.
    assert main([*args, '--check']) == 0
