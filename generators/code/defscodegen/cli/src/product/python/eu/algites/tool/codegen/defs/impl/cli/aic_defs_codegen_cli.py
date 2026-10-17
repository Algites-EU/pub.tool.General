from __future__ import annotations

import argparse
from pathlib import Path

from eu.algites.lib.naming.convention.impl.algites.aic_algites_naming_profiles_1 import AIcAlgitesNamingProfiles_1
from eu.algites.lib.naming.convention.impl.algites.aic_name_convention_catalog_1 import AIcNameConventionCatalog_1
from eu.algites.tool.codegen.defs.aicd_code_generation_request import AIcdCodeGenerationRequest
from eu.algites.tool.codegen.defs.impl.standard.aic_default_defs_codegen_service import AIcDefaultDefsCodegenService
from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import AIcSchemaContractBindingsGenerator
from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_interface_generator import AIcSchemaContractInterfaceGenerator
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind


class AIcDefsCodegenCli:
    """CLI adapter for single-source compatibility and YAML-driven batch generation."""

    @staticmethod
    def main(args: list[str] | None = None) -> int:
        args = list(args) if args is not None else None
        if args is not None and any(arg.startswith('--schema-input-dir=') or
                arg.startswith('--technology-dointf-output-dir=') or arg == '--clean-only' for arg in args):
            return AIcDefsCodegenCli._batch(args)
        if args is None:
            import sys
            if any(arg.startswith('--schema-input-dir=') or arg.startswith('--technology-dointf-output-dir=')
                   or arg == '--clean-only' for arg in sys.argv[1:]):
                return AIcDefsCodegenCli._batch(sys.argv[1:])
        parser = argparse.ArgumentParser(description='Generate Java or Python program types from one canonical definition')
        parser.add_argument('source_kind', choices=[kind.value for kind in AInDefinitionSourceKind])
        parser.add_argument('target', choices=[target.value for target in AInCodeGenerationTarget])
        parser.add_argument('input', type=Path)
        parser.add_argument('package')
        parser.add_argument('output_root', type=Path)
        parsed = parser.parse_args(args)
        source_kind = AInDefinitionSourceKind(parsed.source_kind)
        target = AInCodeGenerationTarget(parsed.target)
        profile = AIcAlgitesNamingProfiles_1.java_profile() if target is AInCodeGenerationTarget.JAVA else AIcAlgitesNamingProfiles_1.python_profile()
        service = AIcDefaultDefsCodegenService()
        definition = service.load(AIcdDefinitionLoadRequest(parsed.input, source_kind, profile))
        generated = AIcSchemaContractInterfaceGenerator().generate(AIcdCodeGenerationRequest(definition, target, parsed.package, profile))
        output = parsed.output_root / generated.relative_path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(generated.source, encoding='utf-8')
        print(output)
        return 0

    @staticmethod
    def _batch(args: list[str]) -> int:
        parser = argparse.ArgumentParser(description='Generate all canonical contracts with explicit per-kind YAML name profiles')
        parser.add_argument('--repository-root', type=Path, default=Path.cwd())
        parser.add_argument('--schema-input-dir', action='append', default=[])
        parser.add_argument('--schema-input-naming-profile', action='append', default=[])
        parser.add_argument('--technology-dointf-output-dir', action='append', default=[])
        parser.add_argument('--technology-dointf-output-naming-profile', action='append', default=[])
        parser.add_argument('--clean-only', action='store_true')
        parser.add_argument('--check', action='store_true')
        parser.add_argument('--allow-unversioned-schemas', action='store_true')
        options = parser.parse_args(args)

        def mapping(entries: list[str], label: str, repeated: bool = False):
            result = {} if not repeated else []
            for entry in entries:
                if ':' not in entry:
                    parser.error(f'{label} requires kind:path, got {entry!r}')
                kind, path = entry.split(':', 1)
                if kind not in (('yamldefs', 'jsondefs', 'xmldefs') if label.startswith('schema') else ('java', 'python')):
                    parser.error(f'Unknown kind in {label}: {kind}')
                if not path:
                    parser.error(f'Empty path in {label}')
                if repeated:
                    result.append(dict(kind=kind, directory=path))
                else:
                    if kind in result:
                        parser.error(f'Duplicate {label} mapping for {kind}')
                    result[kind] = path
            return result

        output_dirs = mapping(options.technology_dointf_output_dir, 'technology-dointf-output-dir')
        output_profiles = mapping(options.technology_dointf_output_naming_profile, 'technology-dointf-output-naming-profile')
        if not output_dirs or set(output_dirs) != set(output_profiles):
            parser.error('Every target technology requires an output directory and naming profile')
        if not options.clean_only and not options.schema_input_dir:
            parser.error('At least one --schema-input-dir is required')
        if options.clean_only and options.check:
            parser.error('--clean-only conflicts with --check')
        input_dirs = mapping(options.schema_input_dir, 'schema-input-dir', repeated=True)
        input_profiles = mapping(options.schema_input_naming_profile, 'schema-input-naming-profile')
        if not options.clean_only and {entry['kind'] for entry in input_dirs} != set(input_profiles):
            parser.error('Each selected schema kind requires exactly one input naming profile')
        manifest = dict(artifact='.', languages=list(output_dirs),
            schema_inputs=input_dirs, schema_input_naming_profiles=input_profiles,
            technology_outputs=output_dirs, technology_naming_profiles=output_profiles,
            clean_only=options.clean_only, allow_unversioned_schemas=options.allow_unversioned_schemas)
        results = AIcSchemaContractBindingsGenerator().generate_manifest(options.repository_root, manifest, options.check)
        for item in results:
            print(item['path'])
        return 0


if __name__ == '__main__':
    raise SystemExit(AIcDefsCodegenCli.main())
