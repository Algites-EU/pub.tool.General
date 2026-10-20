from __future__ import annotations

import argparse
from pathlib import Path

from eu.algites.lib.naming.convention.impl.algites.aic_name_convention_catalog_1 import AIcNameConventionCatalog_1
from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import AIcSchemaContractBindingsGenerator


class AIcDefsCodegenCli:
    """CLI adapter for single-source compatibility and YAML-driven batch generation."""

    @staticmethod
    def main(args: list[str] | None = None) -> int:
        """Generate from a named settings file or from explicit semantic-role arguments."""
        import sys
        args = list(sys.argv[1:] if args is None else args)
        if not args or any(arg.startswith('--settings-file') for arg in args):
            args = AIcDefsCodegenCli._expand_settings(args)
        return AIcDefsCodegenCli._batch(args)

    @staticmethod
    def _expand_settings(args: list[str]) -> list[str]:
        """Expand line-oriented --settings-file; explicit CLI mappings override file mappings."""
        import shlex
        path = None
        rest = []
        for value in args:
            if value.startswith('--settings-file='):
                if path is not None:
                    raise ValueError('--settings-file may be specified only once')
                path = Path(value.partition('=')[2])
            else:
                rest.append(value)
        if path is None and not rest:
            name = 'algites-defscodegen-python-default.settings'
            path = Path.cwd() / 'generators/code/defscodegen/intf/src/product/config/eu/algites/tool/codegen/defs' / name
            if not path.is_file():
                from importlib import resources
                content = None
                for provider in ('eu.algites.tool.codegen.defs',
                                 'algites.pub.tool.general.generators.code.defscodegen.intf'):
                    try:
                        candidate = resources.files(provider).joinpath(
                            *(['eu', 'algites', 'tool', 'codegen', 'defs', name]
                              if provider.startswith('algites.') else [name]))
                        if candidate.is_file():
                            content = candidate.read_text(encoding='utf-8')
                            break
                    except (ModuleNotFoundError, FileNotFoundError, TypeError):
                        continue
                if content is None:
                    raise FileNotFoundError('Packaged default Defs settings are unavailable: ' + name)
            else:
                content = path.read_text(encoding='utf-8')
        elif path is not None:
            content = path.read_text(encoding='utf-8')
        else:
            return rest
        settings = []
        for number, line in enumerate(content.splitlines(), 1):
            parts = shlex.split(line, comments=True)
            if not parts:
                continue
            if len(parts) != 1 or not parts[0].startswith('--') or parts[0].startswith('--settings-file'):
                raise ValueError(f'Invalid settings option at line {number}: {line}')
            settings.append(parts[0])
        return settings + rest

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
        parser.add_argument('--check', action='store_true')
        parser.add_argument('--clean-only', action='store_true')
        parser.add_argument('--allow-unversioned-schemas', action='store_true')
        options = parser.parse_args(args)
        valid_inputs = {'xmldefs', 'yamldefs', 'jsondefs'}
        valid_targets = {'java', 'python'}
        valid_roles = {'common', 'xmldefs_type', 'xmldefs_element', 'yamldefs', 'jsondefs'}

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
        results = AIcSchemaContractBindingsGenerator().generate_manifest(options.repository_root, manifest, options.check)
        for item in results:
            print(item['path'])
        return 0


if __name__ == '__main__':
    raise SystemExit(AIcDefsCodegenCli.main())
