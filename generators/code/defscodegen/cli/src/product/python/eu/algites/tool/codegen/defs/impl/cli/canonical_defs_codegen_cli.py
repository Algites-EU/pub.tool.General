"""Opt-in native canonical Defs CLI, separate from the historical .old CLI.

This CLI exercises the new schema frontend + validation + source emitter end to
end for the explicitly supported contract subset. Naming catalogs and all
source roots are supplied by a checked-in JSON manifest. No legacy generator
is called, and generated files are only written in owned *.gen roots. The
historical bootstrap remains unchanged until full schema parity is verified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping

import yaml

from eu.algites.tool.codegen.common.naming_profiles import (
    resolve_codegen_naming_profiles, with_external_sourcecode_conventions)
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIcgd_jEnum_1, AIigSourceInputKind_1)
from eu.algites.tool.codegen.defs.impl.standard.canonical_pipeline import (
    AIcDefsCodegenCanonicalPipeline, AIcdDefsCodegenSourceDocument)
from eu.algites.tool.codegen.defs.impl.standard.canonical_source_emitter import (
    AIcdDefsCodegenEmissionName, AIcDefsCodegenCanonicalSourceEmitter)

_KINDS = {'xmldefs': AIigSourceInputKind_1.XMLDEFS,
          'jsondefs': AIigSourceInputKind_1.JSONDEFS,
          'yamldefs': AIigSourceInputKind_1.YAMLDEFS}
_ALLOWED_SUFFIXES = {'xmldefs': '.xsd', 'jsondefs': '.jsondef.schema.json',
                     'yamldefs': '.yamldef.schema.json'}


def _read_document(path: Path) -> Mapping[str, Any]:
    """Read a JSON or YAML mapping, rejecting scalar/sequence configurations."""
    if path.suffix == '.json':
        value = json.loads(path.read_text(encoding='utf-8'))
    else:
        value = yaml.safe_load(path.read_text(encoding='utf-8'))
    if not isinstance(value, Mapping):
        raise ValueError(f'Expected mapping document in {path}')
    return value


def _selected_file(manifest_file: Path, configured: str) -> Path:
    """Resolve an explicit catalog path without repository-specific defaults."""
    path = Path(configured)
    return (path if path.is_absolute() else manifest_file.parent / path).resolve()


def _inside(root: Path, configured: str, *, generated: bool = False) -> Path:
    """Require a repository-internal, non-symlink destination/source directory."""
    path = (root / configured).absolute()
    if not path.is_relative_to(root) or path.resolve() != path or path.is_symlink():
        raise ValueError(f'Path escapes repository or traverses a symlink: {configured}')
    if generated and not any(part.endswith('.gen') for part in path.relative_to(root).parts):
        raise ValueError(f'Output directory is not a generated-source root: {configured}')
    return path


def _profile(manifest_file: Path, setting: Mapping[str, str]):
    """Resolve one target's Common/Defs profile plus explicit source-code catalog."""
    if 'sdo_file' in setting or 'sdo_id' in setting:
        raise ValueError('SDO naming belongs to the independent SDO Codegen, not Defs Codegen')
    common = _read_document(_selected_file(manifest_file, setting['common_file']))
    defs = _read_document(_selected_file(manifest_file, setting['defs_file']))
    external = _read_document(_selected_file(manifest_file, setting['sourcecode_catalog']))
    profile = resolve_codegen_naming_profiles(common, setting['common_id'],
                                               defs, setting['defs_id'])
    return with_external_sourcecode_conventions(profile, external)


def _documents(repository: Path, inputs: list[dict[str, str]]):
    """Read typed source schemas with exact repository-relative provenance."""
    documents = []
    for entry in inputs:
        kind = entry['kind'].lower()
        if kind not in _KINDS:
            raise ValueError(f'Unknown canonical input technology: {kind}')
        filename = entry['path']
        if not filename.endswith(_ALLOWED_SUFFIXES[kind]):
            raise ValueError(f'Unexpected {kind} schema extension: {filename}')
        file = _inside(repository, filename)
        if not file.is_file():
            raise FileNotFoundError(file)
        content = (file.read_text(encoding='utf-8') if kind == 'xmldefs'
                   else _read_document(file))
        documents.append(AIcdDefsCodegenSourceDocument(_KINDS[kind],
                                                        file.relative_to(repository).as_posix(), content))
    if not documents:
        raise ValueError('At least one input schema is required')
    return tuple(documents)


