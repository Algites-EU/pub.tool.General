"""Cross-language regression for stable profile paths after the .old migration.

The test compiles the actual Java settings loaders and invokes the actual Python
settings loaders with the repository's original defaults and Algites profiles.
MODUSTRO_TEST_JAVAC and MODUSTRO_TEST_JAVA may select an isolated JDK.
"""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
JAVAC = os.environ.get('MODUSTRO_TEST_JAVAC') or shutil.which('javac')
JAVA = os.environ.get('MODUSTRO_TEST_JAVA') or shutil.which('java')


@unittest.skipUnless(JAVAC and JAVA, 'A JDK is required for Java/Python settings parity')
class OldProfileLoadingTest(unittest.TestCase):
    """Keep implementation defaults separate from public profile identities."""

    @classmethod
    def setUpClass(cls):
        """Compile both real Java loaders and their shared validation exception."""
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.work = Path(cls.temp.name)
        cls.classes = cls.work / 'classes'
        cls.classes.mkdir()
        common = ROOT / 'generators/code/common/src/product/java/eu/algites/tool/codegen/common/AIxCodegenValidationException.java'
        sources = [str(common)]
        for generator, package in [('defscodegen', 'defs'), ('sdocodegen', 'sdo')]:
            sources.append(str(ROOT / f'generators/code/{generator}/cli/src/product/java/eu/algites/tool/codegen/{package}/old/impl/cli/AIcLayeredCodegenSettings.java'))
        harness = cls.work / 'SettingsProbe.java'
        harness.write_text('''
/** Executes actual loaders for cross-language fixture comparison. */
public class SettingsProbe {
    /**
     * Print effective settings using the selected implementation.
     * @param args generator kind, target language and implementation package
     * @throws Exception when configuration expansion fails
     */
    public static void main(String[] args) throws Exception {
        String[] explicit = {"--repository-root=explicit"};
        String[] result = args[0].equals("defscodegen")
            ? eu.algites.tool.codegen.defs.old.impl.cli.AIcLayeredCodegenSettings.expand(explicit, args[0], args[1], args[2])
            : eu.algites.tool.codegen.sdo.old.impl.cli.AIcLayeredCodegenSettings.expand(explicit, args[0], args[1], args[2]);
        java.util.Arrays.stream(result).sorted().forEach(System.out::println);
    }
}
''')
        result = subprocess.run([JAVAC, '-d', str(cls.classes), *sources, str(harness)],
                                text=True, capture_output=True, timeout=30)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)

    def check_generator(self, generator, package):
        """Compare both loaders for each target, enforcing Algites overlays and CLI priority."""
        defaults = ROOT / f'generators/code/{generator}/intf/src/product/config'
        profile = ROOT / 'generators/code/profile/algites/src/product/config'
        common = ROOT / 'generators/code/common/src/product/python'
        helper = ROOT / f'generators/code/{generator}/cli/src/product/python/eu/algites/tool/codegen/{package}/old/impl/cli/_layered_settings.py'
        old_path = list(sys.path)
        self.addCleanup(sys.path.__setitem__, slice(None), old_path)
        # Alternative naming profiles are mutually exclusive deployment choices.
        # Limit the fixture to the single explicitly selected Algites overlay.
        optional_profiles = str(ROOT / 'generators/code/profile/')
        sys.path[:] = [str(defaults), str(profile), str(common)] + [
            item for item in old_path if not str(item).startswith(optional_profiles)]
        spec = importlib.util.spec_from_file_location('settings_fixture_' + generator, helper)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for technology in ('java', 'python'):
            with self.subTest(generator=generator, technology=technology):
                py_args = module.expand(['--repository-root=explicit'], generator, technology, package + '.old')
                cp = os.pathsep.join(map(str, [self.classes, defaults, profile]))
                result = subprocess.run([JAVA, '-cp', cp, 'SettingsProbe', generator, technology, package + '.old'],
                                        cwd=self.work, text=True, capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(sorted(py_args), result.stdout.splitlines())
                self.assertIn('--repository-root=explicit', py_args)
                self.assertTrue(any('=algites-' in arg for arg in py_args), py_args)

    def test_defs_java_python_load_public_profile(self):
        """Both Defs implementations consume unchanged public Algites profile paths."""
        self.check_generator('defscodegen', 'defs')

    def test_sdo_java_python_load_public_profile(self):
        """Both SDO implementations consume unchanged public Algites profile paths."""
        self.check_generator('sdocodegen', 'sdo')


if __name__ == '__main__':
    unittest.main(verbosity=2)
