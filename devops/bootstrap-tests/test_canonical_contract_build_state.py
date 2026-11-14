"""The canonical first-stage bootstrap owns no generated state outside build/."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'devops/bootstrap/generate-canonical-contracts.py'


def _sandbox(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    """Build a tiny fake checkout to test CLI side effects without product deps."""
    root = tmp_path / 'repo'
    bootstrap = root / 'devops/bootstrap'
    bootstrap.mkdir(parents=True)
    shutil.copy2(SCRIPT, bootstrap / SCRIPT.name)
    (bootstrap / 'codegen_settings.py').write_text(
        'def defs_settings(root, language): return {}\n'
        'def setting(settings, name): return name.replace(":", "_")\n', encoding='utf-8')
    (bootstrap / 'normalize-canonical-bootstrap.py').write_text(
        'def normalize(contents, language): return contents\n', encoding='utf-8')
    stub = tmp_path / 'stubs/eu/algites/tool/codegen/defs/old/impl/standard'
    stub.mkdir(parents=True)
    (stub / 'aic_schema_contract_bindings_generator.py').write_text('''\
import json
from pathlib import Path
from tempfile import TemporaryDirectory

class AIcSchemaContractBindingsGenerator:
    def generate_manifest(self, root, manifest):
        # Verify nested tempfile calls also land in the invocation workspace.
        with TemporaryDirectory(prefix='nested-') as nested:
            assert Path(nested).is_relative_to(root)
        paths = []
        for lang, output in manifest['technology_outputs'].items():
            filename = 'AIigSample_1.java' if lang == 'java' else 'aiig_sample_1.py'
            relative = f'{output}/eu/algites/tool/codegen/defs/model/{filename}'
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f'generated {lang}\\n', encoding='utf-8')
            paths.append(relative)
        state = root / 'build/run/schema-contract-bindings/generated-files.json'
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_text(json.dumps(paths), encoding='utf-8')
''', encoding='utf-8')
    schema = (root / 'generators/code/defscodegen/intf/src/product/jsondefs'
              / 'eu/algites/tool/codegen/defs/model/canonical-model_1.jsondef.schema.json')
    schema.parent.mkdir(parents=True)
    schema.write_text('{}', encoding='utf-8')
    env = {**os.environ, 'PYTHONPATH': str(tmp_path / 'stubs'), 'PYTHONDONTWRITEBYTECODE': '1'}
    return root, env


def _run(root: Path, env: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(root / 'devops/bootstrap/generate-canonical-contracts.py'),
                           *args], cwd=root, env=env, text=True, capture_output=True, check=False)


def test_manifest_is_disposable_build_state_and_check_works_without_it(tmp_path):
    """Even first --check in a clean checkout works without tracked build JSON."""
    root, env = _sandbox(tmp_path)
    state = root / 'build/run/canonical-contracts/generated-canonical-contracts.json'
    leaked = root / 'generators/code/defscodegen/intf/generated-canonical-contracts.json'
    generated = root / 'generators/code/defscodegen/intf/src/product'
    result = _run(root, env)
    assert result.returncode == 0, result.stderr
    assert state.is_file() and not leaked.exists()
    assert len(json.loads(state.read_text(encoding='utf-8'))) == 2
    assert not list(state.parent.glob('stage-*'))
    assert not list(root.rglob('__pycache__'))
    result = _run(root, env, '--check')
    assert result.returncode == 0, result.stderr
    state.unlink()
    result = _run(root, env, '--check')
    assert result.returncode == 0, result.stderr
    assert not state.exists() and not leaked.exists()
    # Without previous state, outputs are nevertheless checked byte for byte.
    (generated / 'python.gen/eu/algites/tool/codegen/defs/model/aiig_sample_1.py').write_text('stale')
    result = _run(root, env, '--check')
    assert result.returncode == 1
    assert 'stale or missing' in result.stderr
    assert not list(state.parent.glob('stage-*'))


def test_ownership_state_only_deletes_known_generated_files(tmp_path):
    """The stored manifest can never authorize deletion outside *.gen roots."""
    root, env = _sandbox(tmp_path)
    assert _run(root, env).returncode == 0
    state = root / 'build/run/canonical-contracts/generated-canonical-contracts.json'
    entries = json.loads(state.read_text(encoding='utf-8'))
    stale = ('generators/code/defscodegen/intf/src/product/java.gen/'
             'eu/algites/tool/codegen/defs/model/OldContract.java')
    target = root / stale
    target.write_text('obsolete', encoding='utf-8')
    state.write_text(json.dumps([*entries, stale]), encoding='utf-8')
    assert _run(root, env).returncode == 0
    assert not target.exists()
    protected = root / 'generators/code/defscodegen/intf/critical.txt'
    protected.write_text('keep me', encoding='utf-8')
    state.write_text(json.dumps([*entries, 'generators/code/defscodegen/intf/critical.txt']),
                     encoding='utf-8')
    failed = _run(root, env)
    assert failed.returncode != 0 and 'Invalid canonical contract ownership path' in failed.stderr
    assert protected.read_text(encoding='utf-8') == 'keep me'
    assert not (root / 'generators/code/defscodegen/intf/generated-canonical-contracts.json').exists()
