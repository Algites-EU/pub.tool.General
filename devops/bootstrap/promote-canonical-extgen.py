#!/usr/bin/env python3
"""Replace canonical compiler snapshots with exact freshly generated sources.

Only the explicitly selected Defs interface and implementation artifacts own
these snapshots.  Defs produces the read-only contracts; the independent SDO
Codegen produces mutable contracts and implementations in the same selected
artifact's disposable *.gen tree.  The promotion keeps that generated package
layout and every byte exactly as emitted, splitting the two generator roles
into their respective owning persistent *.extgen roots.

A complete set is checked and staged *before* any existing snapshot changes.
There is no namespace relocation, normalization, compatibility substitution,
or persistent manifest.  Failed validation or staging leaves all snapshots
unchanged.  --check and --prune-seed only inspect existing snapshots.

@author linhart1
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import uuid

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'generators/code/defscodegen/intf/src/product'
IMPLEMENTATION = ROOT / 'generators/code/defscodegen/impl/src/product'
SCHEMA = SOURCE / 'jsondefs/eu/algites/tool/codegen/defs/model/canonical-model_1.jsondef.schema.json'
# Each tuple is (language, complete disposable generated tree, owning snapshot).
# SDO outputs live under model/impl in the same disposable tree as Defs.
OUTPUTS = (
    ('java', SOURCE / 'java.gen', SOURCE / 'java.extgen'),
    ('python', SOURCE / 'python.gen', SOURCE / 'python.extgen'),
    ('java', SOURCE / 'java.gen', IMPLEMENTATION / 'java.extgen'),
    ('python', SOURCE / 'python.gen', IMPLEMENTATION / 'python.extgen'),
)


def _role_files(root: Path, language: str, mutable: bool) -> dict[str, Path]:
    """Collect all generated sources owned by one role without changing paths.

    All of the selected artifact's generated packages belong to its snapshot,
    not just the canonical model package. The generated declaration prefixes
    identify the independent Defs (AIig/AIng) and SDO (AIigd/AIcgd) outputs.
    """
    if root.is_symlink() or not root.is_dir():
        raise RuntimeError('Missing or symlinked generated source root: ' + str(root))
    suffix = '.java' if language == 'java' else '.py'
    writable = ('AIigd', 'AIcgd') if language == 'java' else ('aiigd_', 'aicgd_')
    readonly = ('AIig', 'AIng') if language == 'java' else ('aiig_', 'aing_')
    result = {}
    for source in sorted(root.rglob('*')):
        if source.is_symlink():
            raise RuntimeError('Symlinked generated source: ' + str(source))
        if not source.is_file():
            continue
        if source.suffix != suffix:
            raise RuntimeError('Unexpected file in generated source tree: ' + str(source))
        name = source.stem
        role = ('sdo' if name.startswith(writable) else
                'defs' if name.startswith(readonly) else None)
        if role is None:
            raise RuntimeError('Unrecognized generated declaration: ' + str(source))
        if (role == 'sdo') == mutable:
            result[source.relative_to(root).as_posix()] = source
    if not result:
        raise RuntimeError('Missing generated ' + language + (' SDO' if mutable else ' Defs')
                           + ' contracts under ' + str(root))
    return result


def _symbol(data: bytes, language: str) -> str:
    """Identify a generated type for coverage and cross-language parity checks."""
    source = data.decode('utf-8')
    pattern = (r'(?m)^public\s+(?:(?:sealed|non-sealed|abstract|final)\s+)*'
               r'(?:interface|class|enum|record)\s+(\w+)\b'
               if language == 'java' else r'(?m)^class\s+(\w+)\b')
    match = re.search(pattern, source)
    if not match:
        raise RuntimeError('Cannot identify a generated ' + language + ' declaration')
    return match.group(1)


def _validate(sources: dict[str, bytes]) -> tuple[int, int, int]:
    """Check complete generator roles and semantic metadata before replacement."""
    counts = []
    roles = {}
    for language in ('java', 'python'):
        suffix = '.java' if language == 'java' else '.py'
        read_root = 'generators/code/defscodegen/intf/src/product/' + language + '.extgen/'
        sdo_root = 'generators/code/defscodegen/impl/src/product/' + language + '.extgen/'
        read = {k: v for k, v in sources.items() if k.startswith(read_root) and k.endswith(suffix)}
        sdo = {k: v for k, v in sources.items() if k.startswith(sdo_root) and k.endswith(suffix)}
        if not read or not sdo:
            raise RuntimeError('Missing ' + language + ' canonical Defs/SDO sources')
        symbols = {'read': set(), 'mutable': set(), 'concrete': set()}
        for mapping, role in ((read, 'read'), (sdo, 'sdo')):
            for filename, data in mapping.items():
                source = data.decode('utf-8')
                if 'eu.algites.tool.codegen.defs.bootstrap.model' in source:
                    raise RuntimeError('Obsolete bootstrap package in ' + filename)
                obsolete = (r'\b(?:AIi(?:Json|Yaml|Xml)(?:Smart)?DataObject|'
                            r'AIa(?:Json|Yaml|Xml)DataObject(?:Field)?|'
                            r'AIiMultiMappedListForwarding)\b')
                if re.search(obsolete, source):
                    raise RuntimeError('Obsolete DataObject or list type in ' + filename)
                if ('.jsonschema.AIaDataObjectJsonSchema' in source or
                        '.xmlschema.AIaDataObjectXmlSchema' in source):
                    raise RuntimeError('Obsolete schema annotation in ' + filename)
                sym = _symbol(data, language)
                actual = (role if role == 'read' else
                          'mutable' if '/impl/intf/' in filename else 'concrete')
                if sym in symbols[actual]:
                    raise RuntimeError('Duplicate generated type: ' + sym)
                expected = {'read': ('AIig', 'AIng'), 'mutable': ('AIigd',),
                            'concrete': ('AIcgd',)}[actual]
                if not sym.startswith(expected):
                    raise RuntimeError('Unexpected ' + actual + ' declaration: ' + sym)
                symbols[actual].add(sym)
        if len(symbols['mutable']) != len(symbols['concrete']):
            raise RuntimeError('Incomplete ' + language + ' canonical SDO pairs')
        for sym in symbols['mutable']:
            root = sym.removeprefix('AIigd')
            if 'AIig' + root not in symbols['read'] or 'AIcgd' + root not in symbols['concrete']:
                raise RuntimeError('Missing canonical read/mutable/concrete counterpart: ' + sym)
        if language == 'java':
            # This is a consumer contract, not a revision string: a collection
            # cannot lose its bounded or indexed API during SDO generation.
            read_contract = next((v.decode('utf-8') for k, v in read.items()
                                  if k.endswith('/AIigCanonicalModel_1.java')), '')
            mutable_contract = next((v.decode('utf-8') for k, v in sdo.items()
                                     if k.endswith('/AIigdCanonicalModel_1.java')), '')
            concrete_contract = next((v.decode('utf-8') for k, v in sdo.items()
                                      if k.endswith('/AIcgdCanonicalModel_1.java')), '')
            if 'AIiBoundedList' in read_contract and any(
                    'AIiBoundedList' not in body
                    for body in (mutable_contract, concrete_contract)):
                raise RuntimeError('SDO erased AIiBoundedList from canonical TypesList getter')
            element = next((v.decode('utf-8') for k, v in read.items()
                            if k.endswith('/AIigElement_1.java')), '')
            if element and not all(annotation in element for annotation in (
                    'AIaDataObjectJsonSchema', 'AIaDataObjectYamlSchema',
                    'AIaDataObjectXmlSchema')):
                raise RuntimeError('Merged canonical Element missing XML/JSON/YAML schema annotations')
        counts.append((len(read), len(sdo)))
        roles[language] = symbols
    if counts[0] != counts[1] or roles['java'] != roles['python']:
        raise RuntimeError('Java/Python canonical model role or count mismatch')
    return counts[0][0], counts[0][1], sum(counts[0]) + sum(counts[1])


def _existing() -> dict[str, bytes]:
    """Read all sources in the four persistent roots, rejecting unsafe paths."""
    files = {}
    for language, _, output in OUTPUTS:
        if not output.is_dir() or output.is_symlink():
            raise RuntimeError('Missing canonical snapshot directory: ' + str(output))
        suffix = '.java' if language == 'java' else '.py'
        for file in output.rglob('*'):
            if file.is_symlink() or (file.is_file() and file.suffix != suffix):
                raise RuntimeError('Invalid snapshot path: ' + str(file))
            if file.is_file():
                files[file.relative_to(ROOT).as_posix()] = file.read_bytes()
    return files


def collect_existing() -> dict[str, str]:
    """Return SHA-256 checksums for all persistent generated sources."""
    return {k: hashlib.sha256(v).hexdigest() for k, v in _existing().items()}


def check() -> None:
    """Validate the existing seed without requiring a disposable *.gen tree."""
    read, sdo, total = _validate(_existing())
    print(f'Canonical *.extgen validated from {total} sources '
          f'(read={read}, SDO={sdo} per technology)')


def refresh() -> None:
    """Atomically replace all four snapshots with exact, complete *.gen copies.

    Validation and copy staging finish before touching ANY old *.extgen root.
    The implementation snapshot contains only generated model/impl files;
    the read snapshot contains only the generated read-only model files.
    No path, package, annotation, or source byte is ever rewritten.
    """
    if not SCHEMA.is_file():
        raise RuntimeError('Missing canonical source schema: ' + str(SCHEMA))
    selected = {}
    prospective = {}
    for index, (language, source_root, output) in enumerate(OUTPUTS):
        if output.is_symlink():
            raise RuntimeError('Symlinked canonical snapshot destination: ' + str(output))
        files = _role_files(source_root, language, mutable=index >= 2)
        selected[output] = files
        for relative, source in files.items():
            dest = output / relative
            key = dest.relative_to(ROOT).as_posix()
            if key in prospective:
                raise RuntimeError('Duplicate generated canonical source: ' + key)
            prospective[key] = source.read_bytes()
    read, sdo, total = _validate(prospective)

    token = uuid.uuid4().hex
    staged = []
    completed = []
    success = False
    try:
        for output, files in selected.items():
            output.parent.mkdir(parents=True, exist_ok=True)
            stage = output.with_name(output.name + '.stage-' + token)
            backup = output.with_name(output.name + '.backup-' + token)
            stage.mkdir(mode=0o700)
            staged.append((output, stage, backup))
            for relative, source in files.items():
                target = stage / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                if target.read_bytes() != source.read_bytes():
                    raise RuntimeError('Generated byte mismatch during staging: ' + str(target))
        for output, stage, backup in staged:
            existed = output.exists()
            if existed:
                os.replace(output, backup)
            try:
                os.replace(stage, output)
            except BaseException:
                if existed:
                    os.replace(backup, output)
                raise
            completed.append((output, backup, existed))
        success = True
    except BaseException:
        for output, backup, existed in reversed(completed):
            if output.exists():
                shutil.rmtree(output)
            if existed:
                os.replace(backup, output)
        raise
    finally:
        for _, stage, backup in staged:
            if stage.exists():
                shutil.rmtree(stage)
            if success and backup.exists():
                shutil.rmtree(backup)
    print(f'Copied {total} generated canonical sources byte-for-byte '
          f'into fresh *.extgen roots (read={read}, SDO={sdo} per technology)')


def main() -> None:
    """Check existing snapshots or promote one complete generated compiler ABI."""
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--check', action='store_true')
    modes.add_argument('--refresh', action='store_true')
    modes.add_argument('--prune-seed', action='store_true',
                       help='Validate existing ABI seed only; do not rewrite source')
    args = parser.parse_args()
    if args.refresh:
        refresh()
    else:
        check()


if __name__ == '__main__':
    main()
