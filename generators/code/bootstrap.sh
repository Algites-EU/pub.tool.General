#!/usr/bin/env bash
set -euo pipefail

# Independent emergency bootstrap for both source-code generators.
# The generated Gradle projects deliberately do not apply Modustro conventions.
locCodeDirectory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
locRepositoryDirectory="$(cd -- "$locCodeDirectory/../.." && pwd -P)"
# Every standalone Gradle project, compiled class, test result and staging file
# belongs under the repository's single root build directory.
# Preserve old invocations while making their intent explicit and consistent.
if [[ -z "${MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE:-}" && "${MODUSTRO_BOOTSTRAP_REFRESH_GENERAL_DATAOBJECT:-0}" == 1 ]]; then
    export MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE=source
    echo "Legacy MODUSTRO_BOOTSTRAP_REFRESH_GENERAL_DATAOBJECT=1 selects source mode" >&2
fi
# All standalone bootstraps share the same dependency precedence policy.
# remote: published Cloudsmith snapshot first, Maven Local only as fallback;
# local: Maven Local first; source: source-prepared Maven Local first.
locDependencyMode="${MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE:-remote}"
case "$locDependencyMode" in
    remote|local|source) ;;
    *) echo "Invalid MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE='$locDependencyMode' (remote|local|source)" >&2; exit 2 ;;
esac
export MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE="$locDependencyMode"
echo "Bootstrap dependency mode: $locDependencyMode"
locBuildRoot="$locRepositoryDirectory/build/run/codegen-bootstrap"
mkdir -p "$locBuildRoot/work"
locTemporaryDirectory="$(mktemp -d "$locBuildRoot/work/launcher.XXXXXXXX")"
# Keep Python bytecode and pytest caches out of the checked-out source tree.
export PYTHONDONTWRITEBYTECODE=1
export PYTEST_ADDOPTS="${PYTEST_ADDOPTS:+${PYTEST_ADDOPTS} }-p no:cacheprovider"
trap 'rm -rf -- "$locTemporaryDirectory"' EXIT
# Optionally republish the actual library contracts from a sibling checkout before
# compiling tool generators. A stale 1.1-SNAPSHOT JAR may resolve successfully while
# lacking newly introduced field-presence and XML-representation API types.
if [[ "$locDependencyMode" == source || "${MODUSTRO_BOOTSTRAP_REFRESH_GENERAL_DATAOBJECT:-0}" == 1 ]]; then
    locGeneralDirectory="${MODUSTRO_BOOTSTRAP_GENERAL_SOURCE_DIR:-$(dirname -- "$locRepositoryDirectory")/pub.lib.General}"
    locGeneralDirectory="$(cd -- "$locGeneralDirectory" && pwd -P)" || {
        echo "pub.lib.General source checkout is required for the optional dependency refresh" >&2
        exit 2
    }
    for locRequiredSource in \
        'factory/cpdiscovery/intf/src/product/java/eu/algites/lib/factory/cpdiscovery/AIiCategoryProviderFactory.java' \
        'data/dataobject/intf/src/product/java/eu/algites/lib/data/dataobject/AInFieldPresenceKind.java' \
        'data/dataobject/intf/src/product/java/eu/algites/lib/data/dataobject/xmldefs/AInXmlValueKind.java' \
        'naming/convention/intf/src/product/java/eu/algites/lib/naming/convention/AIiNameConventionCatalog.java' \
        'naming/convention/algites/src/product/java/eu/algites/lib/naming/convention/impl/algites/AIcNameConventionCatalog_1.java' \
        'naming/convention/algites/src/product/config/eu/algites/lib/naming/convention/algites-java-name-conventions.yml'; do
        [[ -f "$locGeneralDirectory/$locRequiredSource" ]] || {
            echo "Required current pub.lib.General source is missing: $locGeneralDirectory/$locRequiredSource" >&2
            exit 2
        }
    done
    for locRequiredModule in factory/cpdiscovery/impl common text/format data/smartdataobject/intf data/smartdataobject/impl; do
        [[ -d "$locGeneralDirectory/$locRequiredModule/src/product/java" ]] || {
            echo "Missing source module: $locGeneralDirectory/$locRequiredModule" >&2; exit 2;
        }
    done
    locGeneralBootstrapDirectory="$(mktemp -d "$locBuildRoot/work/general-dataobject.XXXXXXXX")"
    # The temporary Gradle settings/build scripts and all outputs remain in the
    # tool repository root build directory; source directories stay read-only.
    cat > "$locGeneralBootstrapDirectory/settings.gradle" <<'GENERAL_SETTINGS'
