#!/usr/bin/env bash
set -euo pipefail

locModuleDir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
locRepositoryDir="$(cd -- "${locModuleDir}/../../.." && pwd)"
locBootstrapDir="$(mktemp -d "${TMPDIR:-/tmp}/modustro-defscodegen-bootstrap.XXXXXXXX")"
trap 'rm -rf -- "${locBootstrapDir}"' EXIT

# Break the self-hosting dependency: build the generator without loading repository conventions that use it.
cat > "${locBootstrapDir}/settings.gradle" <<'GRADLE'
rootProject.name = 'modustro-defscodegen-bootstrap'
include 'coreintf', 'coreimpl', 'cli'
['coreintf', 'coreimpl', 'cli'].each { name ->
    project(":" + name).projectDir = new File(System.getenv('_TMP_MODUSTRO_DEFS_MODULE'), name)
}
GRADLE
cat > "${locBootstrapDir}/build.gradle" <<'GRADLE'
subprojects {
    apply plugin: 'java-library'
    apply plugin: 'maven-publish'
    group = 'eu.algites.tool.codegen'
    version = providers.gradleProperty('modustro.defscodegen.version').getOrElse('1.0-SNAPSHOT')
    repositories {
        mavenLocal()
        mavenCentral()
        maven { url = 'https://dl.cloudsmith.io/public/algites/java-snapshots-pub/maven/' }
    }
    java { toolchain { languageVersion = JavaLanguageVersion.of(17) }; withSourcesJar() }
    sourceSets {
        main { java.srcDirs = ['src/product/java'] }
        test {
            java.srcDirs = ['src/develop/java']
            resources.srcDirs = ['src/develop/yamldefs', 'src/develop/jsondefs', 'src/develop/examples']
        }
    }
    tasks.withType(Test).configureEach { useTestNG() }
    publishing {
        publications {
            mavenJava(MavenPublication) {
                from components.java
                artifactId = 'pub.tool.General_generators.code.defscodegen.' + project.name
            }
        }
    }
}
project(':coreintf') {
    dependencies { api 'eu.algites.lib.naming:pub.lib.General_naming.convention.coreintf:1.0-SNAPSHOT' }
}
project(':coreimpl') {
    dependencies {
        api project(':coreintf')
        api 'eu.algites.lib.naming:pub.lib.General_naming.conversion.coreintf:1.0-SNAPSHOT'
        implementation 'eu.algites.lib.naming:pub.lib.General_naming.conversion.coreimpl:1.0-SNAPSHOT'
        implementation 'com.fasterxml.jackson.core:jackson-databind:2.18.3'
        implementation 'com.fasterxml.jackson.dataformat:jackson-dataformat-yaml:2.18.3'
        testImplementation 'org.testng:testng:7.11.0'
        testImplementation 'eu.algites.lib.naming:pub.lib.General_naming.convention.coreimpl:1.0-SNAPSHOT'
    }
}
project(':cli') {
    dependencies {
        implementation project(':coreimpl')
        implementation 'eu.algites.lib.naming:pub.lib.General_naming.convention.coreimpl:1.0-SNAPSHOT'
    }
}
GRADLE

locGradleCommand=(bash "${locRepositoryDir}/gradlew")
if [[ -n "${MODUSTRO_GRADLE_EXECUTABLE:-}" ]]; then locGradleCommand=("${MODUSTRO_GRADLE_EXECUTABLE}"); fi
if [[ $# -eq 0 ]]; then set -- test publishToMavenLocal; fi
_TMP_MODUSTRO_DEFS_MODULE="${locModuleDir}" "${locGradleCommand[@]}" --no-daemon --project-dir "${locBootstrapDir}" "$@"
