"""Regress native SDO selection and common lifecycle event format."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
LIBRARY = ROOT.parent / 'pub.lib.General'


def test_actual_generated_choice_interfaces_are_not_dataobjects():
    """The two reported XML choice markers carry no common DO annotation."""
    generated = (LIBRARY / 'naming/convention/intf/src/product/java.gen/'
                 'eu/algites/lib/naming/convention')
    for name in ('AIigNameFragmentsSegmentChoice_1',
                 'AIigNameFragmentsSegmentValueContent_1'):
        source = (generated / f'{name}.java').read_text(encoding='utf-8')
        assert re.search(rf'interface\s+{name}\s*\{{', source)
        assert '@eu.algites.lib.data.dataobject.AIaDataObject(' not in source
        assert 'extends eu.algites.lib.data.dataobject.AIiDataObject' not in source


def test_java_sdo_requires_neutral_annotation_before_source_dispatch():
    """Type-name recognition must never independently select union markers."""
    cli = (ROOT / 'generators/code/sdocodegen/cli/src/product/java/'
           'eu/algites/tool/codegen/sdo/impl/cli/AIcSdoCodegenCli.java')
    code = cli.read_text(encoding='utf-8')
    assert 'locText.matches(' in code
    assert 'locContracts.add(locSource)' in code
    assert 'locInputNames.recognizeFilename(locSource.getFileName()' not in code
    assert 'AIcSdoCodegenService.isSdoInput(locClass)' in code
    service = (ROOT / 'generators/code/sdocodegen/impl/src/product/java/'
               'eu/algites/tool/codegen/sdo/impl/standard/AIcSdoCodegenService.java')
    assert 'isSdoInput(locClass)' in service.read_text()
    assert 'commonDataObjectMetadata(aClass) != null' in service.read_text()


def test_python_logger_reports_begin_end_and_duration(tmp_path, capsys):
    """Time reports must also be emitted when a direct invocation fails."""
    path = (ROOT / 'generators/code/common/src/product/python/'
            'eu/algites/tool/codegen/common/run_logging.py')
    spec = spec_from_file_location('local_codegen_run_logging', path)
    module = module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    try:
        with module.generation_log('Defs Codegen', 'python', tmp_path, tmp_path/'intf'):
            raise ValueError('example validation failure')
    except ValueError:
        pass
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 2
    assert 'Defs Codegen START artifact=intf technology=python' in lines[0]
    assert 'Defs Codegen END artifact=intf technology=python' in lines[1]
    assert re.search(r'at=\d{4}-\d\d-\d\dT\d\d:', lines[0])
    assert re.search(r'epochMillis=\d{13}', lines[0])
    assert re.search(r'durationMs=\d+ durationSec=\d+\.\d{3}', lines[1])


def test_java_logger_compiles_and_reports_timing(tmp_path):
    """The shared Java logging implementation is usable with plain javac."""
    if not shutil.which('javac') or not shutil.which('java'):
        import pytest
        pytest.skip('JDK not installed')
    files = (ROOT / 'generators/code/common/src/product/java/'
             'eu/algites/tool/codegen/common')
    harness = tmp_path/'LogProbe.java'
    harness.write_text('''import java.nio.file.Path;
import eu.algites.tool.codegen.common.AIcCodegenRunLog;
public class LogProbe {
 public static void main(String[] args) {
  try (var log = new AIcCodegenRunLog("SDO Codegen", "java",
           Path.of(args[0]), Path.of(args[1]))) { }
 }
}
''', encoding='utf-8')
    subprocess.run(['javac', '-d', str(tmp_path),
                    str(files/'AIcCodegenWorkspace.java'),
                    str(files/'AIcCodegenRunLog.java'), str(harness)], check=True)
    completed = subprocess.run(['java', '-cp', str(tmp_path), 'LogProbe',
                                str(tmp_path), str(tmp_path/'intf')],
                               capture_output=True, text=True, check=True)
    assert 'SDO Codegen START artifact=intf technology=java' in completed.stdout
    assert 'SDO Codegen END artifact=intf technology=java' in completed.stdout
    assert 'durationMs=' in completed.stdout


def test_python_logger_artifact_root_is_not_blank(tmp_path, capsys):
    """Artifact-local CLI invocations still report a repository-relative label."""
    path = (ROOT / 'generators/code/common/src/product/python/'
            'eu/algites/tool/codegen/common/run_logging.py')
    spec = spec_from_file_location('artifact_local_python_run_logging', path)
    module = module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    repository = tmp_path / 'pub.lib.General'
    repository.mkdir()
    (repository / 'modustro-source-repository.yml').write_text('SourceRepository: {}\n', encoding='utf-8')
    artifact = repository / 'naming' / 'convention' / 'intf'
    artifact.mkdir(parents=True)
    with module.generation_log('SDO Codegen', 'python', artifact, artifact):
        pass
    assert 'artifact=naming/convention/intf technology=python' in capsys.readouterr().out


def test_java_logger_artifact_root_is_not_blank(tmp_path):
    """Gradle passes an artifact-local root to Java SDO and must keep its identity."""
    files = (ROOT / 'generators/code/common/src/product/java/'
             'eu/algites/tool/codegen/common')
    harness = tmp_path / 'ArtifactLocalLogProbe.java'
    harness.write_text('''import java.nio.file.Path;
import eu.algites.tool.codegen.common.AIcCodegenRunLog;
public class ArtifactLocalLogProbe {
 public static void main(String[] args) {
  try (var log = new AIcCodegenRunLog("SDO Codegen", "java",
      Path.of(args[0]), Path.of(args[0]))) { }
 }
}
''', encoding='utf-8')
    subprocess.run(['javac', '-d', str(tmp_path),
                    str(files / 'AIcCodegenWorkspace.java'),
                    str(files / 'AIcCodegenRunLog.java'), str(harness)], check=True)
    repository = tmp_path / 'pub.lib.General'
    repository.mkdir()
    (repository / 'modustro-source-repository.yml').write_text('SourceRepository: {}\n', encoding='utf-8')
    artifact = repository / 'naming' / 'convention' / 'intf'
    artifact.mkdir(parents=True)
    completed = subprocess.run(['java', '-cp', str(tmp_path), 'ArtifactLocalLogProbe',
                                str(artifact)], capture_output=True, text=True, check=True)
    assert 'artifact=naming/convention/intf technology=java' in completed.stdout
