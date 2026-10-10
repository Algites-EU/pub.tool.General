"""Mutable interface and concrete class generated from one read contract."""
from dataclasses import dataclass
from .aicd_generated_sdo_source import AIcdGeneratedSdoSource

@dataclass(frozen=True)
class AIcdSdoGenerationResult:
    mutable_interface: AIcdGeneratedSdoSource
    implementation: AIcdGeneratedSdoSource
