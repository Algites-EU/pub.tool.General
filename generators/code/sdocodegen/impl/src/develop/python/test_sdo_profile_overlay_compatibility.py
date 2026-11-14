"""Prevent stale deployed SDO profiles from injecting obsolete CLI selectors.

Only the current SDO settings loaders are exercised; archived generators are
intentionally not changed by this test.
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

REPO = Path(__file__).resolve().parents[7]
JAVA_SETTINGS = REPO / 'generators/code/sdocodegen/cli/src/product/java/eu/algites/tool/codegen/sdo/impl/cli/AIcLayeredCodegenSettings.java'
JAVA_EXCEPTION = REPO / 'generators/code/common/src/product/java/eu/algites/tool/codegen/common/AIxCodegenValidationException.java'
COMMON_PYTHON = REPO / 'generators/code/common/src/product/python'
SDO_PYTHON = REPO / 'generators/code/sdocodegen/cli/src/product/python'
RESOURCE = 'eu/algites/tool/codegen/sdo'
FAMILY = '--common-codegen-naming-convention:java=algites-java-codegen-common_1\n--sdo-codegen-naming-convention:java=algites-java-sdocodegen-standard_1\n'
FAMILY_PY = FAMILY.replace(':java=', ':python=').replace('algites-java-', 'algites-python-')
OLD = '--input-technology-naming-convention:java:common:defsintf=algites-java-gen-intf-versioned_1\n'


def write_settings(root: Path, overlay: str) -> None:
    """Create one classpath-like resource directory for either native loader."""
    path = root / RESOURCE
    path.mkdir(parents=True)
    (path / 'sdocodegen-java.settings').write_text(overlay)
    (path / 'sdocodegen-java-default.settings').write_text('--repository-root=.\n')
    (path / 'sdocodegen-python.settings').write_text(overlay.replace(':java=', ':python=').replace('algites-java-', 'algites-python-'))
    (path / 'sdocodegen-python-default.settings').write_text('--repository-root=.\n')


@pytest.fixture()
def java_runner(tmp_path: Path) -> tuple[Path, Path]:
    """Compile the production Java settings loader without Gradle or internet."""
    if not shutil.which('javac') or not shutil.which('java'):
        pytest.skip('Java runtime and compiler not available')
    classes = tmp_path / 'classes'
    classes.mkdir()
    harness = tmp_path / 'SdoOverlayProbe.java'
    harness.write_text('''
import java.util.Arrays;
import eu.algites.tool.codegen.sdo.impl.cli.AIcLayeredCodegenSettings;
public class SdoOverlayProbe {
    public static void main(String[] arguments) throws Exception {
        String[] expanded = AIcLayeredCodegenSettings.expand(
            arguments, "sdocodegen", "java", "sdo");
        for (String argument : expanded) System.out.println(argument);
    }
}
''')
    subprocess.run(['javac', '-d', str(classes), str(JAVA_EXCEPTION), str(JAVA_SETTINGS), str(harness)],
                   check=True, capture_output=True, text=True)
    return tmp_path, classes


def test_java_legacy_jar_overlay_does_not_shadow_source(tmp_path: Path, java_runner: tuple[Path, Path]) -> None:
    """Discard old JAR profile options, retaining current source selectors."""
    _, classes = java_runner
    stale = tmp_path / 'stale'
    fresh = tmp_path / 'fresh'
    write_settings(stale, OLD)
    write_settings(fresh, FAMILY + '--dointf-naming-convention:java=source-input_1\n')
    for resources in ((fresh, stale), (stale, fresh)):
        result = subprocess.run(['java', '-cp', os.pathsep.join(map(str, (classes,) + resources)),
                                 'SdoOverlayProbe', '--repository-root=.',
                                 '--common-codegen-naming-convention:java=algites-java-codegen-common_1',
                                 '--sdo-codegen-naming-convention:java=algites-java-sdocodegen-standard_1'],
                                cwd=tmp_path, capture_output=True, text=True, check=True)
        assert OLD.strip() not in result.stdout
        assert '--dointf-naming-convention:java=source-input_1' in result.stdout


def test_java_only_stale_profile_is_rejected(tmp_path: Path, java_runner: tuple[Path, Path]) -> None:
    """An outdated profile alone must not silently be mistaken for defaults."""
    _, classes = java_runner
    stale = tmp_path / 'stale'
    write_settings(stale, OLD)
    result = subprocess.run(['java', '-cp', os.pathsep.join(map(str, (classes, stale))),
                             'SdoOverlayProbe'], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode != 0
    assert 'Only outdated SDO naming profile overlays' in result.stderr


def test_java_explicit_old_option_still_rejected_by_cli(tmp_path: Path, java_runner: tuple[Path, Path]) -> None:
    """The loader must not discard user input merely because an installed overlay is old."""
    _, classes = java_runner
    fresh = tmp_path / 'fresh'
    write_settings(fresh, FAMILY)
    result = subprocess.run(['java', '-cp', os.pathsep.join(map(str, (classes, fresh))),
                             'SdoOverlayProbe', OLD.strip()], cwd=tmp_path,
                            capture_output=True, text=True, check=True)
    assert OLD.strip() in result.stdout


def run_python(tmp_path: Path, roots: list[Path]) -> subprocess.CompletedProcess[str]:
    """Resolve a native Python settings resource in an isolated child process."""
    code = '''import importlib.util
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
spec = importlib.util.spec_from_file_location('native_sdo_settings', sys.argv[2])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
expand = module.expand
for item in expand(['--common-codegen-naming-convention:python=algites-python-codegen-common_1',
                    '--sdo-codegen-naming-convention:python=algites-python-sdocodegen-standard_1'],
                   'sdocodegen', 'python', 'sdo'):
    print(item)
'''
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1',
               PYTHONPATH=os.pathsep.join(map(str, [COMMON_PYTHON, SDO_PYTHON] + roots)))
    return subprocess.run([sys.executable, '-c', code, str(COMMON_PYTHON),
                           str(SDO_PYTHON / 'eu/algites/tool/codegen/sdo/impl/cli/_layered_settings.py')], cwd=tmp_path,
                          env=env, capture_output=True, text=True)


def test_python_legacy_jar_overlay_does_not_shadow_source(tmp_path: Path) -> None:
    """Python uses the same legacy-profile exclusion as Java."""
    stale, fresh = tmp_path / 'stale', tmp_path / 'fresh'
    write_settings(stale, OLD)
    write_settings(fresh, FAMILY + '--dointf-naming-convention:java=source-input_1\n')
    result = run_python(tmp_path, [fresh, stale])
    assert result.returncode == 0, result.stderr
    assert '--input-technology-naming-convention:' not in result.stdout
    assert '--dointf-naming-convention:python=source-input_1' in result.stdout


def test_python_only_stale_profile_is_rejected(tmp_path: Path) -> None:
    """An outdated Python profile cannot silently become a default layer."""
    stale = tmp_path / 'stale'
    write_settings(stale, OLD)
    result = run_python(tmp_path, [stale])
    assert result.returncode != 0
    assert 'Only outdated SDO naming profile overlays' in result.stderr
