"""Schema-independent SmartDataObject generator contract."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Mapping
from eu.algites.tool.codegen.sdo.aicd_sdo_generation_result import AIcdSdoGenerationResult

class AIiSdoCodegenService(ABC):
    """Defines the schema-independent contract for generating mutable SDO types."""
    @abstractmethod
    def generate(self, read_contract: type, marker: str = 'd') -> AIcdSdoGenerationResult:
        """Generate mutable interfaces and implementations for an annotated read contract."""
        raise NotImplementedError

    @abstractmethod
    def generate_from_sources(self, source_root: Path, contracts: Mapping[Path, str],
                              marker: str = 'd', naming=None) -> dict[Path, AIcdSdoGenerationResult]:
        """Import new AIig source modules and reflect over their annotated classes."""
        raise NotImplementedError
