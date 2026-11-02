from __future__ import annotations

import argparse
from pathlib import Path

from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import AIcNameConventionCatalog
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
        """Load all configuration layers without rewriting qualified option names."""
        return expand_layered_settings(args, 'defscodegen', 'python', 'defs')

    @staticmethod
    def _batch(args: list[str]) -> int:
        """Parse qualified settings directly; no conversion to legacy options."""
        from contextlib import ExitStack
        from tempfile import TemporaryDirectory
        from zipfile import ZipFile
        from eu.algites.tool.codegen.common.artifact_resolver import (
            parse_artifacts, resolve_artifacts)
        import os

        root = Path.cwd()
        inputs: dict[str, str] = {}
        input_profiles: dict[str, str] = {}
        output_dirs: dict[str, str] = {}
        enumerations: dict[str, str] = {}
        method_profiles: dict[str, str] = {}
        roles: dict[str, dict[str, str]] = {}
        catalogs: list[str] = []
        artifact_lists: dict[str, str] = {}
        setter_policy = None
        check = clean = allow_unversioned = False
        targets = {'java', 'python'}
        formats = {'xmldefs', 'yamldefs', 'jsondefs'}
        known_roles = {'common', 'xmldefs_type', 'xmldefs_element', 'xmldefs_namespace', 'yamldefs', 'jsondefs'}
        for option in args:
            if option in ('--check', '--clean-only', '--allow-unversioned-schemas'):
                if option == '--check': check = True
                elif option == '--clean-only': clean = True
                else: allow_unversioned = True
                continue
            if not option.startswith('--') or '=' not in option:
                raise ValueError(f'Invalid qualified Defs option: {option}')
            key, value = option[2:].split('=', 1)
            name, *qualifiers = key.split(':')
            if name in {'repository-root', 'setter-inheritance-policy'} and not qualifiers:
                if name == 'repository-root': root = Path(value).resolve()
                else: setter_policy = value
            elif name == 'naming-conventions-file' and len(qualifiers) == 1:
                catalogs.append(value)
            elif name in {'schema-input-dir', 'input-schema-naming-convention'} and len(qualifiers) == 1 and qualifiers[0] in formats:
                (inputs if name == 'schema-input-dir' else input_profiles)[qualifiers[0]] = value
            elif name in {'technology-dointf-output-dir', 'output-enum-technology-naming-convention',
                          'generated-dataobject-method-naming-convention', 'defs-input-artifacts'} and len(qualifiers) == 1 and qualifiers[0] in targets:
                dest = {'technology-dointf-output-dir': output_dirs,
                        'output-enum-technology-naming-convention': enumerations,
                        'generated-dataobject-method-naming-convention': method_profiles,
                        'defs-input-artifacts': artifact_lists}[name]
                dest[qualifiers[0]] = value
            elif name == 'output-interface-technology-naming-convention' and len(qualifiers) == 3 and qualifiers[0] in targets and qualifiers[1] in known_roles and qualifiers[2] == 'defsintf':
                roles.setdefault(qualifiers[0], {})[qualifiers[1]] = value
            else:
                raise ValueError(f'Unrecognized or unqualified Defs option: {option}')
        if check and clean:
            raise ValueError('--check conflicts with --clean-only')
        if not catalogs:
            raise ValueError('At least one --naming-conventions-file:<id> is required')
        if not clean and (not (inputs or artifact_lists) or not output_dirs):
            raise ValueError('Select schema roots/artifacts and output technologies')
        if any(kind not in input_profiles for kind in inputs):
            raise ValueError('Each input schema directory requires a naming convention')
        if any(tech not in output_dirs for tech in roles):
            raise ValueError('Output naming role requires an output directory')
        original = os.environ.get('ALGITES_DEFS_CODEGEN_SETTER_INHERITANCE_POLICY')
        if setter_policy is not None:
            if setter_policy not in {'INHERIT_AS_GENERIC_PARAMETER', 'INHERIT_AS_FIXED_PARAMETER'}:
                raise ValueError('Invalid setter-inheritance-policy: ' + setter_policy)
            os.environ['ALGITES_DEFS_CODEGEN_SETTER_INHERITANCE_POLICY'] = setter_policy
        try:
            with ExitStack() as stack:
                # Archive inputs are copied into an owned temporary root inside
                # the repository because the generator validates containment.
                schema_roots = dict(inputs)
                if artifact_lists:
                    temp = Path(stack.enter_context(TemporaryDirectory(prefix='defs-artifacts-',
                                               dir=root / 'build' if (root / 'build').is_dir() else root)))
                    suffix_to_kind = {'.xsd': 'xmldefs', '.yamldef.schema.json': 'yamldefs',
                                      '.jsondef.schema.json': 'jsondefs'}
                    for tech, configured in artifact_lists.items():
                        specs = parse_artifacts(configured, tech)
                        for index, archive in enumerate(resolve_artifacts(specs, tech)):
                            with ZipFile(archive) as zf:
                                for member in zf.infolist():
                                    if member.is_dir(): continue
                                    kind = next((v for k, v in suffix_to_kind.items() if member.filename.endswith(k)), None)
                                    if kind is None: continue
                                    # Extraction is path-safe and deterministic; naming
                                    # includes origin to avoid collisions across archives.
                                    relative = Path(member.filename)
                                    if '..' in relative.parts or relative.is_absolute():
                                        raise ValueError(f'Unsafe schema archive member: {member.filename}')
                                    dest = temp / kind / tech / str(index) / relative
                                    dest.parent.mkdir(parents=True, exist_ok=True)
                                    dest.write_bytes(zf.read(member))
                                    # Each archive gets a separate schema root.
                                    schema_roots[f'{kind}:{tech}:{index}'] = str(temp / kind / tech / str(index))
                    if not schema_roots:
                        raise ValueError('No schemas found in selected input archives')
                roots = [{'kind': key.split(':')[0], 'directory': value} for key, value in schema_roots.items()]
                for item in roots:
                    if item['kind'] not in input_profiles:
                        raise ValueError('Missing naming convention for artifact schema kind ' + item['kind'])
                manifest = dict(artifact='.', schema_inputs=roots,
                    schema_input_naming_conventions=input_profiles,
                    technology_outputs=output_dirs,
                    technology_output_naming_conventions=roles,
                    technology_enum_output_naming_conventions=enumerations,
                    generated_dataobject_method_naming_conventions=method_profiles,
                    naming_convention_files=list(dict.fromkeys(catalogs)),
                    languages=list(output_dirs), clean_only=clean,
                    allow_unversioned_schemas=allow_unversioned)
                results = AIcSchemaContractBindingsGenerator().generate_manifest(root, manifest, check)
                for item in results:
                    print(item['path'])
        finally:
            if setter_policy is not None:
                if original is None: os.environ.pop('ALGITES_DEFS_CODEGEN_SETTER_INHERITANCE_POLICY', None)
                else: os.environ['ALGITES_DEFS_CODEGEN_SETTER_INHERITANCE_POLICY'] = original
        return 0


if __name__ == '__main__':
    raise SystemExit(AIcDefsCodegenCli.main())
