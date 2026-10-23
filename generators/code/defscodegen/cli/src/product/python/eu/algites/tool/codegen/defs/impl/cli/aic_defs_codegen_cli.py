from __future__ import annotations

import argparse
from pathlib import Path

from eu.algites.lib.naming.convention.impl.algites.aic_name_convention_catalog_1 import AIcNameConventionCatalog_1
from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import AIcSchemaContractBindingsGenerator
from ._layered_settings import expand as expand_layered_settings


class AIcDefsCodegenCli:
    """CLI adapter for single-source compatibility and YAML-driven batch generation."""

    @staticmethod
    def main(args: list[str] | None = None) -> int:
        """Generate from a named settings file or from explicit semantic-role arguments."""
        import sys
        args = list(sys.argv[1:] if args is None else args)
        args = AIcDefsCodegenCli._expand_settings(args)
        return AIcDefsCodegenCli._batch(args)

    @staticmethod
    def _expand_settings(args: list[str]) -> list[str]:
        """Load all configuration layers and convert qualified settings to CLI options."""
        return expand_layered_settings(args, 'defscodegen', 'python', 'defs')

    @staticmethod
    def _batch(args: list[str]) -> int:
        """Bind source and output roles independently of the catalog file locations."""
        parser = argparse.ArgumentParser(description='Defs Codegen with explicit semantic naming roles')
        parser.add_argument('--repository-root', type=Path, default=Path.cwd())
        parser.add_argument('--schema-input-dir', action='append', default=[])
        parser.add_argument('--input-schema-naming-convention', action='append', default=[])
        parser.add_argument('--technology-dointf-output-dir', action='append', default=[])
        parser.add_argument('--output-interface-technology-naming-convention', action='append', default=[])
        parser.add_argument('--output-enum-technology-naming-convention', action='append', default=[])
        parser.add_argument('--naming-conventions-file', action='append', default=[])
        parser.add_argument('--setter-inheritance-policy', choices=('INHERIT_AS_GENERIC_PARAMETER', 'INHERIT_AS_FIXED_PARAMETER'))
        parser.add_argument('--check', action='store_true')
        parser.add_argument('--clean-only', action='store_true')
        parser.add_argument('--allow-unversioned-schemas', action='store_true')
        options = parser.parse_args(args)
        valid_inputs = {'xmldefs', 'yamldefs', 'jsondefs'}
        valid_targets = {'java', 'python'}
        valid_roles = {'common', 'xmldefs_type', 'xmldefs_element', 'xmldefs_namespace', 'yamldefs', 'jsondefs'}

        def split_map(values, kinds, label):
            result = {}
            for value in values:
                key, sep, name = value.partition(':')
                if sep != ':' or key not in kinds or not name:
                    parser.error(f'Invalid {label}: {value!r}')
                result[key] = name
            return result

        inputs = split_map(options.input_schema_naming_convention, valid_inputs, 'source convention')
        output_dirs = split_map(options.technology_dointf_output_dir, valid_targets, 'output directory')
        enumerations = split_map(options.output_enum_technology_naming_convention, valid_targets, 'enum convention')
        roots = [dict(kind=kind, directory=name) for kind, name in
            (entry.split(':', 1) for entry in options.schema_input_dir)]
        if any(item['kind'] not in valid_inputs or not item['directory'] for item in roots):
            parser.error('Each --schema-input-dir requires xmldefs|yamldefs|jsondefs:path')
        roles = {}
        for value in options.output_interface_technology_naming_convention:
            parts = value.split(':', 2)
            if (len(parts) != 3 or parts[0] not in valid_targets or parts[1] not in valid_roles
                    or not parts[2].startswith('defsintf=') or not parts[2][len('defsintf='):]):
                parser.error('Expected technology:role:defsintf=<naming-convention-id>')
            roles.setdefault(parts[0], {})[parts[1]] = parts[2][len('defsintf='):]
        if not options.clean_only and (not roots or not output_dirs):
            parser.error('Select schema roots and at least one output technology')
        if not options.clean_only and any(kind not in inputs for kind in {entry['kind'] for entry in roots}):
            parser.error('Each selected schema input requires an input naming convention')
        if any(technology not in output_dirs for technology in roles):
            parser.error('Naming role has no corresponding output technology root')
        if not options.naming_conventions_file:
            parser.error('At least one --naming-conventions-file is required')
        if options.check and options.clean_only:
            parser.error('--check conflicts with --clean-only')
        manifest = dict(artifact='.', schema_inputs=roots, schema_input_naming_conventions=inputs,
            technology_outputs=output_dirs, technology_output_naming_conventions=roles,
            technology_enum_output_naming_conventions=enumerations,
            naming_convention_files=list(dict.fromkeys(options.naming_conventions_file)),
            languages=list(output_dirs), clean_only=options.clean_only,
            allow_unversioned_schemas=options.allow_unversioned_schemas)
        import os
        original = os.environ.get('ALGITES_DEFS_CODEGEN_SETTER_INHERITANCE_POLICY')
        if options.setter_inheritance_policy is not None:
            os.environ['ALGITES_DEFS_CODEGEN_SETTER_INHERITANCE_POLICY'] = options.setter_inheritance_policy
        try:
            results = AIcSchemaContractBindingsGenerator().generate_manifest(options.repository_root, manifest, options.check)
        finally:
            if options.setter_inheritance_policy is not None:
                if original is None:
                    os.environ.pop('ALGITES_DEFS_CODEGEN_SETTER_INHERITANCE_POLICY', None)
                else:
                    os.environ['ALGITES_DEFS_CODEGEN_SETTER_INHERITANCE_POLICY'] = original
        for item in results:
            print(item['path'])
        return 0


if __name__ == '__main__':
    raise SystemExit(AIcDefsCodegenCli.main())
