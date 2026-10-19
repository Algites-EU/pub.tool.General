"""Regressions for the final XML/JSON/YAML DataObject and SmartDataObject lineage."""
from __future__ import annotations
from eu.algites.tool.codegen.defs.aicd_data_type import AIcdDataType

import importlib
from pathlib import Path

import pytest
from eu.algites.lib.naming.convention.impl.algites.aic_algites_naming_profiles_1 import AIcAlgitesNamingProfiles_1
from eu.algites.tool.codegen.defs.aicd_canonical_definition import AIcdCanonicalDefinition
from eu.algites.tool.codegen.defs.aicd_code_generation_request import AIcdCodeGenerationRequest
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_interface_generator import AIcSchemaContractInterfaceGenerator
from eu.algites.tool.codegen.sdo.impl.standard.aic_sdo_codegen_service import AIcSdoCodegenService


@pytest.mark.parametrize('family,marker,concrete', [
    (AInDefinitionSourceKind.XMLDEFS, 'Xml', 'AIcXmlSmartDataObject'),
    (AInDefinitionSourceKind.JSONDEFS, 'Json', 'AIcJsonSmartDataObject'),
    (AInDefinitionSourceKind.YAMLDEFS, 'Yaml', 'AIcYamlSmartDataObject'),
])
def test_technology_contracts_and_sdo_implementations(tmp_path: Path, monkeypatch,
                                                           family, marker, concrete):
    """Generated read contracts and concrete SDO implementations preserve source family."""
    definition = AIcdCanonicalDefinition('urn:test:' + marker.lower(), 1, 'Sample', family, 'sample_1.schema', 'Simple marker fixture', AIcdDataType(AInDataTypeKind.OBJECT, properties=()), (), None)
    package = 'example.technology_' + marker.lower()
    python_profile = AIcAlgitesNamingProfiles_1.python_profile()
    java_profile = AIcAlgitesNamingProfiles_1.java_profile()
    generator = AIcSchemaContractInterfaceGenerator()
    java = generator.generate(AIcdCodeGenerationRequest(definition,
        AInCodeGenerationTarget.JAVA, package, java_profile)).source
    python = generator.generate(AIcdCodeGenerationRequest(definition,
        AInCodeGenerationTarget.PYTHON, package, python_profile))
    assert 'AIi' + marker + 'DataObject' in java
    assert 'AIi' + marker + 'DataObject' in python.source
    assert '@eu.algites.lib.data.dataobject.AIaDataObject(' in java
    root = tmp_path / 'python.gen'
    path = root / python.relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(python.source)
    monkeypatch.syspath_prepend(str(root))
    read_contract = getattr(importlib.import_module(package + '.' + path.stem), python.type_name)
    generated = AIcSdoCodegenService().generate(read_contract, 'd',
        naming=(python_profile, python_profile, python_profile))
    assert 'AIi' + marker + 'SmartDataObject' in generated.mutable_interface.source
    assert concrete in generated.implementation.source
    for part in (generated.mutable_interface, generated.implementation):
        target = root / part.relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(part.source)
    implementation_module = importlib.import_module(package + '.' +
        Path(generated.implementation.relative_path).stem)
    implementation = getattr(implementation_module, generated.implementation.type_name)
    assert issubclass(implementation, read_contract)
