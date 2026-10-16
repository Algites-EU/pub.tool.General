"""Generate SmartDataObject types from imported, annotated read-only contracts.

No schema readers or definition types are imported: the normalized AIig contract is
both the input and the sole source of truth. Class inheritance is preserved.
"""
from __future__ import annotations

import re
from inspect import isclass
from typing import get_type_hints, get_args, get_origin, Union
from types import UnionType
from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.tool.codegen.sdo.aicd_generated_sdo_source import AIcdGeneratedSdoSource
from eu.algites.tool.codegen.sdo.aicd_sdo_generation_result import AIcdSdoGenerationResult
from eu.algites.tool.codegen.sdo.aii_sdo_codegen_service import AIiSdoCodegenService


class AIcSdoCodegenService(AIiSdoCodegenService):
    """Generate SDOs from annotated AIig or handwritten AIi read-only contracts."""

    def generate(self, read_contract: type, marker: str = 'd', naming=None) -> AIcdSdoGenerationResult:
        if not isclass(read_contract) or not issubclass(read_contract, AIiDataObject) or not read_contract.__name__.startswith(('AIig', 'AIi')) or read_contract is AIiDataObject:
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
                    raise ValueError('Conflicting inherited field: ' + field.name)
                all_fields[field.name] = field
        if len({f.name for f in fields}) != len(fields):
            raise ValueError('Duplicate field in read contract')
        parents = [c for c in read_contract.__bases__ if c is not AIiDataObject and c.__name__.startswith(('AIig', 'AIi')) and issubclass(c, AIiDataObject)]
        parent = parents[0] if len(parents) == 1 else None
        if len(parents) > 1:
            fields = tuple(all_fields.values())
        input_role = 'algites-python-gen-intf-versioned'
        mutable_role = 'algites-python-gen-data-intf-versioned'
        concrete_role = 'algites-python-gen-data-class-versioned'

        def names_for(contract):
            if naming is None:
                tail = contract.__name__[4 if contract.__name__.startswith('AIig') else 3:]
                return 'AIig' + marker + tail, 'AIcg' + marker + tail
            input_cat, mutable_cat, concrete_cat = naming
            read_name = contract.__name__ if contract.__name__.startswith('AIig') else 'AIig' + contract.__name__[3:]
            values = input_cat.parse(input_role, 'main_container_name', read_name)
            return (mutable_cat.format(mutable_role, 'main_container_name', values, 'upper_camel_case'),
                    concrete_cat.format(concrete_role, 'main_container_name', values, 'upper_camel_case'))

        def stem_for(type_name, is_mutable):
            if naming is None:
                return _snake(type_name, marker)
            cat = naming[1] if is_mutable else naming[2]
            role = mutable_role if is_mutable else concrete_role
            values = cat.parse(role, 'main_container_name', type_name)
            return cat.format(role, 'file_name_stem', values, 'upper_camel_case')

        def extension_for(is_mutable):
            if naming is None:
                return '.py'
            cat = naming[1] if is_mutable else naming[2]
            role = mutable_role if is_mutable else concrete_role
            return cat.format(role, 'file_name_suffix', {})

        mutable_name, concrete_name = names_for(read_contract)
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
            'from eu.algites.lib.data.smartdataobject.aii_smart_data_object import AIiSmartDataObject']
        concrete_lines = [f'"""Generated SmartDataObject implementation for {read_contract.__name__}."""',
            'from __future__ import annotations',
            f'from {package}.{stem_for(mutable_name, True)} import {mutable_name}',
            'from eu.algites.lib.data.smartdataobject.aic_smart_data_object import AIcSmartDataObject']
        if len(parents) > 1:
            mutable_bases = read_contract.__name__ + ', ' + ', '.join(names_for(p)[0] for p in parents) + ', AIiSmartDataObject'
            concrete_base = 'AIcSmartDataObject'
            for inherited in parents:
                parent_mut, _ = names_for(inherited)
                parent_pkg = inherited.__module__.rsplit('.', 1)[0]
                mutable_lines.append(f'from {parent_pkg}.{stem_for(parent_mut, True)} import {parent_mut}')
        elif parent is not None:
            parent_mut, parent_impl = names_for(parent)
            parent_pkg = parent.__module__.rsplit('.', 1)[0]
            mutable_lines.append(f'from {parent_pkg}.{stem_for(parent_mut, True)} import {parent_mut}')
            concrete_lines.append(f'from {parent_pkg}.{stem_for(parent_impl, False)} import {parent_impl}')
            mutable_bases = f'{read_contract.__name__}, {parent_mut}, AIiSmartDataObject'
            concrete_base = parent_impl
        else:
            mutable_bases = f'{read_contract.__name__}, AIiSmartDataObject'
            concrete_base = 'AIcSmartDataObject'
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
            f'xml_local_name={inherited.xml_local_name!r}, xml_namespace={inherited.xml_namespace!r}, '
            f'fingerprint={inherited.fingerprint!r})')
        mutable_lines.insert(4, 'from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject')
        mutable_lines.extend(['', '', f'class {mutable_name}({mutable_bases}):',
                              f'    __data_object__ = {annotation}', 
                              '    """Presence-aware setters, raw getters and unsetters."""'])
        concrete_lines.extend(['', '', f'class {concrete_name}({concrete_base}, {mutable_name}):',
                               '    """Generated implementation; inherited fields use parent behavior."""'])
        mutable_imports = []
        concrete_imports = []
        if not fields:
            mutable_lines.append('    pass')
            concrete_lines.append('    pass')
        for descriptor in fields:
            name = descriptor.name
            suffix = _suffix(descriptor.getter_name or 'get' + name)
            getter = descriptor.getter_name or 'get' + name
            if not getter.isidentifier() or not suffix.isidentifier():
                raise ValueError('Invalid field getter: ' + getter)
            nested_details = _nested_contract(read_contract, getter)
            nested_type = (names_for(nested_details[0])[0]
                + (' | None' if nested_details[1] else '')) if nested_details else None
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


def _nested_contract(read_contract: type, getter: str) -> tuple[type, bool] | None:
    method = read_contract.__dict__.get(getter)
    if method is None:
        return None
    annotation = get_type_hints(method).get('return')
    nullable = False
    if get_origin(annotation) in (Union, UnionType):
        values = get_args(annotation)
        if len(values) != 2 or type(None) not in values:
            return None
        annotation = next(value for value in values if value is not type(None))
        nullable = True
    if isclass(annotation) and annotation.__name__.startswith('AIig') and issubclass(annotation, AIiDataObject):
        return annotation, nullable
    return None
