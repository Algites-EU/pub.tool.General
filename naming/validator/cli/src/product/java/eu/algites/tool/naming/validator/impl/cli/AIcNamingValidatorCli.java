package eu.algites.tool.naming.validator.impl.cli;

import eu.algites.lib.naming.convention.impl.algites.AIcNameConventionCatalog_1;
import java.nio.file.Path;

/** CLI adapter for validating one name using a declarative NameConvention. */
public final class AIcNamingValidatorCli {
    private AIcNamingValidatorCli() { }

    /**
     * Tests one name against a YAML catalog, profile and source-structure kind.
     *
     * @param aArguments catalog YAML, profile ID, structure kind and name
     * @throws Exception when the catalog cannot be loaded
     */
    public static void main(String[] aArguments) throws Exception {
        if (aArguments.length != 4)
            throw new IllegalArgumentException("Usage: <catalog.yml> <name-convention> <source-structure-kind> <name>");
        AIcNameConventionCatalog_1 locCatalog = AIcNameConventionCatalog_1.load(Path.of(aArguments[0]));
        if (!locCatalog.matches(aArguments[1], aArguments[2], aArguments[3])) {
            System.err.println("ERROR: Invalid name for " + aArguments[1] + "/" + aArguments[2] + ": " + aArguments[3]);
            System.exit(2);
        }
    }
}
