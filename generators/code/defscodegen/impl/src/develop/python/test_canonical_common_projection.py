"""Regression coverage for mandatory shared Defs interfaces and XML parent indexing.

The tests use the public input/output naming catalogs and real XSD/JSONDEFS/
YAMLDEFS schemas; no generated source is manually edited.
"""
from __future__ import annotations

from collections import defaultdict
import json
import re
from pathlib import Path
import subprocess

import pytest

from test_canonical_native_cli import _manifest, LIB, TOOL
from eu.algites.tool.codegen.defs.impl.cli.canonical_defs_codegen_cli import (
    _coalesce_equivalent_enum_sources, _existing_contracts,
    _merge_common_contract, prepare,
)


def _common_manifests(tmp_path):
    """Select real naming-conventions schemas across the three formats."""
    paths = []
    for kind, extension in (
        ('jsondefs', 'jsondef.schema.json'),
        ('yamldefs', 'yamldef.schema.json'),
        ('xmldefs', 'xsd'),
    ):
        parent = tmp_path / kind
        manifest, _ = _manifest(parent)
        source = (LIB / 'naming/convention/intf/src/product' / kind
                  / 'eu/algites/lib/naming/convention'
                  / ('common-naming-conventions_1.' + extension))
        data = json.loads(manifest.read_text())
        data['repository_root'] = str(LIB)
        data['inputs'] = [{'kind': kind, 'path': source.relative_to(LIB).as_posix()}]
        data['package_name'] = 'eu.algites.lib.naming.convention'
        data['reference_roots'] = [str(LIB), str(TOOL)]
        data['versions'] = {}
        for language in ('java', 'python'):
            conventions = data['output_compositions'][language]
            # One common output naming role for all three schema dialects.
            # Per-format schema identities remain in annotations, not filenames.
            conventions['interface'] = f'algites-{language}-gen-intf-versioned_1'
            conventions['interface_file'] = f'algites-{language}-gen-intf-versioned-file_1'
        manifest.write_text(json.dumps(data))
        paths.append(manifest)
    return paths


