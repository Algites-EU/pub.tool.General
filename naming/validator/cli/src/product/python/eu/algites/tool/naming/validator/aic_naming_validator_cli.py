from __future__ import annotations

import sys

from eu.algites.lib.naming.validation.aic_algites_convention_profiles import AIcAlgitesConventionProfiles
from eu.algites.lib.naming.validation.aic_default_convention_validator import AIcDefaultConventionValidator
from eu.algites.lib.naming.validation.ain_convention_subject import AInConventionSubject


class AIcNamingValidatorCli:
    """Provides the command-line adapter for strict Algites naming validation."""

    @staticmethod
    def main(args: list[str] | None = None) -> int:
        """Run the command-line entry point."""
        arguments = list(sys.argv[1:] if args is None else args)
        if len(arguments) != 2:
            raise SystemExit("Usage: <CONVENTION_SUBJECT> <value>")
        findings = AIcDefaultConventionValidator().validate_name(
            AInConventionSubject[arguments[0]], arguments[1], AIcAlgitesConventionProfiles.strict()
        )
        for finding in findings:
            print(f"{finding.reaction.value}: {finding.message} value={finding.value}", file=sys.stderr)
        return 2 if any(finding.reaction.value == "ERROR" for finding in findings) else 0


if __name__ == "__main__":
    raise SystemExit(AIcNamingValidatorCli.main())
