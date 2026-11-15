"""Standalone SDO requires schema-neutral metadata, direct or inherited.

Read-only helper interfaces without an annotated DataObject ancestor are never
turned into writable types merely because their names resemble DO contracts.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_java_sdo_requires_schema_neutral_metadata_including_ancestors():
    """Java eligibility and nested-writable conversion must agree."""
    path = ROOT / ('generators/code/sdocodegen/impl/src/product/java/'
                   'eu/algites/tool/codegen/sdo/impl/standard/AIcSdoCodegenService.java')
    source = path.read_text(encoding='utf-8')
    assert 'commonDataObjectMetadata(aClass) == null' in source
    assert 'if (!isSdoInput(aReadContract))' in source
    assert 'if (isSdoInput(locRaw)) return locRaw;' in source
    assert 'if (isSdoInput(locReturn)) {' in source
    assert 'AIiXmlDataObject.class.isAssignableFrom(aClass)' not in source


def test_python_sdo_requires_schema_neutral_metadata_including_ancestors():
    """Python uses the same annotated-or-neutral-descendant rule."""
    path = ROOT / ('generators/code/sdocodegen/impl/src/product/python/'
                   'eu/algites/tool/codegen/sdo/impl/standard/aic_sdo_codegen_service.py')
    source = path.read_text(encoding='utf-8')
    assert "getattr(contract, '__data_object__', None) is None" in source
    assert 'not issubclass(contract, (AIiXmlDataObject,' not in source
    assert 'if isclass(annotation) and _is_sdo_input(annotation):' in source
