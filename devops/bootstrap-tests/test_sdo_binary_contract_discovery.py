"""Regression for the XML namespace marker discovered in the Java SDO binary scan."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JAVA_GENERATED = ROOT / 'generators/code/defscodegen/intf/src/product/java.gen/eu/algites/tool/codegen/defs'
CLI = ROOT / 'generators/code/sdocodegen/cli/src/product/java/eu/algites/tool/codegen/sdo/impl/cli/AIcSdoCodegenCli.java'
SERVICE = ROOT / 'generators/code/sdocodegen/impl/src/product/java/eu/algites/tool/codegen/sdo/impl/standard/AIcSdoCodegenService.java'


def test_namespace_marker_is_not_a_dataobject_definition():
    marker = (JAVA_GENERATED / 'AIig_xnXmlDataObjectUrnEuAlgitesToolCodegenDefsInputProfile1.java').read_text()
    definition = (JAVA_GENERATED / 'AIig_xInputProfile_1.java').read_text()
    assert 'extends eu.algites.lib.data.dataobject.xmldefs.AIiXmlDataObjectNamespace' in marker
    assert '@eu.algites.lib.data.dataobject.AIaDataObject(' not in marker
    assert '@eu.algites.lib.data.dataobject.AIaDataObject(' in definition
    assert 'AIig_xnXmlDataObjectUrnEuAlgitesToolCodegenDefsInputProfile1' in definition


def test_binary_discovery_uses_same_contract_gate_as_sdo_service():
    cli = CLI.read_text()
    service = SERVICE.read_text()
    assert 'if (!AIcSdoCodegenService.isReadContract(locClass)) continue;' in cli
    assert 'public static boolean isReadContract(Class<?> aClass)' in service
    assert 'AIiXmlDataObjectNamespace.class.isAssignableFrom(aClass)' in service
    assert 'aClass.getDeclaredAnnotation(AIaDataObject.class) == null' in service
