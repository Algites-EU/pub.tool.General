"""Regressions for resolving one read-only contract across independent schema kinds."""
from __future__ import annotations

import ast
import importlib.util
import os
from pathlib import Path
import re
import shutil
import subprocess

import pytest

TOOL = next(parent for parent in Path(__file__).resolve().parents if parent.name == 'pub.tool.General')
LIB = TOOL.parent / 'pub.lib.General'
CLI = TOOL / 'generators/code/defscodegen/cli/src/product'
INDEX = CLI / 'java/eu/algites/tool/codegen/defs/impl/cli'
PY_INDEX = CLI / 'python/eu/algites/tool/codegen/defs/impl/cli'
ROOT = LIB / 'naming/convention/intf/src/product'
URLS = (
    'https://defs.dev.algites.eu/api/jsondefs/eu/algites/lib/naming/convention/'
    'common-naming-conventions_1.jsondef.schema.json',
    'https://defs.dev.algites.eu/api/yamldefs/eu/algites/lib/naming/convention/'
    'common-naming-conventions_1.yamldef.schema.json',
    '{https://defs.dev.algites.eu/api/xmldefs/eu/algites/lib/naming/convention/'
    'common-naming-conventions_1.xsd}CommonNamingConventions',
)


def python_index():
    """Exercise the production index without importing unavailable bootstrap packages."""
    module_file = PY_INDEX / 'canonical_defs_codegen_cli.py'
    class_file = PY_INDEX / '_class_contracts.py'
    module_spec = importlib.util.spec_from_file_location('_test_read_class_contracts', class_file)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    tree = ast.parse(module_file.read_text(encoding='utf-8'))
    selected = next(item for item in tree.body if isinstance(item, ast.FunctionDef)
                    and item.name == '_existing_contracts')
    # Its only relative import is the production class reader already loaded above.
    selected.body = [item for item in selected.body if not isinstance(item, ast.ImportFrom)]
    namespace = {'Path': Path, 'ast': ast, 're': re, 'os': os,
                 'read_class_contracts': module.read_class_contracts}
    exec(compile(ast.Module(body=[selected], type_ignores=[]), str(module_file), 'exec'), namespace)
    return namespace['_existing_contracts']


def test_unified_schema_identities_resolve_without_format_children():
    """All schema identities bind the current read-only contract, not extgen seeds."""
    assert ROOT.is_dir(), 'pub.lib.General must be a sibling of pub.tool.General'
    resolved = python_index()((ROOT,), frozenset(URLS))
    for identity in URLS:
        binding = resolved[identity]
        assert binding['java'] == 'eu.algites.lib.naming.convention.AIigCommonNamingConventions_1'
        assert binding['python_type'] == 'AIigCommonNamingConventions_1'
        assert binding['python_module'].endswith('.aiig_common_naming_conventions_1')


def test_unrelated_live_contracts_remain_ambiguous(tmp_path):
    """Do not hide genuine conflicts between independent current source trees."""
    package = 'eu/algites/example'
    contract = ('@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema('
                'schemaId = "urn:foo", schemaVersion = 7, '
                'schemaUrl = "https://defs.dev.algites.eu/api/jsondefs/ambiguous_1.jsondef.schema.json")\n')
    for name in ('A', 'B'):
        target = tmp_path / name / 'src/product/java.gen' / package / f'AIig{name}.java'
        target.parent.mkdir(parents=True)
        target.write_text('package eu.algites.example;\n' + contract +
                          f'public interface AIig{name} extends java.io.Serializable {{}}\n')
    with pytest.raises(ValueError, match='Ambiguous existing generated contract'):
        python_index()((tmp_path / 'A', tmp_path / 'B'),
                       frozenset({'https://defs.dev.algites.eu/api/jsondefs/ambiguous_1.jsondef.schema.json'}))


