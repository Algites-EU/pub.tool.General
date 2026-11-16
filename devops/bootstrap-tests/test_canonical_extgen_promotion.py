"""Regression tests for the canonical compiler-ABI promotion source ownership."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

PACKAGE_PATH = Path('eu/algites/tool/codegen/defs/model')
SCRIPT = Path(__file__).resolve().parents[1] / 'bootstrap/promote-canonical-extgen.py'
spec = importlib.util.spec_from_file_location('canonical_promotion_under_test', SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CanonicalPromotionTests(unittest.TestCase):
    """The two independent generators share a disposable input-artifact root."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='canonical-promotion-')
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        base = self.repo / 'generators/code/defscodegen'
        source = base / 'intf/src/product'
        impl = base / 'impl/src/product'
        schema = source / 'jsondefs/eu/algites/tool/codegen/defs/model/canonical-model_1.jsondef.schema.json'
        schema.parent.mkdir(parents=True, exist_ok=True)
        schema.write_text('{"type":"object"}\n', encoding='utf-8')
        outputs = (
            ('java', source / 'java.gen', source / 'java.extgen'),
            ('python', source / 'python.gen', source / 'python.extgen'),
            ('java', source / 'java.gen', impl / 'java.extgen'),
            ('python', source / 'python.gen', impl / 'python.extgen'),
        )
        updates = {'ROOT': self.repo, 'SOURCE': source, 'IMPLEMENTATION': impl,
                   'SCHEMA': schema, 'OUTPUTS': outputs}
        self.patcher = patch.multiple(module, **updates)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.source = source
        self.impl = impl

    def write(self, language: str, relative: str, content: str):
        file = self.source / (language + '.gen') / PACKAGE_PATH / relative
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding='utf-8')
        return file

    def populate(self):
        self.write('java', 'AIigWidget_1.java',
                   'package eu.algites.tool.codegen.defs.model;\n'
                   '@eu.algites.lib.data.dataobject.AIaDataObject(description = "Widget")\n'
                   'public interface AIigWidget_1 extends eu.algites.lib.data.dataobject.AIiDataObject {}\n')
        self.write('java', 'AIigWidgetChoice_1.java',
                   'package eu.algites.tool.codegen.defs.model;\n'
                   'public sealed interface AIigWidgetChoice_1 permits AIigWidgetVariant_1 {}\n')
        self.write('java', 'AIngWidgetKind_1.java',
                   'package eu.algites.tool.codegen.defs.model;\n'
                   'public enum AIngWidgetKind_1 { ONE }\n')
        self.write('java', 'impl/intf/AIigdWidget_1.java',
                   'package eu.algites.tool.codegen.defs.model.impl.intf;\n'
                   'public interface AIigdWidget_1 extends eu.algites.tool.codegen.defs.model.AIigWidget_1 {}\n')
        self.write('java', 'impl/AIcgdWidget_1.java',
                   'package eu.algites.tool.codegen.defs.model.impl;\n'
                   'public class AIcgdWidget_1 implements eu.algites.tool.codegen.defs.model.impl.intf.AIigdWidget_1 {}\n')
        self.write('python', 'aiig_widget_1.py',
                   'class AIigWidget_1(AIiDataObject):\n'
                   '    __data_object__ = AIcdDataObject(description=\'Widget\')\n')
        self.write('python', 'aiig_widget_choice_1.py',
                   'class AIigWidgetChoice_1(object):\n    pass\n')
        self.write('python', 'aing_widget_kind_1.py',
                   'class AIngWidgetKind_1(object):\n    pass\n')
        self.write('python', 'impl/intf/aiigd_widget_1.py',
                   'from eu.algites.tool.codegen.defs.model.aiig_widget_1 import AIigWidget_1\n'
                   'class AIigdWidget_1(AIigWidget_1, AIiSmartDataObject):\n    pass\n')
        self.write('python', 'impl/aicgd_widget_1.py',
                   'from eu.algites.tool.codegen.defs.model.impl.intf.aiigd_widget_1 import AIigdWidget_1\n'
                   'class AIcgdWidget_1(AIigdWidget_1):\n    pass\n')

    def test_refresh_reads_both_generated_roles_from_intf_and_replaces_old_seeds(self):
        self.populate()
        for _, _, output in module.OUTPUTS:
            (output / 'obsolete.py').parent.mkdir(parents=True, exist_ok=True)
            (output / 'obsolete.py').write_text('old', encoding='utf-8')
        # A stale implementation-side generated directory must NOT be an input.
        bad = self.impl / 'java.gen' / PACKAGE_PATH / 'impl/AIcgdBad_1.java'
        bad.parent.mkdir(parents=True, exist_ok=True)
        bad.write_text('public class AIcgdBad_1 {}', encoding='utf-8')
        # Unrelated files outside selected snapshot directories must be untouched.
        legacy = self.repo / 'generators/code/defscodegen/intf/canonical-bootstrap-extgen.json'
        legacy.write_text('legacy', encoding='utf-8')
        module.refresh()
        module.check()
        self.assertTrue(legacy.exists())
        files = module.collect_existing()
        self.assertEqual(len(files), 10)
        for _, _, output in module.OUTPUTS:
            self.assertFalse((output / 'obsolete.py').exists())
        self.assertTrue((self.impl / 'java.extgen' / PACKAGE_PATH / 'impl/AIcgdWidget_1.java').is_file())
        self.assertFalse(any('Bad' in path for path in files))
        self.assertTrue((self.source / 'java.gen' / PACKAGE_PATH / 'impl/AIcgdWidget_1.java').is_file())
        self.assertIn('defs.model.aiig_widget_1',
                      (self.impl / 'python.extgen' / PACKAGE_PATH / 'impl/intf/aiigd_widget_1.py').read_text())

    def test_all_generated_packages_are_promoted_without_rewriting(self):
        """A selected artifact owns every generated package, not only model."""
        self.populate()
        for language, suffix, readname, writable, concrete in (
                ('java', '.java', 'AIigProfile_1', 'AIigdProfile_1', 'AIcgdProfile_1'),
                ('python', '.py', 'aiig_profile_1', 'aiigd_profile_1', 'aicgd_profile_1')):
            src = self.source / (language + '.gen')
            prefix = Path('eu/algites/tool/codegen/defs/naming')
            for rel, body in ((prefix / (readname + suffix),
                               'public interface AIigProfile_1 {}' if language == 'java'
                               else 'class AIigProfile_1: pass'),
                              (prefix / 'impl/intf' / (writable + suffix),
                               'public interface AIigdProfile_1 {}' if language == 'java'
                               else 'class AIigdProfile_1: pass'),
                              (prefix / 'impl' / (concrete + suffix),
                               'public class AIcgdProfile_1 {}' if language == 'java'
                               else 'class AIcgdProfile_1: pass')):
                f = src / rel
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(body + '\n', encoding='utf-8')
        module.refresh()
        for _, src, out in module.OUTPUTS:
            for filename in src.rglob('*'):
                if not filename.is_file():
                    continue
                role = filename.stem.startswith(('AIigd', 'AIcgd', 'aiigd_', 'aicgd_'))
                destination_is_sdo = 'defscodegen/impl/' in str(out)
                if role == destination_is_sdo:
                    self.assertEqual(filename.read_bytes(),
                                     (out / filename.relative_to(src)).read_bytes())

    def test_incomplete_fresh_sdo_does_not_touch_existing_seeds(self):
        self.populate()
        for _, _, output in module.OUTPUTS:
            output.mkdir(parents=True, exist_ok=True)
            (output / 'seed.txt').write_text('unchanged', encoding='utf-8')
        (self.source / 'python.gen' / PACKAGE_PATH / 'impl/intf/aiigd_widget_1.py').unlink()
        with self.assertRaisesRegex(RuntimeError, 'Incomplete python canonical SDO pairs|differs|Missing freshly'):
            module.refresh()
        for _, _, output in module.OUTPUTS:
            self.assertEqual((output / 'seed.txt').read_text(), 'unchanged')
        self.assertFalse(list(self.repo.rglob('*bootstrap-extgen.json')))

    def test_refresh_preserves_source_bytes_and_paths(self):
        self.populate()
        module.refresh()
        for _, source_root, output in module.OUTPUTS:
            for path in output.rglob('*'):
                if not path.is_file():
                    continue
                relative = path.relative_to(output)
                original = source_root / relative
                self.assertEqual(original.read_bytes(), path.read_bytes())
                self.assertNotIn(b'defs.bootstrap.model', path.read_bytes())

    def test_incomplete_generated_source_does_not_delete_old_snapshot(self):
        self.populate()
        for _, _, output in module.OUTPUTS:
            output.mkdir(parents=True, exist_ok=True)
            (output / 'sentinel.txt').write_text('preserve')
        (self.source / 'java.gen' / PACKAGE_PATH / 'impl/intf/AIigdWidget_1.java').unlink()
        with self.assertRaisesRegex(RuntimeError, 'counterpart|pair'):
            module.refresh()
        for _, _, output in module.OUTPUTS:
            self.assertEqual((output / 'sentinel.txt').read_text(), 'preserve')


if __name__ == '__main__':
    unittest.main()
