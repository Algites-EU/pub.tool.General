#!/usr/bin/env python3
"""Isolated Maven bootstrap staging, verified Modustro-local promotion and Gradle resolution.

Only Maven publication files are promoted. Gradle's private dependency cache is
never edited: the resolver probe uses the configured Modustro repository and verifies SHA-256.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET


def modustro_local_maven() -> Path:
    explicit = os.environ.get('MODUSTRO_LOCAL_MAVEN_REPOSITORY')
    home = Path(os.environ.get('MODUSTRO_HOME') or Path.home() / '.modustro').expanduser()
    return Path(explicit).expanduser().resolve() if explicit else (home / 'artifact-repos/java/maven').resolve()


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def xml_fields(path: Path) -> dict[str, str]:
    root = ET.parse(path).getroot()
    return {child.tag.split('}')[-1]: (child.text or '') for child in root
                 if child.tag.split('}')[-1] in {'groupId', 'artifactId', 'version'}}


def artifact_files(directory: Path, artifact: str, version: str) -> list[Path | None]:
    def get(stem: str) -> list[Path | None]:
        return [directory / (stem + ext) for ext in ('.jar', '.pom', '.module', '-sources.jar')]
    paths = get(f'{artifact}-{version}')
    if all(p.is_file() for p in paths[:3]):
        return [*paths[:3], paths[3] if paths[3].exists() else None]
    metadata = directory / 'maven-metadata.xml'
    if not version.endswith('-SNAPSHOT') or not metadata.exists():
        raise ValueError(f'Missing Maven publication for {artifact}:{version} under {directory}')
    root = ET.parse(metadata).getroot()
    metadata_fields = xml_fields(metadata)
    if metadata_fields.get('artifactId') != artifact or metadata_fields.get('version') != version:
        raise ValueError(f'Wrong snapshot metadata coordinates in {metadata}')
    versions = {}
    for item in root.findall('.//{*}snapshotVersion'):
        extension = item.findtext('{*}extension')
        classifier = item.findtext('{*}classifier') or ''
        value = item.findtext('{*}value')
        if extension and value:
            versions[(extension, classifier)] = value
    snap = root.find('.//{*}snapshot')
    if snap is not None:
        timestamp, build = snap.findtext('{*}timestamp'), snap.findtext('{*}buildNumber')
        fallback = version[:-9] + '-' + timestamp + '-' + build if timestamp and build else None
    else:
        fallback = None
    value = versions.get(('jar', ''), fallback)
    if not value:
        raise ValueError(f'Incomplete snapshot metadata for {artifact} at {metadata}')
    file_versions = [versions.get(key, fallback) for key in
                     (('jar', ''), ('pom', ''), ('module', ''))]
    if any(v != value for v in file_versions):
        raise ValueError(f'Inconsistent snapshot versions for {artifact}: {file_versions}')
    paths = get(f'{artifact}-{value}')
    if not all(p.is_file() for p in paths[:3]):
        raise ValueError(f'Missing timestamped Maven files for {artifact} at {directory}')
    source_version = versions.get(('jar', 'sources'), fallback)
    sources = directory / f'{artifact}-{source_version}-sources.jar' if source_version else None
    return [*paths[:3], sources if sources and sources.exists() else None]


def read_coordinates(path: Path) -> list[tuple[str, str, str]]:
    result = []
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        items = line.split('\t')
        if len(items) != 3 or any(not x.strip() for x in items):
            raise ValueError(f'Expected GROUP\\tARTIFACT\\tVERSION: {line}')
        result.append(tuple(items))
    if len(result) != len(set(result)) or not result:
        raise ValueError('Empty or duplicate Maven coordinates')
    return result


def collect(stage: Path, coords: Path, output: Path) -> None:
    entries = []
    for group, artifact, version in read_coordinates(coords):
        directory = stage / group.replace('.', '/') / artifact / version
        files = artifact_files(directory, artifact, version)
        if not all(f and f.is_file() and f.stat().st_size for f in files[:3]):
            raise ValueError(f'Incomplete Maven publication: {group}:{artifact}:{version}')
        pom_fields = xml_fields(files[1])
        if pom_fields != {'groupId': group, 'artifactId': artifact, 'version': version}:
            raise ValueError(f'Unexpected POM coordinates in {files[1]}: {pom_fields}')
        entries.append({'group': group, 'artifact': artifact, 'version': version,
                        'files': [str(f.resolve()) if f is not None else None for f in files],
                        'sha256': [digest(f) if f is not None else None for f in files]})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(entries, indent=2) + '\n', encoding='utf-8')
    print(f'Validated {len(entries)} staged Maven publications: {output}', flush=True)



def collect_tsv(input_path: Path, output: Path) -> None:
    """Validate an existing four-column JAR/POM/module/sources staging manifest."""
    entries = []
    for line in input_path.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        cols = line.split('\t')
        if len(cols) != 4:
            raise ValueError(f'Expected four Maven files in {input_path}: {line}')
        files = [Path(value) if value else None for value in cols]
        if not all(f is not None and f.is_file() and f.stat().st_size for f in files[:3]):
            raise ValueError(f'Incomplete staging publication: {line}')
        if files[3] is not None and not files[3].is_file():
            files[3] = None
        pom = xml_fields(files[1])
        if set(pom) != {'groupId', 'artifactId', 'version'} or not all(pom.values()):
            raise ValueError(f'Invalid Maven coordinates: {files[1]}: {pom}')
        entries.append({'group': pom['groupId'], 'artifact': pom['artifactId'], 'version': pom['version'],
                        'files': [str(f.resolve()) if f is not None else None for f in files],
                        'sha256': [digest(f) if f is not None else None for f in files]})
    if not entries or len({(e['group'], e['artifact'], e['version']) for e in entries}) != len(entries):
        raise ValueError(f'Empty or duplicate Maven staging manifest: {input_path}')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(entries, indent=2) + '\n', encoding='utf-8')
    print(f'Validated {len(entries)} Maven staging manifest rows', flush=True)

def promote(stage_manifest: Path, local: Path, output: Path) -> None:
    entries = json.loads(stage_manifest.read_text(encoding='utf-8'))
    tasks = []
    installed = []
    for entry in entries:
        group, artifact, version = (entry[k] for k in ('group', 'artifact', 'version'))
        target = local / group.replace('.', '/') / artifact / version
        filenames = [f'{artifact}-{version}{ext}' for ext in ('.jar', '.pom', '.module', '-sources.jar')]
        for path, expected, filename in zip(entry['files'], entry['sha256'], filenames):
            if path is None:
                continue
            source = Path(path)
            if not source.is_file() or digest(source) != expected:
                raise ValueError(f'Staging source changed after verification: {source}')
            tasks.append((source, target / filename, expected))
        installed.append((entry, [str(target / name) if original is not None else None
                                  for name, original in zip(filenames, entry['files'])]))
    # Validate the entire batch before touching Maven Local.
    for source, destination, sha in tasks:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(destination.name + '.bootstrap-new')
        try:
            shutil.copyfile(source, temporary)
            if digest(temporary) != sha:
                raise ValueError(f'Checksum mismatch while preparing {destination}')
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)
    manifest_rows = []
    for entry, files in installed:
        # Repository snapshots may timestamp artifact file URLs inside Gradle
        # module metadata. Maven Local uses the stable -SNAPSHOT filenames.
        # Normalize only those file references; leave the binary JAR untouched.
        module = Path(files[2])
        raw_module = module.read_text(encoding='utf-8')
        try:
            module_header = ''.join(line for line in raw_module.splitlines(keepends=True) if line.lstrip().startswith('//'))
            module_data = json.loads('\n'.join(line for line in raw_module.splitlines() if not line.lstrip().startswith('//')))
        except json.JSONDecodeError as exc:
            raise ValueError(f'Invalid Gradle module metadata: {module}') from exc
        if isinstance(module_data, dict):
            timestamped = Path(entry['files'][0]).name
            logical = Path(files[0]).name
            source_timestamped = Path(entry['files'][3]).name if entry['files'][3] else None
            source_logical = Path(files[3]).name if files[3] else None
            modified = False
            for variant in module_data.get('variants', []):
                for file in variant.get('files', []):
                    for field in ('name', 'url'):
                        value = file.get(field)
                        if not isinstance(value, str):
                            continue
                        updated = value.replace(timestamped, logical)
                        if source_timestamped and source_logical:
                            updated = updated.replace(source_timestamped, source_logical)
                        if updated != value:
                            file[field] = updated
                            modified = True
            if modified:
                tmp = module.with_name(module.name + '.bootstrap-new')
                tmp.write_text(module_header + json.dumps(module_data, indent=2) + '\n', encoding='utf-8')
                os.replace(tmp, module)
        # After promotion, Gradle metadata may legitimately have a different
        # checksum because its file URLs were normalized; binary hashes never do.
        # Do not leave a sources JAR from an older SNAPSHOT if the current
        # publication explicitly has no sources classifier.
        if files[3] is None:
            root = local / entry['group'].replace('.', '/') / entry['artifact'] / entry['version']
            (root / f"{entry['artifact']}-{entry['version']}-sources.jar").unlink(missing_ok=True)
        group, artifact, version = (entry[k] for k in ('group', 'artifact', 'version'))
        artifact_home = local / group.replace('.', '/') / artifact
        now = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
        metadata = ET.Element('metadata')
        ET.SubElement(metadata, 'groupId').text = group
        ET.SubElement(metadata, 'artifactId').text = artifact
        versioning = ET.SubElement(metadata, 'versioning')
        ET.SubElement(versioning, 'latest').text = version
        versions = ET.SubElement(versioning, 'versions')
        ET.SubElement(versions, 'version').text = version
        ET.SubElement(versioning, 'lastUpdated').text = now
        destination = artifact_home / 'maven-metadata-local.xml'
        previous = []
        if destination.exists():
            try:
                previous = [v.text for v in ET.parse(destination).getroot().findall('.//version') if v.text]
            except ET.ParseError as exc:
                raise ValueError(f'Invalid existing Maven Local metadata: {destination}') from exc
        for prior in previous:
            if prior != version:
                ET.SubElement(versions, 'version').text = prior
        temporary = destination.with_name(destination.name + '.bootstrap-new')
        ET.ElementTree(metadata).write(temporary, encoding='utf-8', xml_declaration=True)
        os.replace(temporary, destination)
        for index, (path, expected) in enumerate(zip(files, entry['sha256'])):
            if path is not None and index != 2 and digest(Path(path)) != expected:
                raise ValueError(f'Maven Local promotion mismatch: {path}')
        manifest_rows.append('\t'.join(path or '' for path in files))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text('\n'.join(manifest_rows) + '\n', encoding='utf-8')
    print(f'Promoted {len(installed)} verified Maven publications to {local}', flush=True)


def gradle_verify(manifest: Path, gradle: str, work: Path) -> None:
    rows = [r.split('\t') for r in manifest.read_text(encoding='utf-8').splitlines() if r.strip()]
    config = []
    for row in rows:
        if len(row) != 4:
            raise ValueError('Invalid Maven Local manifest')
        fields = xml_fields(Path(row[1]))
        config.append({'gav': ':'.join(fields[k] for k in ('groupId', 'artifactId', 'version')),
                       'sha256': digest(Path(row[0]))})
    work.mkdir(parents=True, exist_ok=True)
    (work / 'settings.gradle').write_text("rootProject.name='algites-bootstrap-maven-local-verifier'\n", encoding='utf-8')
    (work / 'artifacts.json').write_text(json.dumps(config), encoding='utf-8')
    local_repo = modustro_local_maven()
    (work / 'build.gradle').write_text('''import groovy.json.JsonSlurper
import java.security.MessageDigest
repositories { maven { url = uri(System.getenv('MODUSTRO_LOCAL_MAVEN_REPOSITORY')) } }
configurations { bootstrapVerify { canBeConsumed = false; canBeResolved = true } }
def expected = new JsonSlurper().parse(file('artifacts.json'))
expected.each { row -> dependencies.add('bootstrapVerify', row.gav) { transitive = false } }
tasks.register('verifyMavenLocal') {
    doLast {
        def found = configurations.bootstrapVerify.resolvedConfiguration.resolvedArtifacts
        def actual = found.collectEntries { artifact ->
            def key = artifact.moduleVersion.id.group + ':' + artifact.name + ':' + artifact.moduleVersion.id.version
            def sha = MessageDigest.getInstance('SHA-256').digest(artifact.file.bytes).collect {
                String.format('%02x', it & 0xff)
            }.join('')
            [(key): sha]
        }
        expected.each { row ->
            if (actual[row.gav] != row.sha256) throw new GradleException(
                'Gradle did not resolve current Maven Local JAR ' + row.gav +
                ': expected ' + row.sha256 + ', got ' + actual[row.gav])
        }
        if (found.size() != expected.size()) throw new GradleException('Incorrect Maven Local resolved count')
        logger.lifecycle('Maven Local Gradle resolution verified: ' + expected.size() + ' modules')
    }
}
''', encoding='utf-8')
    command = ([gradle] if gradle != 'gradlew' else ['gradle'])
    subprocess.run([*command, '--no-daemon', '--refresh-dependencies', '--project-dir', str(work),
                    'verifyMavenLocal'], check=True, env={**os.environ, 'MODUSTRO_LOCAL_MAVEN_REPOSITORY': str(local_repo)})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest='action', required=True)
    collect_cmd = actions.add_parser('collect')
    collect_cmd.add_argument('--staging', type=Path, required=True)
    collect_cmd.add_argument('--coordinates', type=Path, required=True)
    collect_cmd.add_argument('--output', type=Path, required=True)
    collect_tsv_cmd = actions.add_parser('collect-tsv')
    collect_tsv_cmd.add_argument('--tsv', type=Path, required=True)
    collect_tsv_cmd.add_argument('--output', type=Path, required=True)
    promote_cmd = actions.add_parser('promote')
    promote_cmd.add_argument('--manifest', type=Path, required=True)
    promote_cmd.add_argument('--maven-local', type=Path, default=modustro_local_maven())
    promote_cmd.add_argument('--output', type=Path, required=True)
    verify_cmd = actions.add_parser('verify-gradle')
    verify_cmd.add_argument('--manifest', type=Path, required=True)
    verify_cmd.add_argument('--gradle', required=True)
    verify_cmd.add_argument('--work', type=Path, required=True)
    args = parser.parse_args()
    if args.action == 'collect':
        collect(args.staging, args.coordinates, args.output)
    elif args.action == 'collect-tsv':
        collect_tsv(args.tsv, args.output)
    elif args.action == 'promote':
        promote(args.manifest, args.maven_local, args.output)
    else:
        gradle_verify(args.manifest, args.gradle, args.work)

if __name__ == '__main__':
    main()
