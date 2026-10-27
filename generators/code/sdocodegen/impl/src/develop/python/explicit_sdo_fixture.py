"""Generated Python SmartDataObject types are independent of schema formats."""
from pathlib import Path

from eu.algites.tool.codegen.sdo.impl.standard.aic_sdo_codegen_service import AIcSdoCodegenService


class AItcConfiguredSdoGenerator:
    """Test-only adapter that supplies an explicit legacy naming profile.

    Production generators deliberately reject missing profiles; old fixture
    contracts use the Algites names, so their tests must select that profile.
    """
    def __init__(self):
        self.service = AIcSdoCodegenService()

    @staticmethod
    def _naming(read_contract, configured=None):
        from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import (
            AIcNameConventionCatalog)
        from eu.algites.lib.data.dataobject.jsondefs.aii_json_data_object import AIiJsonDataObject
        from eu.algites.lib.data.dataobject.yamldefs.aii_yaml_data_object import AIiYamlDataObject
        from eu.algites.lib.data.dataobject.xmldefs.aii_xml_data_object import AIiXmlDataObject
        from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind
        if configured is None:
            common = Path(__file__).resolve().parents[8]
            library = common/'pub.lib.General/naming/convention/profile/algites/src/product/config/eu/algites/lib/naming/convention'
            tool = common/'pub.tool.General/generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention'
            catalog = AIcNameConventionCatalog.load_many([
                library/'algites-python-name-conventions.yml',
                tool/'algites-python-codegen-method-conventions.yml',
            ]).with_generated_method_profile('algites-python-codegen-standard_1')
        else:
            catalog = configured[-1]
        if issubclass(read_contract, AIiXmlDataObject):
            kind = getattr(getattr(read_contract, '__xml_data_object__', None), 'definition_kind', None)
            role = 'xmldefs_element' if kind is AInXmlObjectDefinitionKind.ELEMENT else 'xmldefs_type'
        elif issubclass(read_contract, AIiJsonDataObject):
            role = 'jsondefs'
        elif issubclass(read_contract, AIiYamlDataObject):
            role = 'yamldefs'
        else:
            role = 'common'
        versioned = bool(__import__('re').search(r'_[1-9][0-9]*$', read_contract.__name__))
        suffix = '-versioned_1' if versioned else '_1'
        input_kind = 'intf'
        source_name = read_contract.__name__
        if source_name.startswith('AIi') and not source_name.startswith('AIig'):
            input_kind = 'intf'  # Non-generated handwritten contracts use a distinct prefix.
            input_profile = 'algites-python-intf' + suffix
        else:
            input_profile = 'algites-python-gen-intf' + suffix
        source_annotation = getattr(read_contract, '__data_object__', None)
        specific = getattr(source_annotation, 'naming_convention', '')
        if specific:
            input_profile = specific
        mutable_profile = 'algites-python-gen-data-intf' + suffix
        concrete_profile = 'algites-python-gen-data-class' + suffix
        if configured is not None:
            selected_catalog = configured[0]
        else:
            selected_catalog = catalog
        input_roles = {role: input_profile}
        mutable_roles = {role: mutable_profile}
        concrete_roles = {role: concrete_profile}
        if role == 'xmldefs_element':
            # XML substitution heads and generated elements can inherit from
            # a named XML type, so both roles are required by this fixture.
            input_roles['xmldefs_type'] = 'algites-python-gen-intf' + suffix
            mutable_roles['xmldefs_type'] = mutable_profile
            concrete_roles['xmldefs_type'] = concrete_profile
        return (input_roles, mutable_roles, concrete_roles, selected_catalog)

    def generate(self, read_contract, marker='d', naming=None,
                 mutable_subpackage='', concrete_subpackage=''):
        return self.service.generate(read_contract, marker,
            self._naming(read_contract, naming), mutable_subpackage, concrete_subpackage)

    def generate_from_sources(self, source_root, contract_sources, marker='d',
                              dependency_classpath=(), naming=None, mutable_subpackage='',
                              concrete_subpackage='', enabled_roles=None):
        if naming is None:
            # The source API accepts one profile for a set of contracts, and
            # handwritten test source trees use the unversioned naming family.
            from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
            class AIigTest(AIiDataObject):
                pass
            naming = self._naming(AIigTest)
        return self.service.generate_from_sources(source_root, contract_sources,
            marker, naming, mutable_subpackage, concrete_subpackage, enabled_roles)


def configured_service():
    """Select fixture-specific naming without altering production defaults."""
    return AItcConfiguredSdoGenerator()




def explicit_generic_manifest(artifact='intf', languages=('python',)):
    """Test-only explicit schema and interface profiles for standalone Defs fixtures."""
    roles = {language: {
        'jsondefs': f'algites-{language}-gen-intf-versioned_1',
        'yamldefs': f'algites-{language}-gen-intf-versioned_1',
        'xmldefs_type': f'algites-{language}-gen-intf-versioned_1',
        'xmldefs_element': f'algites-{language}-gen-xml-element-intf-versioned_1',
        'xmldefs_namespace': f'algites-{language}-gen-xml-namespace-intf_1',
    } for language in languages}
    return {
        'artifact': artifact,
        'languages': list(languages),
        'schema_input_naming_conventions': {
            'jsondefs': 'algites-jsondef-schema-versioned_1',
            'yamldefs': 'algites-yamldef-schema-versioned_1',
            'xmldefs': 'algites-xmldef-schema-versioned_1'},
        'technology_outputs': {language: ('' if artifact == '.' else 'intf/') +
            f'src/product/{language}.gen' for language in languages},
        'technology_output_naming_conventions': roles,
        'naming_convention_files': [f'resource:{name}' for name in (
            'standard-conventions.yml', 'algites-java-name-conventions.yml',
            'algites-python-name-conventions.yml',
            'algites-jsondef-name-conventions.yml',
            'algites-yamldef-name-conventions.yml',
            'algites-xmldef-name-conventions.yml')]
    }
