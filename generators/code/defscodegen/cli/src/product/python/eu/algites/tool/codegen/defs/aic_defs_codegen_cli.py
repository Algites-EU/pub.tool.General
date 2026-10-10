from __future__ import annotations

import argparse
from pathlib import Path

from eu.algites.lib.naming.convention.aic_algites_naming_profiles import AIcAlgitesNamingProfiles
from eu.algites.tool.codegen.defs.aicd_code_generation_request import AIcdCodeGenerationRequest
from eu.algites.tool.codegen.defs.aic_default_defs_codegen_service import AIcDefaultDefsCodegenService
from eu.algites.tool.codegen.defs.aic_schema_contract_interface_generator import AIcSchemaContractInterfaceGenerator
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind


class AIcDefsCodegenCli:
    """Provides the command-line adapter for the default defs-codegen service."""

    @staticmethod
    def main(args: list[str] | None = None) -> int:
        """Run the command-line entry point."""
        parser = argparse.ArgumentParser(description="Generate Java or Python program types from yamldefs, jsondefs, or xmldefs definitions")
        parser.add_argument("source_kind", choices=[kind.value for kind in AInDefinitionSourceKind])
        parser.add_argument("target", choices=[target.value for target in AInCodeGenerationTarget])
        parser.add_argument("input", type=Path)
        parser.add_argument("package")
        parser.add_argument("output_root", type=Path)
        parsed = parser.parse_args(args)
        source_kind = AInDefinitionSourceKind(parsed.source_kind)
        target = AInCodeGenerationTarget(parsed.target)
        profile = AIcAlgitesNamingProfiles.java_profile() if target is AInCodeGenerationTarget.JAVA else AIcAlgitesNamingProfiles.python_profile()
        service = AIcDefaultDefsCodegenService()
        definition = service.load(AIcdDefinitionLoadRequest(parsed.input, source_kind, profile))
        generated = AIcSchemaContractInterfaceGenerator().generate(AIcdCodeGenerationRequest(definition, target, parsed.package, profile))
        output = parsed.output_root / generated.relative_path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(generated.source, encoding="utf-8")
        print(output)
        return 0


if __name__ == "__main__":
    raise SystemExit(AIcDefsCodegenCli.main())
