"""Regression tests for named XSD types and JSON/YAML ``$defs`` contracts."""
from pathlib import Path

import pytest

from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind
from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import AIcNameConventionCatalog
from eu.algites.tool.codegen.defs.aicd_data_type import AIcdDataType
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.aicd_key_definition import AIcdKeyDefinition
from eu.algites.tool.codegen.defs.aicd_property_definition import AIcdPropertyDefinition
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.impl.standard.aic_common_contract_projection import _common_type
from eu.algites.tool.codegen.defs.impl.standard.aic_declared_type_identity import canonical_type_identifier
from eu.algites.tool.codegen.defs.impl.standard.aic_json_defs_frontend import AIcJsonDefsFrontend
from eu.algites.tool.codegen.defs.impl.standard.aic_yaml_defs_frontend import AIcYamlDefsFrontend
from eu.algites.tool.codegen.defs.impl.standard.aic_xml_defs_frontend import AIcXmlDefsFrontend
from eu.algites.tool.codegen.defs.impl.standard._schema_loading import load_schema
from eu.algites.tool.codegen.defs.impl.standard.aic_json_schema_reader import AIcJsonSchemaReader


def _fixture():
    """Use checked-out configuration sources, never installed wheel defaults."""
    tool = next(path for path in Path(__file__).resolve().parents if path.name == 'pub.tool.General')
    lib = tool.parent / 'pub.lib.General'
    config = lib / 'naming/convention'
    standard = config / 'intf/src/product/config/eu/algites/lib/naming/convention/standard-conventions.yml'
    directory = config / 'profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode'
    catalogs = [standard] + [directory / f'algites-{kind}-name-conventions.yml'
                                  for kind in ('jsondef', 'yamldef', 'xmldef')]
    profile = AIcNameConventionCatalog.load_many(catalogs)
    definitions = config / 'intf/src/product'
    return profile, definitions


def test_named_definitions_share_local_names_but_keep_source_identity():
    """Document-qualified identities are preserved despite equivalent local API names."""
    catalog, base = _fixture()
    roots = []
    for kind, extension, source, frontend in (
            ('jsondefs', 'jsondef.schema.json', AInDefinitionSourceKind.JSONDEFS, AIcJsonDefsFrontend()),
            ('yamldefs', 'yamldef.schema.json', AInDefinitionSourceKind.YAMLDEFS, AIcYamlDefsFrontend()),
            ('xmldefs', 'xsd', AInDefinitionSourceKind.XMLDEFS, AIcXmlDefsFrontend())):
        request = AIcdDefinitionLoadRequest(
            base / kind / 'eu/algites/lib/naming/convention' / f'common-naming-conventions_1.{extension}',
            source, catalog, f'algites-{kind[:-1]}-schema-versioned_1')
        root = frontend.load(request)
        roots.append((request, root))
    shared = ('IdentifierConventions', 'VersionConventions', 'NameFragments', 'NameCompositions')
    for name in shared:
        types = [next(field.data_type for field in definition.data_type.properties
                      if field.source_name == name) for _, definition in roots]
        assert all(t.kind is AInDataTypeKind.REFERENCE for t in types)
        assert len({(t.reference.logical_name, t.reference.version) for t in types}) == 1
        assert len({t.reference.identity for t in types}) > 1
    assert canonical_type_identifier(catalog, roots[0][0].source_naming_profile,
                                     'IdentifierConventions') == 'identifier-conventions'
    with pytest.raises(ValueError, match='does not match'):
        canonical_type_identifier(catalog, roots[0][0].source_naming_profile,
                                  'identifier-conventions')


def test_named_maps_are_compatible_only_with_typed_key_and_value():
    """XML repeated keyed values and JSON/YAML maps share a checked structural model."""
    catalog, base = _fixture()
    xml_path = base / 'xmldefs/eu/algites/lib/naming/convention/common-naming-conventions_1.xsd'
    xml_request = AIcdDefinitionLoadRequest(xml_path, AInDefinitionSourceKind.XMLDEFS,
                                            catalog, 'algites-xmldef-schema-versioned_1')
    xml = AIcXmlDefsFrontend()
    parser = AIcJsonSchemaReader()
    for name in ('IdentifierConventions', 'VersionConventions', 'NameFragments', 'NameCompositions'):
        native = xml.load_named_type(xml_request, name).data_type
        representations = []
        for kind, extension, source in (
                ('jsondefs', 'jsondef.schema.json', AInDefinitionSourceKind.JSONDEFS),
                ('yamldefs', 'yamldef.schema.json', AInDefinitionSourceKind.YAMLDEFS)):
            path = base / kind / 'eu/algites/lib/naming/convention' / f'common-naming-conventions_1.{extension}'
            request = AIcdDefinitionLoadRequest(path, source, catalog,
                                                f'algites-{kind[:-1]}-schema-versioned_1')
            representations.append(parser._recursive_type(load_schema(path)['$defs'][name], request))
        merged = _common_type(representations + [native], name)
        assert merged.kind is AInDataTypeKind.OBJECT
        assert merged.keyed_value_type.kind is AInDataTypeKind.OBJECT
        assert len(merged.key_definitions) == 1
        assert merged.key_definitions[0].virtual
        if name.startswith('Name'):
            member = next(field for field in merged.keyed_value_type.properties
                          if field.source_name == 'Segments')
            assert member.data_type.kind is AInDataTypeKind.ARRAY


def test_key_compatibility_rejects_non_string_physical_key():
    """A physical XML xs:key cannot alias an arbitrary numeric or nullable field."""
    value = AIcdDataType(AInDataTypeKind.OBJECT,
        properties=(AIcdPropertyDefinition('name', AIcdDataType(AInDataTypeKind.INTEGER),
                    AInFieldPresenceKind.REQUIRED),))
    xml = AIcdDataType(AInDataTypeKind.OBJECT, keyed_value_type=value,
        key_definitions=(AIcdKeyDefinition('UniqueNames', ('name',)),))
    json = AIcdDataType(AInDataTypeKind.OBJECT, keyed_value_type=value,
        key_definitions=(AIcdKeyDefinition('json-property-name', ('_getKey',), virtual=True),))
    with pytest.raises(ValueError, match='Physical common key must be a required string'):
        _common_type((json, xml), 'Names')
