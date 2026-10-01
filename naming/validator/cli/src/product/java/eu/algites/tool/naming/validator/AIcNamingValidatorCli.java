package eu.algites.tool.naming.validator;

import eu.algites.lib.naming.validation.AIcAlgitesConventionProfiles;
import eu.algites.lib.naming.validation.AIcdConventionViolation;
import eu.algites.lib.naming.validation.AIcDefaultConventionValidator;
import eu.algites.lib.naming.validation.AInConventionSubject;


import java.util.List;

/** Command-line adapter for validating one governed name. */
public final class AIcNamingValidatorCli {
    private AIcNamingValidatorCli() {
    }

    /**
     * Validates one name with the strict Algites convention profile.
     *
     * @param args convention subject and value
     */
    public static void main(String[] args) {
        if (args.length != 2) {
            throw new IllegalArgumentException("Usage: <CONVENTION_SUBJECT> <value>");
        }
        AInConventionSubject subject = AInConventionSubject.valueOf(args[0]);
        List<AIcdConventionViolation> findings = new AIcDefaultConventionValidator().validateName(subject, args[1], AIcAlgitesConventionProfiles.strict());
        for (AIcdConventionViolation finding : findings) System.err.println(finding.reaction() + ": " + finding.message() + " value=" + finding.value());
        if (findings.stream().anyMatch(finding -> finding.reaction().name().equals("ERROR"))) System.exit(2);
    }
}
