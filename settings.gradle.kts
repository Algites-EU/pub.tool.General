/* The single build-domain bootstrap; all initialization is compiled in gradleinit. */
buildscript {
    repositories {
        val locMode = providers.gradleProperty("modustro.dependencyMode")
            .orElse(providers.environmentVariable("MODUSTRO_DEPENDENCY_MODE"))
            .orElse(providers.environmentVariable("MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE"))
            .orElse("remote").get()
        val locUseLocal = locMode in setOf("local", "source", "offline") ||
            providers.gradleProperty("modustro.useMavenLocalForResolution")
                .orElse(providers.environmentVariable("MODUSTRO_USE_MAVEN_LOCAL_FOR_RESOLUTION"))
                .orNull.equals("true", ignoreCase = true)
        if (locUseLocal) {
            maven {
                name = "modustro-local"
                url = uri(providers.environmentVariable("MODUSTRO_LOCAL_MAVEN_REPOSITORY").orNull
                    ?: java.io.File(providers.environmentVariable("MODUSTRO_HOME").orNull
                        ?: java.io.File(System.getProperty("user.home"), ".modustro").path,
                        "artifact-repos/java/maven"))
                content { includeGroupByRegex("eu\\.algites(\\..*)?") }
            }
        }
        mavenCentral()
        if (locMode == "remote") {
            maven { url = uri("https://dl.cloudsmith.io/public/algites/java-snapshots-pub/maven/") }
        }
    }
    dependencies {
        classpath("eu.algites.pltf.modustro.builder:pub.gov.Algites_devops.build.modustro.builder.gradleinit:1.0-SNAPSHOT")
    }
}
apply(plugin = "eu.algites.pltf.modustro.builder.settings")
