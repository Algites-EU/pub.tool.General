from __future__ import annotations

import sys
from pathlib import Path
from eu.algites.lib.naming.convention.aic_name_convention_catalog import AIcNameConventionCatalog


class AIcNamingValidatorCli:
    """Validates structural names directly against a YAML naming convention catalog."""

    @staticmethod
    def main(args: list[str] | None = None) -> int:
        arguments = list(sys.argv[1:] if args is None else args)
        if len(arguments) != 4:
            raise SystemExit('Usage: <catalog.yml> <name-convention> <source-structure-kind> <name>')
        catalog = AIcNameConventionCatalog.load(Path(arguments[0]))
        if catalog.matches(arguments[1], arguments[2], arguments[3]):
            return 0
        print(f'ERROR: Invalid name for {arguments[1]}/{arguments[2]}: {arguments[3]}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(AIcNamingValidatorCli.main())
