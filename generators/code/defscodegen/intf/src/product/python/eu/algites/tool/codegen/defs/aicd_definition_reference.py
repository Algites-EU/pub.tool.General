"""Reference identity and optional recursive target type, without a duplicate kind projection."""
from __future__ import annotations
from dataclasses import dataclass
from .aicd_data_type import AIcdDataType
from .ain_data_type_kind import AInDataTypeKind

@dataclass(frozen=True, slots=True)
class AIcdDefinitionReference:
    """Identity of a target; its DataType may initially describe only the known root kind."""
    identity: str
    version: int | None
    logical_name: str
    target_data_type: AIcdDataType | None = None

    @property
    def targets_enum(self) -> bool:
        """Return whether the target's currently known recursive root type is ENUM."""
        return self.target_data_type is not None and self.target_data_type.kind is AInDataTypeKind.ENUM
