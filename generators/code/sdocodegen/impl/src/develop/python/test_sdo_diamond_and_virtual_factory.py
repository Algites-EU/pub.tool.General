"""Diamond-inherited SDO contracts retain all parents and their concrete runtime identity."""
import importlib
from pathlib import Path

from eu.algites.tool.codegen.sdo.aic_sdo_codegen_service import AIcSdoCodegenService
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField
from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
from eu.algites.lib.data.smartdataobject.ais_smart_data_object_factory import AIsSmartDataObjectFactory


def test_diamond_contract_generated_and_constructed(tmp_path, monkeypatch):
    package = 'sdo_diamond_case'
    folder = tmp_path / package
    folder.mkdir()
    (folder / '__init__.py').write_text('')
    contracts = {
        'A': ('AIiDataObject', None, 'Name'),
        'B': ('AIigA_1', 'A', 'B'),
        'C': ('AIigA_1', 'A', 'C'),
        'D': ('AIigB_1, AIigC_1', 'B', 'D'),
    }
    for suffix, (parent, _, field) in contracts.items():
        if suffix == 'A':
            imports = 'from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject\n'
        elif suffix == 'D':
            imports = 'from .aiig_b_1 import AIigB_1\nfrom .aiig_c_1 import AIigC_1\n'
        else:
            imports = 'from .aiig_a_1 import AIigA_1\n'
        name = f'AIig{suffix}_1'
        (folder / f'aiig_{suffix.lower()}_1.py').write_text(
            imports + 'from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject\n'
            'from eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField\n'
            f'class {name}({parent}):\n'
            f'    __data_object__ = AIcdDataObject(schema_id="test.diamond.{suffix.lower()}", schema_version=1)\n'
            f'    __data_object_fields__ = (AIcdDataObjectField({field!r}, getter_name={"get"+field!r}),)\n'
            f'    def get{field}(self): raise NotImplementedError\n')
    monkeypatch.syspath_prepend(str(tmp_path))
    generator = AIcSdoCodegenService()
    for suffix in contracts:
        module = importlib.import_module(f'{package}.aiig_{suffix.lower()}_1')
        result = generator.generate(getattr(module, f'AIig{suffix}_1'))
        for source in (result.mutable_interface, result.implementation):
            path = tmp_path / source.relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source.source)
    mutable_b = importlib.import_module(f'{package}.aiigd_b_1').AIigdB_1
    mutable_c = importlib.import_module(f'{package}.aiigd_c_1').AIigdC_1
    cls = importlib.import_module(f'{package}.aicgd_d_1').AIcgdD_1
    value = cls()
    assert isinstance(value, mutable_b) and isinstance(value, mutable_c)
    value.setName('shared')
    value.setB('b')
    value.setC('c')
    value.setD('d')
    assert value.getName() == 'shared'
    mapping = value.toMapping_RawValues()
    assert mapping['Name'].value_representation == 'shared'
    duplicate = AIsSmartDataObjectFactory.from_mapping(cls, mapping)
    assert duplicate.getName() == 'shared'
    assert duplicate.getD() == 'd'
    assert duplicate.__data_object__.schema_id == 'test.diamond.d'
