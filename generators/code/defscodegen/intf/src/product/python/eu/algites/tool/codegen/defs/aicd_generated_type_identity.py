from __future__ import annotations

from dataclasses import dataclass
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
from eu.algites.tool.codegen.defs.ain_defs_name_role import AInDefsNameRole


@dataclass(frozen=True, slots=True)
class AIcdGeneratedTypeIdentity:
    """A primary generated type's importable identity, role and canonical origin.

    A Python qualified name includes its module and symbol; a Java qualified
    name contains the package and type. Never infer either from source text.
    """

    type_name: str
    namespace: str
    module_name: str
    fully_qualified_type_name: str
    type_role: AInDefsNameRole
    technology_kind: AInCodeGenerationTarget
    source_definition_id: str
    source_definition_version: int | None

    @classmethod
    def from_request(cls, request, type_name: str, relative_path: str,
                     role: AInDefsNameRole) -> AIcdGeneratedTypeIdentity:
        namespace = request.package_name
        if request.target is AInCodeGenerationTarget.PYTHON:
            module_name = namespace + '.' + relative_path.rsplit('/', 1)[-1].removesuffix('.py')
            qualified = module_name + '.' + type_name
        elif request.target is AInCodeGenerationTarget.JAVA:
            module_name = namespace
            qualified = namespace + '.' + type_name
        else:
            raise ValueError(f'Unsupported generation target: {request.target}')
        return cls(type_name, namespace, module_name, qualified, role, request.target,
                   request.definition.identity, request.definition.version)
