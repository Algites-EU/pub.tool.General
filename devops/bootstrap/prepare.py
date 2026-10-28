#!/usr/bin/env python3
"""Stage Modustro native modules from the selected source repository.

This helper does not invoke the Modustro Builder and never contacts Cloudsmith.
It reads the repository's native artifact descriptors and generates a separate
Gradle Maven publishing project and independent Python distribution workspaces.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import email
import os
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import xml.etree.ElementTree as ET
import zipfile

import yaml

# Resources are discovered per artifact; bootstrap does not maintain a schema-kind
# whitelist (a repository may introduce additional data formats).
CODE_SOURCE_DIRS = {'java', 'java.gen', 'python', 'python.gen'}


def product_resource_dirs(artifact_root: Path) -> list[str]:
    """Find resource roots declared by the product source-tree convention.

    Exclude code roots, generated roots and tooling caches.  The returned
    paths are relative to the artifact directory and remain stable across
    different source repositories.
    """
    source = artifact_root / 'src/product'
    if not source.is_dir():
        return []
    return ['src/product/' + part.name for part in sorted(source.iterdir())
            if part.is_dir() and not part.is_symlink()
            and part.name not in CODE_SOURCE_DIRS and part.name not in IGNORED
            and not part.name.startswith('.') and not part.name.endswith('.gen')]

IGNORED = {'__pycache__', '.pytest_cache', 'build', 'node_modules', '.mypy_cache'}


def artifact_id(repository: Path, path: Path) -> str:
    descriptor = read_yaml(repository / 'modustro-source-repository.yml')
    return str(descriptor['SourceRepository']['Id']) + '_' + '.'.join(path.parts)


def python_name(identifier: str, prefix: str) -> str:
    """Convert the native artifact identifier to its configured distribution name."""
    return prefix + '-' + re.sub('[^a-z0-9]+', '-', identifier.lower()).strip('-')


def python_version(java_version: str, override: str | None) -> str:
    if override:
        value = override
    elif java_version.endswith('-SNAPSHOT'):
        # Cloudsmith snapshots must not reuse the previous wheel's immutable name.
        value = java_version.removesuffix('-SNAPSHOT') + '.dev' + datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')
    else:
        value = java_version
    if not re.fullmatch(r'\d+(?:\.\d+)*(?:\.dev\d+)?', value):
        raise ValueError(f'Invalid Python package version {value!r}')
    return value


def read_yaml(path: Path) -> dict:
    with path.open(encoding='utf-8') as stream:
        return yaml.safe_load(stream) or {}


def inferred_group(repository: Path, module: Path) -> str:
    # Modustro artifact-set group IDs override the nearest enclosing ancestor.
    root = module
    while root != repository:
        descriptor = root / 'modustro-artifact-set.yml'
        if descriptor.is_file():
            group = read_yaml(descriptor).get('GroupId')
            if group:
                return str(group)
        root = root.parent
    return str(read_yaml(repository / 'modustro-source-repository.yml')['GroupId'])


def spec(requirement: dict | None, version: str) -> str:
    requirement = requirement or {}
    if 'Exact' in requirement:
        exact = str(requirement['Exact'])
        if exact.endswith('-SNAPSHOT'):
            prefix = exact.removesuffix('-SNAPSHOT')
            return f'>={prefix}.dev0,<{prefix}a0'
        return f'=={exact}'
    result = []
    for key, comparator in (('Minimum', '>='), ('Maximum', '<=')):
        if key not in requirement:
            continue
        raw = str(requirement[key])
        if raw.startswith(('>=', '<=', '==', '>', '<')):
            result.append(raw)
        else:
            op = '<' if key == 'Maximum' and requirement.get('MaximumStrict') else comparator
            result.append(op + raw)
    if result:
        return ','.join(result)
    return spec({'Exact': version}, version)


def java_version(name: str, requirement: dict | None, preferred: dict[str, str]) -> str:
    req = requirement or {}
    if 'Exact' in req:
        return str(req['Exact'])
    if name in preferred:
        return str(preferred[name])
    if 'Minimum' in req:
        return str(req['Minimum']).removeprefix('>=')
    raise ValueError(f'Cannot select a concrete Java dependency version for {name}: {req}')


def module_records(repository: Path, release: str, py_release: str) -> list[dict]:
    owner = str(read_yaml(repository / 'modustro-source-repository.yml')['SourceRepository']['Id'])
    bootstrap_settings = read_yaml(repository / 'modustro-bootstrap.yml')
    prefix = bootstrap_settings['DistributionNaming']['PythonPrefix']
    if not isinstance(prefix, str) or not re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*', prefix):
        raise ValueError('Invalid DistributionNaming.PythonPrefix')
    preferred_java_versions = bootstrap_settings.get('DependencyVersions', {}).get('JavaPreferred', {})
    if not isinstance(preferred_java_versions, dict):
        raise ValueError('DependencyVersions.JavaPreferred must be a mapping')
    python_requires = bootstrap_settings['Build']['PythonRequires']
    owner_python_prefix = python_name(owner, prefix) + '-'
    records = []
    for path in sorted(repository.rglob('modustro-artifact.yml')):
        # No build output or virtual environment may become a source artifact.
        relative = path.parent.relative_to(repository)
        if any(part in IGNORED or part.startswith('.') for part in relative.parts):
            continue
        doc = read_yaml(path)
        kinds = doc.get('Artifact', {}).get('TechnologyKinds', [])
        if 'java' not in kinds and 'python' not in kinds:
            continue
        identifier = artifact_id(repository, relative)
        dependencies = []
        python_deps = []
        for dep_group in doc.get('Dependencies') or []:
            kind = dep_group.get('DependencyKind')
            for item in dep_group.get('Items') or []:
                usages = item.get('Usages') or []
                if not any(str(u).startswith('product_') for u in usages):
                    continue
                dep_id = str(item['ArtifactId'])
                if kind == 'modustro':
                    configuration = 'api' if 'product_api' in usages else 'implementation'
                    if dep_id.startswith(owner + '_'):
                        dependencies.append({'kind': 'project', 'artifactId': dep_id,
                                             'configuration': configuration,
                                             'groupId': str(item.get('GroupId') or ''),
                                             'version': release})
                        if 'python' in kinds:
                            python_deps.append(python_name(dep_id, prefix) + '==' + py_release)
                    else:
                        # Dependencies belonging to another source repository are
                        # published contracts, never local Gradle projects. The
                        # bootstrap --root selection must not pull other trees in.
                        group = str(item.get('GroupId') or '')
                        if not group:
                            raise ValueError(f'Missing group for external Modustro artifact {dep_id}')
                        requirement = item.get('VersionRequirement') or {'Exact': release}
                        external_version = str(requirement.get('Exact', release))
                        dependencies.append({'kind': 'external',
                                             'coordinate': f'{group}:{dep_id}:{external_version}',
                                             'configuration': configuration})
                        if 'python' in kinds:
                            python_deps.append(python_name(dep_id, prefix) + spec(requirement, external_version))
                elif kind == 'java' and 'java' in kinds:
                    name = str(item['GroupId']) + ':' + dep_id
                    config = ('compileOnlyApi' if 'product_compile_only_api' in usages else
                              'compileOnly' if 'product_compile_only_implementation' in usages else
                              'api' if 'product_api' in usages else 'implementation')
                    dependencies.append({'kind': 'external', 'coordinate': name + ':' + java_version(name, item.get('VersionRequirement'), preferred_java_versions),
                                         'configuration': config})
                elif kind == 'python' and 'python' in kinds:
                    python_deps.append(dep_id.replace('_', '-') + spec(item.get('VersionRequirement'), py_release))
        records.append({
            'path': relative.as_posix(), 'artifactId': identifier, 'groupId': inferred_group(repository, path.parent),
            'name': str(doc['Artifact'].get('Name', identifier)),
            'description': str(doc['Artifact'].get('Description', identifier)),
            'java': 'java' in kinds, 'python': 'python' in kinds,
            'dependencies': dependencies, 'pythonDependencies': list(dict.fromkeys(python_deps)),
            'resourceDirs': product_resource_dirs(path.parent),
            'pythonName': python_name(identifier, prefix),
            'pythonOwnerPrefix': owner_python_prefix,
            'pythonRequires': str(python_requires),
        })
    if not records:
        raise ValueError('No native Java or Python products declared in modustro-artifact.yml')
    # Artifact descriptors, rather than a manually maintained number of packages,
    # determine which native products must be prepared and verified.
    lookup = {v['artifactId']: v for v in records}
    for record in records:
        for dep in record['dependencies']:
            if dep['kind'] != 'project':
                continue
            other = lookup.get(dep['artifactId'])
            if not other or not other['java']:
                raise ValueError(f'Missing Java dependency for {record["artifactId"]}: {dep["artifactId"]}')
            if dep['groupId'] and dep['groupId'] != other['groupId']:
                raise ValueError(f'Group ID mismatch for {dep["artifactId"]}: descriptor says '
                                 f'{dep["groupId"]}, module is {other["groupId"]}')
        for package in record['pythonDependencies']:
            prefix = package.split('==')[0]
            # If it is an internal reference, it must really be a Python product.
            if prefix.startswith(owner_python_prefix):
                other = next((v for v in records if v['pythonName'] == prefix), None)
                if not other or not other['python']:
                    raise ValueError(f'Invalid Python dependency of {record["artifactId"]}: {package}')
    return records


def restrict_to_selection(records: list[dict], java_release: str, python_release: str) -> list[dict]:
    """Compile/publish only selected products; resolve other products externally.

    Internal dependencies outside --root must never implicitly widen the scope.
    They retain their canonical coordinates and resolve through the configured
    published/local repository. Python dependencies use an appropriate
    snapshot version range instead of a newly generated unpublished timestamp.
    """
    ids = {record['artifactId'] for record in records}
    for record in records:
        converted = []
        for dependency in record['dependencies']:
            if dependency['kind'] == 'project' and dependency['artifactId'] not in ids:
                converted.append({
                    'kind': 'external',
                    'configuration': dependency['configuration'],
                    'coordinate': dependency['groupId'] + ':' + dependency['artifactId'] + ':' + java_release,
                })
            else:
                converted.append(dependency)
        record['dependencies'] = converted
        if java_release.endswith('-SNAPSHOT'):
            base = java_release.removesuffix('-SNAPSHOT')
            replacement = f'>={base}.dev0,<{base}a0'
        else:
            replacement = f'=={java_release}'
        selected_python_names = {item['pythonName'] for item in records if item['python']}
        updated = []
        for requirement in record['pythonDependencies']:
            name, separator, constraint = requirement.partition('==')
            if (separator and constraint == python_release
                    and name.startswith(record['pythonOwnerPrefix'])
                    and name not in selected_python_names):
                updated.append(name + replacement)
            else:
                updated.append(requirement)
        record['pythonDependencies'] = updated
    return records


def stage_gradle(repository: Path, work: Path, records: list[dict], version: str) -> None:
    stage = work / 'gradle'
    stage.mkdir(parents=True, exist_ok=True)
    java_modules = [r for r in records if r['java']]
    for number, record in enumerate(java_modules, 1):
        record['gradleProject'] = 'native%03d' % number
    ids = {r['artifactId']: r['gradleProject'] for r in java_modules}
    modules = [{'project': r['gradleProject'], 'groupId': r['groupId'], 'artifactId': r['artifactId'], 'path': r['path'],
                'resourceDirs': r['resourceDirs'],
                'dependencies': [{'kind': d['kind'], 'configuration': d['configuration'],
                                  'target': ids[d['artifactId']] if d['kind'] == 'project' else d['coordinate']}
                                 for d in r['dependencies']]}
               for r in java_modules]
    (stage / 'modules.json').write_text(json.dumps(modules, indent=2), encoding='utf-8')
    lines = ["rootProject.name = 'modustro-native-bootstrap'"]
    for r in java_modules:
        # JSON encoded paths are valid Groovy double-quoted string literals.
        lines.append('include(' + json.dumps(':' + r['gradleProject']) + ')')
        lines.append('project(' + json.dumps(':' + r['gradleProject']) + ').projectDir = file(' +
                     json.dumps(str(repository / r['path'])) + ')')
    (stage / 'settings.gradle').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    build = '''import groovy.json.JsonSlurper\n\ndef manifest = new JsonSlurper().parse(new File(rootProject.projectDir, 'modules.json'))\ndef configByProject = manifest.collectEntries { [(it.project): it] }\ndef outputRoot = new File(System.getenv('MODUSTRO_BOOTSTRAP_NATIVE_OUTPUT') ?: rootProject.projectDir)\nlayout.buildDirectory.set(new File(outputRoot, 'gradle-build/root'))\nsubprojects { project ->\n    def config = configByProject[project.name]\n    if (config == null) throw new GradleException("Missing bootstrap configuration: ${project.name}")\n    project.layout.buildDirectory.set(new File(outputRoot, 'gradle-build/modules/' + project.name))\n    apply plugin: 'java-library'\n    apply plugin: 'maven-publish'\n    group = config.groupId\n    version = System.getenv('MODUSTRO_BOOTSTRAP_NATIVE_VERSION') ?: 'unspecified'\n    repositories {\n        def bootstrapMode = System.getenv('MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE') ?: 'remote'\n        if (bootstrapMode != 'remote') maven { name = 'modustro-local'; url = uri(System.getenv('MODUSTRO_LOCAL_MAVEN_REPOSITORY') ?: new File(System.getenv('MODUSTRO_HOME') ?: new File(System.getProperty('user.home'), '.modustro').path, 'artifact-repos/java/maven')) }\n        if (bootstrapMode == 'remote') maven {\n            url = uri(System.getenv('MODUSTRO_BOOTSTRAP_REMOTE_MAVEN_URL'))\n            content { includeGroupByRegex(System.getenv('MODUSTRO_BOOTSTRAP_REMOTE_GROUP_REGEX')) }\n        }\n        mavenCentral()\n    }\n    java { withSourcesJar() }\n    tasks.withType(JavaCompile).configureEach { options.release = Integer.parseInt(System.getenv('MODUSTRO_BOOTSTRAP_JAVA_RELEASE')) }\n    sourceSets {\n        main {\n            java.srcDirs = ['src/product/java', 'src/product/java.gen']\n            resources.srcDirs = __MODUSTRO_RESOURCE_SOURCE_DIRS__\n        }\n    }\n    dependencies {\n        config.dependencies.each { d ->\n            if (d.kind == 'project') {\n                add(d.configuration, rootProject.project(':' + d.target))\n            } else {\n                add(d.configuration, d.target)\n            }\n        }\n    }\n    publishing {\n        publications {\n            mavenJava(MavenPublication) {\n                from components.java\n                artifactId = config.artifactId\n            }\n        }\n        repositories {\n            maven { name = 'Bootstrap'; url = uri(new File(outputRoot, 'maven-repository')) }\n        }\n    }\n}\n'''
    build = build.replace('__MODUSTRO_RESOURCE_SOURCE_DIRS__', 'config.resourceDirs')
    # The same universal SDO phase is applied to every staged Gradle build.
    # It runs after initial classes, before the final publication rebuild.
    build += '\nrootProject.ext.bootstrapSdoManifest = manifest\n'
    build += 'apply from: ' + json.dumps(str((Path(__file__).parent / 'sdo-java.gradle').resolve())) + '\n'
    (stage / 'build.gradle').write_text(build, encoding='utf-8')
    (stage / 'release-version.txt').write_text(version + '\n', encoding='utf-8')


def stage_one_python(repository: Path, work: Path, record: dict, release: str) -> Path:
    package = work / 'python-projects' / record['artifactId'].replace('.', '-')
    source_target = package / 'src'
    source_target.mkdir(parents=True, exist_ok=True)
    native_source = repository / record['path']
    for subdir in ('src/product/python', 'src/product/python.gen',
                   *product_resource_dirs(native_source)):
        source = native_source / subdir
        if not source.is_dir():
            continue
        for file in sorted(source.rglob('*')):
            if not file.is_file() or file.suffix in ('.pyc', '.pyo') or any(p in IGNORED for p in file.parts):
                continue
            dst = source_target / file.relative_to(source)
            if dst.exists():
                if dst.read_bytes() != file.read_bytes():
                    raise ValueError(f'Conflicting resource {dst}')
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, dst)
    if not any(f.is_file() for f in source_target.rglob('*')):
        raise ValueError(f'Empty Python product for {record["artifactId"]}')
    license_file = repository / 'LICENSE'
    if license_file.is_file():
        shutil.copy2(license_file, package / 'LICENSE')
    toml = ('[build-system]\nrequires = ["setuptools>=69", "wheel"]\n'
            'build-backend = "setuptools.build_meta"\n\n'
            '[project]\nname = ' + json.dumps(record['pythonName']) + '\n'
            'version = ' + json.dumps(release) + '\n'
            'description = ' + json.dumps(record['description']) + '\n'
            'requires-python = ' + json.dumps(record['pythonRequires']) + '\n'
            'dependencies = ' + json.dumps(record['pythonDependencies']) + '\n\n'
            '[tool.setuptools]\ninclude-package-data = true\n\n'
            '[tool.setuptools.packages.find]\nwhere = ["src"]\nnamespaces = true\n\n'
            '[tool.setuptools.package-data]\n"*" = ["*", "**/*"]\n')
    (package / 'pyproject.toml').write_text(toml, encoding='utf-8')
    # Every staged product resource is part of the distribution, irrespective
    # of its file extension.  Do not silently omit e.g. .properties files.
    (package / 'MANIFEST.in').write_text('recursive-include src *\n', encoding='utf-8')
    return package


def package_python(repository: Path, work: Path, records: list[dict], release: str, python_command: str) -> None:
    dist = work / 'python-dist'
    dist.mkdir(parents=True, exist_ok=True)
    manifest = []
    for record in records:
        if not record['python']:
            continue
        package = stage_one_python(repository, work, record, release)
        # PEP 517 hooks produce both sdist and wheel without installing Modustro.
        # setuptools/wheel are the only build backend dependencies.
        command = ('import setuptools.build_meta as m; from pathlib import Path; '
                   'd = ' + repr(str(dist)) + '; '
                   'print("SDIST:", m.build_sdist(d)); print("WHEEL:", m.build_wheel(d))')
        output = subprocess.run([python_command, '-c', command], cwd=package,
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if output.returncode:
            raise RuntimeError(f'Python build failed for {record["artifactId"]}:\n{output.stdout[-10000:]}')
        sdists = [dist / name.strip() for name in re.findall(r'^SDIST:\s*(.+)$', output.stdout, re.M)]
        wheels = [dist / name.strip() for name in re.findall(r'^WHEEL:\s*(.+)$', output.stdout, re.M)]
        if len(sdists) != 1 or len(wheels) != 1:
            raise RuntimeError(f'Unexpected Python build output for {record["artifactId"]}:\n{output.stdout[-3000:]}')
        sdist, wheel = sdists[0], wheels[0]
        verify_python_distribution(record, release, wheel, sdist, package / 'src')
        manifest.append((str(wheel), str(sdist)))
        print(f'Python package verified: {record["artifactId"]}', flush=True)
    (work / 'python-packages.tsv').write_text(''.join('\t'.join(row)+'\n' for row in manifest), encoding='utf-8')


def expected_python_files(staged_source: Path) -> dict[str, Path]:
    """Return product files copied to the distribution's source tree.

    setuptools creates its own ``*.egg-info`` metadata below ``src`` while
    building.  It is not part of the product and must not be expected inside
    the installed package.  All other staged files, regardless of extension,
    must survive both the wheel and source distribution unchanged.
    """
    return {
        file.relative_to(staged_source).as_posix(): file
        for file in sorted(staged_source.rglob('*'))
        if file.is_file() and not any(part.endswith('.egg-info') for part in
                                       file.relative_to(staged_source).parts)
    }


def verify_python_distribution(record: dict, release: str, wheel: Path,
                               sdist: Path, staged_source: Path) -> None:
    """Verify identity and exact staged product contents of both artifacts.

    Namespace packages need not live below a specific Algites package root:
    Validate actual source files rather than assuming any package namespace
    or any fixed list of resource formats.
    """
    if not wheel.is_file() or not sdist.is_file():
        raise FileNotFoundError(f'Missing distribution: {wheel}, {sdist}')
    expected = expected_python_files(staged_source)
    if not expected:
        raise ValueError(f'Empty Python product for {record["artifactId"]}: {staged_source}')
    with zipfile.ZipFile(wheel) as archive:
        paths = set(archive.namelist())
        meta_files = [name for name in paths if name.endswith('.dist-info/METADATA')]
        if len(meta_files) != 1:
            raise ValueError(f'Wheel must have exactly one METADATA file: {wheel}')
        metadata = email.message_from_bytes(archive.read(meta_files[0]))
        norm = lambda name: re.sub('[-_.]+', '-', name).lower()
        if norm(metadata['Name'] or '') != norm(record['pythonName']) or metadata['Version'] != release:
            raise ValueError(f'Incorrect Python distribution identity/version in {wheel}')
        for name, source in expected.items():
            if name not in paths:
                raise ValueError(f'Wheel is missing product file {name}: {wheel}')
            if archive.read(name) != source.read_bytes():
                raise ValueError(f'Wheel has modified product file {name}: {wheel}')
    with tarfile.open(sdist, 'r:gz') as archive:
        members = {member.name.split('/src/', 1)[1]: member
                   for member in archive.getmembers()
                   if member.isfile() and '/src/' in member.name}
        if not any(path.endswith('/PKG-INFO') for path in archive.getnames()):
            raise ValueError(f'Source distribution missing PKG-INFO: {sdist}')
        for name, source in expected.items():
            member = members.get(name)
            if member is None:
                raise ValueError(f'Source distribution is missing product file {name}: {sdist}')
            stream = archive.extractfile(member)
            if stream is None or stream.read() != source.read_bytes():
                raise ValueError(f'Source distribution has modified product file {name}: {sdist}')


def maven_publication_files(directory: Path, artifact_id: str, release: str) -> tuple[Path, Path, Path, Path]:
    """Locate Gradle-published artifacts, including uniquely timestamped Maven snapshots.

    Maven repository publications of a *-SNAPSHOT version usually write timestamped
    files inside a directory still named *-SNAPSHOT. Their actual file versions are
    recorded per extension/classifier in that directory's maven-metadata.xml.
    Maven-local or older publications can instead use literal *-SNAPSHOT filenames.
    """
    def paths_for(version: str) -> tuple[Path, Path, Path, Path]:
        stem = artifact_id + '-' + version
        return (directory / (stem + '.jar'), directory / (stem + '.pom'),
                directory / (stem + '.module'), directory / (stem + '-sources.jar'))

    ordinary = paths_for(release)
    if all(path.is_file() and path.stat().st_size > 0 for path in ordinary):
        return ordinary

    metadata_path = directory / 'maven-metadata.xml'
    if not release.endswith('-SNAPSHOT') or not metadata_path.is_file():
        existing = sorted(path.name for path in directory.iterdir()) if directory.is_dir() else []
        raise FileNotFoundError(
            f'Incomplete Maven publication of {artifact_id} at {directory}; '
            f'expected {tuple(path.name for path in ordinary)}; existing files: {existing}'
        )

    metadata = ET.parse(metadata_path).getroot()
    coordinates = {
        child.tag.rsplit('}', 1)[-1]: child.text
        for child in metadata
        if child.tag.rsplit('}', 1)[-1] in ('groupId', 'artifactId', 'version')
    }
    expected_coordinates = {'artifactId': artifact_id, 'version': release}
    if any(coordinates.get(key) != value for key, value in expected_coordinates.items()):
        raise ValueError(f'Incorrect Maven snapshot metadata identity at {metadata_path}: {coordinates}')

    def child_named(element: ET.Element, name: str) -> ET.Element | None:
        return next((child for child in element if child.tag.rsplit('}', 1)[-1] == name), None)

    def child_text(element: ET.Element, name: str) -> str | None:
        child = child_named(element, name)
        return child.text if child is not None else None

    versioning = child_named(metadata, 'versioning')
    snapshot_versions = child_named(versioning, 'snapshotVersions') if versioning is not None else None
    resolved: dict[tuple[str, str], str] = {}
    if snapshot_versions is not None:
        for item in snapshot_versions:
            if item.tag.rsplit('}', 1)[-1] != 'snapshotVersion':
                continue
            extension = child_text(item, 'extension')
            classifier = child_text(item, 'classifier') or ''
            value = child_text(item, 'value')
            if extension and value:
                key = (extension, classifier)
                if key in resolved and resolved[key] != value:
                    raise ValueError(f'Ambiguous Maven snapshot metadata for {key} at {metadata_path}')
                resolved[key] = value

    # The snapshotVersion list is canonical, but some repository metadata
    # versions list only the timestamp and build number. Support both formats.
    snapshot = child_named(versioning, 'snapshot') if versioning is not None else None
    timestamp = child_text(snapshot, 'timestamp') if snapshot is not None else None
    build_number = child_text(snapshot, 'buildNumber') if snapshot is not None else None
    fallback = (release.removesuffix('-SNAPSHOT') + '-' + timestamp + '-' + build_number
                if timestamp and build_number else None)
    versions = [resolved.get(key, fallback) for key in
                (('jar', ''), ('pom', ''), ('module', ''), ('jar', 'sources'))]
    if any(not version for version in versions):
        raise ValueError(f'Incomplete Maven snapshot version metadata at {metadata_path}: {resolved}')
    if len(set(versions)) != 1:
        raise ValueError(f'Inconsistent Maven snapshot file versions at {metadata_path}: {versions}')
    actual = paths_for(versions[0])
    if not all(path.is_file() and path.stat().st_size > 0 for path in actual):
        existing = sorted(path.name for path in directory.iterdir())
        raise FileNotFoundError(f'Incomplete timestamped Maven publication of {artifact_id} at {directory}; '
                                f'expected {[path.name for path in actual]}; existing files: {existing}')
    return actual


def expected_java_resources(artifact_root: Path) -> dict[str, Path]:
    """Map Gradle resource paths to their corresponding product source files.

    Each Gradle resource directory is a resource *root*: its own directory name
    is not included in the JAR entry.  Read the same roots used by stage_gradle
    so schema-only artifacts and naming-profile resources can be verified
    without special-casing a package or repository name.
    """
    resources: dict[str, Path] = {}
    for directory in product_resource_dirs(artifact_root):
        source_root = artifact_root / directory
        if not source_root.is_dir():
            continue
        for source in sorted(source_root.rglob('*')):
            if not source.is_file():
                continue
            entry = source.relative_to(source_root).as_posix()
            previous = resources.get(entry)
            if previous is not None and previous.read_bytes() != source.read_bytes():
                raise ValueError(f'Conflicting Java resources {entry}: {previous} and {source}')
            resources[entry] = source
    return resources


def verify_java_jar(jar: Path, artifact_root: Path) -> None:
    """Require compiled Java classes when declared, and all product resources.

    Resource-only artifacts (schemas, naming catalogs, settings) are valid.
    A MANIFEST-only JAR or a JAR missing a declared source/resource is not.
    """
    java_sources = [source for directory in ('java', 'java.gen')
                    for source in (artifact_root / 'src' / 'product' / directory).rglob('*.java')
                    if source.is_file()]
    resources = expected_java_resources(artifact_root)
    with zipfile.ZipFile(jar) as archive:
        names = set(archive.namelist())
        compiled = any(name.endswith('.class') for name in names)
        if java_sources and not compiled:
            raise ValueError(f'JAR is missing compiled Java classes for {artifact_root}: {jar}')
        for entry, source in resources.items():
            if entry not in names:
                raise ValueError(f'JAR is missing product resource {entry} from {source}: {jar}')
            if archive.read(entry) != source.read_bytes():
                raise ValueError(f'JAR contains outdated or modified product resource {entry}: {jar}')
        if not compiled and not resources:
            raise ValueError(f'JAR has neither compiled classes nor product resources: {jar}')


def verify_maven(repository: Path, work: Path, records: list[dict], release: str) -> None:
    maven = work / 'maven-repository'
    rows = []
    for record in records:
        if not record['java']:
            continue
        directory = maven / record['groupId'].replace('.', '/') / record['artifactId'] / release
        jar, pom, module, sources = maven_publication_files(directory, record['artifactId'], release)
        root = ET.parse(pom).getroot()
        names = {node.tag.rsplit('}', 1)[-1]: node.text for node in root
                 if node.tag.rsplit('}', 1)[-1] in ('groupId', 'artifactId', 'version')}
        if any(names.get(k) != value for k, value in [('groupId', record['groupId']),
                                                       ('artifactId', record['artifactId']),
                                                       ('version', release)]):
            raise ValueError(f'Incorrect Maven POM coordinates for {record["artifactId"]}: {names}')
        verify_java_jar(jar, repository / record['path'])
        rows.append((str(jar), str(pom), str(module), str(sources)))
    (work / 'packages.tsv').write_text(''.join('\t'.join(row) + '\n' for row in rows), encoding='utf-8')
    print(f'Maven publications verified: {len(rows)}', flush=True)


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('plan','package-python','verify-maven'))
    parser.add_argument('--repository',type=Path,required=True)
    parser.add_argument('--root',type=Path,help='Limit the source artifacts to this repository subtree')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--version',required=True)
    parser.add_argument('--python-version')
    parser.add_argument('--python-executable',default=sys.executable)
    args=parser.parse_args()
    repository=args.repository.resolve(strict=True)
    output=args.output.absolute()
    output.mkdir(parents=True,exist_ok=True)
    # Preserve one immutable version for all Python wheels during this invocation.
    version_file=output / 'python-release.txt'
    if args.action == 'plan':
        release=python_version(args.version,args.python_version)
        version_file.write_text(release+'\n',encoding='utf-8')
    else:
        release=version_file.read_text(encoding='utf-8').strip()
        if args.python_version and args.python_version != release:
            raise ValueError('Python version changed during bootstrap')
    records=module_records(repository,args.version,release)
    if args.root is not None:
        root = args.root.resolve(strict=True)
        if not root.is_dir() or not root.is_relative_to(repository):
            raise ValueError(f'Invalid bootstrap root outside source repository: {root}')
        selected = [r for r in records if (repository / r['path']).is_relative_to(root)]
        if not selected:
            raise ValueError(f'No Java/Python source artifacts beneath {root}')
        records = restrict_to_selection(selected, args.version, release)
    (output/'artifacts.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    if args.action == 'plan':
        stage_gradle(repository,output,records,args.version)
        print(f'Bootstrap plan: {sum(r["java"] for r in records)} Java Maven and '
              f'{sum(r["python"] for r in records)} Python distributions; release {args.version} / {release}',flush=True)
    elif args.action=='package-python':
        package_python(repository,output,records,release,args.python_executable)
    elif args.action=='verify-maven':
        verify_maven(repository,output,records,args.version)

if __name__ == '__main__':
    main()
