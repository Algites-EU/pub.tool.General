"""Regression checks for the interim, universally invoked Java SDO phase."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
GRADLE = ROOT / 'devops/bootstrap/sdo-java.gradle'


def _interface_pattern() -> re.Pattern[str]:
    """Read the exact Java-compatible regex used by the Gradle pre-filter."""
    text = GRADLE.read_text(encoding='utf-8')
    found = re.search(r'body =~ /(.+?)/\)\.find\(\)', text)
    assert found, 'Expected a declaration-based pre-filter in sdo-java.gradle'
    return re.compile(found.group(1))


def test_sdo_command_converts_gstrings_to_java_strings_before_processbuilder():
    source = GRADLE.read_text(encoding='utf-8')
    assert 'List<String> command' in source
    assert '.collect { String.valueOf(it) }' in source
    assert 'new ProcessBuilder(command.toArray(new String[0]))' in source
    assert source.index('.collect { String.valueOf(it) }') < source.index('new ProcessBuilder(command.toArray(new String[0]))')


def test_candidates_require_an_interface_declaration_not_mentions_in_code_templates():
    pattern = _interface_pattern()
    renderer = '''
    package example;
    class Renderer {
        String generate() {
            return "public interface AIigFoo extends eu.algites.lib.data.dataobject.AIiDataObject {";
        }
        String annotation = "@eu.algites.lib.data.dataobject.AIaDataObject";
    }
    '''
    assert not pattern.search(renderer)
    assert pattern.search('public interface Foo extends AIiDataObject {}')
    assert pattern.search('interface Another extends eu.algites.lib.data.dataobject.AIiDataObject {}')
    assert pattern.search('public interface AIigFoo extends AIiJsonDataObject {}')


def test_real_defscodegen_implementation_is_not_a_false_sdo_candidate():
    pattern = _interface_pattern()
    impl = ROOT / 'generators/code/defscodegen/impl/src/product/java'
    assert any('AIiDataObject' in path.read_text(encoding='utf-8') for path in impl.rglob('*.java'))
    assert not any(pattern.search(path.read_text(encoding='utf-8')) for path in impl.rglob('*.java'))


def test_real_generated_dataobject_interfaces_are_candidates():
    pattern = _interface_pattern()
    directory = ROOT / 'generators/code/defscodegen/intf/src/product/java.gen'
    source = directory / 'eu/algites/tool/codegen/defs/AIigSchemaFieldBindings_1.java'
    assert source.is_file()
    assert pattern.search(source.read_text(encoding='utf-8'))


def test_java_sdo_surfaces_child_stderr_and_persists_diagnostics():
    source = GRADLE.read_text(encoding='utf-8')
    assert '.redirectErrorStream(true)' in source
    assert "process.inputStream.withReader('UTF-8')" in source
    assert "logger.lifecycle('SDO Java ['" in source
    assert "new File(diagnosticsRoot, entry.project + '.log')" in source
    assert 'exit code ' in source
    assert '.inheritIO().start()' not in source


def test_sdo_resource_loader_uses_unambiguous_parent_classloader():
    """Guard the Groovy URLClassLoader call against ambiguous null overloads."""
    source = GRADLE.read_text(encoding='utf-8')
    assert 'ClassLoader.getPlatformClassLoader()' in source
    assert 'classpathUrls.toArray(new java.net.URL[0]), null)' not in source
    assert 'new java.net.URLClassLoader(' in source
    assert 'resourceLoader.getResource(resourceName)' in source
    assert 'resourceLoader.close()' in source