rootProject.name = 'modustro-general-dependencies-bootstrap'
def modules = [
    'factory-intf': 'factory/cpdiscovery/intf',
    'factory-impl': 'factory/cpdiscovery/impl',
    'common': 'common',
    'text-format': 'text/format',
    'dataobject-intf': 'data/dataobject/intf',
    'smartdataobject-intf': 'data/smartdataobject/intf',
    'smartdataobject-impl': 'data/smartdataobject/impl',
    'naming-intf': 'naming/convention/intf',
    'naming-algites': 'naming/convention/algites'
]
modules.each { name, path ->
    include ':' + name
    project(':' + name).projectDir = new File(System.getenv('MODUSTRO_BOOTSTRAP_GENERAL_SOURCE_DIR'), path)
}
GENERAL_SETTINGS
    cat > "$locGeneralBootstrapDirectory/build.gradle" <<'GENERAL_BUILD'
def outputRoot = new File(System.getenv('MODUSTRO_BOOTSTRAP_BUILD_ROOT'), 'gradle/general-dataobject')
layout.buildDirectory.set(new File(outputRoot, 'root'))
subprojects {
    layout.buildDirectory.set(new File(outputRoot, 'modules/' + project.name))
    apply plugin: 'java-library'
    apply plugin: 'maven-publish'
    version = '1.1-SNAPSHOT'
    java { toolchain { languageVersion = JavaLanguageVersion.of(17) }; withSourcesJar() }
    sourceSets.main.java.srcDirs = ['src/product/java']
    publishing {
        publications {
            mavenJava(MavenPublication) {
                from components.java
                artifactId = [
                    'factory-intf': 'pub.lib.General_factory.cpdiscovery.intf',
                    'factory-impl': 'pub.lib.General_factory.cpdiscovery.impl',
                    'common': 'pub.lib.General_common',
                    'text-format': 'pub.lib.General_text.format',
                    'dataobject-intf': 'pub.lib.General_data.dataobject.intf',
                    'smartdataobject-intf': 'pub.lib.General_data.smartdataobject.intf',
                    'smartdataobject-impl': 'pub.lib.General_data.smartdataobject.impl',
                    'naming-intf': 'pub.lib.General_naming.convention.intf',
                    'naming-algites': 'pub.lib.General_naming.convention.algites'
                ][project.name]
            }
        }
    }
}
project(':factory-intf') { group = 'eu.algites.lib.common' }
project(':factory-impl') {
    group = 'eu.algites.lib.common'
    dependencies { api project(':factory-intf') }
}
project(':common') {
    group = 'eu.algites.lib.common'
    dependencies {
        api project(':factory-intf')
        implementation 'jakarta.annotation:jakarta.annotation-api:3.0.0'
        compileOnly 'org.jetbrains:annotations:26.0.2'
    }
}
project(':text-format') { group = 'eu.algites.lib.text' }
project(':smartdataobject-intf') {
    group = 'eu.algites.lib.data'
    dependencies {
        api project(':common')
        api project(':dataobject-intf')
        api project(':text-format')
    }
}
project(':smartdataobject-impl') {
    group = 'eu.algites.lib.data'
    dependencies {
        api project(':smartdataobject-intf')
        api project(':text-format')
        implementation project(':common')
        implementation project(':factory-impl')
    }
}
project(':naming-intf') {
    group = 'eu.algites.lib.naming'
    dependencies { api project(':dataobject-intf') }
}
project(':naming-algites') {
    group = 'eu.algites.lib.naming'
    sourceSets.main.resources.srcDirs = ['src/product/config', 'src/product/resources']
    repositories { mavenCentral() }
    dependencies {
        api project(':naming-intf')
        implementation 'com.fasterxml.jackson.core:jackson-databind:2.18.3'
        implementation 'com.fasterxml.jackson.dataformat:jackson-dataformat-yaml:2.18.3'
    }
}
project(':dataobject-intf') {
    group = 'eu.algites.lib.data'
    dependencies { api project(':factory-intf') }
}
GENERAL_BUILD
    locGeneralGradleCommand=(bash "$locRepositoryDirectory/gradlew")
    if [[ -n "${MODUSTRO_GRADLE_EXECUTABLE:-}" ]]; then
        locGeneralGradleCommand=("${MODUSTRO_GRADLE_EXECUTABLE}")
    fi
    echo "Refreshing pub.lib.General bootstrap dependency graph (9 artifacts including common and smartdataobject) from $locGeneralDirectory"
    MODUSTRO_BOOTSTRAP_GENERAL_SOURCE_DIR="$locGeneralDirectory" \
    MODUSTRO_BOOTSTRAP_BUILD_ROOT="$locBuildRoot" \
        "${locGeneralGradleCommand[@]}" --no-daemon --project-dir "$locGeneralBootstrapDirectory" publishToMavenLocal
    rm -rf -- "$locGeneralBootstrapDirectory"