def test_three_representations_share_one_common_contract_and_compile(tmp_path):
    """No last-writer-wins common projection; all representations still compile."""
    outputs = {}
    contexts = defaultdict(list)
    for manifest in _common_manifests(tmp_path):
        _, files, common = prepare(manifest, include_common_context=True)
        for path, definition in common.items():
            contexts[path].append(definition)
        for path, source in files.items():
            if path in common:
                continue
            if path in outputs:
                outputs[path] = _coalesce_equivalent_enum_sources(outputs[path], source, path)
            else:
                outputs[path] = source
    for path, definitions in contexts.items():
        assert path not in outputs
        outputs[path] = _merge_common_contract(path, definitions)
    java = {path: text for path, text in outputs.items() if path.endswith('.java')}
    python = {path: text for path, text in outputs.items() if path.endswith('.py')}
    # The named list-item and Content contracts add generated classes; the
    # invariant is Java/Python parity, not an obsolete snapshot file count.
    assert len(java) == len(python)
    # XML, JSON and YAML describe one nominal DataObject contract. Their
    # annotations are combined on that one contract; no x/j/y variants exist.
    assert len(java) >= 18
    assert len(java) < 78  # No duplicate technology-specific projections.
    root = 'intf/src/product/java.gen/eu/algites/lib/naming/convention/'
    common = java[root + 'AIigCommonNamingConventions_1.java']
    assert 'extends eu.algites.lib.data.dataobject.AIiDataObject' in common
    assert 'String getStandardConventionsFile()' in common
    assert 'getAdditionalProperties(' not in common  # Unconstrained map omitted.
    assert '@eu.algites.lib.data.dataobject.AIaDataObject(' in common
    assert '@eu.algites.lib.data.dataobject.AIaDataObjectField(' in common
    assert '@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(' in common
    assert '@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(' in common
    assert '@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(' in common
    assert 'dataFieldName = "IdentifierConventions"' in common
    assert 'KEY_ID__UNIQUE_IDENTIFIER_CONVENTION_NAMES' in common
    assert 'https://defs.dev.algites.eu/api/jsondefs/' in common
    assert 'https://defs.dev.algites.eu/api/yamldefs/' in common
    for prefix in ('x', 'j', 'y'):
        assert root + f'AIig_{prefix}CommonNamingConventions_1.java' not in java
        assert not any('/AIig_' + prefix in name for name in java)
    py_root = 'intf/src/product/python.gen/eu/algites/lib/naming/convention/'
    shared = python[py_root + 'aiig_common_naming_conventions_1.py']
    assert '__json_schema__' in shared and '__xml_schema__' in shared
    assert '__yaml_schema__' in shared
    assert '__xml_schema_fields__' in shared
    assert '__scoped_key_definitions__' in shared
    for prefix in ('x', 'j', 'y'):
        assert py_root + f'aiig__{prefix}_common_naming_conventions_1.py' not in python
    # All new annotation imports must refer to the relocated libraries; this
    # checks emitted Python sources, not just handwritten runtime imports.
    for path, source in python.items():
        if '__json_schema__ = AIaDataObjectJsonSchema(' in source:
            assert ('from eu.algites.lib.data.dataobject.jsondefs.aia_data_object_json_schema '
                    'import AIaDataObjectJsonSchema') in source, path
        if '__xml_schema__ = AIaDataObjectXmlSchema(' in source:
            assert ('from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_xml_schema '
                    'import AIaDataObjectXmlSchema') in source, path
        if '__xml_schema_fields__' in source and 'AIaDataObjectFieldXmlSchema(' in source:
            assert ('from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_field_xml_schema '
                    'import AIaDataObjectFieldXmlSchema') in source, path
    for path, source in outputs.items():
        if path.endswith('.py'):
            compile(source, path, 'exec')
    source_tree = tmp_path / 'generated'
    for path, text in java.items():
        output = source_tree / path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text)
    roots = [str(path) for repo in (LIB, TOOL) for path in repo.rglob('src/product/java')]
    roots += [str(path) for repo in (LIB, TOOL) for path in repo.rglob('src/product/java.gen')]
    roots += [str(path) for repo in (LIB, TOOL) for path in repo.rglob('src/product/java.extgen')]
    result = subprocess.run(['javac', '-d', str(tmp_path / 'classes'),
                             '-sourcepath', ':'.join(roots),
                             *map(str, source_tree.rglob('*.java'))],
                            text=True, capture_output=True)
    assert result.returncode == 0, result.stderr


def _xml_reference_files(tmp_path):
    """Materialize realistic Defs read-only interface headers, without old schemaId."""
    ns = 'https://defs.dev.algites.eu/api/xmldefs/eu/algites/lib/naming/convention/common-naming-conventions_1.xsd'
    pkg = 'eu/algites/lib/naming/convention'
    java = tmp_path / 'intf/src/product/java.gen' / pkg
    py = tmp_path / 'intf/src/product/python.gen' / pkg
    java.mkdir(parents=True)
    py.mkdir(parents=True)
    (java / 'AIigCommonNamingConventions_1.java').write_text(
        'package eu.algites.lib.naming.convention;\n'
        '@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema('
        'definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, '
        f'namespace = "{ns}", namespaceLocalName = "CommonNamingConventions")\n'
        '@eu.algites.lib.data.dataobject.AIaDataObject(description = "CommonNamingConventions")\n'
        'public interface AIigCommonNamingConventions_1 '
        'extends AIigCommonNamingConventions_1, '
        'eu.algites.lib.data.dataobject.xmldefs.AIiXmlDataObject {}\n')
    (py / 'aiig_common_naming_conventions_1.py').write_text(
        'from .aiig_common_naming_conventions_1 import AIigCommonNamingConventions_1\n'
        'from eu.algites.lib.data.dataobject.xmldefs.aii_xml_data_object import AIiXmlDataObject\n'
        'from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject\n'
        'from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_xml_schema import AIaDataObjectXmlSchema\n'
        'from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind\n'
        'class AIigCommonNamingConventions_1(AIigCommonNamingConventions_1, AIiXmlDataObject):\n'
        '    """Generated read-only XML contract."""\n'
        '    __data_object__ = AIcdDataObject(description="CommonNamingConventions")\n'
        '    __xml_schema__ = AIaDataObjectXmlSchema('
        'definition_kind=AInXmlObjectDefinitionKind.TYPE, '
        f'namespace={ns!r}, namespace_local_name="CommonNamingConventions")\n')
    return '{' + ns + '}CommonNamingConventions'


