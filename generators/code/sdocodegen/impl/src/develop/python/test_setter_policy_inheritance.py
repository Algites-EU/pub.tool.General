"""Regression cases for cross-artifact writable generic inheritance."""
from __future__ import annotations
import importlib
import sys
from pathlib import Path
import pytest
from eu.algites.tool.codegen.sdo.impl.standard.aic_sdo_codegen_service import AIcSdoCodegenService


def _write(folder: Path, module: str, body: str):
    target = folder / f'{module}.py'
    target.write_text(body, encoding='utf-8')


def _emit(folder: Path, generated):
    for item in (generated.mutable_interface, generated.implementation):
        target = folder / item.relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(item.source, encoding='utf-8')


def test_nested_generic_setter_refinement_and_mutable_inheritance(tmp_path, monkeypatch):
    package = 'setter_scope_' + tmp_path.name.replace('-', '_')
    root = tmp_path / package
    root.mkdir()
    (root / '__init__.py').touch()
    _write(root, 'aiig_a', '''from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
class AIigA(AIiDataObject):
    __data_object__ = AIcdDataObject(schema_id='sample.a', schema_version=1)
''')
    _write(root, 'aiig_b', '''from .aiig_a import AIigA
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
class AIigB(AIigA):
    __data_object__ = AIcdDataObject(schema_id='sample.b', schema_version=1)
''')
    _write(root, 'aiig_c', '''from __future__ import annotations
from .aiig_a import AIigA
from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField
class AIigC(AIiDataObject):
    __data_object__ = AIcdDataObject(schema_id='sample.c', schema_version=1)
    __data_object_fields__ = (AIcdDataObjectField('A', getter_name='getA'),)
    def getA(self) -> list[AIigA]: ...
''')
    _write(root, 'aiig_d', '''from __future__ import annotations
from .aiig_c import AIigC
from .aiig_b import AIigB
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField
class AIigD(AIigC):
    __data_object__ = AIcdDataObject(schema_id='sample.d', schema_version=1)
    __data_object_fields__ = (AIcdDataObjectField('A', getter_name='getA'),)
    def getA(self) -> list[AIigB]: ...
''')
    monkeypatch.syspath_prepend(str(tmp_path))
    classes = [getattr(importlib.import_module(f'{package}.aiig_{key.lower()}'), f'AIig{key}')
               for key in 'ABCD']
    generator = AIcSdoCodegenService()
    results = [generator.generate(cls) for cls in classes]
    for generated in results:
        _emit(tmp_path, generated)
    mutable = importlib.import_module(package + '.aiigd_d').AIigdD
    mutable_parent = importlib.import_module(package + '.aiigd_c').AIigdC
    concrete = importlib.import_module(package + '.aicgd_d').AIcgdD
    nested = importlib.import_module(package + '.aicgd_b').AIcgdB
    assert issubclass(mutable, mutable_parent)
    assert issubclass(concrete, mutable)
    instance, value = concrete(), nested()
    instance.setA([value])
    assert instance.getA()[0] is value
    assert 'AIigdC[TA]' in results[3].mutable_interface.source
    assert 'def setA(self, a_value: list[TA])' in results[3].mutable_interface.source
    assert "AIigdD['AIigdB']" in results[3].implementation.source


def test_fixed_setter_rejects_refined_getter(tmp_path, monkeypatch):
    from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
    from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
    from eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField
    from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy as Policy
    class AIigA(AIiDataObject):
        pass
    class AIigB(AIigA):
        pass
    class AIigC(AIiDataObject):
        __data_object__ = AIcdDataObject(schema_id='fixed.c', schema_version=1)
        __data_object_fields__ = (AIcdDataObjectField('A', getter_name='getA',
            setter_inheritance_policy=Policy.INHERIT_AS_FIXED_PARAMETER),)
        def getA(self) -> AIigA: ...
    class AIigD(AIigC):
        __data_object__ = AIcdDataObject(schema_id='fixed.d', schema_version=1)
        __data_object_fields__ = (AIcdDataObjectField('A', getter_name='getA'),)
        def getA(self) -> AIigB: ...
    for cls in (AIigA, AIigB, AIigC, AIigD):
        cls.__module__ = 'fixture.module'
    AIigC.getA.__annotations__['return'] = AIigA
    AIigD.getA.__annotations__['return'] = AIigB
    with pytest.raises(ValueError, match='fixed inherited setter'):
        AIcSdoCodegenService().generate(AIigD)
