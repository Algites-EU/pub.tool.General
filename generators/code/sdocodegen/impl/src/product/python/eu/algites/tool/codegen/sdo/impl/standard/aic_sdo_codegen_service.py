"""Generate SmartDataObject types from imported, annotated read-only contracts.

No schema readers or definition types are imported: the normalized AIig contract is
both the input and the sole source of truth. Class inheritance is preserved.
"""
from __future__ import annotations

import re
import importlib
from pathlib import Path
import sys
from inspect import isclass
from typing import get_type_hints, get_args, get_origin, Union
from types import UnionType
from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
from eu.algites.lib.data.dataobject.xmldefs.aii_xml_data_object import AIiXmlDataObject
from eu.algites.lib.data.dataobject.jsondefs.aii_json_data_object import AIiJsonDataObject
from eu.algites.lib.data.dataobject.yamldefs.aii_yaml_data_object import AIiYamlDataObject
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.common.object.props.labels.aia_field_label import AIaFieldLabel
from eu.algites.tool.codegen.sdo.aicd_generated_sdo_source import AIcdGeneratedSdoSource
from eu.algites.tool.codegen.sdo.aicd_sdo_generation_result import AIcdSdoGenerationResult
from eu.algites.tool.codegen.sdo.aii_sdo_codegen_service import AIiSdoCodegenService


