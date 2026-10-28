"""Explicit fixture profiles for legacy Defs frontend/rendering tests.

These are test-only inputs. The production generator intentionally has no
preselected vendor naming catalogue or implicit source-structure convention.
"""
from pathlib import Path
from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import AIcNameConventionCatalog


def catalog(language: str):
    """Return explicit installed naming resources, independent of sibling checkouts."""
    return AIcNameConventionCatalog.load_many([
        f'resource:algites-{family}-name-conventions.yml'
        for family in (language, 'jsondef', 'yamldef', 'xmldef')])


def source_convention(kind):
    """Name the schema-file convention explicitly, independently of URL metadata."""
    value = kind.value if hasattr(kind, 'value') else str(kind)
    return f'algites-{value.lower()[:-1]}-schema-versioned_1'


def output_convention(language, category='data'):
    """Select one contract/enum/DTO output role for the fixture assertions."""
    suffix = {'data': 'gen-data-class', 'interface': 'gen-intf',
              'enum': 'gen-enum'}[category]
    return f'algites-{language}-{suffix}-versioned_1'


def rendering_catalog(source, language: str):
    """Bind all semantic rendering roles in an explicitly selected test profile."""
    from eu.algites.tool.codegen.defs.ain_defs_name_role import AInDefsNameRole as R
    from eu.algites.tool.codegen.defs.impl.standard.aic_selected_naming_catalog import (
        AIcSelectedNamingCatalog)
    codes = {
        R.DATA_TYPE: output_convention(language),
        R.DATA_TYPE_FILE_STEM: output_convention(language),
        R.ENUM_TYPE: output_convention(language, 'enum'),
        R.ENUM_TYPE_FILE_STEM: output_convention(language, 'enum'),
        R.INTERFACE_TYPE: output_convention(language, 'interface'),
        R.INTERFACE_TYPE_FILE_STEM: output_convention(language, 'interface'),
        R.XML_ELEMENT_INTERFACE_TYPE: f'algites-{language}-gen-xml-element-intf-versioned_1',
        R.XML_ELEMENT_INTERFACE_TYPE_FILE_STEM: f'algites-{language}-gen-xml-element-intf-versioned_1',
        R.XML_NAMESPACE_INTERFACE_TYPE: f'algites-{language}-gen-xml-namespace-intf_1',
        R.XML_NAMESPACE_INTERFACE_TYPE_FILE_STEM: f'algites-{language}-gen-xml-namespace-intf_1',
    }
    return AIcSelectedNamingCatalog(source, codes)


def configured_load(path, kind, profile, source_naming_profile=''):
    """Create a test load request with an explicitly selected source-file convention."""
    from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
    chosen = source_naming_profile or source_convention(kind)
    # This test fixture deliberately provides the missing source-family catalog.
    # Do not add equivalent fallback behavior to the production frontend.
    if chosen not in profile.names:
        profile = catalog('python')
    return AIcdDefinitionLoadRequest(path, kind, profile, chosen)


def configured_generation(definition, target, package_name, profile,
                          xml_type_qname=None, naming_convention='', contract_role=''):
    """Create a test generation request with all named roles selected explicitly.

    This lives only in test sources; production requests remain strict and do not
    infer a naming profile. Existing already-selected profiles are preserved.
    """
    from eu.algites.tool.codegen.defs.aicd_code_generation_request import AIcdCodeGenerationRequest
    from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
    from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
    lang = 'java' if target is AInCodeGenerationTarget.JAVA else 'python'
    base = profile.catalog if hasattr(profile, 'selected') else profile
    selected = profile if hasattr(profile, 'selected') else rendering_catalog(base, lang)
    category = ('enum' if definition.data_type.kind is AInDataTypeKind.ENUM else 'interface')
    role_name = naming_convention or output_convention(lang, category)
    return AIcdCodeGenerationRequest(definition, target, package_name, selected,
        xml_type_qname, role_name, contract_role)
