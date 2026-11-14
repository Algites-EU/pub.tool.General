"""Regression tests for the canonical compiler-ABI promotion source ownership."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).with_name('promote-canonical-extgen.py')
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
        file = self.source / (language + '.gen') / module.OLD_PATH / relative
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
        bad = self.impl / 'java.gen' / module.OLD_PATH / 'impl/AIcgdBad_1.java'
        bad.parent.mkdir(parents=True, exist_ok=True)
        bad.write_text('public class AIcgdBad_1 {}', encoding='utf-8')
        # Older checkouts may contain a retired sidecar; refresh removes it.
        legacy = self.repo / 'generators/code/defscodegen/intf/canonical-bootstrap-extgen.json'
        legacy.write_text('legacy', encoding='utf-8')
        module.refresh()
        module.check()
        self.assertFalse(legacy.exists())
        files = module.collect_existing()
        self.assertEqual(len(files), 10)
        for _, _, output in module.OUTPUTS:
            self.assertFalse((output / 'obsolete.py').exists())
        self.assertTrue((self.impl / 'java.extgen' / module.NEW_PATH / 'impl/AIcgdWidget_1.java').is_file())
        self.assertFalse(any('Bad' in path for path in files))
        self.assertTrue((self.source / 'java.gen' / module.OLD_PATH / 'impl/AIcgdWidget_1.java').is_file())
        self.assertIn('defs.bootstrap.model.aiig_widget_1',
                      (self.impl / 'python.extgen' / module.NEW_PATH / 'impl/intf/aiigd_widget_1.py').read_text())

    def test_incomplete_fresh_sdo_does_not_touch_existing_seeds(self):
        self.populate()
        for _, _, output in module.OUTPUTS:
            output.mkdir(parents=True, exist_ok=True)
            (output / 'seed.txt').write_text('unchanged', encoding='utf-8')
        (self.source / 'python.gen' / module.OLD_PATH / 'impl/intf/aiigd_widget_1.py').unlink()
        with self.assertRaisesRegex(RuntimeError, 'Incomplete python canonical SDO pairs|differs|Missing freshly'):
            module.refresh()
        for _, _, output in module.OUTPUTS:
            self.assertEqual((output / 'seed.txt').read_text(), 'unchanged')
        self.assertFalse(list(self.repo.rglob('*bootstrap-extgen.json')))

    def test_refresh_defs_skips_mutable_files_in_same_generated_directory(self):
        self.populate()
        module.refresh()
        # The explicitly supported Defs-only refresh must not inadvertently
        # absorb the already present SDO files into the read-only root.
        module.refresh_defs()
        module.check()
        self.assertFalse(any('/impl/' in path for path in module.collect_existing()
                             if '/intf/src/product/' in path))


if __name__ == '__main__':
    unittest.main()
