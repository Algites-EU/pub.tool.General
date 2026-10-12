"""Generate SmartDataObject implementations from imported DO contracts.

Both the legacy single-contract CLI and the new YAML-profile-driven batch CLI
are supported.  The native Python CLI never invokes Java.
"""
from __future__ import annotations

import argparse
import importlib
from pathlib import Path
import sys

from eu.algites.lib.naming.convention.aic_name_convention_catalog import AIcNameConventionCatalog
from eu.algites.tool.codegen.sdo.aic_sdo_codegen_service import AIcSdoCodegenService


def _write(root, item, check):
    output = (root / item.relative_path).resolve()
    if not output.is_relative_to(root):
        raise ValueError('Generated output escapes its target root')
    if check:
        if not output.is_file() or output.read_text(encoding='utf-8') != item.source:
            raise ValueError('Missing or outdated generated SDO output: ' + str(output))
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        if not output.is_file() or output.read_text(encoding='utf-8') != item.source:
            output.write_text(item.source, encoding='utf-8')
    print(output)


def main(args=None):
    arguments = list(args) if args is not None else sys.argv[1:]
    if any(arg.startswith('--technology-') or arg == '--clean-only' for arg in arguments):
        return _batch(arguments)
    parser = argparse.ArgumentParser(description='Generate AIigd and AIcgd from an imported AIig contract')
    parser.add_argument('contract', help='Qualified module:class name')
    parser.add_argument('mutable_root', type=Path)
    parser.add_argument('implementation_root', type=Path)
    parser.add_argument('--marker', default='d')
    parser.add_argument('--check', action='store_true')
    options = parser.parse_args(arguments)
    module, name = options.contract.rsplit(':', 1)
    read_contract = getattr(importlib.import_module(module), name)
    mutable = options.mutable_root.absolute().resolve()
    implementation = options.implementation_root.absolute().resolve()
    if mutable == implementation:
        raise ValueError('Mutable interfaces and implementations require separate roots')
    result = AIcSdoCodegenService().generate(read_contract, options.marker)
    for root, item in ((mutable, result.mutable_interface), (implementation, result.implementation)):
        _write(root, item, options.check)
    return 0


def _batch(arguments: list[str]) -> int:
    parser = argparse.ArgumentParser(description='Generate SDO sources from YAML-profile-managed DO contract roots')
    parser.add_argument('--technology-dointf-input-dir', action='append', default=[])
    parser.add_argument('--technology-dointf-input-naming-profile', action='append', default=[])
    parser.add_argument('--technology-sdointf-output-dir', action='append', default=[])
    parser.add_argument('--technology-sdointf-output-naming-profile', action='append', default=[])
    parser.add_argument('--technology-sdoimpl-output-dir', action='append', default=[])
    parser.add_argument('--technology-sdoimpl-output-naming-profile', action='append', default=[])
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--clean-only', action='store_true')
    options = parser.parse_args(arguments)

    def group(values, label):
        result = {}
        for entry in values:
            kind, sep, path = entry.partition(':')
            if sep != ':' or kind != 'python' or not path:
                parser.error(f'Python SDO CLI expects python:path in {label}, got {entry!r}')
            if kind in result:
                parser.error('Duplicate ' + label)
            result[kind] = Path(path).resolve()
        return result

    input_roots = group(options.technology_dointf_input_dir, 'dointf input directory')
    input_profiles = group(options.technology_dointf_input_naming_profile, 'dointf input profile')
    mutable_roots = group(options.technology_sdointf_output_dir, 'sdointf output directory')
    mutable_profiles = group(options.technology_sdointf_output_naming_profile, 'sdointf output profile')
    implementation_roots = group(options.technology_sdoimpl_output_dir, 'sdoimpl output directory')
    implementation_profiles = group(options.technology_sdoimpl_output_naming_profile, 'sdoimpl output profile')
    if set(mutable_roots) != set(mutable_profiles) or set(implementation_roots) != set(implementation_profiles):
        parser.error('Each SDO output root must have a matching naming catalog')
    if not mutable_roots or not implementation_roots:
        parser.error('Both sdointf and sdoimpl output roles are required')
    if not options.clean_only and (set(input_roots) != set(input_profiles) or not input_roots):
        parser.error('Each DO input root requires a matching naming catalog')
    if options.clean_only and options.check:
        parser.error('--clean-only cannot be combined with --check')

    mutable_root, concrete_root = mutable_roots['python'], implementation_roots['python']
    mutable_cat = AIcNameConventionCatalog.load(mutable_profiles['python'])
    concrete_cat = AIcNameConventionCatalog.load(implementation_profiles['python'])
    role_mut = 'algites-python-gen-data-intf-versioned'
    role_impl = 'algites-python-gen-data-class-versioned'
    if not options.check:
        mutable_cat.clean(mutable_root, {role_mut})
        concrete_cat.clean(concrete_root, {role_impl})
    if options.clean_only:
        return 0
    do_root = input_roots['python']
    input_cat = AIcNameConventionCatalog.load(input_profiles['python'])
    input_role = 'algites-python-gen-intf-versioned'
    if not do_root.is_dir():
        raise ValueError('DO input directory does not exist: ' + str(do_root))
    if str(do_root) not in sys.path:
        sys.path.insert(0, str(do_root))
    for source in sorted(do_root.rglob('*.py')):
        found = input_cat.recognize_filename(source.name, {input_role})
        if found is None:
            continue
        rel = source.relative_to(do_root).with_suffix('')
        module_name = '.'.join(rel.parts)
        module = importlib.import_module(module_name)
        class_name = input_cat.format(input_role, 'main_container_name', found.variables, 'lower_snake_case')
        read_contract = getattr(module, class_name)
        generated = AIcSdoCodegenService().generate(read_contract, naming=(input_cat, mutable_cat, concrete_cat))
        if mutable_cat.recognize_filename(Path(generated.mutable_interface.relative_path).name, {role_mut}) is None:
            raise ValueError('Generated mutable type violates output naming convention: ' + generated.mutable_interface.relative_path)
        if concrete_cat.recognize_filename(Path(generated.implementation.relative_path).name, {role_impl}) is None:
            raise ValueError('Generated concrete type violates output naming convention: ' + generated.implementation.relative_path)
        _write(mutable_root, generated.mutable_interface, options.check)
        _write(concrete_root, generated.implementation, options.check)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