fi

cat > "$locTemporaryDirectory/defs.sh" <<'MODUSTRO_DEFS_BOOTSTRAP'
#!/usr/bin/env bash
set -euo pipefail

locModuleDir="${MODUSTRO_BOOTSTRAP_MODULE_DIRECTORY:?}"
locRepositoryDir="${MODUSTRO_BOOTSTRAP_REPOSITORY_DIRECTORY:?}"
locBuildRoot="${MODUSTRO_BOOTSTRAP_BUILD_ROOT:?}"
locBootstrapDir="$(mktemp -d "$locBuildRoot/work/defscodegen.XXXXXXXX")"
trap 'rm -rf -- "${locBootstrapDir}"' EXIT

# Break the self-hosting dependency: build the generator without loading repository conventions that use it.
cat > "${locBootstrapDir}/settings.gradle" <<'GRADLE'
rootProject.name = 'modustro-defscodegen-bootstrap'
include 'intf', 'impl', 'cli'
['intf', 'impl', 'cli'].each { name ->
    project(":" + name).projectDir = new File(System.getenv('_TMP_MODUSTRO_DEFS_MODULE'), name)
}
GRADLE
cat > "${locBootstrapDir}/build.gradle" <<'GRADLE'
def locBootstrapOutput = new File(System.getenv('MODUSTRO_BOOTSTRAP_BUILD_ROOT'), 'gradle/defscodegen')
layout.buildDirectory.set(new File(locBootstrapOutput, 'root'))
subprojects {
    layout.buildDirectory.set(new File(locBootstrapOutput, 'modules/' + project.name))
    apply plugin: 'java-library'
    apply plugin: 'maven-publish'
    group = 'eu.algites.tool.codegen'
    version = providers.gradleProperty('modustro.defscodegen.version').getOrElse('1.1-SNAPSHOT')
    repositories {
        def bootstrapMode = System.getenv('MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE') ?: 'remote'
        if (bootstrapMode != 'remote') mavenLocal()
        maven {
            url = uri('https://dl.cloudsmith.io/public/algites/java-snapshots-pub/maven/')
            content { includeGroupByRegex('eu\\.algites\\..*') }
        }
        mavenCentral()
        if (bootstrapMode == 'remote') mavenLocal()
    }
    java { toolchain { languageVersion = JavaLanguageVersion.of(17) }; withSourcesJar() }
    sourceSets {
        main { java.srcDirs = ['src/product/java']; resources.srcDirs = ['src/product/resources'] }
        test {
            java.srcDirs = ['src/develop/java']
            resources.srcDirs = ['src/develop/yamldefs', 'src/develop/jsondefs', 'src/develop/xmldefs', 'src/develop/examples']
        }
    }
    tasks.withType(Test).configureEach {
        useTestNG()
        testLogging {
            exceptionFormat = 'full'
            events 'failed', 'standardError'
        }
    }
    publishing {
        publications {
            mavenJava(MavenPublication) {
                from components.java
                artifactId = 'pub.tool.General_generators.code.defscodegen.' + project.name
            }
        }
    }
}
project(':intf') {
    dependencies {
        api 'eu.algites.lib.naming:pub.lib.General_naming.convention.intf:1.1-SNAPSHOT'
        api 'eu.algites.lib.data:pub.lib.General_data.dataobject.intf:1.1-SNAPSHOT'
    }
}
project(':impl') {
    dependencies {
        api project(':intf')
        api 'eu.algites.lib.data:pub.lib.General_data.dataobject.intf:1.1-SNAPSHOT'
        api 'eu.algites.lib.common:pub.lib.General_common:1.1-SNAPSHOT'
        implementation 'com.fasterxml.jackson.core:jackson-databind:2.18.3'
        implementation 'com.fasterxml.jackson.dataformat:jackson-dataformat-yaml:2.18.3'
        testImplementation 'org.testng:testng:7.11.0'
        implementation 'eu.algites.lib.naming:pub.lib.General_naming.convention.algites:1.1-SNAPSHOT'
    }
}
project(':cli') {
    dependencies {
        implementation project(':impl')
        implementation 'com.fasterxml.jackson.core:jackson-databind:2.18.3'
        implementation 'eu.algites.lib.naming:pub.lib.General_naming.convention.algites:1.1-SNAPSHOT'
    }
}