def _names(declarations, versions: Mapping[str, str], profile, compositions: Mapping[str, str],
           language: str) -> dict[str, tuple[str, str]]:
    """Use selected catalog compositions to form exact names for every TYPE."""
    result = {}
    for declaration in declarations:
        enum = isinstance(declaration.structure, AIcgd_jEnum_1)
        role = 'enum' if enum else 'interface'
        version = declaration.schema_version or versions.get(declaration.identity) or versions.get('*')
        if not version:
            raise ValueError(f'Missing source version and explicit default for {declaration.identity}')
        typename = profile.composed_name(compositions[role], declaration.name, version=str(version))
        module = (profile.composed_name(compositions[role + '_file'], declaration.name,
                                        version=str(version)) if language == 'python' else typename)
        result[declaration.identity] = (typename, module)
    return result


def prepare(manifest_file: Path):
    """Construct and render all output targets without modifying the repository.

    This is intentionally strict: the manifest provides the original schema
    documents, selected naming catalogs, explicit versions and source outputs.
    Every supported source is validated through the generated JSON contract.
    """
    manifest_file = manifest_file.resolve()
    manifest = _read_document(manifest_file)
    if {'mutable_sdo_java', 'mutable_sdo_python'} & manifest.keys():
        raise ValueError('Defs Codegen produces read-only DataObject contracts only; '
                         'run SDO Codegen separately on generated or manually written interfaces')
    root_value = manifest['repository_root']
    repository = _selected_file(manifest_file, root_value)
    if not repository.is_dir():
        raise ValueError('Repository root does not exist')
    schema = _read_document(_selected_file(manifest_file, manifest['canonical_schema']))
    package = manifest['package_name']
    documents = _documents(repository, manifest['inputs'])
    versions = manifest.get('versions', {})
    outputs = {}
    for language in ('java', 'python'):
        settings = manifest['profiles'][language]
        naming = _profile(manifest_file, settings)
        compiled = AIcDefsCodegenCanonicalPipeline(naming, schema).process(documents)
        declarations = AIcDefsCodegenCanonicalSourceEmitter.declarations(compiled.types)
        selected = _names(declarations, versions, naming,
                          manifest['output_compositions'][language], language)
        # This target may carry different (yet semantically equivalent) synthetic
        # identifier spellings than the other language's naming profile.
        names = {node.identity: AIcdDefsCodegenEmissionName(
            selected[node.identity][0] if language == 'java' else f'AIxUnused{index}',
            selected[node.identity][0] if language == 'python' else f'AIxUnused{index}',
            selected[node.identity][1] if language == 'python' else f'aix_unused_{index}')
            for index, node in enumerate(declarations)}
        emitter = AIcDefsCodegenCanonicalSourceEmitter(
            naming, names, package, manifest['output_compositions'][language]['interface'])
        produced = [item for item in emitter.render(compiled.types) if item.language == language]
        output_root = _inside(repository, manifest['output_dirs'][language], generated=True)
        for item in produced:
            file = output_root / item.relative_path
            if not file.is_relative_to(output_root):
                raise ValueError('Invalid generated relative path')
            relative = file.relative_to(repository).as_posix()
            if relative in outputs:
                raise ValueError('Duplicate generated output file: ' + relative)
            outputs[relative] = item.content
    return repository, outputs