class AIcSdoCodegenService(AIiSdoCodegenService):
    """Generate SDOs from annotated AIig or handwritten AIi read-only contracts."""

    def generate_from_sources(self, source_root: Path, contracts: dict[Path, str],
                              marker: str = 'd', naming=None) -> dict[Path, AIcdSdoGenerationResult]:
        """Import AIig modules from source roots and reuse the reflection-based generator.

        No separate packaging or Python build step is needed. Relative imports from
        sibling generated contracts work through the temporary import search entry.
        """
        root = Path(source_root).resolve(strict=True)
        if not root.is_dir():
            raise ValueError(f'Not a DO contract source root: {root}')
        if not contracts:
            return {}
        prepared = {}
        for path, name in contracts.items():
            source = (root / path).resolve(strict=True)
            if not source.is_relative_to(root) or source.suffix != '.py' or not source.is_file():
                raise ValueError(f'Invalid DO contract source: {path}')
            if not name.isidentifier():
                raise ValueError(f'Invalid DO contract class name: {name}')
            prepared[source] = ('.'.join(source.relative_to(root).with_suffix('').parts), name)
        inserted = str(root) not in sys.path
        if inserted:
            sys.path.insert(0, str(root))
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
                    raise ValueError(f'Imported DO contract is not the requested source: {source} (loaded {loaded})')
                contract = getattr(module, class_name)
                results[source] = self.generate(contract, marker, naming)
            return results
        finally:
            if inserted:
                sys.path.remove(str(root))

    def generate(self, read_contract: type, marker: str = 'd', naming=None) -> AIcdSdoGenerationResult:
        """Generate native SDO types while preserving inherited field and label annotations."""
        if not isclass(read_contract) or not issubclass(read_contract, AIiDataObject) or not read_contract.__name__.startswith(('AIig', 'AIi')) or read_contract.__module__.startswith("eu.algites.lib.data.dataobject"):
            # Source-family marker types are infrastructure, not generated schema contracts.
            raise ValueError('Read contract must be an AIig subclass of AIiDataObject')
        if not re.fullmatch(r'[a-z][a-z0-9]*', marker):
            raise ValueError(f'Invalid mutable implementation marker: {marker!r}')
        if '.' not in read_contract.__module__:
            raise ValueError('Read contract must live in an importable package')
        fields = tuple(read_contract.__dict__.get('__data_object_fields__', ()))
        all_fields = {}
        for base in reversed(read_contract.__mro__):
            for field in base.__dict__.get('__data_object_fields__', ()):
                previous = all_fields.get(field.name)
                if previous is not None and previous != field:
                    from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind
                    if (previous.presence is AInFieldPresenceKind.REQUIRED
                            and field.presence is not AInFieldPresenceKind.REQUIRED
                            or previous.presence is AInFieldPresenceKind.FORBIDDEN
                            and field.presence is not AInFieldPresenceKind.FORBIDDEN
                            or not previous.allows_null and field.allows_null):
                        raise ValueError('Invalid inherited field relaxation: ' + field.name)
                all_fields[field.name] = field
        if len({f.name for f in fields}) != len(fields):
            raise ValueError('Duplicate field in read contract')
        parents = [c for c in read_contract.__bases__ if not c.__module__.startswith('eu.algites.lib.data.dataobject')
                   and c.__name__.startswith(('AIig', 'AIi')) and issubclass(c, AIiDataObject)]
        parent = parents[0] if len(parents) == 1 else None
        if len(parents) > 1:
            fields = tuple(all_fields.values())
        def roles_for(contract):
            """Select each contract's source/output roles independently of its child."""
            is_xml = contract.__name__.startswith(('AIig_xe', 'AIi_xe'))
            return (
                'algites-python-gen-xml-element-intf-versioned' if is_xml else 'algites-python-gen-intf-versioned',
                'algites-python-gen-data-xml-element-intf-versioned' if is_xml else 'algites-python-gen-data-intf-versioned',
                'algites-python-gen-data-xml-element-class-versioned' if is_xml else 'algites-python-gen-data-class-versioned',
            )

        input_role, mutable_role, concrete_role = roles_for(read_contract)

        def names_for(contract):
            if naming is None:
                tail = contract.__name__[4 if contract.__name__.startswith('AIig') else 3:]
                return 'AIig' + marker + tail, 'AIcg' + marker + tail
            input_cat, mutable_cat, concrete_cat = naming
            source_role, target_mutable_role, target_concrete_role = roles_for(contract)
            read_name = contract.__name__ if contract.__name__.startswith('AIig') else 'AIig' + contract.__name__[3:]
            values = input_cat.parse(source_role, 'main_container_name', read_name)
            return (mutable_cat.format(target_mutable_role, 'main_container_name', values, 'upper_camel_case'),
                    concrete_cat.format(target_concrete_role, 'main_container_name', values, 'upper_camel_case'))

        def stem_for(type_name, is_mutable):
            if naming is None:
                return _snake(type_name, marker)
            cat = naming[1] if is_mutable else naming[2]
            is_xml = type_name.startswith(('AIigd__xe', 'AIcgd__xe', 'AIigd_xe', 'AIcgd_xe'))
            role = ('algites-python-gen-data-xml-element-intf-versioned' if is_mutable else
                    'algites-python-gen-data-xml-element-class-versioned') if is_xml else (
                    'algites-python-gen-data-intf-versioned' if is_mutable else 'algites-python-gen-data-class-versioned')
            values = cat.parse(role, 'main_container_name', type_name)
            return cat.format(role, 'file_name_stem', values, 'upper_camel_case')

        def extension_for(is_mutable):
            if naming is None:
                return '.py'
            cat = naming[1] if is_mutable else naming[2]
            role = mutable_role if is_mutable else concrete_role
            return cat.format(role, 'file_name_suffix', {})

        mutable_name, concrete_name = names_for(read_contract)
        if issubclass(read_contract, AIiXmlDataObject):
            technology = 'xmldefs'
            mutable_technology = 'AIiXmlSmartDataObject'
            concrete_technology = 'AIcXmlSmartDataObject'
        elif issubclass(read_contract, AIiJsonDataObject):
            technology = 'jsondefs'
            mutable_technology = 'AIiJsonSmartDataObject'
            concrete_technology = 'AIcJsonSmartDataObject'
        elif issubclass(read_contract, AIiYamlDataObject):
            technology = 'yamldefs'
            mutable_technology = 'AIiYamlSmartDataObject'
            concrete_technology = 'AIcYamlSmartDataObject'
        else:
            technology = None
            mutable_technology = 'AIiSmartDataObject'
            concrete_technology = 'AIcSmartDataObject' 
        # The selected YAML profiles also own names of generated method parameters.
        parameter_name = 'value'
        if naming is not None:
            parameter_name = naming[1].format(mutable_role, 'method_parameter_name',
                                              {'identifier': 'value'}, 'lower_snake_case')
            if not naming[2].matches(concrete_role, 'method_parameter_name', parameter_name):
                raise ValueError('SDO parameter name does not match the implementation naming profile')
        package = read_contract.__module__.rsplit('.', 1)[0]
        prefix = package.replace('.', '/') + '/'
        contract_import = f'from {read_contract.__module__} import {read_contract.__name__}'
        mutable_lines = [f'"""Generated mutable contract for {read_contract.__name__}."""',
            'from __future__ import annotations',
            'from abc import abstractmethod',
            contract_import,
            (f'from eu.algites.lib.data.smartdataobject.{technology}.aii_{technology.removesuffix("defs")}_smart_data_object import {mutable_technology}' if technology else
            'from eu.algites.lib.data.smartdataobject.aii_smart_data_object import AIiSmartDataObject')]
        concrete_lines = [f'"""Generated SmartDataObject implementation for {read_contract.__name__}."""',
            'from __future__ import annotations',
            f'from {package}.{stem_for(mutable_name, True)} import {mutable_name}',
            (f'from eu.algites.lib.data.smartdataobject.impl.{technology}.aic_{technology.removesuffix("defs")}_smart_data_object import {concrete_technology}' if technology else
            'from eu.algites.lib.data.smartdataobject.impl.standard.aic_smart_data_object import AIcSmartDataObject')]
        if len(parents) > 1:
            mutable_bases = read_contract.__name__ + ', ' + ', '.join(names_for(p)[0] for p in parents) + ', ' + mutable_technology
            concrete_base = concrete_technology
            for inherited in parents:
                parent_mut, _ = names_for(inherited)
                parent_pkg = inherited.__module__.rsplit('.', 1)[0]
                mutable_lines.append(f'from {parent_pkg}.{stem_for(parent_mut, True)} import {parent_mut}')
        elif parent is not None:
            parent_mut, parent_impl = names_for(parent)
            parent_pkg = parent.__module__.rsplit('.', 1)[0]
            mutable_lines.append(f'from {parent_pkg}.{stem_for(parent_mut, True)} import {parent_mut}')
            concrete_lines.append(f'from {parent_pkg}.{stem_for(parent_impl, False)} import {parent_impl}')
            mutable_bases = f'{read_contract.__name__}, {parent_mut}, {mutable_technology}'
            concrete_base = parent_impl
        else:
            mutable_bases = f'{read_contract.__name__}, {mutable_technology}'
            concrete_base = concrete_technology
        import re as _re
        inherited_definition = getattr(read_contract, '__data_object__', None)
        schema_id = getattr(inherited_definition, 'schema_id', '') if inherited_definition else ''
        schema_version = getattr(inherited_definition, 'schema_version', -1) if inherited_definition else -1
        parsed = _re.fullmatch(r'AIi(?:g)?(.+?)(?:_([1-9][0-9]*))?', read_contract.__name__)
        if not schema_id:
            if not parsed:
                raise ValueError('Cannot derive SchemaId from contract name')
            if naming is not None:
                read_name = read_contract.__name__ if read_contract.__name__.startswith('AIig') else 'AIig' + read_contract.__name__[3:]
                details = naming[0].parse(input_role, 'main_container_name', read_name)
                logical = naming[0].convert_identifier(details['identifier'],
                    'upper_camel_case', 'lower_kebab_case')
            else:
                logical = _re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', parsed.group(1)).lower()
            schema_id = read_contract.__module__.rsplit('.', 1)[0] + '.' + logical
        if schema_version < 0:
            if not parsed or parsed.group(2) is None:
                raise ValueError('SchemaVersion is required for an unversioned handwritten AIig')
            schema_version = int(parsed.group(2))
        inherited = inherited_definition or AIcdDataObject()
        annotation = (f'AIcdDataObject(schema_id={schema_id!r}, schema_version={schema_version}, '
            f'title={inherited.title!r}, description={inherited.description!r}, schema_url={inherited.schema_url!r}, '
            f'fingerprint={inherited.fingerprint!r}, source_contract={read_contract.__name__})')
        mutable_lines.insert(4, 'from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject')
        mutable_lines.insert(5, 'from eu.algites.lib.common.object.props.labels.aia_field_label import AIaFieldLabel')
        labels = {}
        for field in fields:
            method = getattr(read_contract, field.getter_name or 'get' + field.name, None)
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
        xml_metadata = read_contract.__dict__.get('__xml_data_object__')
        if xml_metadata is not None:
            mutable_lines.insert(4, 'from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object import AIaXmlDataObject')
            mutable_lines.insert(5, 'from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind')
            mutable_lines.append("    __xml_data_object__ = AIaXmlDataObject("
                + f'definition_kind=AInXmlObjectDefinitionKind.{xml_metadata.definition_kind.name}, '
                + f'namespace={xml_metadata.namespace!r}, '
                + f'namespace_local_name={xml_metadata.namespace_local_name!r})')
        xml_fields = read_contract.__dict__.get('__xml_data_object_fields__')
        if xml_fields:
            mutable_lines.insert(4, 'from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object_field import AIaXmlDataObjectField')
            mutable_lines.insert(5, 'from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind')
            mutable_lines.append('    __xml_data_object_fields__ = {')
            for name, metadata in xml_fields.items():
                mutable_lines.append(f'        {name!r}: AIaXmlDataObjectField(namespace={metadata.namespace!r}, '
                    f'namespace_local_name={metadata.namespace_local_name!r}, '
                    f'value_kind=AInXmlValueKind.{metadata.value_kind.name}, order={metadata.order}, '
                    f'min_occurs={metadata.min_occurs}, max_occurs={metadata.max_occurs}),')
            mutable_lines.append('    }')
        if labels:
            # A new mapping would shadow the read contract's mapping.  Start with
            # its explicit annotations, then add defaults only for missing fields.
            # Getter decorators and custom resolvers remain on the read contract.
            mutable_lines.append(f"    __field_labels__ = {{**getattr({read_contract.__name__}, '__field_labels__', {{}}),")
            for field_name, label in labels.items():
                mutable_lines.append(f'        {field_name!r}: {encode_label(label)},')
            mutable_lines.append('    }')
        concrete_lines.extend(['', '', f'class {concrete_name}({concrete_base}, {mutable_name}):',
                               '    """Generated implementation; inherited fields use parent behavior."""'])
        mutable_imports = []
        concrete_imports = []
        xml_nested_imports = {}
        xml_repeated = set()
        if not fields:
            mutable_lines.append('    pass')
            concrete_lines.append('    pass')
        for descriptor in fields:
            name = descriptor.name
            suffix = _suffix(descriptor.getter_name or 'get' + name)
            getter = descriptor.getter_name or 'get' + name
            if not getter.isidentifier() or not suffix.isidentifier():
                raise ValueError('Invalid field getter: ' + getter)
            nested_details = _nested_contract(read_contract, getter, name)
            nested_type = (('list[' + names_for(nested_details[0])[0] + ']'
                if nested_details[2] else names_for(nested_details[0])[0])
                + (' | None' if nested_details[1] else '')) if nested_details else None
            if technology == 'xmldefs':
                if nested_details and nested_details[2] or _repeated_contract_field(read_contract, getter, name, descriptor):
                    xml_repeated.add(name)
                if nested_details:
                    nested_concrete = names_for(nested_details[0])[1]
                    nested_package = nested_details[0].__module__.rsplit('.', 1)[0]
                    nested_concrete_module = nested_package + '.' + stem_for(nested_concrete, False)
                    xml_nested_imports[name] = nested_concrete_module + ':' + nested_concrete
            typed_value = nested_type or 'object'
            if nested_type is not None:
                nested_class = nested_details[0]
                nested_name = names_for(nested_class)[0]
                nested_package = nested_class.__module__.rsplit('.', 1)[0]
                nested_file = stem_for(nested_name, True)
                mutable_imports.append(f'from {nested_package}.{nested_file} import {nested_name}')
                concrete_imports.append(f'from {nested_package}.{nested_file} import {nested_name}')
            if nested_type is not None:
                mutable_lines.extend(['', '    @abstractmethod',
                    f'    def {getter}(self) -> {typed_value}: ...'])
            mutable_lines.extend(['', '    @abstractmethod',
                f'    def set{suffix}(self, {parameter_name}: {typed_value}) -> None: ...',
                '', '    @abstractmethod', f'    def get_{suffix}(self) -> {typed_value}: ...',
                '', '    @abstractmethod', f'    def isPresent_{suffix}(self) -> bool: ...',
                '', '    @abstractmethod', f'    def unset_{suffix}(self) -> None: ...'])
            concrete_lines.extend(['', f'    def {getter}(self)' + (f' -> {typed_value}' if nested_type else '') + ':',
                f'        return self.get_EffectiveField({name!r})',
                '', f'    def set{suffix}(self, {parameter_name}' + (f': {typed_value}' if nested_type else '') + '):',
                f'        self.set_RawField({name!r}, {parameter_name})',
                '', f'    def get_{suffix}(self)' + (f' -> {typed_value}' if nested_type else '') + ':',
                f'        return self.get_RawField({name!r})',
                '', f'    def isPresent_{suffix}(self):',
                f'        return self.isPresent_Field({name!r})',
                '', f'    def unset_{suffix}(self):',
                f'        self.unset_Field({name!r})'])
        if technology == 'xmldefs':
            mutable_lines.append('    __xml_repeated_fields__ = ' + repr(tuple(sorted(xml_repeated))))
            concrete_lines.append('    __xml_field_type_imports__ = ' + repr(xml_nested_imports))
            concrete_lines.extend(['', '    @classmethod',
                '    def from_xml(cls, aXml: str, aNestedTypes=None):',
                '        """Decode XML into this concrete generated SDO, resolving nested types lazily."""',
                '        import importlib',
                '        resolved = {}',
                '        for base in reversed(cls.__mro__):',
                "            for name, qualified in base.__dict__.get('__xml_field_type_imports__', {}).items():",
                "                module, sep, type_name = qualified.partition(':')",
                '                if not sep: raise ValueError("Invalid generated XML nested implementation mapping")',
                '                resolved[name] = getattr(importlib.import_module(module), type_name)',
                '        if aNestedTypes: resolved.update(aNestedTypes)',
                '        return super().from_xml(aXml, aNestedTypes=resolved)'])
        mutable_lines[4:4] = ['from typing import TYPE_CHECKING', '', 'if TYPE_CHECKING:',
            *['    ' + item for item in sorted(set(mutable_imports))]] if mutable_imports else []
        concrete_lines[2:2] = ['from typing import TYPE_CHECKING', '', 'if TYPE_CHECKING:',
            *['    ' + item for item in sorted(set(concrete_imports))]] if concrete_imports else []
        source_id = schema_id
        source_version = schema_version
        mutable_module = package + '.' + stem_for(mutable_name, True)
        concrete_module = package + '.' + stem_for(concrete_name, False)
        return AIcdSdoGenerationResult(
            AIcdGeneratedSdoSource(
                mutable_name, prefix + stem_for(mutable_name, True) + '.py',
                '\n'.join(mutable_lines) + '\n', package, mutable_module,
                mutable_module + '.' + mutable_name, 'MUTABLE_INTERFACE_TYPE', source_id, source_version),
            AIcdGeneratedSdoSource(
                concrete_name, prefix + stem_for(concrete_name, False) + extension_for(False),
                '\n'.join(concrete_lines) + '\n', package, concrete_module,
                concrete_module + '.' + concrete_name, 'SMART_DATA_OBJECT_TYPE', source_id, source_version))


