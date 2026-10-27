/* Local builds use the adjacent, actual governance checkout instead of GitHub main. */
val locMode = System.getenv("MODUSTRO_DEPENDENCY_MODE")
    ?: System.getenv("MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE") ?: "remote"
val locUseLocalGovernance = locMode in setOf("local", "source", "offline")
val locGovernanceDirectory = file(System.getenv("MODUSTRO_GOVERNANCE_SOURCE_DIR")
    ?: file("../pub.gov.Algites").absolutePath)
val locSharedBuildScript = file("gradle/tool/repository/modustro-root-build.gradle.kts")
val locAdjacentBuildScript = locGovernanceDirectory.resolve("gradle/tool/repository/modustro-root-build.gradle.kts")
when {
    locSharedBuildScript.isFile -> apply(from = locSharedBuildScript)
    locUseLocalGovernance -> {
        require(locAdjacentBuildScript.isFile) {
            "Local Modustro build requires local governance Gradle conventions: $locAdjacentBuildScript"
        }
        apply(from = locAdjacentBuildScript)
    }
    else -> apply(from = uri("https://raw.githubusercontent.com/Algites-EU/pub.gov.Algites/${System.getenv("MODUSTRO_PUBLIC_GOVERNANCE_REVISION") ?: "main"}/gradle/tool/repository/modustro-root-build.gradle.kts"))
}
