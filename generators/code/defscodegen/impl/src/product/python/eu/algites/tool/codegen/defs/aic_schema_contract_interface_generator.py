"""First-stage generator that emits only annotated read contracts and enums."""
import re
from eu.algites.tool.codegen.defs.aic_schema_interface_generator import AIcSchemaInterfaceGenerator
from eu.algites.tool.codegen.defs.aicd_generated_source import AIcdGeneratedSource
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget

class AIcSchemaContractInterfaceGenerator:
    def generate(self, request, parent: tuple[str, str] | None = None) -> AIcdGeneratedSource:
        result = AIcSchemaInterfaceGenerator().generate(request).contract
        if request.target is not AInCodeGenerationTarget.PYTHON or not result.type_name.startswith('AIig'):
            if parent is not None and result.type_name.startswith('AIig'):
                parent_type, parent_module = parent
                declaration = f'public interface {result.type_name} extends eu.algites.lib.data.dataobject.AIiDataObject {{'
                replacement = f'public interface {result.type_name} extends {parent_module}.{parent_type} {{'
                if declaration not in result.source:
                    raise ValueError('Cannot locate Java contract declaration for inheritance')
                return AIcdGeneratedSource(result.type_name, result.relative_path,
                    result.source.replace(declaration, replacement))
            return result
        source = result.source
        # SmartDataObject owns serialization; read contract getters are the complete abstract API.
        source = source.split('\n\n    @abstractmethod\n    def to_mapping(', 1)[0].rstrip() + '\n'
        source = re.sub(r'(?m)^(    def get[A-Za-z0-9_]+\(self\)(?: -> [^:]+)?:)$',
                        r'    @abstractmethod\n\1', source)
        if parent is not None:
            parent_type, parent_module = parent
            source = source.replace(f'class {result.type_name}(ABC, AIiDataObject):',
                f'class {result.type_name}({parent_type}):')
            source = source.replace('from __future__ import annotations\n',
                'from __future__ import annotations\n'
                + f'from {parent_module} import {parent_type}\n', 1)
        return AIcdGeneratedSource(result.type_name, result.relative_path, source)
