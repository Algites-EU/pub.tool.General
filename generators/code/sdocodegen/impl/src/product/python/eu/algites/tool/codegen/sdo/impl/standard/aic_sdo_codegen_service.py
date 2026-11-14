"""Generate SmartDataObject types from imported, annotated read-only contracts.

No schema readers or definition types are imported: the normalized read-only data-object contract is
both the input and the sole source of truth. Class inheritance is preserved.
"""
from __future__ import annotations

from eu.algites.tool.codegen.common.aix_codegen_validation_exception import AIxCodegenValidationException

import re
import os
import importlib
import ast
from functools import lru_cache
from pathlib import Path
import sys
from inspect import isclass
from dataclasses import dataclass
from typing import get_type_hints, get_args, get_origin, Union
from types import UnionType
from eu.algites.lib.common.list.aii_multi_mapped_list import AIiMultiMappedList
from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
from eu.algites.lib.data.dataobject.xmldefs.aii_xml_data_object import AIiXmlDataObject
from eu.algites.lib.data.dataobject.xmldefs.aii_xml_data_object_namespace import AIiXmlDataObjectNamespace
from eu.algites.lib.data.dataobject.jsondefs.aii_json_data_object import AIiJsonDataObject
from eu.algites.lib.data.dataobject.yamldefs.aii_yaml_data_object import AIiYamlDataObject
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from ._read_contract_fields import _data_object_fields, _declared_fields
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.lib.common.object.props.labels.aia_field_label import AIaFieldLabel
from eu.algites.tool.codegen.sdo.aicd_generated_sdo_source import AIcdGeneratedSdoSource
from eu.algites.tool.codegen.sdo.aicd_sdo_generation_result import AIcdSdoGenerationResult
from eu.algites.tool.codegen.sdo.aii_sdo_codegen_service import AIiSdoCodegenService
from eu.algites.lib.naming.convention.aii_name_convention_catalog import AIiNameConventionCatalog



def _default_setter_inheritance_policy() -> AInFieldSetterInheritancePolicy:
    """Native invocation fallback for unannotated handwritten contracts."""
    return AInFieldSetterInheritancePolicy(os.environ.get(
        'ALGITES_SDO_CODEGEN_SETTER_INHERITANCE_POLICY',
        'INHERIT_AS_GENERIC_PARAMETER'))


@dataclass(frozen=True)
class _EffectiveXmlField:
    """Joined semantic DataObject field and explicit inherited XML wire metadata.

    The schema-neutral field descriptor owns value restrictions. The XML
    projection owns only its QName mapping; these are separate declarations in
    generated contracts, and neither may be inferred from the other's name.
    """
    semantic_name: str
    descriptor: object
    wire: object | None


def _effective_xml_fields(contract: type, fields: dict[str, object]) -> dict[str, _EffectiveXmlField]:
    """Join XSD overlays with inherited DataObject fields before code emission.

    Follow the runtime metadata precedence (base-to-derived, modern overriding
    deprecated annotations) and detect orphaned, conflicting XML mappings.
    Contract field names, not Python getter spelling, identify the wire overlay.
    """
    mapping: dict[str, object] = {}
    for ancestor in reversed(contract.__mro__):
        legacy = ancestor.__dict__.get('__xml_data_object_fields__', {}) or {}
        modern = ancestor.__dict__.get('__xml_schema_fields__', {}) or {}
        if not isinstance(legacy, dict) or not isinstance(modern, dict):
            raise AIxCodegenValidationException(
                'Invalid XML field metadata on ' + ancestor.__module__ + '.' + ancestor.__name__,
                'Supply mappings from semantic or data field names to XML field descriptors.')
        for name in legacy.keys() & modern.keys():
            a, b = legacy[name], modern[name]
            if (a.namespace, a.namespace_local_name, a.value_kind) != (
                    b.namespace, b.namespace_local_name, b.value_kind):
                raise AIxCodegenValidationException(
                    'Conflicting XML field metadata for ' + str(name) + ' on ' + ancestor.__name__,
                    'Align modern and compatibility XML QName and value-kind declarations.')
        mapping.update(legacy)
        mapping.update(modern)
    joined = {}
    consumed = set()
    for semantic, descriptor in fields.items():
        alternatives = (semantic, descriptor.field_name)
        matched = [name for name in dict.fromkeys(alternatives) if name in mapping]
        if len(matched) > 1 and any(mapping[name] != mapping[matched[0]] for name in matched[1:]):
            raise AIxCodegenValidationException(
                'Ambiguous XML field projection for ' + semantic + ' on ' + contract.__name__,
                'Use one unambiguous semantic/data-name mapping for this inherited field.')
        consumed.update(matched)
        joined[semantic] = _EffectiveXmlField(
            semantic, descriptor, mapping[matched[0]] if matched else None)
    unknown = mapping.keys() - consumed
    if unknown:
        raise AIxCodegenValidationException(
            'XML field metadata has no inherited DataObject field on '
            + contract.__name__ + ': ' + ', '.join(sorted(map(str, unknown))),
            'Add a matching schema-neutral DataObject field or correct the XML field identity.')
    return joined


def _is_sdo_input(contract: type) -> bool:
    """Select common annotated DataObjects and their neutral descendants.

    XML/JSON/YAML marker descendants from historical split projections are
    not independently generated. Naming conventions only interpret accepted
    contracts; they never establish DataObject identity.

    Args:
        contract: Loaded candidate Python class.
    Returns:
        True for one eligible read-only contract.
    """
    if (not isclass(contract) or not issubclass(contract, AIiDataObject)
            or contract.__module__.startswith('eu.algites.lib.data.dataobject')):
        return False
    return (getattr(contract, '__data_object__', None) is not None
            and not issubclass(contract, (AIiXmlDataObject,
                                          AIiJsonDataObject, AIiYamlDataObject)))


