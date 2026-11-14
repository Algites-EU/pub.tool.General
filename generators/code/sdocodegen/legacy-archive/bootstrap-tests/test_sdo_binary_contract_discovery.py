"""Regression for the XML namespace marker discovered in the Java SDO binary scan."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JAVA_GENERATED = ROOT / 'generators/code/defscodegen/intf/src/product/java.gen/eu/algites/tool/codegen/defs'
CLI = ROOT / 'generators/code/sdocodegen/cli/src/product/java/eu/algites/tool/codegen/sdo/old/impl/cli/AIcSdoCodegenCli.java'
SERVICE = ROOT / 'generators/code/sdocodegen/impl/src/product/java/eu/algites/tool/codegen/sdo/old/impl/standard/AIcSdoCodegenService.java'


def test_namespace_marker_is_not_a_dataobject_definition():
    """The XML marker is generated separately from an annotated read contract.

    The canonical model has no XML namespace marker of its own; generate a
    representative one rather than depending on a defunct bootstrap filename.
    """
    from types import SimpleNamespace
    from eu.algites.tool.codegen.defs.old.ain_code_generation_target import AInCodeGenerationTarget
    from eu.algites.tool.codegen.defs.old.impl.standard.aic_xml_namespace_contracts import (
        source, decorate)
    from eu.algites.lib.naming.convention.profile.algites.aic_algites_naming_profiles import AIcAlgitesNamingProfiles
    from eu.algites.tool.codegen.defs.old.ain_defs_name_role import AInDefsNameRole
    from eu.algites.tool.codegen.defs.old.impl.standard.aic_selected_naming_catalog import AIcSelectedNamingCatalog

    # Bootstrap test modules are independently runnable; they must not import
    # helpers from a different test directory via incidental PYTHONPATH order.
    role = 'algites-java-gen-xml-namespace-intf_1'
    selected = AIcSelectedNamingCatalog(AIcAlgitesNamingProfiles.java_profile(), {
        AInDefsNameRole.XML_NAMESPACE_INTERFACE_TYPE: role,
        AInDefsNameRole.XML_NAMESPACE_INTERFACE_TYPE_FILE_STEM: role,
    })
    request = SimpleNamespace(target=AInCodeGenerationTarget.JAVA,
        package_name='example.xml', naming_profile=selected)
    marker_name, _, marker = source(request, 'urn:eu:algites:example')
    assert 'extends eu.algites.lib.data.dataobject.xmldefs.AIiXmlDataObjectNamespace' in marker
    assert '@eu.algites.lib.data.dataobject.AIaDataObject(' not in marker
    generated = ('package example.xml;\n'
                 '@eu.algites.lib.data.dataobject.AIaDataObject(' 
                 'namingConvention="example")\n'
                 'public interface AIigExample extends '
                 'eu.algites.lib.data.dataobject.xmldefs.AIiXmlDataObject {\n}\n')
    result = decorate(generated, request, 'example.xml.' + marker_name, {}, False)
    assert '@eu.algites.lib.data.dataobject.AIaDataObject(' in result
    assert 'example.xml.' + marker_name in result
    # The actual generated canonical read contracts remain explicitly annotated.
    model = JAVA_GENERATED / 'model/AIigCanonicalModel_1.java'
    assert '@eu.algites.lib.data.dataobject.AIaDataObject(' in model.read_text()


def test_binary_discovery_uses_same_contract_gate_as_sdo_service():
    cli = CLI.read_text()
    service = SERVICE.read_text()
    assert 'if (!AIcSdoCodegenService.isReadContract(locClass)) continue;' in cli
    assert 'public static boolean isReadContract(Class<?> aClass)' in service
    assert 'AIiXmlDataObjectNamespace.class.isAssignableFrom(aClass)' in service
    assert 'aClass.getDeclaredAnnotation(AIaDataObject.class) == null' in service
