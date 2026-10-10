"""Schema-independent SmartDataObject generator contract."""
from abc import ABC, abstractmethod
from .aicd_sdo_generation_result import AIcdSdoGenerationResult

class AIiSdoCodegenService(ABC):
    @abstractmethod
    def generate(self, read_contract: type, marker: str = 'd') -> AIcdSdoGenerationResult:
        raise NotImplementedError