def _snake(type_name: str, marker: str) -> str:
    """Preserve AIig/AIcg plus marker as a single naming-profile prefix."""
    if type_name.startswith('AIig' + marker):
        return 'aiig' + marker + '_' + _camel_to_snake(type_name[4 + len(marker):])
    if type_name.startswith('AIcg' + marker):
        return 'aicg' + marker + '_' + _camel_to_snake(type_name[4 + len(marker):])
    return _camel_to_snake(type_name)


def _camel_to_snake(value: str) -> str:
    return re.sub(r'(?<=[a-z0-9])(?=[A-Z])', '_', value).lower()


def _suffix(getter: str) -> str:
    text = getter[3:] if getter.startswith('get') and len(getter) > 3 else getter
    return text[0].upper() + text[1:]


def _field_annotation(read_contract: type, getter: str, field_name: str):
    """Obtain a source annotation without mistaking missing type hints for scalar values."""
    method = getattr(read_contract, getter, None)
    if method is not None:
        try:
            annotation = get_type_hints(method).get('return')
            if annotation is not None:
                return annotation
        except (NameError, TypeError):
            pass
    candidates = (field_name, field_name[:1].lower() + field_name[1:],
                  getter[3:4].lower() + getter[4:] if getter.startswith('get') else getter)
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
    if get_origin(annotation) in (list, tuple):
        args = get_args(annotation)
        if args:
            repeated = True
            annotation, _ = _unwrap_optional(args[0])
    if isclass(annotation) and annotation.__name__.startswith('AIig') and issubclass(annotation, AIiDataObject):
        return annotation, nullable, repeated
    return None


def _repeated_contract_field(read_contract: type, getter: str, field_name: str, descriptor) -> bool:
    """Recognize XML repeated element contracts even when the items are scalars."""
    annotation, _ = _unwrap_optional(_field_annotation(read_contract, getter, field_name))
    return (get_origin(annotation) in (list, tuple)
            or getattr(descriptor, 'expected_type', None) in (list, tuple))


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
