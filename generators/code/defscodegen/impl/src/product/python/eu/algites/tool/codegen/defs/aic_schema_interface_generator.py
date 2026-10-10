from __future__ import annotations

from dataclasses import dataclass
import re

from eu.algites.lib.naming.convention.ain_output_name_kind import AInOutputNameKind
from eu.algites.tool.codegen.defs._support import _java_integer, _java_quote, _java_type
from eu.algites.tool.codegen.defs.aic_default_defs_codegen_service import AIcDefaultDefsCodegenService
from eu.algites.tool.codegen.defs.aic_generation_names import AIcGenerationNames
from eu.algites.tool.codegen.defs.aic_scalar_generation import java_identifier
from eu.algites.tool.codegen.defs.aicd_generated_source import AIcdGeneratedSource
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
from eu.algites.tool.codegen.defs.ain_definition_kind import AInDefinitionKind
from eu.algites.tool.codegen.defs.ain_value_kind import AInValueKind


class AIcSchemaInterfaceGenerator:
    """Generate a native contract and implementation from the same canonical object."""

    @dataclass(frozen=True, slots=True)
    class AIcdSources:
        """Contract in the interface artifact and optional concrete implementation."""

        contract: AIcdGeneratedSource
        implementation: AIcdGeneratedSource | None

    def __init__(self):
        self.names = AIcGenerationNames()

    def _metadata(self, request) -> str:
        """Metadata is derived exclusively from normalized canonical definitions."""
        model = request.definition
        result = ('    __data_object__ = AIcdDataObject(id=' + repr(model.identity)
            + ', version=' + str(model.version if model.version is not None else -1)
            + ', description=' + repr(model.description or '') + ')\n')
        result += '    __data_object_fields__ = (\n'
        for prop in model.properties:
            suffix = self.names.property_name(prop.source_name, request.naming_profile)
            result += ('        AIcdDataObjectField(name=' + repr(prop.source_name)
                + ', description=' + repr(prop.description or '')
                + ', presence_required=' + str(bool(prop.required))
                + ', allows_null=' + str(bool(prop.nullable))
                + ', getter_name=' + repr('get' + suffix[0].upper() + suffix[1:]) + '),\n')
        result += '    )\n\n'
        for prop in model.properties:
            property_name = self.names.property_name(prop.source_name, request.naming_profile)
            suffix = property_name[0].upper() + property_name[1:]
            returned = ''
            if (prop.reference is not None and prop.value_kind is AInValueKind.REFERENCE
                    and prop.reference.target_kind is not AInDefinitionKind.ENUM):
                nested = self.names.render(prop.reference.logical_name, prop.reference.version,
                    request.naming_profile, AInOutputNameKind.INTERFACE_TYPE)
                returned = f' -> {nested}' + (' | None' if prop.nullable else '')
            result += f'    def get{suffix}(self){returned}:\n        return self.{property_name}\n\n' 
        return result

    def generate(self, request) -> AIcdSources:
        """Render both native types without changing the standalone DTO API."""
        dto = AIcDefaultDefsCodegenService().generate(request)
        if request.definition.kind is AInDefinitionKind.ENUM:
            return self.AIcdSources(dto, None)
        interface = self.names.type_name(request.definition, request.naming_profile, AInOutputNameKind.INTERFACE_TYPE)
        path = request.package_name.replace('.', '/') + '/'
        if request.target is AInCodeGenerationTarget.PYTHON:
            file = self.names.file_stem(request.definition, request.naming_profile, AInOutputNameKind.INTERFACE_TYPE_FILE_STEM)
            marker = f'@dataclass(frozen=True, slots=True)\nclass {dto.type_name}:\n'
            if marker not in dto.source:
                raise ValueError(f'Missing primary DTO declaration: {dto.type_name}')
            fields = dto.source.split(marker, 1)[1].split('\n\n    def __post_init__', 1)[0]
            fields = re.sub(r'(?m)^    ([a-zA-Z_][a-zA-Z0-9_]*: [^\n]+?) = _AI_UNSET$', r'    \1', fields)
            fields = re.sub(r'(?m)^(    SCHEMA_FIELD_NAME__[A-Z0-9_]+) =', r'\1: ClassVar[str] =', fields)
            imports = set()
            for prop in request.definition.properties:
                ref = prop.reference
                if ref is None:
                    continue
                is_enum = ref.target_kind is AInDefinitionKind.ENUM
                concrete = self.names.render(ref.logical_name, ref.version, request.naming_profile,
                    AInOutputNameKind.ENUM_TYPE if is_enum else AInOutputNameKind.DATA_TYPE)
                abstract = self.names.render(ref.logical_name, ref.version, request.naming_profile,
                    AInOutputNameKind.ENUM_TYPE if is_enum else AInOutputNameKind.INTERFACE_TYPE)
                abstract_file = self.names.render(ref.logical_name, ref.version, request.naming_profile,
                    AInOutputNameKind.ENUM_TYPE_FILE_STEM if is_enum else AInOutputNameKind.INTERFACE_TYPE_FILE_STEM)
                fields = fields.replace(concrete, abstract)
                imports.add(f'from .{abstract_file} import {abstract}')
            helpers = ''
            if 'AIcSchemaTemporalValue' in fields or 'AIcSchemaDuration' in fields:
                helpers = dto.source[dto.source.index('from dataclasses import dataclass'):dto.source.index('\ndef _ai_convert')]
            contract = ('from __future__ import annotations\n\nfrom abc import ABC, abstractmethod\n'
                'from typing import Any, ClassVar, Mapping, TYPE_CHECKING\nfrom decimal import Decimal\n'
                'from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject\n'
                'from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject\n'
                'from eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField\n\n'
                + helpers + '\n'.join(sorted(imports)) + f'\n\nclass {interface}(ABC, AIiDataObject):\n'
                + self._metadata(request) + fields
                + '\n\n    __slots__ = ()\n\n    @abstractmethod\n'
                '    def to_mapping(self) -> Mapping[str, object]:\n'
                '        """Return canonical wire fields, omitting absent optional values."""\n'
                '        raise NotImplementedError\n')
            implementation = dto.source.replace(marker,
                f'from .{file} import {interface}\n\n@dataclass(frozen=True, slots=True)\nclass {dto.type_name}({interface}):\n', 1)
            if helpers:
                implementation = implementation.replace(helpers,
                    f'from .{file} import AIcSchemaTemporalValue, AIcSchemaDuration\n'
                    'from dataclasses import dataclass\nfrom decimal import Decimal\nimport base64\nimport re\nimport struct\n\n_AI_UNSET = object()\n', 1)
            return self.AIcdSources(AIcdGeneratedSource(interface, path + file + '.py', contract),
                AIcdGeneratedSource(dto.type_name, dto.relative_path, implementation))

        rows = [f'package {request.package_name};\n\n/** Generated schema contract. Do not edit manually. */',
            f'@eu.algites.lib.data.dataobject.AIaDataObject(id = {_java_quote(request.definition.identity)}, version = {_java_integer(request.definition.version) if request.definition.version is not None else -1}, description = {_java_quote(request.definition.description or "")})',
            f'public interface {interface} extends eu.algites.lib.data.dataobject.AIiDataObject {{',
            f'    String CANONICAL_SOURCE_ID = {_java_quote(request.definition.identity)};',
            f'    Integer CANONICAL_SOURCE_VERSION = {_java_integer(request.definition.version)};',
            f'    String CANONICAL_SOURCE_RESOURCE = {_java_quote(request.definition.source_resource)};']
        for prop in request.definition.properties:
            description = prop.description if prop.description is not None else f'Canonical field {prop.source_name}.'
            description = re.sub(r'\s+', ' ', description.replace('*/', '* /')).replace('<', '&lt;').replace('>', '&gt;')
            name = java_identifier(self.names.property_name(prop.source_name, request.naming_profile))
            field = prop.source_name.replace('*/', '* /')
            rows.extend([f'    /** <strong>Field Name:</strong> {{@code {field}}}. {description} */',
                f'    String {self.names.schema_field_name_constant(prop.source_name, request.naming_profile)} = {_java_quote(prop.source_name)};',
                f'    /** {description} */'])
            typ = _java_type(prop, request, self.names)
            if prop.reference is not None and prop.reference.target_kind is not AInDefinitionKind.ENUM:
                ref = prop.reference
                concrete = self.names.render(ref.logical_name, ref.version, request.naming_profile, AInOutputNameKind.DATA_TYPE)
                abstract = self.names.render(ref.logical_name, ref.version, request.naming_profile, AInOutputNameKind.INTERFACE_TYPE)
                typ = typ.replace(concrete, abstract)
                if prop.value_kind is AInValueKind.ARRAY:
                    typ = typ.replace('<', '<? extends ')
            rows.append(f'    @eu.algites.lib.data.dataobject.AIaDataObjectField(name = {_java_quote(prop.source_name)}, description = {_java_quote(prop.description or "")}, presenceRequired = {str(bool(prop.required)).lower()}, allowsNull = {str(bool(prop.nullable)).lower()})')
            rows.append(f'    {typ} {name}();')
        rows.append('}')
        marker = ') {\n'
        if marker not in dto.source:
            raise ValueError(f'Missing record declaration: {dto.type_name}')
        implementation = dto.source.replace(marker, f') implements {interface} {{\n', 1)
        return self.AIcdSources(AIcdGeneratedSource(interface, path + interface + '.java', '\n'.join(rows) + '\n'),
            AIcdGeneratedSource(dto.type_name, dto.relative_path, implementation))
