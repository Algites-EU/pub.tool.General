"""Run schema-independent SDO generation into separate mutable and concrete roots."""
import argparse
import importlib
from pathlib import Path
from eu.algites.tool.codegen.sdo.aic_sdo_codegen_service import AIcSdoCodegenService


def main(args=None):
    parser = argparse.ArgumentParser(description='Generate AIigd and AIcgd from imported AIig contracts')
    parser.add_argument('contract', help='Qualified module:class name')
    parser.add_argument('mutable_root', type=Path)
    parser.add_argument('implementation_root', type=Path)
    parser.add_argument('--marker', default='d')
    parser.add_argument('--check', action='store_true')
    options = parser.parse_args(args)
    module, name = options.contract.rsplit(':', 1)
    read_contract = getattr(importlib.import_module(module), name)
    mutable = options.mutable_root.absolute().resolve()
    implementation = options.implementation_root.absolute().resolve()
    if mutable == implementation:
        raise ValueError('Mutable interfaces and implementations require separate roots')
    result = AIcSdoCodegenService().generate(read_contract, options.marker)
    for root, item in ((mutable, result.mutable_interface), (implementation, result.implementation)):
        output = (root / item.relative_path).resolve()
        if not output.is_relative_to(root):
            raise ValueError('Generated output escapes its target root')
        if options.check:
            if not output.is_file() or output.read_text(encoding='utf-8') != item.source:
                raise ValueError('Missing or outdated generated SDO output: ' + str(output))
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            if not output.is_file() or output.read_text(encoding='utf-8') != item.source:
                output.write_text(item.source, encoding='utf-8')
        print(output)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
