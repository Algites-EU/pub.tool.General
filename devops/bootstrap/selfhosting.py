#!/usr/bin/env python3
"""Repository-neutral bootstrap self-hosting policy and seed promotion.

Only bootstrap-specializations.yml differs between repositories.  An absent
configuration means an ordinary repository without compiler-ABI exceptions.
Generated sources are never modified by hand: promotion copies only generated
output after the prescribed generation/build stages have completed.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys

import yaml

CONFIGURATION = 'bootstrap-specializations.yml'


def policies(repository: Path) -> dict:
    """Load and validate the repository-specific bootstrap exceptions."""
    path = repository / 'devops/bootstrap' / CONFIGURATION
    if not path.is_file():
        return {}
    document = yaml.safe_load(path.read_text(encoding='utf-8')) or {}
    if not isinstance(document, dict):
        raise ValueError(f'Bootstrap specializations must be a mapping: {path}')
    for key in ('CleanGeneratedDefault', 'RequireFreshGenerated'):
        if key in document and not isinstance(document[key], bool):
            raise ValueError(f'{path}: {key} must be a boolean')
    for entry in document.get('Snapshots') or ():
        if not isinstance(entry, dict) or 'ArtifactPath' not in entry or 'Program' not in entry:
            raise ValueError(f'{path}: invalid snapshot specialization: {entry!r}')
        artifact = Path(entry['ArtifactPath'])
        if artifact.is_absolute() or '..' in artifact.parts:
            raise ValueError(f'Unsafe specialized artifact path: {artifact}')
        program = str(entry['Program'])
        if Path(program).name != program or not program.endswith('.py'):
            raise ValueError(f'Unsafe specialized bootstrap program: {program}')
        if not (repository / artifact / 'modustro-artifact.yml').is_file():
            raise ValueError(f'Specialization has no owning artifact: {artifact}')
    return document


def source_policy(repository: Path, artifact_id: str) -> dict:
    """Return generated-vs-seed source selection for one declared artifact."""
    for item in policies(repository).get('GeneratedSourceSelection') or ():
        if item.get('ArtifactId') == artifact_id:
            return item
    return {}


def generated_ready(artifact: Path, language: str, rule: dict) -> bool:
    """Both mutable interfaces and implementations must exist before seed switch."""
    patterns = rule.get(language.capitalize() + 'CompletionPatterns') or ()
    root = artifact / ('src/product/' + language + '.gen')
    return bool(patterns) and root.is_dir() and all(any(root.glob(pattern)) for pattern in patterns)


def source_directories(artifact: Path, artifact_id: str, language: str, repository: Path) -> tuple[str, ...]:
    """Return source roots, never including colliding seed and generated packages."""
    base = ('src/product/' + language,)
    rule = source_policy(repository, artifact_id)
    if not rule:
        return base + ('src/product/' + language + '.extgen',
                       'src/product/' + language + '.gen')
    seed = os.environ.get('MODUSTRO_BOOTSTRAP_SDO_ABI_SEED') == '1'
    chosen = ('extgen' if seed or not generated_ready(artifact, language, rule)
              else 'gen')
    return base + ('src/product/' + language + '.' + chosen,)


def run_phase(repository: Path, root: Path, phase: str) -> None:
    """Execute configured seed checks/promotions only for selected artifacts."""
    if not root.is_relative_to(repository):
        raise ValueError(f'Selected root is outside repository: {root}')
    for entry in policies(repository).get('Snapshots') or ():
        artifact = (repository / entry['ArtifactPath']).resolve(strict=True)
        applies_to_selected = root == repository or artifact.is_relative_to(root)
        if not applies_to_selected and not (phase == 'before-generation' and
                                           entry.get('BeforeGenerationAnyRoot', False)):
            continue
        if (phase in ('after-build', 'after-bootstrap') and
                entry.get('RequireWholeRepository', False) and root != repository):
            continue
        if phase == 'before-generation' and entry.get('BeforeGenerationSeedOnly', False):
            if os.environ.get('MODUSTRO_BOOTSTRAP_SDO_ABI_SEED') != '1':
                continue
        if phase in ('after-build', 'after-bootstrap') and os.environ.get(
                'MODUSTRO_BOOTSTRAP_SDO_ABI_SEED') == '1':
            continue
        option = entry.get({
            'check-seed': 'CheckSeed',
            'before-generation': 'BeforeGeneration',
            'after-build': 'AfterBuild',
            'after-bootstrap': 'AfterBootstrap',
        }[phase])
        if not option:
            continue
        args = option if isinstance(option, list) else [option]
        if not all(isinstance(part, str) and part.startswith('--') for part in args):
            raise ValueError(f'Invalid phase arguments for {entry["Program"]}: {args!r}')
        script = repository / 'devops/bootstrap' / entry['Program']
        if not script.is_file() or script.is_symlink():
            raise ValueError(f'Configured seed program is unavailable or unsafe: {script}')
        subprocess.run([sys.executable, str(script), *args], cwd=repository, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('clean-default', 'require-fresh', 'phase'))
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--root', type=Path)
    parser.add_argument('--phase', choices=('check-seed', 'before-generation', 'after-build', 'after-bootstrap'))
    args = parser.parse_args()
    repo = args.repository.resolve(strict=True)
    if args.command == 'clean-default':
        print(str(policies(repo).get('CleanGeneratedDefault', False)).lower())
    elif args.command == 'require-fresh':
        print(str(policies(repo).get('RequireFreshGenerated', False)).lower())
    else:
        if args.root is None or not args.phase:
            parser.error('phase requires --root and --phase')
        run_phase(repo, args.root.resolve(strict=True), args.phase)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, yaml.YAMLError, subprocess.CalledProcessError) as error:
        print(f'Bootstrap specialization failed: {error}', file=sys.stderr)
        raise SystemExit(2) from error
