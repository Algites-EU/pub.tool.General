"""Keep the Defs read-only model separate from mutable SDO output.

The first-stage ABI snapshot is generated from a single canonical contract
family, without separate technology-specific interfaces.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / 'generators/code/defscodegen'
JAVA_IMPL = MODEL / 'impl/src/product/java/eu/algites/tool/codegen/defs/impl/standard/model'
READ = MODEL / 'intf/src/product'
MUTABLE = MODEL / 'impl/src/product'
PKG = 'eu/algites/tool/codegen/defs/model'


def test_handwritten_canonical_classes_belong_to_defs_not_sdo():
    """Defs frontend owns the canonical structures, SDO owns none of them."""
    assert len(list(JAVA_IMPL.glob('AIcDefsCanonical*.java'))) == 14
    assert (JAVA_IMPL / 'AIiDefsCanonicalStructure.java').is_file()
    assert not list(JAVA_IMPL.glob('AI*SdoCanonical*.java'))


def test_one_writable_family_extends_one_read_only_family():
    """The current ABI contains only shared read and writable contracts."""
    java_read = READ / 'java.extgen' / PKG / 'AIigElement_1.java'
    py_read = READ / 'python.extgen' / PKG / 'aiig_element_1.py'
    java_write = MUTABLE / 'java.extgen' / PKG / 'impl/intf/AIigdElement_1.java'
    py_write = MUTABLE / 'python.extgen' / PKG / 'impl/intf/aiigd_element_1.py'
    assert all(p.is_file() for p in (java_read, py_read, java_write, py_write))
    assert 'extends eu.algites.tool.codegen.defs.model.AIigElement_1' in java_write.read_text()
    assert 'AIigElement_1' in py_write.read_text()
    assert not any('AIiJsonSmartDataObject' in p.read_text()
                   for p in (java_read, java_write))
    assert len(list((READ / 'java.extgen').rglob('AIigElement_1.java'))) == 1
    assert len(list((MUTABLE / 'java.extgen').rglob('AIigdElement_1.java'))) == 1
