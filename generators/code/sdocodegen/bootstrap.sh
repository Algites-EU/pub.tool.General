#!/usr/bin/env bash
set -euo pipefail

locModuleDirectory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
locRepositoryDirectory="$(cd -- "${locModuleDirectory}/../../.." && pwd)"
locBootstrapDirectory="$(mktemp -d "${TMPDIR:-/tmp}/modustro-sdocodegen-bootstrap.XXXXXXXX")"
trap 'rm -rf -- "${locBootstrapDirectory}"' EXIT

# Bootstrap without loading the self-hosting Builder conventions.
cat > "${locBootstrapDirectory}/settings.gradle" <<'GRADLE'
rootProject.name = 'modustro-sdocodegen-bootstrap'
include 'intf', 'impl', 'cli'
['intf', 'impl', 'cli'].each { name ->
    project(":" + name).projectDir = new File(System.getenv('_TMP_MODUSTRO_SDO_MODULE'), name)
}
GRADLE
cat > "${locBootstrapDirectory}/build.gradle" <<'GRADLE'
subprojects {
    apply plugin: 'java-library'
    apply plugin: 'maven-publish'
    group = 'eu.algites.tool.codegen'
    version = providers.gradleProperty('modustro.sdocodegen.version').getOrElse('1.1-SNAPSHOT')
    repositories {
        mavenLocal()
        mavenCentral()
        maven { url = 'https://dl.cloudsmith.io/public/algites/java-snapshots-pub/maven/' }
    }
    java { toolchain { languageVersion = JavaLanguageVersion.of(17) }; withSourcesJar() }
    sourceSets {
        main { java.srcDirs = ['src/product/java'] }
        test { java.srcDirs = ['src/develop/java'] }
    }
    tasks.withType(Test).configureEach { useTestNG() }
    publishing {
        publications {
            mavenJava(MavenPublication) {
                from components.java
                artifactId = 'pub.tool.General_generators.code.sdocodegen.' + project.name
            }
        }
    }
}
project(':intf') {
    dependencies { api 'eu.algites.lib.data:pub.lib.General_data.dataobject.intf:1.1-SNAPSHOT' }
}
project(':impl') {
    dependencies {
        api project(':intf')
        api 'eu.algites.lib.data:pub.lib.General_data.smartdataobject.impl:1.1-SNAPSHOT'
        testImplementation 'org.testng:testng:7.11.0'
    }
}
project(':cli') { dependencies { implementation project(':impl') } }

/* SDO native Python regressions also run when bootstrapped outside the repository build. */
def module = new File(System.getenv('_TMP_MODUSTRO_SDO_MODULE'))
def sdoPython = rootProject.layout.buildDirectory.dir('sdo-parity/python-dependencies')
def prepareSdoPython = tasks.register('prepareSdoPython', Exec) {
    commandLine(System.getenv('ALGITES_PYTHON_EXECUTABLE') ?: 'python3',
        new File(module, '../defscodegen/prepare_parity_python.py').canonicalPath,
        '--target', sdoPython.get().asFile.absolutePath,
        '--endpoints-json', '["pypi\\thttps://pypi.org/simple\\t\\t","snapshots\\thttps://dl.cloudsmith.io/public/algites/python-snapshots-pub/python/simple/\\t\\t"]',
        '--requirement', 'pytest>=8,<10',
        '--requirement', 'eu-algites-lib-data-pub-lib-general-data-dataobject-intf>=1.1.dev0,<1.1a0',
        '--requirement', 'eu-algites-lib-data-pub-lib-general-data-smartdataobject-impl>=1.1.dev0,<1.1a0')
}
project(':impl').tasks.withType(Test).configureEach {
    dependsOn prepareSdoPython
    environment 'MODUSTRO_SDO_PYTHON_DEPENDENCIES', sdoPython.get().asFile.absolutePath
}
GRADLE
locGradleCommand=(bash "${locRepositoryDirectory}/gradlew")
if [[ -n "${MODUSTRO_GRADLE_EXECUTABLE:-}" ]]; then locGradleCommand=("${MODUSTRO_GRADLE_EXECUTABLE}"); fi
if [[ $# -eq 0 ]]; then set -- test publishToMavenLocal; fi
_TMP_MODUSTRO_SDO_MODULE="${locModuleDirectory}" "${locGradleCommand[@]}" --no-daemon --project-dir "${locBootstrapDirectory}" "$@"