class AIcSdoCodegenService(AIiSdoCodegenService):
    """Generate SDOs from annotated or handwritten read-only data-object contracts."""

    def generate_from_sources(self, source_root: Path, contracts: dict[Path, str],
                              marker: str = 'd', naming=None, mutable_subpackage: str = '', concrete_subpackage: str = '',
                              enabled_roles: set[str] | None = None) -> dict[Path, AIcdSdoGenerationResult]:
        """Import read-only contract modules from source roots and reuse the reflection-based generator.

        No separate packaging or Python build step is needed. Relative imports from
        sibling generated contracts work through the temporary import search entry.
        """
        root = Path(source_root).resolve(strict=True)
        if not root.is_dir():
            raise AIxCodegenValidationException(f'Not a DO contract source root: {root}', 'Check the configured source, output and artifact paths; ensure inputs exist, paths stay inside their allowed roots and required dependencies are present.')
        if not contracts:
            return {}
        prepared = {}
        for path, name in contracts.items():
            source = (root / path).resolve(strict=True)
            if not source.is_relative_to(root) or source.suffix != '.py' or not source.is_file():
                raise AIxCodegenValidationException(f'Invalid DO contract source: {path}', 'Check the configured source, output and artifact paths; ensure inputs exist, paths stay inside their allowed roots and required dependencies are present.')
            if not name.isidentifier():
                raise AIxCodegenValidationException(f'Invalid DO contract class name: {name}', 'Inspect the selected DataObject contract and SDO naming profile; correct the incompatible declaration, then regenerate the SDO sources.')
            prepared[source] = ('.'.join(source.relative_to(root).with_suffix('').parts), name)
        inserted = str(root) not in sys.path
        if inserted:
            sys.path.insert(0, str(root))
        # pkgutil.extend_path-based Algites packages capture their search paths
        # when first imported. A newly staged read-only contract must override
        # that stale snapshot (and any same-named generated module) for this
        # invocation only; restore all package paths afterwards.
        previous_package_paths = {}
        for module_name, _ in prepared.values():
            parts = module_name.split('.')
            for count in range(1, len(parts)):
                package_name = '.'.join(parts[:count])
                package = sys.modules.get(package_name)
                if package is None or not hasattr(package, '__path__'):
                    continue
                staged_directory = root.joinpath(*parts[:count])
                if not staged_directory.is_dir():
                    continue
                if package_name not in previous_package_paths:
                    previous_package_paths[package_name] = package.__path__
                original_paths = list(package.__path__)
                stage_path = str(staged_directory)
                package.__path__ = [stage_path] + [path for path in original_paths
                                                   if path != stage_path]
        try:
            importlib.invalidate_caches()
            # Reload precisely the requested source contracts, not possibly stale
            # installed/generated modules with the same qualified import names.
            for module_name, _ in prepared.values():
                sys.modules.pop(module_name, None)
            results = {}
            for source, (module_name, class_name) in prepared.items():
                module = importlib.import_module(module_name)
                loaded = Path(module.__file__).resolve() if getattr(module, '__file__', None) else None
                if loaded != source:
                    raise AIxCodegenValidationException(f'Imported DO contract is not the requested source: {source} (loaded {loaded})', 'Check the configured source, output and artifact paths; ensure inputs exist, paths stay inside their allowed roots and required dependencies are present.')
                contract = getattr(module, class_name)
                # The input schema dialect does not select an SDO naming role.
                # Every annotated read-only DataObject belongs to the one
                # format-neutral 'common' contract family.  XML/JSON/YAML
                # metadata are interpreted later by format binding providers.
                if (not _is_sdo_input(contract)
                        or (enabled_roles is not None and 'common' not in enabled_roles)):
                    continue
                results[source] = self.generate(contract, marker, naming, mutable_subpackage, concrete_subpackage)
            return results
        finally:
            for package_name, original_path in previous_package_paths.items():
                package = sys.modules.get(package_name)
                if package is not None:
                    package.__path__ = original_path
            if inserted:
                sys.path.remove(str(root))

    def generate(self, read_contract: type, marker: str = 'd', naming=None, mutable_subpackage: str = '', concrete_subpackage: str = '') -> AIcdSdoGenerationResult:
        """Generate native SDO types while preserving inherited field and label annotations."""
        if naming is None or len(naming) not in (3, 4):
            raise AIxCodegenValidationException('Missing explicit SDO input/mutable/implementation naming profiles', 'Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.')
        if not isclass(read_contract) or not issubclass(read_contract, AIiDataObject) or read_contract.__module__.startswith("eu.algites.lib.data.dataobject"):
            # Source-family marker types are infrastructure, not generated schema contracts.
            raise AIxCodegenValidationException('Read contract must extend AIiDataObject', 'Inspect the selected DataObject contract and SDO naming profile; correct the incompatible declaration, then regenerate the SDO sources.')
        if not _is_sdo_input(read_contract):
            raise AIxCodegenValidationException(
                'SDO input must declare or inherit schema-neutral __data_object__ '
                'without being a technology-specific projection: '
                + read_contract.__module__ + '.' + read_contract.__name__,
                'Pass an annotated read-only DataObject or its neutral descendant; '
                'not an XML/JSON/YAML projection or compiler ABI seed.')
        if not re.fullmatch(r'[a-z][a-z0-9]*', marker):
            raise AIxCodegenValidationException(f'Invalid mutable implementation marker: {marker!r}', 'Inspect the selected DataObject contract and SDO naming profile; correct the incompatible declaration, then regenerate the SDO sources.')
        if '.' not in read_contract.__module__:
            raise AIxCodegenValidationException('Read contract must live in an importable package', 'Check the configured source, output and artifact paths; ensure inputs exist, paths stay inside their allowed roots and required dependencies are present.')
        def role_for_identity(contract):
            """Contract naming is independent of its original source schema."""
            return 'common'

        def resolve_identity(owner, getter_name):
            name_catalog = naming[3] if len(naming) == 4 else naming[0]
            role = role_for_identity(owner)
            roles = naming[0]
            role_profile = roles.get(role) if isinstance(roles, dict) else None
            source_metadata = owner.__dict__.get('__data_object__')
            profile = role_profile
            if not profile:
                raise AIxCodegenValidationException('Missing source getter naming convention for ' + owner.__name__, 'Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.')
            parsed = name_catalog.parse(profile, 'getter_method_name', getter_name)
            identifier = parsed.get('identifier')
            if not identifier:
                raise AIxCodegenValidationException('Getter naming convention lacks an identifier: ' + getter_name, 'Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.')
            return name_catalog.convert_identifier(identifier,
                name_catalog.identifier_convention(profile, 'getter_method_name'), 'upper_camel_case_1')

        all_fields = _data_object_fields(read_contract, resolve_identity)
        owned_identifiers = {resolve_identity(read_contract, field.getter_name)
                             for field in _declared_fields(read_contract, resolve_identity)}
        fields = tuple(field for key, field in all_fields.items() if key in owned_identifiers)
        parents = [c for c in read_contract.__bases__ if not c.__module__.startswith('eu.algites.lib.data.dataobject')
                   and issubclass(c, AIiDataObject)
                   and not (issubclass(c, AIiXmlDataObjectNamespace)
                            and '__data_object__' not in c.__dict__)]
        parent = parents[0] if len(parents) == 1 else None
        # Concrete implementations derive from the technology runtime base,
        # never from a parent's concrete class. They must therefore implement
        # every inherited semantic field, including format-only projections.
        fields = tuple(all_fields.values())
        def role_for(contract):
            """One naming convention per read/mutable/implementation role."""
            return 'common'

        def selected(contract, index):
            role = role_for(contract)
            if naming is None:
                return None
            profiles = naming[index]
            if isinstance(profiles, dict):
                result = profiles.get(role)
                if not result:
                    raise AIxCodegenValidationException(f'No configured SDO naming convention for {role}/{index}', 'Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.')
                return result
            raise AIxCodegenValidationException(f'SDO naming profile for role {role}/{index} must be explicitly selected', 'Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.')

        def catalog() -> AIiNameConventionCatalog | None:
            """Return the naming catalog through its public contract."""
            chosen = naming[3] if naming is not None and len(naming) == 4 else None
            if chosen is not None and not isinstance(chosen, AIiNameConventionCatalog):
                raise TypeError('SDO naming catalog must implement AIiNameConventionCatalog')
            return chosen

        def accessor_profile(contract, index):
            """Require configured naming catalogs and roles for every generated accessor."""
            if naming is None:
                raise AIxCodegenValidationException('Missing required SDO generator naming profile', 'Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.')
            return (catalog() or naming[index]), selected(contract, index)

        def semantic_identifier(name):
            """Use the canonical ID already resolved through the input getter catalog."""
            return name, 'upper_camel_case_1'

        def accessor_name(contract, field, structure, index):
            profile_catalog, profile_name = accessor_profile(contract, index)
            identifier, source_convention = semantic_identifier(field.name)
            return profile_catalog.format(profile_name, structure,
                                          {'identifier': identifier}, source_convention)

        def names_for(contract):
            input_catalog = catalog() or naming[0]
            source = getattr(contract, '__data_object__', None)
            source_profile = selected(contract, 0)
            values = input_catalog.parse(source_profile, 'type_name', contract.__name__)
            return (input_catalog.format(selected(contract, 1), 'type_name', values,
                                          input_catalog.identifier_convention(source_profile, 'type_name')),
                    input_catalog.format(selected(contract, 2), 'type_name', values,
                                          input_catalog.identifier_convention(source_profile, 'type_name')))

        def stem_for(type_name, is_mutable, contract=None):
            target = contract or read_contract
            profile = selected(target, 1 if is_mutable else 2)
            all_catalog = catalog() or naming[1 if is_mutable else 2]
            values = all_catalog.parse(profile, 'type_name', type_name)
            return all_catalog.format(profile, 'file_name_stem', values,
                                      all_catalog.identifier_convention(profile, 'type_name'))

        def extension_for(is_mutable):
            profile = selected(read_contract, 1 if is_mutable else 2)
            all_catalog = catalog() or naming[1 if is_mutable else 2]
            return all_catalog.format(profile, 'file_name_suffix', {})

        mutable_name, concrete_name = names_for(read_contract)
        input_role = selected(read_contract, 0)
        mutable_role = selected(read_contract, 1)
        concrete_role = selected(read_contract, 2)
        # SDO implementations are independent of their original Defs technology.
        # Schema-specific annotations remain on the read-only getter contracts.
        technology = None
        mutable_technology = 'AIiSmartDataObject'
        concrete_technology = 'AIcSmartDataObject'
        # The selected YAML profiles also own names of generated method parameters.
        parameter_catalog, parameter_profile = accessor_profile(read_contract, 1)
        parameter_name = parameter_catalog.format(parameter_profile, 'method_parameter_name',
                                                  {'identifier': 'value'}, 'lower_snake_case_1')
        if naming is not None and not (catalog() or naming[2]).matches(
                concrete_role, 'method_parameter_name', parameter_name):
            raise AIxCodegenValidationException('SDO parameter name does not match the implementation naming profile', 'Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.')
        package = read_contract.__module__.rsplit('.', 1)[0]
        def subpackage(base, value):
            if not value:
                return base
            if not all(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', part) for part in value.split('.')):
                raise AIxCodegenValidationException(f'Invalid generated subpackage: {value!r}', 'Rename the indicated type, method or field to match the selected naming convention and update every reference to the renamed declaration.')
            return base + '.' + value

        mutable_package = subpackage(package, mutable_subpackage)
        concrete_package = subpackage(package, concrete_subpackage)
        mutable_prefix = mutable_package.replace('.', '/') + '/'
        concrete_prefix = concrete_package.replace('.', '/') + '/'
        contract_import = f'from {read_contract.__module__} import {read_contract.__name__}'
        mutable_lines = [f'"""Generated mutable contract for {read_contract.__name__}."""',
            'from __future__ import annotations',
            'from abc import abstractmethod',
            contract_import,
            'from eu.algites.lib.data.smartdataobject.aii_smart_data_object import AIiSmartDataObject']
        concrete_lines = [f'"""Generated SmartDataObject implementation for {read_contract.__name__}."""',
            'from __future__ import annotations',
            f'from {mutable_package}.{stem_for(mutable_name, True)} import {mutable_name}',
            'from eu.algites.lib.data.smartdataobject.impl.common.aic_smart_data_object import AIcSmartDataObject',
            'from eu.algites.lib.data.smartdataobject.impl.common.aia_smart_data_object_implementation_binding import AIaSmartDataObjectImplementationBinding',
            f'from {read_contract.__module__} import {read_contract.__name__}']
        def policy_for(field, owner):
            explicit = field.setter_inheritance_policy
            if explicit is not AInFieldSetterInheritancePolicy.DEFAULT:
                return explicit
            annotation = getattr(owner, '__data_object__', None)
            contract_policy = (annotation.setter_inheritance_policy
                               if annotation is not None else AInFieldSetterInheritancePolicy.DEFAULT)
            return (contract_policy if contract_policy is not AInFieldSetterInheritancePolicy.DEFAULT
                    else _default_setter_inheritance_policy())

        generic_fields = {}
        type_variables = {}
        for field in all_fields.values():
            getter = field.getter_name or accessor_name(read_contract, field, 'getter_method_name', 0)
            nested = _nested_contract(read_contract, getter, field.name)
            if nested is not None and policy_for(field, read_contract) is AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER:
                type_variables[field.name] = 'T' + field.name
                generic_fields[field.name] = nested
        # Any parent generic parameter must survive through this mutable descendant;
        # concrete implementations cannot extend an already-specialized parent.
        parent_parameter_names = {}
        for ancestor in parents:
            inherited_names = []
            for base in reversed(ancestor.__mro__):
                for field in _data_object_fields(base, resolve_identity).values():
                    getter = field.getter_name or accessor_name(ancestor, field, 'getter_method_name', 0)
                    if (_nested_contract(ancestor, getter, field.name) is not None
                            and policy_for(field, ancestor) is AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER):
                        if field.name not in inherited_names:
                            inherited_names.append(field.name)
            parent_parameter_names[ancestor] = inherited_names
            for name in inherited_names:
                current = all_fields[name]
                if current.setter_inheritance_policy is AInFieldSetterInheritancePolicy.INHERIT_AS_FIXED_PARAMETER:
                    raise AIxCodegenValidationException('An inherited generic setter cannot become fixed: ' + name, 'Check the inherited type and its parent contract. Preserve required setter parameter types, method signatures and valid inheritance relations.')
                if name not in type_variables:
                    getter = current.getter_name or accessor_name(read_contract, current, 'getter_method_name', 0)
                    nested = _nested_contract(read_contract, getter, name)
                    if nested is None:
                        raise AIxCodegenValidationException('An inherited generic setter cannot lose its value type: ' + name, 'Check the inherited type and its parent contract. Preserve required setter parameter types, method signatures and valid inheritance relations.')
                    type_variables[name] = 'T' + name
                    generic_fields[name] = nested
        generic_arguments = ', '.join(type_variables.values())
        generic_imports = ['from typing import TypeVar, Generic'] if type_variables else []
        typevar_rows = [f'{var} = TypeVar({var!r}, bound={names_for(generic_fields[name][0])[0]!r})'
                        for name, var in type_variables.items()]
        parent_mutable_annotations = {}
        for ancestor in parents:
            entries = parent_parameter_names[ancestor]
            parent_mutable_annotations[ancestor] = ('' if not entries else '['
                 + ', '.join(type_variables[name] for name in entries) + ']')

        if len(parents) > 1:
            mutable_bases = read_contract.__name__ + ', ' + ', '.join(names_for(p)[0] + parent_mutable_annotations[p] for p in parents) + ', ' + mutable_technology
            concrete_base = concrete_technology
            for inherited in parents:
                parent_mut, _ = names_for(inherited)
                parent_pkg = inherited.__module__.rsplit('.', 1)[0]
                mutable_lines.append(f'from {subpackage(parent_pkg, mutable_subpackage)}.{stem_for(parent_mut, True, inherited if len(parents)>1 else parent)} import {parent_mut}')
        elif parent is not None:
            parent_mut, parent_impl = names_for(parent)
            parent_pkg = parent.__module__.rsplit('.', 1)[0]
            mutable_lines.append(f'from {subpackage(parent_pkg, mutable_subpackage)}.{stem_for(parent_mut, True, inherited if len(parents)>1 else parent)} import {parent_mut}')
            concrete_lines.append(f'from {subpackage(parent_pkg, concrete_subpackage)}.{stem_for(parent_impl, False, parent)} import {parent_impl}')
            mutable_bases = f'{read_contract.__name__}, {parent_mut}{parent_mutable_annotations[parent]}, {mutable_technology}'
            # The parent SDO already extends the shared common runtime.
            # Generic setter inheritance requires a direct shared runtime base.
            concrete_base = (concrete_technology if parent_parameter_names[parent]
                             else parent_impl)
            if parent_parameter_names[parent]:
                fields = tuple(all_fields.values())
        else:
            mutable_bases = f'{read_contract.__name__}, {mutable_technology}'
            concrete_base = concrete_technology
        for ancestor in parents:
            for base in reversed(ancestor.__mro__):
                for field in _data_object_fields(base, resolve_identity).values():
                    if policy_for(field, ancestor) is AInFieldSetterInheritancePolicy.INHERIT_AS_FIXED_PARAMETER:
                        getter = field.getter_name or accessor_name(ancestor, field, 'getter_method_name', 0)
                        ancestor_nested = _nested_contract(ancestor, getter, field.name)
                        current = all_fields.get(field.name)
                        if ancestor_nested is not None and current is not None:
                            child_getter = current.getter_name or accessor_name(read_contract, current, 'getter_method_name', 0)
                            child_nested = _nested_contract(read_contract, child_getter, current.name)
                            if child_nested is None or child_nested[0] is not ancestor_nested[0]:
                                raise AIxCodegenValidationException('Cannot refine a fixed inherited setter parameter: ' + field.name, 'Verify that the referenced type, schema or artifact exists, is included in explicit inputs, and uses the expected namespace/version. Check import and classpath configuration.')
        if type_variables:
            mutable_bases += ', Generic[' + generic_arguments + ']'
            mutable_lines[2:2] = generic_imports
            mutable_lines.extend([''] + typevar_rows)
        import re as _re
        inherited_definition = getattr(read_contract, '__data_object__', None)
        inherited_format = (read_contract.__dict__.get('__json_schema__')
                            or read_contract.__dict__.get('__json_data_object__')
                            or read_contract.__dict__.get('__yaml_data_object__'))
        schema_id = getattr(inherited_format, 'schema_id', '') if inherited_format else ''
        schema_version = getattr(inherited_format, 'schema_version', -1) if inherited_format else -1
        input_catalog = catalog() or naming[0]
        selected_source_profile = input_role
        details = input_catalog.parse(selected_source_profile, 'type_name',
                                      read_contract.__name__)
        if not schema_id:
            identifier = details.get('identifier')
            if not identifier:
                raise AIxCodegenValidationException('Input naming convention does not identify the contract: '
                                 + selected_source_profile, 'Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.')
            lexical = input_catalog.identifier_convention(selected_source_profile,
                                                          'type_name')
            logical = input_catalog.convert_identifier(identifier, lexical, 'lower_kebab_case_1')
            schema_id = read_contract.__module__.rsplit('.', 1)[0] + '.' + logical
        if schema_version < 0:
            version = details.get('version')
            if not version or not str(version).isdigit() or int(version) <= 0:
                raise AIxCodegenValidationException('SchemaVersion requires explicit metadata or a versioned input naming profile', 'Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.')
            schema_version = int(version)
        inherited = inherited_definition or AIcdDataObject()
        # Only source-declared schema metadata is copied into the mutable SDO
        # contract. Generated types still retain their independent canonical
        # identity for naming, even when a source member was disabled.
        annotation = ('AIcdDataObject('
            + f'title={inherited.title!r}, description={inherited.description!r}, '
            + f'setter_inheritance_policy=AInFieldSetterInheritancePolicy.{(inherited.setter_inheritance_policy if inherited.setter_inheritance_policy is not AInFieldSetterInheritancePolicy.DEFAULT else _default_setter_inheritance_policy()).name})')
        mutable_lines.insert(4, 'from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject')
        mutable_lines.insert(5, 'from eu.algites.lib.common.object.props.labels.aia_field_label import AIaFieldLabel')
        mutable_lines.insert(6, 'from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy')
        labels = {}
        for field in fields:
            getter = field.getter_name or accessor_name(read_contract, field, 'getter_method_name', 0)
            method = getattr(read_contract, getter, None)
            explicit = getattr(method, '__field_label__', None)
            if explicit is None:
                for base in read_contract.__mro__:
                    explicit = base.__dict__.get('__field_labels__', {}).get(field.name)
                    if explicit is not None: break
            if explicit is not None:
                # Preserve the entire original annotation (including resolver and rendering axes)
                # on the inherited read contract instead of flattening it into partial metadata.
                continue
            else:
                value = _default_field_title(field.name)
                labels[field.name] = AIaFieldLabel(label=value)
        def encode_label(label):
            entries = ', '.join('AIaFieldLabel.Entry(' + ', '.join(f'{a}={getattr(entry, a)!r}' for a in ('label','roleCode')) + ')'
                for entry in label.labels)
            tuple_text = '(' + entries + (',' if len(label.labels) == 1 else '') + ')'
            return f'AIaFieldLabel(label={label.label!r}, roleCode={label.roleCode!r}, labels={tuple_text})'
        mutable_lines.extend(['', '', f'class {mutable_name}({mutable_bases}):',
                              f'    __data_object__ = {annotation}', 
                              '    """Presence-aware setters, raw getters and unsetters."""'])
        # JSON and YAML bindings are independent: a contract can originate from
        # both schema representations. Preserve both format-specific descriptors,
        # never flattening their identity into the neutral AIcdDataObject.
        concrete_format_annotations = []
        # The modern JSON Schema descriptor is authoritative for the common
        # contract. It must be emitted once, never reconstructed from a YAML
        # or JSON compatibility annotation (whose identities may differ).
        modern_metadata = read_contract.__dict__.get('__json_schema__')
        if modern_metadata is not None:
            modern_import = ('from eu.algites.lib.data.dataobject.jsonschema.aia_data_object_json_schema '
                             'import AIaDataObjectJsonSchema')
            mutable_lines.insert(4, modern_import)
            concrete_lines.insert(2, modern_import)
            modern_values = ', '.join(f'{key}={getattr(modern_metadata, key)!r}' for key in (
                'schema_id', 'schema_version', 'schema_url', 'data_source_schema_url_field',
                'data_source_schema_identifier_field', 'data_source_schema_version_field'))
            schema = f'    __json_schema__ = AIaDataObjectJsonSchema({modern_values})'
            mutable_lines.append(schema)
            concrete_format_annotations.append(schema)
        # Compatibility descriptors are kept format-local during migration.
        # They are NOT used as authoritative metadata and are never compared
        # to one another or to the modern descriptor.
        for format_kind in ('json', 'yaml'):
            format_metadata = read_contract.__dict__.get(f'__{format_kind}_data_object__')
            if format_metadata is None:
                continue
            format_type = 'Json' if format_kind == 'json' else 'Yaml'
            import_line = (f'from eu.algites.lib.data.dataobject.{format_kind}defs.'
                           f'aia_{format_kind}_data_object import AIa{format_type}DataObject')
            mutable_lines.insert(4, import_line)
            concrete_lines.insert(2, import_line)
            format_values = ', '.join(f'{key}={getattr(format_metadata, key)!r}' for key in (
                'schema_id', 'schema_version', 'schema_url', 'data_source_schema_url_field',
                'data_source_schema_identifier_field', 'data_source_schema_version_field'))
            descriptor = f'    __{format_kind}_data_object__ = AIa{format_type}DataObject({format_values})'
            mutable_lines.append(descriptor)
            concrete_format_annotations.append(descriptor)
        xml_metadata = (read_contract.__dict__.get('__xml_schema__') or read_contract.__dict__.get('__xml_data_object__'))
        if xml_metadata is not None:
            mutable_lines.insert(4, 'from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object import AIaXmlDataObject')
            mutable_lines.insert(5, 'from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind')
            mutable_lines.append("    __xml_data_object__ = AIaXmlDataObject("
                + f'definition_kind=AInXmlObjectDefinitionKind.{xml_metadata.definition_kind.name}, '
                + f'namespace={xml_metadata.namespace!r}, '
                + f'namespace_local_name={xml_metadata.namespace_local_name!r})')
            mutable_lines.insert(4, 'from eu.algites.lib.data.dataobject.xmlschema.aia_data_object_xml_schema import AIaDataObjectXmlSchema')
            mutable_lines.append("    __xml_schema__ = AIaDataObjectXmlSchema("
                + f'definition_kind=AInXmlObjectDefinitionKind.{xml_metadata.definition_kind.name}, '
                + f'namespace={xml_metadata.namespace!r}, '
                + f'namespace_local_name={xml_metadata.namespace_local_name!r})')
        xml_fields = (read_contract.__dict__.get('__xml_schema_fields__')
                      or read_contract.__dict__.get('__xml_data_object_fields__'))
        if xml_fields:
            mutable_lines.insert(4, 'from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object_field import AIaXmlDataObjectField')
            mutable_lines.insert(5, 'from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind')
            mutable_lines.append('    __xml_data_object_fields__ = {')
            for name, metadata in xml_fields.items():
                mutable_lines.append(f'        {name!r}: AIaXmlDataObjectField(namespace={metadata.namespace!r}, '
                    f'namespace_local_name={metadata.namespace_local_name!r}, '
                    f'value_kind=AInXmlValueKind.{metadata.value_kind.name}),')
            mutable_lines.append('    }')
            mutable_lines.insert(4, 'from eu.algites.lib.data.dataobject.xmlschema.aia_data_object_field_xml_schema import AIaDataObjectFieldXmlSchema')
            mutable_lines.append('    __xml_schema_fields__ = {')
            for name, metadata in xml_fields.items():
                mutable_lines.append(f'        {name!r}: AIaDataObjectFieldXmlSchema(namespace={metadata.namespace!r}, '
                    f'namespace_local_name={metadata.namespace_local_name!r}, '
                    f'value_kind=AInXmlValueKind.{metadata.value_kind.name}),')
            mutable_lines.append('    }')
        if labels:
            # A new mapping would shadow the read contract's mapping.  Start with
            # its explicit annotations, then add defaults only for missing fields.
            # Getter decorators and custom resolvers remain on the read contract.
            mutable_lines.append(f"    __field_labels__ = {{**getattr({read_contract.__name__}, '__field_labels__', {{}}),")
            for field_name, label in labels.items():
                mutable_lines.append(f'        {field_name!r}: {encode_label(label)},')
            mutable_lines.append('    }')
        concrete_lines.insert(2, 'from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject')
        concrete_lines.insert(3, 'from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy')
        concrete_lines.extend(['', '',
                               f'@AIaSmartDataObjectImplementationBinding(readContracts=({read_contract.__name__},))',
                               f'class {concrete_name}({concrete_base}, {mutable_name}' + ('' if not type_variables else '[' + ', '.join(repr(names_for(generic_fields[key][0])[0]) for key in type_variables) + ']') + '):',
                               f'    __data_object__ = AIcdDataObject(setter_inheritance_policy=AInFieldSetterInheritancePolicy.{(inherited.setter_inheritance_policy if inherited.setter_inheritance_policy is not AInFieldSetterInheritancePolicy.DEFAULT else _default_setter_inheritance_policy()).name})',
                               '    """Generated implementation; inherited fields use parent behavior."""'])
        concrete_lines.extend(concrete_format_annotations)
        # A named schema type may be both a SmartDataObject and the owner of
        # an ordered indexed collection.  A SmartDataObject base has no list
        # storage: build a real AIcMultiMappedList and delegate every ABC method.
        mapped_contract = issubclass(read_contract, AIiMultiMappedList)
        method_catalog = catalog()
        synthetic_key_method = None
        synthetic_value_method = None
        if method_catalog is not None and method_catalog.generated_method_profile:
            composition = method_catalog.generated_method_reference(
                'multi_mapped_list_key_synthetic_getter')
            if composition is not None:
                # Synthetic getter role stores its literal identifier directly.
                # Unlike accessor method roles, this is not a composition ID.
                candidate = composition
                if not candidate.isidentifier():
                    raise AIxCodegenValidationException('Invalid synthetic key getter identifier: ' + repr(candidate), 'Rename the indicated type, method or field to match the selected naming convention and update every reference to the renamed declaration.')
                if callable(getattr(read_contract, candidate, None)):
                    if issubclass(read_contract, AIiXmlDataObject):
                        raise AIxCodegenValidationException('Virtual object-property key getter is not an XML field', 'Check the collection shape, entry type, key definition and key field paths. Use a complete, resolvable key or declare the intended virtual map property key explicitly.')
                    if candidate in all_fields:
                        raise AIxCodegenValidationException('Virtual parent property key cannot be a serialized field', 'Check the inherited type and its parent contract. Preserve required setter parameter types, method signatures and valid inheritance relations.')
                    synthetic_key_method = candidate
            value_getter = method_catalog.generated_method_reference(
                'multi_mapped_list_value_synthetic_getter')
            if value_getter is not None:
                if not value_getter.isidentifier():
                    raise AIxCodegenValidationException('Invalid synthetic value getter identifier: ' + repr(value_getter), 'Update the Common method naming catalog and regenerate the contracts.')
                method = getattr(read_contract, value_getter, None)
                if callable(method):
                    if issubclass(read_contract, AIiXmlDataObject):
                        raise AIxCodegenValidationException('Virtual map value getter is not an XML field', 'Use the matching source contract and Common naming profile.')
                    if value_getter in all_fields or getattr(method, '__data_object_field__', None) is not None:
                        raise AIxCodegenValidationException('Virtual map value getter cannot be a serialized field', 'Remove the field annotation from the synthetic getter.')
                    if synthetic_key_method is None:
                        raise AIxCodegenValidationException('Virtual map value getter requires a virtual key getter', 'Declare both synthetic map-entry getters in the read-only contract.')
                    synthetic_value_method = value_getter
        if mapped_contract or synthetic_key_method is not None:
            concrete_lines.extend(['',
                '    def __init__(self, aMapping=None, *, definitions=(), parent_property_key=None, parent_property_value=None):',
                '        """Initialize the SDO and its nonserialized collection/key identity.',
                '',
                '        Args:',
                '            aMapping: Optional typed virtual field graph.',
                '            definitions: Stable key definitions owned by this mapped collection.',
                '            parent_property_key: Actual property name of this JSON/YAML map entry.',
                '            parent_property_value: Typed value belonging to the map entry, not an embedded field.',
                '        """',
                '        super().__init__(aMapping)'])
            if mapped_contract:
                concrete_lines.insert(4,
                    'from eu.algites.lib.common.list.aic_multi_mapped_list import AIcMultiMappedList')
                concrete_lines.append('        self._mapped_entries = AIcMultiMappedList(definitions)')
            if synthetic_key_method is not None:
                concrete_lines.extend([
                    '        if parent_property_key is not None and (not isinstance(parent_property_key, str) or not parent_property_key):',
                    "            raise ValueError('Map property key must be nonempty text')",
                    '        self._parent_property_key = parent_property_key',
                    '',
                    f'    def {synthetic_key_method}(self) -> str:',
                    '        """Return the containing map property name, never a data field."""',
                    '        if self._parent_property_key is None:',
                    "            raise ValueError('Map entry was not constructed with its parent property key')",
                    '        return self._parent_property_key'])
            if synthetic_value_method is not None:
                # Constructor assignment is inserted before the key accessor, not inside it.
                constructor_end = next(i for i, line in enumerate(concrete_lines)
                                       if line == '        self._parent_property_key = parent_property_key')
                concrete_lines.insert(constructor_end + 1,
                    '        self._parent_property_value = parent_property_value')
                concrete_lines.extend([
                    '',
                    f'    def {synthetic_value_method}(self):',
                    "        '''Return the typed map value without introducing a serialized field.'''",
                    '        if self._parent_property_value is None:',
                    "            raise ValueError('Map entry was not constructed with its parent property value')",
                    '        return self._parent_property_value'])
            if mapped_contract:
                concrete_lines.extend(['',
                    '    def __len__(self):',
                    '        """Return the number of indexed elements."""',
                    '        return len(self._mapped_entries)',
                    '',
                    '    def __getitem__(self, index):',
                    '        """Return the element at an index."""',
                    '        return self._mapped_entries[index]',
                    '',
                    '    def __setitem__(self, index, value):',
                    '        """Replace an indexed value using atomic key validation."""',
                    '        self._mapped_entries[index] = value',
                    '',
                    '    def __delitem__(self, index):',
                    '        """Remove an indexed entry and refresh key maps."""',
                    '        del self._mapped_entries[index]',
                    '',
                    '    def insert(self, index, value):',
                    '        """Insert an entry, rejecting conflicting unique keys."""',
                    '        self._mapped_entries.insert(index, value)',
                    '',
                    '    def map_by_key_type(self, definition):',
                    '        """Return the cached live map for an exact registered definition."""',
                    '        return self._mapped_entries.map_by_key_type(definition)',
                    '',
                    '    def key_definition(self, identifier):',
                    '        """Look up the registered definition by schema index identity."""',
                    '        return self._mapped_entries.key_definition(identifier)',
                    '',
                    '    def copy_range(self, start, stop):',
                    '        """Return a detached indexed shallow copy of the given range."""',
                    '        return self._mapped_entries.copy_range(start, stop)',
                    '',
                    '    def sub_list(self, start, stop):',
                    '        """Return a tracked membership-backed subsequence."""',
                    '        return self._mapped_entries.sub_list(start, stop)'])
        mutable_imports = []
        concrete_imports = []
        xml_nested_imports = {}
        xml_repeated = set()
        # An XML specialization can inherit schema-neutral DataObject fields.
        # Only an explicitly XML-mapped field belongs in the XML parser's
        # nested-type/repeated-field tables. Collect mappings along the MRO so
        # genuine XML ancestors remain supported without inventing QNames for
        # neutral fields. Match Java SDO's @AIaDataObjectFieldXmlSchema rule.
        effective_xml = (_effective_xml_fields(read_contract, all_fields)
                         if technology == 'xmldefs' else {})
        if not fields:
            mutable_lines.append('    pass')
            concrete_lines.append('    pass')
        for descriptor in fields:
            name = descriptor.name
            getter = descriptor.getter_name or accessor_name(read_contract, descriptor, 'getter_method_name', 0)
            suffix = name[:1].upper() + name[1:]
            method_catalog = catalog() if naming is not None else None
            if method_catalog is not None and method_catalog.generated_method_profile:
                method_profile = method_catalog.generated_method_profile
                identifier, source_convention = semantic_identifier(name)
                def method_name(kind):
                    if method_catalog.generated_method_reference(kind) is None:
                        return None
                    return method_catalog.format(method_profile, kind,
                                                 {'identifier': identifier}, source_convention)
                raw_getter = method_name('raw_getter')
                presence_checker = method_name('raw_presence_checker_method')
                unsetter = method_name('raw_unsetter')
                empty_setter = method_name('raw_empty_setter') if descriptor.is_empty_allowed else None
                empty_checker = method_name('raw_empty_checker_method') if descriptor.is_empty_allowed else None
            else:
                raw_getter, presence_checker, unsetter = ('get_' + suffix,
                    'isPresent_' + suffix, 'unset_' + suffix)
                empty_setter = empty_checker = None
            if descriptor.is_empty_allowed and (empty_setter is None or empty_checker is None):
                raise AIxCodegenValidationException('Missing empty-state naming roles for ' + name,
                    'Configure raw_empty_setter and raw_empty_checker_method in the selected SDO naming profile.')
            active_methods = [item for item in (getter, raw_getter, presence_checker, unsetter,
                                                empty_setter, empty_checker)
                              if item is not None]
            if (len(set(active_methods)) != len(active_methods)
                    or not all(item.isidentifier() for item in active_methods)):
                raise AIxCodegenValidationException('Conflicting or invalid SDO method names for ' + name, 'Inspect the declarations named in the error, their source schemas, namespaces and naming profiles; remove the duplicate or make their canonical identities unambiguous.')
            # A setter is named independently from its read getter and from the raw SDO API.
            setter = accessor_name(read_contract, descriptor, 'setter_method_name', 1)
            if naming is not None and not (catalog() or naming[2]).matches(
                    concrete_role, 'setter_method_name', setter):
                raise AIxCodegenValidationException('SDO setter name does not match concrete naming profile: ' + setter, 'Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.')
            if not getter.isidentifier() or not suffix.isidentifier():
                raise AIxCodegenValidationException('Invalid field getter: ' + getter, 'Inspect the indicated schema declaration, its source metadata and field types. Correct the invalid name, requiredness, type or version at that source rather than editing generated files.')
            nested_details = _nested_contract(read_contract, getter, name)
            auxiliary_details = (_auxiliary_read_only_contract(read_contract, getter, name)
                                 if nested_details is None else None)
            keyed_collection = get_origin(_unwrap_optional(_field_annotation(read_contract, getter, name))[0]) is AIiMultiMappedList
            nested_type = ((('AIiMultiMappedList[' if keyed_collection else 'list[') + names_for(nested_details[0])[0] + ']' 
                if nested_details[2] else names_for(nested_details[0])[0])
                + (' | None' if nested_details[1] else '')) if nested_details else None
            if technology == 'xmldefs' and (effective_xml[name].wire is not None or descriptor.embedded):
                if (effective_xml[name].wire is not None and nested_details
                        and not issubclass(nested_details[0], AIiXmlDataObject)):
                    raise AIxCodegenValidationException(
                        'XML field references a non-XML DataObject: '
                        + read_contract.__module__ + '.' + read_contract.__name__ + '.' + getter
                        + ' -> ' + nested_details[0].__module__ + '.' + nested_details[0].__name__,
                        'The explicitly XML-mapped getter must reference an XML DataObject. '
                        'Review its XML Schema declaration and XML field mapping.')
                if (nested_details and nested_details[2]) or _repeated_contract_field(read_contract, getter, name, descriptor):
                    xml_repeated.add(name)
                if nested_details and issubclass(nested_details[0], AIiXmlDataObject):
                    nested_concrete = names_for(nested_details[0])[1]
                    nested_package = nested_details[0].__module__.rsplit('.', 1)[0]
                    nested_concrete_module = subpackage(nested_package, concrete_subpackage) + '.' + stem_for(nested_concrete, False, nested_details[0])
                    xml_nested_imports[name] = nested_concrete_module + ':' + nested_concrete
            auxiliary_type = None
            if auxiliary_details is not None:
                aux_class, aux_nullable, aux_repeated = auxiliary_details
                auxiliary_type = ((('AIiMultiMappedList[' if keyed_collection else 'list[')
                                   + aux_class.__name__ + ']') if aux_repeated else aux_class.__name__)
                if aux_nullable:
                    auxiliary_type += ' | None'
                aux_import = f'from {aux_class.__module__} import {aux_class.__name__}'
                mutable_imports.append(aux_import)
                concrete_imports.append(aux_import)
                if keyed_collection:
                    collection_import = 'from eu.algites.lib.common.list.aii_multi_mapped_list import AIiMultiMappedList'
                    mutable_imports.append(collection_import)
                    concrete_imports.append(collection_import)
            typed_value = nested_type or auxiliary_type or 'object'
            variable = type_variables.get(name)
            interface_type = (((f'AIiMultiMappedList[{variable}]' if keyed_collection else f'list[{variable}]') if nested_details[2] else variable)
                              + (' | None' if nested_details[1] else '')) if variable else typed_value
            if nested_type is not None:
                nested_class = nested_details[0]
                nested_name = names_for(nested_class)[0]
                nested_package = nested_class.__module__.rsplit('.', 1)[0]
                nested_file = stem_for(nested_name, True, nested_class)
                if keyed_collection:
                    mutable_imports.append('from eu.algites.lib.common.list.aii_multi_mapped_list import AIiMultiMappedList')
                    concrete_imports.append('from eu.algites.lib.common.list.aii_multi_mapped_list import AIiMultiMappedList')
                mutable_imports.append(f'from {subpackage(nested_package, mutable_subpackage)}.{nested_file} import {nested_name}')
                concrete_imports.append(f'from {subpackage(nested_package, mutable_subpackage)}.{nested_file} import {nested_name}')
            named_mapped_collection = bool(nested_details and not nested_details[2]
                and issubclass(nested_details[0], AIiMultiMappedList))
            is_collection = (named_mapped_collection or keyed_collection
                or nested_details is not None and nested_details[2]
                or get_origin(_unwrap_optional(_field_annotation(read_contract, getter, name))[0])
                in (list, tuple, AIiMultiMappedList))
            if nested_type is not None or auxiliary_type is not None:
                mutable_lines.extend(['', '    @abstractmethod',
                    f'    def {getter}(self) -> {interface_type}: ...'])
            if not is_collection:
                mutable_lines.extend(['', '    @abstractmethod',
                    f'    def {setter}(self, {parameter_name}: {interface_type}) -> None: ...'])
            if named_mapped_collection:
                nested_concrete = names_for(nested_details[0])[1]
                nested_package = nested_details[0].__module__.rsplit('.', 1)[0]
                nested_module = (subpackage(nested_package, concrete_subpackage) + '.'
                    + stem_for(nested_concrete, False, nested_details[0]))
                getter_body = ('        from ' + nested_module + ' import ' + nested_concrete + '\n'
                    + f'        return self.get_OrCreateNamedMappedCollectionField({name!r}, {nested_concrete})')
            elif is_collection:
                getter_body = f'        return self.get_OrCreateCollectionField({name!r}, {keyed_collection})'
            else:
                getter_body = f'        return self.get_EffectiveField({name!r})'
            concrete_lines.extend(['', f'    def {getter}(self)' + (f' -> {typed_value}' if typed_value != 'object' else '') + ':', getter_body])
            if not is_collection:
                concrete_lines.extend(['', f'    def {setter}(self, {parameter_name}'
                    + (f': {typed_value}' if typed_value != 'object' else '') + '):',
                    f'        self.set_RawField({name!r}, {parameter_name})'])
            if raw_getter is not None:
                mutable_lines.extend(['', '    @abstractmethod',
                    f'    def {raw_getter}(self) -> {interface_type}: ...'])
                concrete_lines.extend(['', f'    def {raw_getter}(self)' + (f' -> {typed_value}' if typed_value != 'object' else '') + ':',
                    f'        return self.get_RawField({name!r})'])
            if presence_checker is not None:
                mutable_lines.extend(['', '    @abstractmethod',
                    f'    def {presence_checker}(self) -> bool: ...'])
                concrete_lines.extend(['', f'    def {presence_checker}(self):',
                    f'        return self.isPresent_Field({name!r})'])
            if unsetter is not None:
                mutable_lines.extend(['', '    @abstractmethod',
                    f'    def {unsetter}(self) -> None: ...'])
                concrete_lines.extend(['', f'    def {unsetter}(self):',
                    f'        self.unset_Field({name!r})'])
            if empty_setter is not None:
                mutable_lines.extend(['', '    @abstractmethod',
                    f'    def {empty_setter}(self) -> None: ...'])
                concrete_lines.extend(['', f'    def {empty_setter}(self):',
                    f'        self.set_EmptyField({name!r})'])
            if empty_checker is not None:
                mutable_lines.extend(['', '    @abstractmethod',
                    f'    def {empty_checker}(self) -> bool: ...'])
                concrete_lines.extend(['', f'    def {empty_checker}(self):',
                    f'        return self.isEmpty_Field({name!r})'])
        mutable_lines[4:4] = ['from typing import TYPE_CHECKING', '', 'if TYPE_CHECKING:',
            *['    ' + item for item in sorted(set(mutable_imports))]] if mutable_imports else []
        concrete_lines[2:2] = ['from typing import TYPE_CHECKING', '', 'if TYPE_CHECKING:',
            *['    ' + item for item in sorted(set(concrete_imports))]] if concrete_imports else []
        source_id = schema_id
        source_version = schema_version
        mutable_module = mutable_package + '.' + stem_for(mutable_name, True)
        concrete_module = concrete_package + '.' + stem_for(concrete_name, False)
        return AIcdSdoGenerationResult(
            AIcdGeneratedSdoSource(
                mutable_name, mutable_prefix + stem_for(mutable_name, True) + extension_for(True),
                '\n'.join(mutable_lines) + '\n', mutable_package, mutable_module,
                mutable_module + '.' + mutable_name, 'MUTABLE_INTERFACE_TYPE', source_id, source_version),
            AIcdGeneratedSdoSource(
                concrete_name, concrete_prefix + stem_for(concrete_name, False) + extension_for(False),
                '\n'.join(concrete_lines) + '\n', concrete_package, concrete_module,
                concrete_module + '.' + concrete_name, 'SMART_DATA_OBJECT_TYPE', source_id, source_version))


def _camel_to_snake(value: str) -> str:
    return re.sub(r'(?<=[a-z0-9])(?=[A-Z])', '_', value).lower()


@lru_cache(maxsize=256)
def _type_checking_imports(filename: str) -> tuple[tuple[str, str, int, str], ...]:
    """Index TYPE_CHECKING imports without executing the source code as a module.

    Defs Codegen deliberately emits many recursive read-only references only
    under TYPE_CHECKING to prevent runtime import cycles. Runtime reflection
    must resolve those declared types lazily rather than treating them as
    untyped fields or synthesizing a writable class from the field name.
    """
    try:
        document = ast.parse(Path(filename).read_text(encoding='utf-8'), filename)
    except (OSError, SyntaxError):
        return ()
    bindings = []
    for statement in document.body:
        if not isinstance(statement, ast.If):
            continue
        condition = statement.test
        is_type_checking = (isinstance(condition, ast.Name) and condition.id == 'TYPE_CHECKING'
                            or isinstance(condition, ast.Attribute)
                            and condition.attr == 'TYPE_CHECKING'
                            and isinstance(condition.value, ast.Name)
                            and condition.value.id == 'typing')
        if not is_type_checking:
            continue
        for entry in statement.body:
            if not isinstance(entry, ast.ImportFrom):
                continue
            for alias in entry.names:
                bindings.append((alias.asname or alias.name, entry.module or '',
                                 entry.level, alias.name))
    return tuple(bindings)


def _get_type_hints_with_type_checking_imports(method):
    """Resolve explicit annotations using their source-declared lazy imports."""
    try:
        return get_type_hints(method)
    except NameError:
        pass
    module_globals = getattr(method, '__globals__', {})
    filename = module_globals.get('__file__')
    if not filename:
        return {}
    annotations = getattr(method, '__annotations__', {})
    expression = annotations.get('return', '')
    referenced_names = set()
    if isinstance(expression, str):
        try:
            referenced_names = {node.id for node in ast.walk(ast.parse(expression, mode='eval'))
                                if isinstance(node, ast.Name)}
        except SyntaxError:
            return {}
    namespace = dict(module_globals)
    package = module_globals.get('__package__') or module_globals.get('__name__', '').rpartition('.')[0]
    for local_name, from_module, level, symbol in _type_checking_imports(str(filename)):
        if local_name not in referenced_names or local_name in namespace:
            continue
        try:
            module = importlib.import_module('.' * level + from_module, package=package)
            namespace[local_name] = getattr(module, symbol)
        except (ImportError, AttributeError, TypeError, ValueError):
            continue
    try:
        return get_type_hints(method, globalns=namespace)
    except (NameError, TypeError):
        return {}


def _field_annotation(read_contract: type, getter: str, field_name: str):
    """Obtain a source annotation without mistaking missing type hints for scalar values."""
    method = getattr(read_contract, getter, None)
    if method is not None:
        try:
            annotation = _get_type_hints_with_type_checking_imports(method).get('return')
            if annotation is not None:
                return annotation
        except (NameError, TypeError):
            pass
    candidates = (field_name, field_name[:1].lower() + field_name[1:])
    for base in read_contract.__mro__:
        declarations = base.__dict__.get('__annotations__', {})
        for candidate in candidates:
            if candidate not in declarations:
                continue
            try:
                annotation = get_type_hints(base).get(candidate)
                if annotation is not None:
                    return annotation
            except (NameError, TypeError):
                pass
    return None


def _unwrap_optional(annotation):
    nullable = False
    if get_origin(annotation) in (Union, UnionType):
        values = get_args(annotation)
        if len(values) == 2 and type(None) in values:
            annotation = next(value for value in values if value is not type(None))
            nullable = True
    return annotation, nullable


def _nested_contract(read_contract: type, getter: str, field_name: str = '') -> tuple[type, bool, bool] | None:
    """Discover referenced contracts under optional single values and repeated collections."""
    annotation, nullable = _unwrap_optional(_field_annotation(read_contract, getter, field_name))
    repeated = False
    if get_origin(annotation) in (list, tuple, AIiMultiMappedList):
        args = get_args(annotation)
        if args:
            repeated = True
            annotation, _ = _unwrap_optional(args[0])
    # Converting an unannotated read-only helper into a writable type would
    # invent a module/class that SDO never generates. Keep choice/union helpers
    # as original read-only types rather than treating them as nested SDOs.
    if isclass(annotation) and _is_sdo_input(annotation):
        return annotation, nullable, repeated
    return None


def _auxiliary_read_only_contract(read_contract: type, getter: str,
                                  field_name: str = '') -> tuple[type, bool, bool] | None:
    """Preserve a typed read-only helper without inventing an SDO counterpart.

    Covers XML choices (including concrete choice variants) and unannotated
    DataObject-compatible helper interfaces. These types can appear in fields,
    but have no writable AIigd equivalent because they are not SDO inputs.
    """
    annotation, nullable = _unwrap_optional(_field_annotation(read_contract, getter, field_name))
    repeated = False
    if get_origin(annotation) in (list, tuple, AIiMultiMappedList):
        arguments = get_args(annotation)
        if arguments:
            repeated = True
            annotation, _ = _unwrap_optional(arguments[0])
    if not isclass(annotation) or _is_sdo_input(annotation):
        return None
    is_choice = any('__xml_choice_variant_imports__' in base.__dict__
                    for base in annotation.__mro__)
    is_unannotated_dataobject = (issubclass(annotation, AIiDataObject)
                                 and not annotation.__module__.startswith('eu.algites.lib.data.dataobject'))
    return (annotation, nullable, repeated) if is_choice or is_unannotated_dataobject else None


def _repeated_contract_field(read_contract: type, getter: str, field_name: str, descriptor) -> bool:
    """Recognize XML repeated element contracts even when the items are scalars."""
    annotation, _ = _unwrap_optional(_field_annotation(read_contract, getter, field_name))
    return (get_origin(annotation) in (list, tuple, AIiMultiMappedList)
            or getattr(descriptor, 'expected_type', None) in (list, tuple, AIiMultiMappedList))


def _default_field_title(name: str) -> str:
    """Create a sentence-case fallback, retaining uppercase acronyms."""
    value = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', name)
    value = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', value).replace('_', ' ').replace('-', ' ')
    words = value.split()
    if not words:
        return name
    normalized = [word if len(word) > 1 and word.isupper() else word.lower() for word in words]
    if not normalized[0].isupper():
        normalized[0] = normalized[0].capitalize()
    return ' '.join(normalized)