def test_external_xsd_contract_is_selected_without_generic_schema_id(tmp_path):
    """The XML type's own annotation, not AIaDataObject, supplies identity."""
    key = _xml_reference_files(tmp_path)
    selected = _existing_contracts((tmp_path,), frozenset({key}))
    assert selected[key]['java'].endswith('.AIigCommonNamingConventions_1')
    assert selected[key]['python_type'] == 'AIigCommonNamingConventions_1'
    assert selected[key]['python_module'].endswith('.aiig_common_naming_conventions_1')


def test_native_java_xml_contract_index_matches_python_index(tmp_path):
    """Compile the independent Java scanner and verify identical QName binding."""
    key = _xml_reference_files(tmp_path)
    path = tmp_path / 'IndexCheck.java'
    path.write_text('''import java.nio.file.Path;
import java.util.List;
import java.util.Set;
import eu.algites.tool.codegen.defs.impl.cli.AIcDefsCodegenExternalContractIndex;
public class IndexCheck {
    public static void main(String[] args) throws Exception {
        var result = AIcDefsCodegenExternalContractIndex.resolve(
            List.of(Path.of(args[0])), Set.of(args[1]));
        var contract = result.get(args[1]);
        if (contract == null || !contract.javaType().endsWith(".AIigCommonNamingConventions_1")
            || !contract.pythonType().equals("AIigCommonNamingConventions_1"))
            throw new IllegalStateException("XML parent index was not resolved: " + result);
    }
}
''')
    scanner = (TOOL / 'generators/code/defscodegen/cli/src/product/java/eu/algites/tool/'
               'codegen/defs/impl/cli/AIcDefsCodegenExternalContractIndex.java')
    cls = tmp_path / 'classes'
    subprocess.run(['javac', '-d', str(cls), str(scanner),
                    str(scanner.with_name('AIcDefsCodegenCompiledContractReader.java')),
                    str(path)], check=True)
    subprocess.run(['java', '-cp', str(cls), 'IndexCheck', str(tmp_path), key], check=True)


def test_emission_does_not_duplicate_unified_contracts(tmp_path):
    """Three source dialects coalesce to one semantic read contract per name."""
    outputs, contexts = {}, defaultdict(list)
    for manifest in _common_manifests(tmp_path):
        _, produced, common = prepare(manifest, include_common_context=True)
        for path, source in produced.items():
            if path not in common:
                previous = outputs.get(path)
                outputs[path] = (source if previous is None else
                                 _coalesce_equivalent_enum_sources(previous, source, path))
        for path, definition in common.items():
            contexts[path].append(definition)
    for path, definitions in contexts.items():
        assert path not in outputs
        outputs[path] = _merge_common_contract(path, definitions)
    for suffix in ('AIigCommonNamingConventions_1.java',
                   'aiig_common_naming_conventions_1.py'):
        matches = [name for name in outputs if name.endswith('/' + suffix)]
        assert len(matches) == 1, (suffix, matches)
    assert len(outputs) == len(set(outputs))