def test_java_index_unifies_three_formats(tmp_path):
    """The Java source/bytecode index observes exactly the same unified identity."""
    javac, java = shutil.which('javac'), shutil.which('java')
    if not javac or not java:
        pytest.skip('A JDK is required for this Java parity check')
    build = tmp_path / 'java-classes'
    build.mkdir()
    main = tmp_path / 'VerifyIndex.java'
    main.write_text('''import java.nio.file.Path;
import java.util.List;
import java.util.Set;
import eu.algites.tool.codegen.defs.impl.cli.AIcDefsCodegenExternalContractIndex;
public class VerifyIndex {
 public static void main(String[] values) throws Exception {
   var result = AIcDefsCodegenExternalContractIndex.resolve(
       List.of(Path.of(values[0])), Set.of(values[1], values[2], values[3]));
   for (int i = 1; i < values.length; i++) {
     var symbol = result.get(values[i]);
     if (symbol == null || !"eu.algites.lib.naming.convention.AIigCommonNamingConventions_1".equals(symbol.javaType())
          || !"AIigCommonNamingConventions_1".equals(symbol.pythonType()))
        throw new AssertionError(values[i] + " => " + symbol);
   }
 }
}''')
    inputs = [INDEX / name for name in (
        'AIcDefsCodegenCompiledContractReader.java',
        'AIcDefsCodegenExternalContractIndex.java')]
    subprocess.run([javac, '-d', str(build), *(str(file) for file in inputs), str(main)],
                   check=True, capture_output=True, text=True)
    subprocess.run([java, '-cp', str(build), 'VerifyIndex', str(ROOT), *URLS],
                   check=True, capture_output=True, text=True)


def test_compiled_unified_contract_exposes_all_independent_identities(tmp_path):
    """Compiled Java ABI inputs must advertise XML/JSON/YAML on one symbol."""
    javac, java = shutil.which('javac'), shutil.which('java')
    if not javac or not java:
        pytest.skip('A JDK is required for compiled contract parity')
    source = tmp_path / 'Synthetic.java'
    source.write_text('''
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
@Retention(RetentionPolicy.RUNTIME)
@interface AIaDataObjectJsonSchema {
    String schemaId(); int schemaVersion(); String schemaUrl();
}
@Retention(RetentionPolicy.RUNTIME)
@interface AIaDataObjectYamlSchema {
    String schemaId(); int schemaVersion(); String schemaUrl();
}
enum Kind { TYPE, ELEMENT }
@Retention(RetentionPolicy.RUNTIME)
@interface AIaDataObjectXmlSchema {
    Kind definitionKind(); String namespace(); String namespaceLocalName();
}
@AIaDataObjectJsonSchema(schemaId="urn:json:id", schemaVersion=2,
    schemaUrl="https://defs.dev.algites.eu/api/jsondefs/sample_2.jsondef.schema.json")
@AIaDataObjectYamlSchema(schemaId="urn:yaml:id", schemaVersion=18,
    schemaUrl="https://defs.dev.algites.eu/api/yamldefs/sample_18.yamldef.schema.json")
@AIaDataObjectXmlSchema(definitionKind=Kind.TYPE, namespace="urn:xml:other", namespaceLocalName="Sample")
interface Sample { String getName(); }
''')
    subprocess.run([javac, '-d', str(tmp_path), str(source)], check=True,
                   capture_output=True, text=True)
    bytecode = tmp_path / 'Sample.class'
    reader = PY_INDEX / '_class_contracts.py'
    spec = importlib.util.spec_from_file_location('_compiled_reader_parity', reader)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    identities = {identity for identity, name, _ in module.read_class_contracts(bytecode)}
    assert identities == {
        'https://defs.dev.algites.eu/api/jsondefs/sample_2.jsondef.schema.json',
        'https://defs.dev.algites.eu/api/yamldefs/sample_18.yamldef.schema.json',
        '{urn:xml:other}Sample',
    }
    runner = tmp_path / 'ReadCompiled.java'
    runner.write_text('''import java.nio.file.Path;
import eu.algites.tool.codegen.defs.impl.cli.AIcDefsCodegenCompiledContractReader;
public class ReadCompiled {
    public static void main(String[] args) throws Exception {
        var all = AIcDefsCodegenCompiledContractReader.readAll(Path.of(args[0]));
        for (var entry : all) System.out.println(entry.identity());
    }
}''')
    subprocess.run([javac, '-d', str(tmp_path),
                    str(INDEX / 'AIcDefsCodegenCompiledContractReader.java'),
                    str(runner)], check=True, capture_output=True, text=True)
    output = subprocess.run([java, '-cp', str(tmp_path), 'ReadCompiled', str(bytecode)],
                            check=True, capture_output=True, text=True).stdout
    assert set(output.strip().splitlines()) == identities
