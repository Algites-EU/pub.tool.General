"""Execute the real Gradle SDO phase against isolated Java fixture projects.

Set MODUSTRO_TEST_GRADLE to a Gradle 9 executable, or install gradle on PATH.
No Maven artifacts or remote dependencies are needed by these fixtures.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'bootstrap/sdo-java.gradle'
GRADLE = os.environ.get('MODUSTRO_TEST_GRADLE') or shutil.which('gradle')


@unittest.skipUnless(GRADLE, 'Gradle executable required for integration fixtures')
class LazyRuntimeTest(unittest.TestCase):
    """Ensure only a real read contract can trigger engine validation."""

    def setUp(self):
        """Create a temporary Gradle build with marker APIs and a stub engine."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'profile').mkdir()
        self.write('settings.gradle', "rootProject.name='sdo-lazy-test'\ninclude 'target', 'markers', 'cli', 'profile'\n")
        self.write('build.gradle', '''
subprojects {
    apply plugin: 'java'
    sourceSets.main.java.srcDirs = ['src/product/java']
}
def scenario = providers.gradleProperty('scenario').getOrElse('ordinary')
project(':target') {
    sourceSets.main.java.srcDirs = ['fixtures/' + scenario]
    if (scenario != 'no-api') dependencies { implementation project(':markers') }
}
project(':cli') {
    sourceSets.main.resources.srcDirs = providers.gradleProperty('resources').getOrElse('yes') == 'yes' ? ['src/main/resources'] : []
}
ext.bootstrapSdoManifest = [[artifactId: 'fixture_target', project: 'target', path: 'target']]
if (scenario in ['read', 'mutable', 'namespace', 'ordinary']) {
    ext.bootstrapSdoManifest += [
        [artifactId: 'fixture_generators.code.sdocodegen.cli', project: 'cli', path: 'cli'],
        [artifactId: 'fixture_generators.code.profile.algites', project: 'profile', path: 'profile']]
}
apply from: file('sdo-java.gradle')
''')
        shutil.copyfile(SCRIPT, self.root / 'sdo-java.gradle')
        self.java('markers', 'eu.algites.lib.data.dataobject', 'AIiDataObject', 'public interface AIiDataObject {}')
        self.java('markers', 'eu.algites.lib.data.smartdataobject', 'AIiSmartDataObject',
                  'public interface AIiSmartDataObject extends eu.algites.lib.data.dataobject.AIiDataObject {}')
        self.java('markers', 'eu.algites.lib.data.dataobject.xmldefs', 'AIiXmlDataObjectNamespace',
                  'public interface AIiXmlDataObjectNamespace extends eu.algites.lib.data.dataobject.AIiDataObject {}')
        self.java('markers', 'eu.algites.lib.data.dataobject', 'AIaDataObject',
                  '@java.lang.annotation.Retention(java.lang.annotation.RetentionPolicy.RUNTIME) public @interface AIaDataObject {}')
        cases = {
            'no-api': 'public interface Contract {}',
            'ordinary': 'public interface Contract {}',
            'read': 'public interface Contract extends eu.algites.lib.data.dataobject.AIiDataObject {}',
            'mutable': 'public interface Contract extends eu.algites.lib.data.smartdataobject.AIiSmartDataObject {}',
            'namespace': 'public interface Contract extends eu.algites.lib.data.dataobject.xmldefs.AIiXmlDataObjectNamespace {}',
        }
        for scenario, body in cases.items():
            self.write(f'target/fixtures/{scenario}/example/Contract.java', 'package example;\n' + body)
        self.java('cli', 'eu.algites.tool.codegen.sdo.impl.standard', 'AIcSdoCodegenService', '''
public class AIcSdoCodegenService {
}''')
        self.java('cli', 'eu.algites.tool.codegen.sdo.impl.cli', 'AIcSdoCodegenCli', '''
public class AIcSdoCodegenCli {
    public static void main(String[] args) {
        if (!java.util.Arrays.asList(args).contains("--dointf-input-classes:java=example.Contract"))
            throw new IllegalArgumentException("Missing selected read contract");
        System.out.println("FIXTURE_ENGINE_EXECUTED");
    }
}''')
        repo = SCRIPT.parents[2]
        if not (repo / 'generators/code').is_dir():
            repo = repo.parent / 'pub.tool.General'
        default = 'eu/algites/tool/codegen/sdo/sdocodegen-java-default.settings'
        overlay = 'eu/algites/tool/codegen/sdo/sdocodegen-java.settings'
        self.write('cli/src/main/resources/' + default,
                   (repo / 'generators/code/sdocodegen/intf/src/product/config' / default).read_text())
        self.write('profile/src/main/resources/' + overlay,
                   (repo / 'generators/code/profile/algites/src/product/config' / overlay).read_text())

    def write(self, relative, text):
        """Write UTF-8 fixture content beneath the isolated project root."""
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def java(self, module, package, name, body):
        """Create one Java source fixture in the selected module and package."""
        self.write(module + '/src/product/java/' + package.replace('.', '/') + '/' + name + '.java',
                   'package ' + package + ';\n' + body)

    def run_gradle(self, scenario, *options):
        """Run the real bootstrap task offline and return its captured process result."""
        self.write('target/src/product/java/example/Contract.java',
                   (self.root / ('target/fixtures/' + scenario + '/example/Contract.java')).read_text())
        environment = dict(os.environ, MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE='source')
        environment.pop('MODUSTRO_BOOTSTRAP_SDO_ABI_SEED', None)
        result = subprocess.run([GRADLE, '--offline', '--no-daemon', '--console=plain',
                                 '--max-workers=1', '-Dorg.gradle.vfs.watch=false',
                                 'bootstrapSdoJava', '-Pscenario=' + scenario, *options],
                                cwd=self.root, env=environment, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=90)
        if result.returncode and not (scenario == 'read' and '-Presources=no' in options):
            print(result.stdout, flush=True)
        return result

    def test_no_dataobject_api_never_resolves_missing_engine(self):
        """A module without DataObject APIs must not resolve any SDO binary."""
        result = self.run_gradle('no-api')
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('skipping generator', result.stdout)
        self.assertNotIn('FIXTURE_ENGINE_EXECUTED', result.stdout)

    def test_unrelated_interface_does_not_validate_old_engine_resources(self):
        """An ordinary interface must bypass unavailable engine resources."""
        result = self.run_gradle('ordinary', '-Presources=no')
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('skipping generator', result.stdout)

    def test_mutable_interface_does_not_require_engine_resources(self):
        """Mutable descendants must not be treated as read contract inputs."""
        result = self.run_gradle('mutable', '-Presources=no')
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('skipping generator', result.stdout)

    def test_namespace_marker_does_not_require_engine_resources(self):
        """Unannotated XML namespace markers must not trigger generation."""
        result = self.run_gradle('namespace', '-Presources=no')
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('skipping generator', result.stdout)

    def test_read_contract_still_requires_engine_resources(self):
        """An actual read contract must still enforce packaged engine settings."""
        result = self.run_gradle('read', '-Presources=no')
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn('Missing SDO generator resource', result.stdout)

    def test_read_contract_launches_cli_with_selected_class(self):
        """A valid engine must receive exactly the eligible contract class."""
        result = self.run_gradle('read')
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('FIXTURE_ENGINE_EXECUTED', result.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
