"""Canonical ElementKind and embedded group emission integration tests."""
from test_canonical_source_emitter import _pipeline, _emitter
from eu.algites.tool.codegen.defs.impl.standard.canonical_pipeline import AIcdDefsCodegenSourceDocument
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIngSourceInputKind_1 as Kind, AIngElementKind_1 as ElementKind)
from eu.algites.tool.codegen.defs.impl.standard.canonical_source_emitter import (
    AIcDefsCodegenCanonicalSourceEmitter as Emitter, AIcdDefsCodegenEmissionName as Name)


XSD = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
      targetNamespace="urn:embedded" xmlns:tns="urn:embedded"
      elementFormDefault="qualified">
  <xs:complexType name="Employee"><xs:sequence>
    <xs:element name="Kind" type="xs:string"/>
    <xs:choice>
      <xs:element name="Value" type="xs:string"/>
      <xs:element name="Convention" type="xs:string"/>
      <xs:sequence><xs:element name="Name" type="xs:string"/>
                   <xs:element name="Regexp" type="xs:string"/></xs:sequence>
    </xs:choice>
  </xs:sequence></xs:complexType>
</xs:schema>'''


def test_nested_choice_has_embedded_member_and_emits_without_wire_name(tmp_path):
    result = _pipeline().process((AIcdDefsCodegenSourceDocument(Kind.XMLDEFS, 'employee.xsd', XSD),))
    employee = next(t for t in result.types if t.name == 'Employee')
    embedded = [child for child in employee.structure.children
                if getattr(child, 'element_kind', None) is ElementKind.EMBEDDED]
    assert len(embedded) == 1
    assert embedded[0].structure.origin.name == 'SYNTHETIC'
    all_types = Emitter.declarations(result.types)
    names = {t.identity: Name(f'AIigT{i}', f'AIigT{i}', f'aiig_t{i}')
             for i, t in enumerate(all_types)}
    output = _emitter(result.types, names).render(result.types)
    java = {o.relative_path: o.content for o in output if o.language == 'java'}
    py = {o.relative_path: o.content for o in output if o.language == 'python'}
    main = java['test/output/' + names[employee.identity].java_type + '.java']
    assert 'embedded = true' in main
    assert 'fieldName = "Choice' not in main
    main_python = py['test/output/' + names[employee.identity].python_module + '.py']
    assert 'embedded=True' in main_python
    for output_file, content in java.items():
        path = tmp_path / 'java' / output_file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    import subprocess
    from test_canonical_source_emitter import LIB
    compiled = subprocess.run(['javac', '-sourcepath', str(LIB / 'data/dataobject/intf/src/product/java'),
        '-d', str(tmp_path / 'classes'), *map(str, (tmp_path / 'java').rglob('*.java'))],
        capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    for name, content in py.items():
        compile(content, name, 'exec')
