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
from eu.algites.tool.codegen.sdo.aicd_generated_sdo_source import AIcdGeneratedSdoSource
from eu.algites.tool.codegen.sdo.aicd_sdo_generation_result import AIcdSdoGenerationResult
from eu.algites.tool.codegen.sdo.aii_sdo_codegen_service import AIiSdoCodegenService


class AIcSdoCodegenService(AIiSdoCodegenService):
    """Turn any importable AIig contract into a mutable interface and implementation."""

    def generate(self, read_contract: type, marker: str = 'd') -> AIcdSdoGenerationResult:
        if not isclass(read_contract) or not issubclass(read_contract, AIiDataObject) or not read_contract.__name__.startswith('AIig'):
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
        if not all_fields:
            raise ValueError('No annotated read contract fields')
        if len({f.name for f in fields}) != len(fields):
            raise ValueError('Duplicate field in read contract')
        parents = [c for c in read_contract.__bases__ if c.__name__.startswith('AIig') and issubclass(c, AIiDataObject)]
        if len(parents) > 1:
            raise ValueError('Multiple read-contract parents need an explicit conflict policy')
        parent = parents[0] if parents else None
        tail = read_contract.__name__[4:]
        mutable_name = 'AIig' + marker + tail
        concrete_name = 'AIcg' + marker + tail
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
            f'from {package}.{_snake(mutable_name, marker)} import {mutable_name}',
            'from eu.algites.lib.data.smartdataobject.aic_smart_data_object import AIcSmartDataObject']
        if parent is not None:
            parent_mut = 'AIig' + marker + parent.__name__[4:]
            parent_impl = 'AIcg' + marker + parent.__name__[4:]
            parent_pkg = parent.__module__.rsplit('.', 1)[0]
            mutable_lines.append(f'from {parent_pkg}.{_snake(parent_mut, marker)} import {parent_mut}')
            concrete_lines.append(f'from {parent_pkg}.{_snake(parent_impl, marker)} import {parent_impl}')
            mutable_bases = f'{read_contract.__name__}, {parent_mut}, AIiSmartDataObject'
            concrete_base = parent_impl
        else:
            mutable_bases = f'{read_contract.__name__}, AIiSmartDataObject'
            concrete_base = 'AIcSmartDataObject'
        mutable_lines.extend(['', '', f'class {mutable_name}({mutable_bases}):',
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
            nested_type = (('AIig' + marker + nested_details[0].__name__[4:])
                + (' | None' if nested_details[1] else '')) if nested_details else None
            typed_value = nested_type or 'object'
            if nested_type is not None:
                nested_class = nested_details[0]
                nested_name = 'AIig' + marker + nested_class.__name__[4:]
                nested_package = nested_class.__module__.rsplit('.', 1)[0]
                nested_file = _snake(nested_name, marker)
                mutable_imports.append(f'from {nested_package}.{nested_file} import {nested_name}')
                concrete_imports.append(f'from {nested_package}.{nested_file} import {nested_name}')
            if nested_type is not None:
                mutable_lines.extend(['', '    @abstractmethod',
                    f'    def {getter}(self) -> {typed_value}: ...'])
            mutable_lines.extend(['', '    @abstractmethod',
                f'    def set{suffix}(self, value: {typed_value}) -> None: ...',
                '', '    @abstractmethod', f'    def get_{suffix}(self) -> {typed_value}: ...',
                '', '    @abstractmethod', f'    def isPresent_{suffix}(self) -> bool: ...',
                '', '    @abstractmethod', f'    def unset_{suffix}(self) -> None: ...'])
            concrete_lines.extend(['', f'    def {getter}(self)' + (f' -> {typed_value}' if nested_type else '') + ':',
                f'        return self.get_EffectiveField({name!r})',
                '', f'    def set{suffix}(self, value' + (f': {typed_value}' if nested_type else '') + '):',
                f'        self.set_RawField({name!r}, value)',
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
        return AIcdSdoGenerationResult(
            AIcdGeneratedSdoSource(mutable_name, prefix + _snake(mutable_name, marker) + '.py', '\n'.join(mutable_lines) + '\n'),
            AIcdGeneratedSdoSource(concrete_name, prefix + _snake(concrete_name, marker) + '.py', '\n'.join(concrete_lines) + '\n'))


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