// Fail before Java compilation when a resolvable snapshot lacks required 1.1 API.
// This checks the actual resolved artifact, not merely its Maven version string.
def verifyDataObjectDependency = tasks.register('verifyDataObjectDependency') {
    doLast {
        def artifact = project(':intf').configurations.compileClasspath.resolvedConfiguration.resolvedArtifacts.findAll {
            it.moduleVersion.id.name == 'pub.lib.General_data.dataobject.intf'
        }
        if (artifact.size() != 1) {
            throw new GradleException("Expected one pub.lib.General_data.dataobject.intf artifact on bootstrap classpath; found ${artifact.size()}")
        }
        def archive = artifact[0].file
        def requiredClasses = [
            'eu/algites/lib/data/dataobject/AInFieldPresenceKind.class',
            'eu/algites/lib/data/dataobject/xmldefs/AInXmlValueKind.class'
        ]
        def missing = []
        new java.util.zip.ZipFile(archive).withCloseable { zip ->
            missing = requiredClasses.findAll { zip.getEntry(it) == null }
        }
        if (!missing.isEmpty()) {
            throw new GradleException("Incompatible pub.lib.General_data.dataobject.intf:1.1-SNAPSHOT: "
                + "${archive} is missing ${missing}. Republish current pub.lib.General data/dataobject/intf "
                + "to Maven Local, or rerun generators/code/bootstrap.sh with "
                + "MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE=source and a sibling pub.lib.General checkout.")
        }
        logger.lifecycle("Bootstrap data-object API verified: ${archive}")
    }
}
project(':intf').tasks.named('compileJava') { dependsOn verifyDataObjectDependency }

