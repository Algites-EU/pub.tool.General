"""Mutable interface and concrete class generated from one read contract."""
from dataclasses import dataclass
from eu.algites.tool.codegen.sdo.aicd_generated_sdo_source import AIcdGeneratedSdoSource

@dataclass(frozen=True)
class AIcdSdoGenerationResult:
    mutable_interface: AIcdGeneratedSdoSource
    implementation: AIcdGeneratedSdoSource