def publish(repository: Path, outputs: Mapping[str, str], check: bool = False) -> list[str]:
    """Write only generator-owned output files, or verify them without mutation.

    Output files are staged before replacement. Existing output not in ownership
    state is never overwritten; independently modified owned output requires
    explicit human recovery, and obsolete files are removed only if unmodified.
    """
    state = repository / 'build/run/canonical-defscodegen/generated-files.json'
    old = json.loads(state.read_text(encoding='utf-8')) if state.is_file() else {}
    if not isinstance(old, dict) or any(not isinstance(k, str) or not isinstance(v, str)
                                       for k, v in old.items()):
        raise ValueError('Invalid canonical Defs generated-file ownership manifest')
    hashes = {name: hashlib.sha256(text.encode('utf-8')).hexdigest()
              for name, text in sorted(outputs.items())}
    for rel in set(old) | set(outputs):
        file = _inside(repository, rel)
        if file.is_file():
            digest = hashlib.sha256(file.read_bytes()).hexdigest()
            if rel in old and old[rel] != digest:
                raise ValueError(f'Generated file modified independently: {rel}')
            if rel not in old:
                raise ValueError(f'Unowned file already exists: {rel}')
        elif rel in old and check:
            raise ValueError(f'Owned generated file missing: {rel}')
    if check:
        if old != hashes:
            raise ValueError('Canonical codegen outputs are outdated or incomplete')
        for rel, digest in hashes.items():
            file = _inside(repository, rel)
            if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != digest:
                raise ValueError(f'Outdated generated source: {rel}')
        return sorted(outputs)
    # Prepare *all* new files, backups, and the manifest before touching any
    # owned destination. Filesystem rename is atomic per path, not per batch;
    # a recoverable exception mid-batch must restore the old manifest's files.
    staged: list[tuple[Path, Path]] = []
    backups: dict[Path, Path] = {}
    committed: set[Path] = set()
    temp_state: Path | None = None
    try:
        for rel in sorted(set(old) | set(outputs)):
            destination = _inside(repository, rel)
            if destination.is_file():
                with tempfile.NamedTemporaryFile('wb', dir=destination.parent,
                                                 delete=False) as handle:
                    handle.write(destination.read_bytes())
                    backups[destination] = Path(handle.name)
        for rel, content in sorted(outputs.items()):
            destination = _inside(repository, rel)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile('w', encoding='utf-8',
                                             dir=destination.parent, delete=False) as handle:
                handle.write(content)
                staged.append((Path(handle.name), destination))
        state.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile('w', encoding='utf-8',
                                         dir=state.parent, delete=False) as handle:
            handle.write(json.dumps(hashes, indent=2, sort_keys=True) + '\n')
            temp_state = Path(handle.name)

        try:
            for src, dest in staged:
                os.replace(src, dest)
                committed.add(dest)
            for rel in sorted(set(old) - set(hashes)):
                file = _inside(repository, rel)
                if file.is_file():
                    file.unlink()
                    committed.add(file)
            os.replace(temp_state, state)
        except BaseException as error:
            # Restore old source bytes or remove previously absent outputs.
            # Never change the ownership manifest on an unsuccessful batch.
            failures = []
            for dest in sorted(committed):
                try:
                    if dest in backups:
                        os.replace(backups[dest], dest)
                    else:
                        dest.unlink(missing_ok=True)
                except OSError as failure:
                    failures.append(f'{dest}: {failure}')
            if failures:
                raise RuntimeError('Canonical Defs publish failed and rollback was '
                                   'incomplete: ' + '; '.join(failures)) from error
            raise
    finally:
        for src, _ in staged:
            src.unlink(missing_ok=True)
        for backup in backups.values():
            backup.unlink(missing_ok=True)
        if temp_state is not None:
            temp_state.unlink(missing_ok=True)
    return sorted(outputs)


def main(args: list[str] | None = None) -> int:
    """Run opt-in native codegen from an explicitly selected repository manifest."""
    parser = argparse.ArgumentParser(description='Native canonical Defs Codegen (limited opt-in subset)')
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--check', action='store_true', help='Do not modify outputs; verify ownership and content')
    parsed = parser.parse_args(args)
    repository, outputs = prepare(parsed.manifest)
    for path in publish(repository, outputs, check=parsed.check):
        print(path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
