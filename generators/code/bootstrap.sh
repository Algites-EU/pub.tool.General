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
# Published Maven SNAPSHOT coordinates are mutable. The remote bootstrap must
# revalidate snapshot metadata after new Cloudsmith publications, rather than
# silently compiling against an earlier Gradle changing-module cache entry.
# Developers can override this for offline/local work or force a refresh in
# other modes without clearing their Gradle dependency cache by hand.
locRefreshDependencies="${MODUSTRO_BOOTSTRAP_REFRESH_DEPENDENCIES:-}"
if [[ -z "$locRefreshDependencies" ]]; then
    if [[ "$locDependencyMode" == remote ]]; then
        locRefreshDependencies=1
    else
        locRefreshDependencies=0
    fi
fi
case "$locRefreshDependencies" in
    0|1) ;;
    *) echo "Invalid MODUSTRO_BOOTSTRAP_REFRESH_DEPENDENCIES='$locRefreshDependencies' (0|1)" >&2; exit 2 ;;
esac
export MODUSTRO_BOOTSTRAP_REFRESH_DEPENDENCIES="$locRefreshDependencies"
echo "Bootstrap dependency mode: $locDependencyMode; refresh published dependencies: $locRefreshDependencies"
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
        'data/dataobject/intf/src/product/java/eu/algites/lib/data/dataobject/AInFieldSetterInheritancePolicy.java' \
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
    locGeneralGradleArgs=(--no-daemon)
    if [[ "$locRefreshDependencies" == 1 ]]; then locGeneralGradleArgs+=(--refresh-dependencies); fi
    MODUSTRO_BOOTSTRAP_GENERAL_SOURCE_DIR="$locGeneralDirectory" \
    MODUSTRO_BOOTSTRAP_BUILD_ROOT="$locBuildRoot" \
        "${locGeneralGradleCommand[@]}" "${locGeneralGradleArgs[@]}" --project-dir "$locGeneralBootstrapDirectory" publishToMavenLocal
    rm -rf -- "$locGeneralBootstrapDirectory"
    # The Java dependencies above are rebuilt locally, but Python wheels in the
    # published snapshot index may still contain earlier naming/DataObject APIs.
    # Make parity tests and native SDO regressions use the same checked-out
    # library sources as the freshly published Java bootstrap modules.
    locGeneralPythonDirectories=()
    for locGeneralPythonModule in \
        common \
        factory/cpdiscovery/intf factory/cpdiscovery/impl \
        data/dataobject/intf \
        data/smartdataobject/intf data/smartdataobject/impl \
        text/format naming/convention/intf naming/convention/algites; do
        locGeneralPythonSource="$locGeneralDirectory/$locGeneralPythonModule/src/product/python"
        if [[ -d "$locGeneralPythonSource" ]]; then
            locGeneralPythonDirectories+=("$locGeneralPythonSource")
        fi
    done
    locGeneralNamingConfig="$locGeneralDirectory/naming/convention/algites/src/product/config"
    [[ -d "$locGeneralNamingConfig" ]] && locGeneralPythonDirectories+=("$locGeneralNamingConfig")
    locGeneralPythonPath="$(IFS=:; echo "${locGeneralPythonDirectories[*]}")"
    export MODUSTRO_BOOTSTRAP_GENERAL_PYTHON_PATH="$locGeneralPythonPath"
    echo "Bootstrap source mode: native Python tests use current pub.lib.General checkout"
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
include 'intf', 'impl', 'cli', 'common'
['intf', 'impl', 'cli'].each { name ->
    project(":" + name).projectDir = new File(System.getenv('_TMP_MODUSTRO_DEFS_MODULE'), name)
}
project(':common').projectDir = new File(System.getenv('_TMP_MODUSTRO_DEFS_MODULE'), '../common').canonicalFile
GRADLE
cat > "${locBootstrapDir}/build.gradle" <<'GRADLE'
def locBootstrapOutput = new File(System.getenv('MODUSTRO_BOOTSTRAP_BUILD_ROOT'), 'gradle/defscodegen')
layout.buildDirectory.set(new File(locBootstrapOutput, 'root'))
subprojects {
    layout.buildDirectory.set(new File(locBootstrapOutput, 'modules/' + project.name))
    apply plugin: 'java-library'
    apply plugin: 'maven-publish'
    group = 'eu.algites.tool.codegen'
    version = System.getenv('MODUSTRO_CODEGEN_BOOTSTRAP_VERSION') ?: providers.gradleProperty('modustro.defscodegen.version').getOrElse('1.1-SNAPSHOT')
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
        main { java.srcDirs = ['src/product/java']; resources.srcDirs = ['src/product/resources', 'src/product/config'] }
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
                artifactId = project.name == 'common' ? 'pub.tool.General_generators.code.common' : 'pub.tool.General_generators.code.defscodegen.' + project.name
            }
        }
    }
}
// Shared schema-driven method-naming profiles are a real bootstrap artifact.
// The Java compiler and its consumers see exactly the same config resources.
project(':common') {
    sourceSets.main.resources.srcDirs = ['src/product/config', 'src/product/yamldefs',
                                         'src/product/jsondefs', 'src/product/xmldefs']
}
project(':intf') {
    dependencies {
        api 'eu.algites.lib.naming:pub.lib.General_naming.convention.intf:1.1-SNAPSHOT'
        api 'eu.algites.lib.data:pub.lib.General_data.dataobject.intf:1.1-SNAPSHOT'
    }
}
project(':impl') {
    dependencies {
        implementation project(':common')
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
        testImplementation 'org.testng:testng:7.11.0'
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
        def contractPackage = 'eu.algites.lib.data.dataobject'
        def requiredClasses = [
            'eu/algites/lib/data/dataobject/AInFieldPresenceKind.class',
            'eu/algites/lib/data/dataobject/xmldefs/AInXmlValueKind.class',
            'eu/algites/lib/data/dataobject/AInFieldSetterInheritancePolicy.class',
            'eu/algites/lib/data/dataobject/AIaDataObject.class',
            'eu/algites/lib/data/dataobject/AIaDataObjectField.class'
        ]
        def problems = []
        new java.util.zip.ZipFile(archive).withCloseable { zip ->
            problems.addAll(requiredClasses.findAll { zip.getEntry(it) == null }
                .collect { "missing class ${it}" })
        }
        if (problems.isEmpty()) {
            /* Inspect class signatures, not just archive entries: a mixed 1.1-SNAPSHOT
             * can contain the enum while retaining older annotations without the
             * setterInheritancePolicy element required by generated contracts. */
            try {
                new java.net.URLClassLoader([archive.toURI().toURL()] as URL[], (ClassLoader) null).withCloseable { loader ->
                    def policy = loader.loadClass("${contractPackage}.AInFieldSetterInheritancePolicy")
                    if (!policy.isEnum()) {
                        problems.add("AInFieldSetterInheritancePolicy is not an enum")
                    } else {
                        def values = policy.enumConstants.collect { it.name() }
                        ['DEFAULT', 'INHERIT_AS_GENERIC_PARAMETER', 'INHERIT_AS_FIXED_PARAMETER'].each { expected ->
                            if (!values.contains(expected)) problems.add("missing setter policy constant ${expected}")
                        }
                    }
                    ['AIaDataObject', 'AIaDataObjectField'].each { annotationName ->
                        def annotation = loader.loadClass("${contractPackage}.${annotationName}")
                        try {
                            def member = annotation.getDeclaredMethod('setterInheritancePolicy')
                            if (member.returnType != policy) {
                                problems.add("${annotationName}.setterInheritancePolicy() returns an incompatible type")
                            }
                            if (member.defaultValue?.name() != 'DEFAULT') {
                                problems.add("${annotationName}.setterInheritancePolicy() must default to DEFAULT")
                            }
                        } catch (NoSuchMethodException ignored) {
                            problems.add("${annotationName} lacks setterInheritancePolicy()")
                        }
                    }
                }
            } catch (ReflectiveOperationException | LinkageError failure) {
                problems.add("cannot inspect DataObject setter-policy API: ${failure.class.simpleName}: ${failure.message}")
            }
        }
        if (!problems.isEmpty()) {
            def mode = System.getenv('MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE') ?: 'remote'
            def remedy
            if (mode == 'remote') {
                remedy = [
                    'Publish the updated pub.lib.General data/dataobject/intf 1.1-SNAPSHOT to the remote repository first,',
                    'then rerun the Codegen bootstrap (remote mode automatically refreshes dependencies);',
                    'or switch to MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE=source using a current sibling pub.lib.General checkout.'
                ].join(' ')
            } else {
                remedy = [
                    'Build/publish the current pub.lib.General data/dataobject/intf 1.1-SNAPSHOT locally,',
                    'or use MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE=source with a current sibling checkout.'
                ].join(' ')
            }
            throw new GradleException(
                "Incompatible resolved pub.lib.General_data.dataobject.intf:1.1-SNAPSHOT " +
                "at ${archive}: ${problems.join('; ')}. ${remedy}")
        }
        logger.lifecycle("Bootstrap data-object API verified (setter policy and both annotations): ${archive}")
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
                def language = path.contains('java') ? 'java' : 'python'
                def required = ['xml-type-intf', 'xml-element-intf', 'yaml-intf', 'json-intf']
                        .collect { 'algites-' + language + '-gen-' + it + '-versioned_1:' }
                def content = entry == null ? '' : zip.getInputStream(entry).getText('UTF-8')
                def missing = required.findAll { !content.contains(it) }
                if (!missing.isEmpty()) {
                    throw new GradleException("Outdated pub.lib.General naming catalog in ${archive}: " +
                        "missing profiles ${missing} in ${path}. " +
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
    environment 'MODUSTRO_PYTHON_TEST_PATH', (
        (System.getenv('MODUSTRO_BOOTSTRAP_GENERAL_PYTHON_PATH') ?: '').tokenize(File.pathSeparator) + [
            new File(module, '../common/src/product/config').canonicalPath,
            new File(module, 'intf/src/product/python').absolutePath,
            new File(module, 'intf/src/product/config').absolutePath,
            new File(module, 'impl/src/product/python').absolutePath,
            parityPython.get().asFile.absolutePath
        ]
    ).join(File.pathSeparator)
}
GRADLE

locGradleCommand=(bash "${locRepositoryDir}/gradlew")
if [[ -n "${MODUSTRO_GRADLE_EXECUTABLE:-}" ]]; then locGradleCommand=("${MODUSTRO_GRADLE_EXECUTABLE}"); fi
if [[ $# -eq 0 ]]; then set -- test publishToMavenLocal; fi
locGradleArgs=(--no-daemon)
if [[ "${MODUSTRO_BOOTSTRAP_REFRESH_DEPENDENCIES:-0}" == 1 ]]; then locGradleArgs+=(--refresh-dependencies); fi
_TMP_MODUSTRO_DEFS_MODULE="${locModuleDir}" MODUSTRO_BOOTSTRAP_BUILD_ROOT="$locBuildRoot" "${locGradleCommand[@]}" "${locGradleArgs[@]}" --project-dir "${locBootstrapDir}" "$@"

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
include 'intf', 'impl', 'cli', 'common'
['intf', 'impl', 'cli'].each { name ->
    project(":" + name).projectDir = new File(System.getenv('_TMP_MODUSTRO_SDO_MODULE'), name)
}
project(':common').projectDir = new File(System.getenv('_TMP_MODUSTRO_SDO_MODULE'), '../common').canonicalFile
GRADLE
cat > "${locBootstrapDirectory}/build.gradle" <<'GRADLE'
def locBootstrapOutput = new File(System.getenv('MODUSTRO_BOOTSTRAP_BUILD_ROOT'), 'gradle/sdocodegen')
layout.buildDirectory.set(new File(locBootstrapOutput, 'root'))
subprojects {
    layout.buildDirectory.set(new File(locBootstrapOutput, 'modules/' + project.name))
    apply plugin: 'java-library'
    apply plugin: 'maven-publish'
    group = 'eu.algites.tool.codegen'
    version = System.getenv('MODUSTRO_CODEGEN_BOOTSTRAP_VERSION') ?: providers.gradleProperty('modustro.sdocodegen.version').getOrElse('1.1-SNAPSHOT')
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
        main { java.srcDirs = ['src/product/java']; resources.srcDirs = ['src/product/resources', 'src/product/config'] }
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
                artifactId = project.name == 'common' ? 'pub.tool.General_generators.code.common' : 'pub.tool.General_generators.code.sdocodegen.' + project.name
            }
        }
    }
}
// Shared schema-driven method-naming profiles are a real bootstrap artifact.
// The Java compiler and its consumers see exactly the same config resources.
project(':common') {
    sourceSets.main.resources.srcDirs = ['src/product/config', 'src/product/yamldefs',
                                         'src/product/jsondefs', 'src/product/xmldefs']
}
project(':intf') {
    dependencies { api 'eu.algites.lib.data:pub.lib.General_data.dataobject.intf:1.1-SNAPSHOT' }
}
project(':impl') {
    dependencies {
        implementation project(':common')
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
        testImplementation 'org.testng:testng:7.11.0'
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
    commandLine python, '-m', 'pytest', '-q', new File(module, 'impl/src/develop/python').absolutePath
    def defsModule = new File(module, '../defscodegen')
    environment 'PYTHONPATH', (
        (System.getenv('MODUSTRO_BOOTSTRAP_GENERAL_PYTHON_PATH') ?: '').tokenize(File.pathSeparator) + [
            new File(module, '../common/src/product/config').canonicalPath,
            new File(module, 'intf/src/product/python').absolutePath,
            new File(module, 'intf/src/product/config').absolutePath,
            new File(module, 'impl/src/product/python').absolutePath,
            new File(module, 'cli/src/product/python').absolutePath,
            new File(defsModule, 'intf/src/product/python').absolutePath,
            new File(defsModule, 'intf/src/product/config').absolutePath,
            new File(defsModule, 'impl/src/product/python').absolutePath,
            sdoPython.get().asFile.absolutePath
        ]
    ).join(File.pathSeparator)
}
project(':impl').tasks.named('test').configure { finalizedBy runSdoPython }
GRADLE
locGradleCommand=(bash "${locRepositoryDirectory}/gradlew")
if [[ -n "${MODUSTRO_GRADLE_EXECUTABLE:-}" ]]; then locGradleCommand=("${MODUSTRO_GRADLE_EXECUTABLE}"); fi
if [[ $# -eq 0 ]]; then set -- test publishToMavenLocal; fi
locGradleArgs=(--no-daemon)
if [[ "${MODUSTRO_BOOTSTRAP_REFRESH_DEPENDENCIES:-0}" == 1 ]]; then locGradleArgs+=(--refresh-dependencies); fi
_TMP_MODUSTRO_SDO_MODULE="${locModuleDirectory}" MODUSTRO_BOOTSTRAP_BUILD_ROOT="$locBuildRoot" "${locGradleCommand[@]}" "${locGradleArgs[@]}" --project-dir "${locBootstrapDirectory}" "$@"

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
locPythonRepo="${MODUSTRO_CODEGEN_BOOTSTRAP_PYTHON_CLOUDSMITH_REPO:-algites/python-snapshots-pub}"
locPythonOutput="$locBuildRoot/python-dist"
locPythonManifest="$locBuildRoot/python-packages.tsv"
# The seven native Python distributions must come from the same current source
# tree as the seven Maven artifacts. Test-only Python imports are not publication.
# Prepare and verify all wheels and sdists before any Cloudsmith upload.
locPythonBuildExecutable="${MODUSTRO_BOOTSTRAP_PYTHON_BUILD_EXECUTABLE:-}"
if [[ -z "$locPythonBuildExecutable" ]]; then
    locPythonBuildVenv="$locBuildRoot/python-build-venv"
    "${ALGITES_PYTHON_EXECUTABLE:-python3}" -m venv "$locPythonBuildVenv"
    locPythonBuildExecutable="$locPythonBuildVenv/bin/python"
    "$locPythonBuildExecutable" -m pip install --disable-pip-version-check \
        'build>=1,<2' 'setuptools>=69' 'wheel>=0.43' 'pyyaml>=6,<7'
fi
locPythonBuildArgs=(--repository "$locRepositoryDirectory" --maven-version "$locVersion"
    --output "$locPythonOutput" --manifest "$locPythonManifest")
if [[ -n "${MODUSTRO_CODEGEN_BOOTSTRAP_PYTHON_VERSION:-}" ]]; then
    locPythonBuildArgs+=(--python-version "$MODUSTRO_CODEGEN_BOOTSTRAP_PYTHON_VERSION")
fi
"$locPythonBuildExecutable" "$locCodeDirectory/bootstrap-python-dist.py" "${locPythonBuildArgs[@]}"
locMavenRoot="${HOME}/.m2/repository/eu/algites/tool/codegen"
locManifest="$locTemporaryDirectory/packages.tsv"
for locGenerator in common defscodegen sdocodegen; do
    if [[ "$locGenerator" == common ]]; then locParts=(common); else locParts=(intf impl cli); fi
    for locPart in "${locParts[@]}"; do
        if [[ "$locGenerator" == common ]]; then
            locArtifactId="pub.tool.General_generators.code.common"
        else
            locArtifactId="pub.tool.General_generators.code.${locGenerator}.${locPart}"
        fi
        locLocation="$locMavenRoot/$locArtifactId/$locVersion/$locArtifactId-$locVersion"
        for locExtension in jar pom module; do
            [[ -s "$locLocation.$locExtension" ]] || {
                echo "Missing ${locLocation}.${locExtension}; bootstrap cannot safely publish incomplete Maven module" >&2
                exit 1
            }
        done
        if [[ "$locGenerator" == common ]]; then
            "${ALGITES_PYTHON_EXECUTABLE:-python3}" - "$locLocation.jar" <<'VERIFY_COMMON_JAR'
import sys
import zipfile

with zipfile.ZipFile(sys.argv[1]) as archive:
    for language in ('java', 'python'):
        resource = ('eu/algites/lib/naming/convention/'
                    f'algites-{language}-codegen-method-conventions.yml')
        if resource not in archive.namelist():
            raise SystemExit(f'Missing shared naming catalog in Maven JAR: {resource}')
VERIFY_COMMON_JAR
        fi
        printf '%s\t%s\t%s\t%s\n' "$locLocation.jar" "$locLocation.pom" \
            "$locLocation.module" "$locLocation-sources.jar" >> "$locManifest"
    done
done

if [[ "${MODUSTRO_BOOTSTRAP_PREPARE_ONLY:-0}" == 1 ]]; then
    locOutput="${MODUSTRO_BOOTSTRAP_OUTPUT_DIR:-$locBuildRoot}"
    mkdir -p "$locOutput"
    cp "$locManifest" "$locOutput/packages.tsv"
    if [[ "$locOutput/python-packages.tsv" != "$locPythonManifest" ]]; then
        cp "$locPythonManifest" "$locOutput/python-packages.tsv"
    fi
    echo "Validated seven Maven packages and seven Python wheels with sdists; preparation-only manifests: $locOutput/packages.tsv and $locOutput/python-packages.tsv"
    exit 0
fi

command -v algites-cloudsmith >/dev/null || { echo "algites-cloudsmith is required for bootstrap upload" >&2; exit 2; }

# The outer wrapper resolves the secret exactly once, and cloudsmith inside
# the session inherits the credential without reconsulting Secret Service.
algites-cloudsmith --session -- bash -c '
    set -euo pipefail
    locRepo="$1"; locManifest="$2"; locPythonRepo="$3"; locPythonManifest="$4"
    while IFS=$'"'"'\t'"'"' read -r locJar locPom locModule locSources; do
        locArgs=(--pom-file "$locPom" --extra-files "$locModule")
        if [[ -s "$locSources" ]]; then locArgs+=(--sources-file "$locSources"); fi
        cloudsmith push maven "$locRepo" "$locJar" "${locArgs[@]}"
    done < "$locManifest"
    while IFS=$'"'"'\t'"'"' read -r locWheel locSdist; do
        [[ -s "$locWheel" && -s "$locSdist" ]] || {
            echo "Python distribution missing before upload: $locWheel / $locSdist" >&2; exit 1;
        }
        cloudsmith push python "$locPythonRepo" "$locWheel"
        cloudsmith push python "$locPythonRepo" "$locSdist"
    done < "$locPythonManifest"
' _ "$locRepo" "$locManifest" "$locPythonRepo" "$locPythonManifest"