// Bootstrap mirrors the native naming dependencies while bypassing generated project metadata.
def parityPython = rootProject.layout.buildDirectory.dir('generator-parity/python-dependencies')
def module = new File(System.getenv('_TMP_MODUSTRO_DEFS_MODULE'))
def prepareParityPython = tasks.register('prepareGeneratorParityPython', Exec) {
    def command = [System.getenv('ALGITES_PYTHON_EXECUTABLE') ?: 'python3', new File(module, 'impl/src/develop/python/prepare_parity_python.py').absolutePath,
        '--target', parityPython.get().asFile.absolutePath,
        '--endpoints-json', '["pypi\\thttps://pypi.org/simple\\t\\t","snapshots\\thttps://dl.cloudsmith.io/public/algites/python-snapshots-pub/python/simple/\\t\\t"]',
        '--requirement', 'pyyaml>=6,<7',
        '--requirement', 'pytest>=8,<10',
        '--requirement', 'eu-algites-pub-lib-general-data-dataobject-intf>=1.1.dev0,<1.1a0',
        '--requirement', 'eu-algites-pub-lib-general-common>=1.1.dev0,<1.1a0']
    // The Algites naming profiles/catalog live in naming.convention.algites,
    // not naming.convention.impl (despite their Java/Python package names).
    ['convention.intf', 'convention.impl', 'convention.algites'].each { artifact ->
        command += ['--requirement', 'eu-algites-pub-lib-general-naming-' + artifact.replace('.', '-') + '>=1.1.dev0,<1.1a0']
    }
    command += ['--verify-import', 'eu.algites.lib.naming.convention.impl.algites.aic_algites_naming_profiles_1',
                '--verify-import', 'eu.algites.lib.naming.convention.impl.algites.aic_name_convention_catalog_1']
    commandLine(command)
}
// Fail explicitly when resolved Maven Local naming snapshots predate XML element contracts.
def verifyNamingCatalog = tasks.register('verifyNamingCatalog') {
    doLast {
        def artifact = project(':impl').configurations.runtimeClasspath.resolvedConfiguration.resolvedArtifacts.findAll {
            it.moduleVersion.id.name == 'pub.lib.General_naming.convention.algites'
        }
        if (artifact.size() != 1) {
            throw new GradleException("Expected precisely one Algites naming catalog artifact on the generator runtime classpath; found ${artifact.size()}")
        }
        def archive = artifact[0].file
        def entries = ['eu/algites/lib/naming/convention/algites-java-name-conventions.yml',
                       'eu/algites/lib/naming/convention/algites-python-name-conventions.yml']
        new java.util.zip.ZipFile(archive).withCloseable { zip ->
            entries.each { path ->
                def entry = zip.getEntry(path)
                if (entry == null || !zip.getInputStream(entry).getText('UTF-8').contains('algites-' +
                        (path.contains('java') ? 'java' : 'python') + '-gen-xml-element-intf-versioned:')) {
                    throw new GradleException("Outdated pub.lib.General naming catalog in ${archive}: missing XML element profile ${path}. " +
                        "Use MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE=source with current pub.lib.General sources.")
                }
            }
        }
        logger.lifecycle("Bootstrap Algites naming catalogs verified: ${archive}")
    }
}
project(':impl').tasks.withType(Test).configureEach {
    dependsOn prepareParityPython, verifyNamingCatalog
    environment 'MODUSTRO_ARTIFACT_DIRECTORY', new File(module, 'impl').absolutePath
    environment 'MODUSTRO_PYTHON_TEST_EXECUTABLE', System.getenv('ALGITES_PYTHON_EXECUTABLE') ?: 'python3'
    environment 'MODUSTRO_PYTHON_TEST_PATH', [
        new File(module, 'intf/src/product/python').absolutePath,
        new File(module, 'impl/src/product/python').absolutePath,
        parityPython.get().asFile.absolutePath
    ].join(File.pathSeparator)
}
GRADLE

