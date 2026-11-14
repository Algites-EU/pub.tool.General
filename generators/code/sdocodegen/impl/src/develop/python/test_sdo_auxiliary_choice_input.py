"""Only annotated DataObjects, not XML choice markers, are SDO inputs."""
from pathlib import Path

from eu.algites.tool.codegen.sdo.impl.standard.aic_sdo_codegen_service import AIcSdoCodegenService


def test_unannotated_choice_marker_is_not_an_implicit_sdo_input(tmp_path: Path):
    """A marker with an Algites-looking name is still not a DataObject."""
    rel = Path('eu/algites/tool/codegen/sdo/aiig_choice_marker_1.py')
    file = tmp_path / rel
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text('class AIigChoiceMarker_1:\n    pass\n', encoding='utf-8')
    actual = AIcSdoCodegenService().generate_from_sources(
        tmp_path, {rel: 'AIigChoiceMarker_1'}, enabled_roles={'common'})
    assert actual == {}


def test_direct_annotated_dataobject_remains_an_input(tmp_path: Path, monkeypatch):
    """Do not discard a real DataObject because XML markers exist beside it."""
    rel = Path('eu/algites/tool/codegen/sdo/aiig_annotated_probe_1.py')
    file = tmp_path / rel
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(
        'from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject\n'
        'from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject\n'
        'class AIigAnnotatedProbe_1(AIiDataObject):\n'
        '    __data_object__ = AIcdDataObject()\n', encoding='utf-8')
    value = object()
    service = AIcSdoCodegenService()
    monkeypatch.setattr(service, 'generate', lambda *_args, **_kwargs: value)
    actual = service.generate_from_sources(
        tmp_path, {rel: 'AIigAnnotatedProbe_1'}, enabled_roles={'common'})
    assert actual == {file: value}


def test_unannotated_nested_dataobject_is_not_rewritten_as_sdo():
    """Nested helper with DO ancestry alone cannot acquire phantom AIigd types."""
    from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
    from eu.algites.tool.codegen.sdo.impl.standard.aic_sdo_codegen_service import (
        _nested_contract, _is_sdo_input)

    class ChoiceHelper(AIiDataObject):
        pass

    class Parent(AIiDataObject):
        def getContent(self) -> ChoiceHelper:
            raise NotImplementedError

    assert not _is_sdo_input(ChoiceHelper)
    assert _nested_contract(Parent, 'getContent', 'Content') is None


class AIigAuxiliaryChoice_1:
    """Read-only helper built by Defs Codegen, not itself a DataObject."""
    __xml_choice_variant_imports__ = ('example:Example',)


class AIigAuxiliaryContent_1:
    """Another read-only helper; its writable name must never be fabricated."""
    __xml_choice_variant_imports__ = ('example:Content',)


def test_auxiliary_choice_fields_keep_read_only_type_annotations():
    """Python mirrors Java: helper fields retain their actual typed interfaces."""
    from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
    from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
    from eu.algites.lib.data.dataobject.aia_data_object_field import AIaDataObjectField
    from explicit_sdo_fixture import configured_service

    class AIigChoiceContainer_1(AIiDataObject):
        __data_object__ = AIcdDataObject()

        @AIaDataObjectField(dataFieldName='Segments')
        def getSegmentsList(self) -> list[AIigAuxiliaryChoice_1]: ...

        @AIaDataObjectField(dataFieldName='Content')
        def getContent(self) -> AIigAuxiliaryContent_1: ...

    # A generated read-only DataObject normally resides in a nested package.
    AIigChoiceContainer_1.__module__ = 'fixture.read_contracts'
    # The read-only definitions are actual module-global classes; no
    # SDO module is generated for either choice interface.
    value = configured_service().generate(AIigChoiceContainer_1)
    for text in (value.mutable_interface.source, value.implementation.source):
        assert 'list[AIigAuxiliaryChoice_1]' in text
        assert 'AIigAuxiliaryContent_1' in text
        assert 'AIigdAuxiliaryChoice_1' not in text
        assert 'AIigdAuxiliaryContent_1' not in text


def test_type_checking_only_choice_import_retains_nested_type(tmp_path: Path, monkeypatch):
    """Defs' TYPE_CHECKING-only imports are resolved by their declared modules."""
    from importlib import import_module
    from eu.algites.tool.codegen.sdo.impl.standard.aic_sdo_codegen_service import (
        _auxiliary_read_only_contract, _field_annotation)

    package = tmp_path / 'choice_lazy_annotations'
    package.mkdir()
    (package / '__init__.py').touch()
    (package / 'choice.py').write_text(
        'class AIigChoice_1:\n'
        '    __xml_choice_variant_imports__ = ("choice:Example",)\n', encoding='utf-8')
    (package / 'contract.py').write_text(
        'from __future__ import annotations\n'
        'from typing import TYPE_CHECKING\n'
        'if TYPE_CHECKING:\n'
        '    from .choice import AIigChoice_1\n'
        'class AIigContainer_1:\n'
        '    def getSegmentsList(self) -> list[AIigChoice_1]: ...\n', encoding='utf-8')
    monkeypatch.syspath_prepend(str(tmp_path))
    contract = import_module('choice_lazy_annotations.contract').AIigContainer_1
    assert str(_field_annotation(contract, 'getSegmentsList', 'Segments')).endswith(
        'choice_lazy_annotations.choice.AIigChoice_1]')
    helper = _auxiliary_read_only_contract(contract, 'getSegmentsList', 'Segments')
    assert helper is not None and helper[0].__name__ == 'AIigChoice_1'
    assert helper[2] is True
