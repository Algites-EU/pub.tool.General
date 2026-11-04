"""New Common/Defs/SDO naming profiles for the independent Defs/SDO pipelines.

The loader is intentionally independent of the legacy ``GeneratedDataObjectMethodNameConventions``
file format. The new domains are strictly typed, reference one common profile,
and preserve configurable helper segments, including tuple position numbering.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from types import MappingProxyType
from typing import Any, Mapping

COMMON_ROLES = frozenset(('standard_getter', 'standard_setter',
    'multi_mapped_list_key_synthetic_getter',
    'multi_mapped_list_value_synthetic_getter',
    'positional_item_synthetic_getter', 'const_container_interface'))
DEFS_ROLES = frozenset(('synthetic_property_type', 'synthetic_list_item_type',
    'synthetic_map_value_type', 'synthetic_positional_item_type',
    'synthetic_choice_variant_type', 'synthetic_group_type',
    'string_enum_item', 'non_string_enum_item'))
SDO_ROLES = frozenset(('raw_getter', 'raw_presence_checker_method', 'raw_unsetter'))
METADATA_ROLES = frozenset(('schema_source_schema_url', 'schema_source_schema_identifier',
    'schema_source_schema_version', 'data_source_schema_url',
    'data_source_schema_identifier', 'data_source_schema_version'))
ROOTS = {'common': 'CommonCodegenNameConventions',
         'defs': 'DefsCodegenNameConventions',
         'sdo': 'SdoCodegenNameConventions'}
DOMAINS = {'common': COMMON_ROLES, 'defs': DEFS_ROLES, 'sdo': SDO_ROLES}


def _camel_words(identifier: str) -> list[str]:
    """Split a source identifier into lexical tokens without discarding numbers."""
    text = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', identifier)
    text = re.sub(r'([A-Z])([A-Z][a-z])', r'\1 \2', text)
    return [word for word in re.split(r'[^A-Za-z0-9]+', text) if word]


def _format_identifier(value: str, convention: str) -> str:
    """Render one common lexical convention using the shared conversion semantics."""
    words = _camel_words(value)
    if not words:
        raise ValueError('Empty identifier after splitting')
    if 'upper_camel' in convention or 'upper-camel' in convention:
        return ''.join(word[0].upper() + word[1:].lower() for word in words)
    if 'lower_camel' in convention or 'lower-camel' in convention:
        return words[0].lower() + ''.join(w[0].upper() + w[1:].lower() for w in words[1:])
    if 'upper_snake' in convention:
        return '_'.join(w.upper() for w in words)
    if 'lower_snake' in convention:
        return '_'.join(w.lower() for w in words)
    if 'upper_kebab' in convention:
        return '-'.join(w.upper() for w in words)
    if 'lower_kebab' in convention:
        return '-'.join(w.lower() for w in words)
    if 'upper_flat' in convention:
        return ''.join(w.upper() for w in words)
    if 'lower_flat' in convention:
        return ''.join(w.lower() for w in words)
    raise ValueError(f'Unsupported lexical convention {convention!r}; use the naming catalog for custom conventions')


@dataclass(frozen=True)
class AIcdCodegenNamingProfile:
    """Resolved common profile and its optional Defs/SDO specializations."""
    common_profile_id: str
    common_roles: Mapping[str, str]
    defs_roles: Mapping[str, str]
    sdo_roles: Mapping[str, str]
    schema_metadata: Mapping[str, str]
    indexes_starting_from: int
    name_compositions: Mapping[str, Mapping[str, Any]]

    def positional_number(self, zero_based_index: int) -> int:
        """Convert a zero-based position to the configurable display suffix."""
        if not isinstance(zero_based_index, int) or isinstance(zero_based_index, bool) or zero_based_index < 0:
            raise ValueError('Position must be a non-negative integer')
        return zero_based_index + self.indexes_starting_from

    def method_name(self, role: str, identifier: str = '', **variables: str) -> str:
        """Render a supported role through its configured composition or literal getter.

        Roles whose compositions belong to a standard external catalog require
        that catalog to supply them; no implicit prefix or suffix is invented.
        """
        if role in COMMON_ROLES:
            target = self.common_roles.get(role)
        elif role in DEFS_ROLES:
            target = self.defs_roles.get(role)
        elif role in SDO_ROLES:
            target = self.sdo_roles.get(role)
        else:
            raise KeyError(f'Unknown naming role {role!r}')
        if not target:
            raise KeyError(f'Role {role!r} is not configured')
        if role in ('multi_mapped_list_key_synthetic_getter', 'multi_mapped_list_value_synthetic_getter'):
            return target
        composition = self.name_compositions.get(target)
        if composition is None:
            raise KeyError(f'Composition {target!r} is external or absent from the loaded profile documents')
        return self._render_segments(composition['Segments'], identifier, variables, frozenset((target,)))

    def _render_segments(self, segments: list[dict], identifier: str,
                         variables: Mapping[str, str], visited: frozenset[str]) -> str:
        rendered = []
        for segment in segments:
            if 'Ref' in segment:
                target = segment['Ref']
                if target in visited:
                    raise ValueError(f'Cyclic naming composition reference: {target}')
                composition = self.name_compositions.get(target)
                if composition is None:
                    raise KeyError(f'Unknown referenced composition {target!r}')
                rendered.append(self._render_segments(composition['Segments'], identifier,
                                                      variables, visited | {target}))
                continue
            value = segment['NameFragmentsSegmentValue']
            kind = value['Kind']
            if kind == 'constant_string':
                rendered.append(value['Value'])
            elif kind == 'identifier':
                rendered.append(_format_identifier(identifier, value['Convention']))
            elif kind == 'variable':
                name = value['Name']
                text = str(variables[name])
                if re.fullmatch(value['Regexp'], text) is None:
                    raise ValueError(f'Variable {name!r} does not match its naming rule')
                rendered.append(text)
            elif kind == 'version':
                rendered.append(str(variables['version']))
            else:
                raise ValueError(f'Unknown naming segment kind {kind!r}')
        return ''.join(rendered)

    def composed_name(self, composition_id: str, identifier: str, **variables: str) -> str:
        """Format a catalog-selected type/file name using resolved compositions.

        Unlike a method naming role this accepts a named type, enum or file-stem
        composition explicitly selected by the caller. An absent composition is
        a configuration error, never an implicit naming convention.
        """
        composition = self.name_compositions.get(composition_id)
        if composition is None:
            raise KeyError(f'Unknown output naming composition {composition_id!r}')
        return self._render_segments(composition['Segments'], identifier, variables,
                                     frozenset((composition_id,)))

    def synthetic_type_name(self, role: str, owner_type: str, identifier: str,
                            zero_based_index: int | None = None) -> str:
        """Use configurable semantic segments and optional position to name a synthetic type."""
        if role not in DEFS_ROLES or not role.startswith('synthetic_'):
            raise ValueError('Expected a synthetic Defs role')
        variables = {'owner_type': owner_type}
        if zero_based_index is not None:
            variables['position'] = str(self.positional_number(zero_based_index))
        return self.method_name(role, identifier, **variables)


def resolve_codegen_naming_profiles(common_doc: Mapping, common_id: str,
                                    defs_doc: Mapping | None = None, defs_id: str | None = None,
                                    sdo_doc: Mapping | None = None, sdo_id: str | None = None
                                    ) -> AIcdCodegenNamingProfile:
    """Resolve named, typed configuration profiles and validate their cross-references.

    Validation is deliberately repeated at runtime for XMLDEFS and for callers that
    construct configuration dictionaries without first validating their JSON Schema.
    """
    documents = [('common', common_doc, common_id)]
    if defs_doc is not None:
        documents.append(('defs', defs_doc, defs_id))
    if sdo_doc is not None:
        documents.append(('sdo', sdo_doc, sdo_id))
    roles: dict[str, Mapping[str, str]] = {}
    metadata: Mapping[str, str] = {}
    compositions: dict[str, Mapping] = {}
    starting_from = 1
    for domain, doc, profile_id in documents:
        profiles = doc[ROOTS[domain]]['NameConventions']
        if not profile_id or profile_id not in profiles:
            raise ValueError(f'Missing {domain} naming profile {profile_id!r}')
        profile = profiles[profile_id]
        if domain != 'common' and profile.get('CommonNamingConvention') != common_id:
            raise ValueError(f'{domain} must reference existing common profile {common_id!r}')
        mapping = profile['StructureNaming']
        if not isinstance(mapping, dict) or set(mapping) - DOMAINS[domain]:
            raise ValueError(f'Unknown or foreign {domain} naming roles: {set(mapping) - DOMAINS[domain]}')
        if any(not isinstance(value, str) or not value for value in mapping.values()):
            raise ValueError(f'Empty {domain} naming composition identifier')
        if domain == 'common':
            if not {'standard_getter', 'standard_setter'} <= set(mapping):
                raise ValueError('Common getter and setter roles are required')
            source_meta = profile.get('SchemaMetadataNaming') or {}
            if set(source_meta) - METADATA_ROLES:
                raise ValueError('Unknown schema metadata role')
            for suffix in ('url', 'identifier', 'version'):
                if source_meta.get('data_source_schema_' + suffix) and not source_meta.get('schema_source_schema_' + suffix):
                    raise ValueError(f'Configured data_source_schema_{suffix} requires source metadata mapping')
            metadata = MappingProxyType(dict(source_meta))
            starting_from = profile.get('IndexesStartingFrom', 1)
            if isinstance(starting_from, bool) or not isinstance(starting_from, int) or starting_from < 0:
                raise ValueError('IndexesStartingFrom must be a non-negative integer')
        for name, composition in doc.get('NameCompositions', {}).items():
            if name in compositions and compositions[name] != composition:
                raise ValueError(f'Conflicting composition {name!r}')
            compositions[name] = composition
        roles[domain] = MappingProxyType(dict(mapping))
    return AIcdCodegenNamingProfile(common_id, roles['common'], roles.get('defs', MappingProxyType({})),
                                    roles.get('sdo', MappingProxyType({})), metadata,
                                    starting_from, MappingProxyType(compositions))


def with_external_sourcecode_conventions(
        profile: AIcdCodegenNamingProfile, source_document: Mapping[str, Any]
        ) -> AIcdCodegenNamingProfile:
    """Resolve selected source-code naming fragments from an external catalog.

    The Common/Defs/SDO profile identifies getter and setter compositions by name.
    Their definitions live in the shared source-code naming catalog, not in the
    codegen-specific profile. Importing that explicitly selected catalog gives
    every target a complete compositional naming context without hardcoded
    `get`/`set` prefixes or language-specific fallback paths.

    Historical `NameFragmentsSegmentReference` and the newer direct `Ref` shape
    are both resolved into the common `Ref` representation. Conflicting IDs are
    not silently overwritten. The original profile and source documents remain
    unchanged.
    """
    if not isinstance(profile, AIcdCodegenNamingProfile):
        raise TypeError('Expected an explicit resolved Common naming profile')
    if not isinstance(source_document, Mapping):
        raise TypeError('Source-code naming catalog must be a mapping')
    from dataclasses import replace
    compositions = dict(profile.name_compositions)
    for domain in ('NameFragments', 'NameCompositions'):
        group = source_document.get(domain, {})
        if not isinstance(group, Mapping):
            raise ValueError(f'Invalid source-code naming catalog {domain}')
        for identifier, definition in group.items():
            if not isinstance(definition, Mapping) or not isinstance(definition.get('Segments'), list):
                raise ValueError(f'Invalid source-code composition {identifier!r}')
            segments = []
            for segment in definition['Segments']:
                if not isinstance(segment, Mapping):
                    raise ValueError(f'Invalid source-code naming segment in {identifier!r}')
                if 'NameFragmentsSegmentReference' in segment:
                    reference = segment['NameFragmentsSegmentReference']
                    if not isinstance(reference, Mapping) or not isinstance(reference.get('Ref'), str):
                        raise ValueError(f'Invalid source-code fragment reference in {identifier!r}')
                    segments.append({'Ref': reference['Ref']})
                elif 'Ref' in segment:
                    segments.append({'Ref': segment['Ref']})
                elif 'NameFragmentsSegmentValue' in segment:
                    segments.append({'NameFragmentsSegmentValue': dict(segment['NameFragmentsSegmentValue'])})
                else:
                    raise ValueError(f'Unsupported source-code naming segment in {identifier!r}')
            normalized = {'Segments': segments}
            if identifier in compositions and compositions[identifier] != normalized:
                raise ValueError(f'Conflicting source-code composition {identifier!r}')
            compositions[identifier] = normalized
    return replace(profile, name_compositions=MappingProxyType(compositions))