locGradleCommand=(bash "${locRepositoryDir}/gradlew")
if [[ -n "${MODUSTRO_GRADLE_EXECUTABLE:-}" ]]; then locGradleCommand=("${MODUSTRO_GRADLE_EXECUTABLE}"); fi
if [[ $# -eq 0 ]]; then set -- test publishToMavenLocal; fi
_TMP_MODUSTRO_DEFS_MODULE="${locModuleDir}" MODUSTRO_BOOTSTRAP_BUILD_ROOT="$locBuildRoot" "${locGradleCommand[@]}" --no-daemon --project-dir "${locBootstrapDir}" "$@"

MODUSTRO_DEFS_BOOTSTRAP
cat > "$locTemporaryDirectory/sdo.sh" <<'MODUSTRO_SDO_BOOTSTRAP'
#!/usr/bin/env bash
set -euo pipefail

locModuleDirectory="${MODUSTRO_BOOTSTRAP_MODULE_DIRECTORY:?}"
locRepositoryDirectory="${MODUSTRO_BOOTSTRAP_REPOSITORY_DIRECTORY:?}"
locBuildRoot="${MODUSTRO_BOOTSTRAP_BUILD_ROOT:?}"
locBootstrapDirectory="$(mktemp -d "$locBuildRoot/work/sdocodegen.XXXXXXXX")"
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
def locBootstrapOutput = new File(System.getenv('MODUSTRO_BOOTSTRAP_BUILD_ROOT'), 'gradle/sdocodegen')
layout.buildDirectory.set(new File(locBootstrapOutput, 'root'))
subprojects {
    layout.buildDirectory.set(new File(locBootstrapOutput, 'modules/' + project.name))
    apply plugin: 'java-library'
    apply plugin: 'maven-publish'
    group = 'eu.algites.tool.codegen'
    version = providers.gradleProperty('modustro.sdocodegen.version').getOrElse('1.1-SNAPSHOT')
    repositories {
        def bootstrapMode = System.getenv('MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE') ?: 'remote'
        if (bootstrapMode != 'remote') mavenLocal()
        maven {
            url = uri('https://dl.cloudsmith.io/public/algites/java-snapshots-pub/maven/')
            content { includeGroupByRegex('eu\\.algites\\..*') }
        }
        mavenCentral()
        if (bootstrapMode == 'remote') mavenLocal()
    }
    java { toolchain { languageVersion = JavaLanguageVersion.of(17) }; withSourcesJar() }
    sourceSets {
        main { java.srcDirs = ['src/product/java'] }
        test { java.srcDirs = ['src/develop/java'] }
    }
    tasks.withType(Test).configureEach {
        useTestNG()
        testLogging {
            exceptionFormat = 'full'
            events 'failed', 'standardError'
        }
    }
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
        api 'eu.algites.lib.common:pub.lib.General_common:1.1-SNAPSHOT'
        implementation 'eu.algites.lib.data:pub.lib.General_data.smartdataobject.impl:1.1-SNAPSHOT'
        implementation 'eu.algites.lib.naming:pub.lib.General_naming.convention.algites:1.1-SNAPSHOT'
        testImplementation 'org.testng:testng:7.11.0'
    }
}
project(':cli') {
    dependencies {
        implementation project(':impl')
        implementation 'eu.algites.lib.naming:pub.lib.General_naming.convention.algites:1.1-SNAPSHOT'
    }
}

/* SDO native Python regressions also run when bootstrapped outside the repository build. */
def module = new File(System.getenv('_TMP_MODUSTRO_SDO_MODULE'))
def sdoPython = rootProject.layout.buildDirectory.dir('sdo-parity/python-dependencies')
def prepareSdoPython = tasks.register('prepareSdoPython', Exec) {
    commandLine(System.getenv('ALGITES_PYTHON_EXECUTABLE') ?: 'python3',
        new File(module, '../defscodegen/impl/src/develop/python/prepare_parity_python.py').canonicalPath,
        '--target', sdoPython.get().asFile.absolutePath,
        '--endpoints-json', '["pypi\\thttps://pypi.org/simple\\t\\t","snapshots\\thttps://dl.cloudsmith.io/public/algites/python-snapshots-pub/python/simple/\\t\\t"]',
        '--requirement', 'pytest>=8,<10',
        '--requirement', 'eu-algites-pub-lib-general-data-dataobject-intf>=1.1.dev0,<1.1a0',
        '--requirement', 'eu-algites-pub-lib-general-common>=1.1.dev0,<1.1a0',
        '--requirement', 'eu-algites-pub-lib-general-data-smartdataobject-impl>=1.1.dev0,<1.1a0',
        '--requirement', 'eu-algites-pub-lib-general-naming-convention-impl>=1.1.dev0,<1.1a0',
        '--requirement', 'eu-algites-pub-lib-general-naming-convention-algites>=1.1.dev0,<1.1a0',
        '--verify-import', 'eu.algites.lib.naming.convention.impl.algites.aic_name_convention_catalog_1')
}
def runSdoPython = tasks.register('testSdoPython', Exec) {
    dependsOn prepareSdoPython
    def python = System.getenv('ALGITES_PYTHON_EXECUTABLE') ?: 'python3'
    commandLine python, '-m', 'pytest', '-q', new File(module, 'impl/src/develop/python/test_sdocodegen.py').absolutePath
    def defsModule = new File(module, '../defscodegen')
    environment 'PYTHONPATH', [
        new File(module, 'intf/src/product/python').absolutePath,
        new File(module, 'impl/src/product/python').absolutePath,
        new File(defsModule, 'intf/src/product/python').absolutePath,
        new File(defsModule, 'impl/src/product/python').absolutePath,
        sdoPython.get().asFile.absolutePath
    ].join(File.pathSeparator)
}
project(':impl').tasks.named('test').configure { finalizedBy runSdoPython }
GRADLE
locGradleCommand=(bash "${locRepositoryDirectory}/gradlew")
if [[ -n "${MODUSTRO_GRADLE_EXECUTABLE:-}" ]]; then locGradleCommand=("${MODUSTRO_GRADLE_EXECUTABLE}"); fi
if [[ $# -eq 0 ]]; then set -- test publishToMavenLocal; fi
_TMP_MODUSTRO_SDO_MODULE="${locModuleDirectory}" MODUSTRO_BOOTSTRAP_BUILD_ROOT="$locBuildRoot" "${locGradleCommand[@]}" --no-daemon --project-dir "${locBootstrapDirectory}" "$@"

MODUSTRO_SDO_BOOTSTRAP
chmod 700 "$locTemporaryDirectory/defs.sh" "$locTemporaryDirectory/sdo.sh"
# These separate independent Gradle contexts must complete before uploading anything.
for locGenerator in defs sdo; do
    if [[ "$locGenerator" == defs ]]; then
        locModuleDirectory="$locCodeDirectory/defscodegen"
    else
        locModuleDirectory="$locCodeDirectory/sdocodegen"
    fi
    MODUSTRO_BOOTSTRAP_MODULE_DIRECTORY="$locModuleDirectory" \
    MODUSTRO_BOOTSTRAP_REPOSITORY_DIRECTORY="$locRepositoryDirectory" \
    MODUSTRO_BOOTSTRAP_BUILD_ROOT="$locBuildRoot" \
        bash "$locTemporaryDirectory/$locGenerator.sh" test publishToMavenLocal
done

locVersion="${MODUSTRO_CODEGEN_BOOTSTRAP_VERSION:-1.1-SNAPSHOT}"
locRepo="${MODUSTRO_CODEGEN_BOOTSTRAP_CLOUDSMITH_REPO:-algites/java-snapshots-pub}"
locMavenRoot="${HOME}/.m2/repository/eu/algites/tool/codegen"
locManifest="$locTemporaryDirectory/packages.tsv"
for locGenerator in defscodegen sdocodegen; do
    for locPart in intf impl cli; do
        locArtifactId="pub.tool.General_generators.code.${locGenerator}.${locPart}"
        locLocation="$locMavenRoot/$locArtifactId/$locVersion/$locArtifactId-$locVersion"
        for locExtension in jar pom module; do
            [[ -s "$locLocation.$locExtension" ]] || {
                echo "Missing ${locLocation}.${locExtension}; bootstrap cannot safely publish incomplete Maven module" >&2
                exit 1
            }
        done
        printf '%s\t%s\t%s\t%s\n' "$locLocation.jar" "$locLocation.pom" \
            "$locLocation.module" "$locLocation-sources.jar" >> "$locManifest"
    done
done

if [[ "${MODUSTRO_BOOTSTRAP_PREPARE_ONLY:-0}" == 1 ]]; then
    locOutput="${MODUSTRO_BOOTSTRAP_OUTPUT_DIR:-$locBuildRoot}"
    mkdir -p "$locOutput"
    cp "$locManifest" "$locOutput/packages.tsv"
    echo "Validated six Maven packages; preparation-only manifest: $locOutput/packages.tsv"
    exit 0
fi

command -v algites-cloudsmith >/dev/null || { echo "algites-cloudsmith is required for bootstrap upload" >&2; exit 2; }

# The outer wrapper resolves the secret exactly once, and cloudsmith inside
# the session inherits the credential without reconsulting Secret Service.
algites-cloudsmith --session -- bash -c '
    set -euo pipefail
    locRepo="$1"; locManifest="$2"
    while IFS=$'"'"'\t'"'"' read -r locJar locPom locModule locSources; do
        locArgs=(--pom-file "$locPom" --extra-files "$locModule")
        if [[ -s "$locSources" ]]; then locArgs+=(--sources-file "$locSources"); fi
        cloudsmith push maven "$locRepo" "$locJar" "${locArgs[@]}"
    done < "$locManifest"
' _ "$locRepo" "$locManifest"
