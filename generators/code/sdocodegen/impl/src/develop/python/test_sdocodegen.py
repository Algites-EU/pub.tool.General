"""Generated Python SmartDataObject types are independent of schema formats."""
import importlib
import sys
from pathlib import Path
import pytest

from eu.algites.tool.codegen.sdo.impl.standard.aic_sdo_codegen_service import AIcSdoCodegenService
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject


@pytest.fixture
def contracts(tmp_path, monkeypatch):
    package = 'contracts_' + tmp_path.name.replace('-', '_')
    loc = tmp_path / package
    loc.mkdir()
    (loc / '__init__.py').write_text('')
    (loc / 'aiig_parent.py').write_text("from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject\nfrom eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField\nfrom eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject\nclass AIigParent(AIiDataObject):\n    __data_object__ = AIcdDataObject(schema_id='tests.parent', schema_version=1)\n    __data_object_fields__ = (AIcdDataObjectField('Name', presence_required=True, getter_name='getName'),)\n    def getName(self): raise NotImplementedError\n")
    (loc / 'aiig_child.py').write_text("from .aiig_parent import AIigParent\nfrom eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField\nfrom eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject\nclass AIigChild(AIigParent):\n    __data_object__ = AIcdDataObject(schema_id='tests.child', schema_version=1)\n    __data_object_fields__ = (AIcdDataObjectField('Amount', getter_name='getAmount'),)\n    def getAmount(self): raise NotImplementedError\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    return tmp_path, importlib.import_module(package + '.aiig_parent').AIigParent, importlib.import_module(package + '.aiig_child').AIigChild


def emit(result, root: Path):
    for item in (result.mutable_interface, result.implementation):
        output = root / item.relative_path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(item.source, encoding='utf-8')


def test_inherited_generated_implementations_and_runtime(contracts):
    root, parent, child = contracts
    generator = AIcSdoCodegenService()
    one, two = generator.generate(parent), generator.generate(child)
    assert one.mutable_interface.type_name == 'AIigdParent'
    assert one.implementation.type_name == 'AIcgdParent'
    assert 'AIcgdParent' in two.implementation.source
    assert 'AIigdParent' in two.mutable_interface.source
    assert 'get_EffectiveField' in one.implementation.source
    emit(one, root)
    emit(two, root)
    pkg = parent.__module__.rsplit('.', 1)[0]
    Parent = importlib.import_module(pkg + '.aicgd_parent').AIcgdParent
    Child = importlib.import_module(pkg + '.aicgd_child').AIcgdChild
    c = Child()
    assert isinstance(c, Parent)
    assert not c.is_ByRawValuesValid()
    c.setName('item')
    c.setAmount(42)
    assert c.getName() == 'item'
    assert c.getAmount() == 42
    assert c.get_Name() == 'item'
    assert c.get_Amount() == 42
    assert c.isPresent_Name()
    c.unset_Name()
    assert not c.isPresent_Name()


def test_handwritten_contract_and_marker(contracts):
    _, parent, _ = contracts
    result = AIcSdoCodegenService().generate(parent, 'sdo')
    assert result.mutable_interface.type_name == 'AIigsdoParent'
    assert result.implementation.type_name == 'AIcgsdoParent'
    assert 'aiigsdo_parent.py' in result.mutable_interface.relative_path
    with pytest.raises(ValueError, match='Invalid'):
        AIcSdoCodegenService().generate(parent, '../')


def test_conflicting_inherited_fields(contracts):
    _, parent, _ = contracts
    from eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField
    class AIigBad(parent):
        __data_object_fields__ = (AIcdDataObjectField('Name', allows_null=True),)
    AIigBad.__module__ = parent.__module__
    with pytest.raises(ValueError, match='Conflicting'):
        AIcSdoCodegenService().generate(AIigBad)


def test_nested_data_object_getter_is_covariant(contracts):
    root, parent, child = contracts
    from eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField
    package = parent.__module__.rsplit('.', 1)[0]
    module = importlib.import_module(parent.__module__)
    class AIigContainer(parent.__bases__[0]):
        __data_object_fields__ = (AIcdDataObjectField('Child', getter_name='getChild'),)
        def getChild(self) -> child: raise NotImplementedError
    AIigContainer.__data_object__ = AIcdDataObject(schema_id='tests.container', schema_version=1)
    AIigContainer.__module__ = parent.__module__
    setattr(module, 'AIigContainer', AIigContainer)
    generator=AIcSdoCodegenService()
    for contract in (parent, child):
        emit(generator.generate(contract), root)
    generated=generator.generate(AIigContainer)
    assert 'def getChild(self) -> AIigdChild' in generated.mutable_interface.source
    assert 'def setChild(self, value: AIigdChild)' in generated.mutable_interface.source
    assert 'def get_Child(self) -> AIigdChild' in generated.mutable_interface.source
    emit(generated, root)
    Container=importlib.import_module(package+'.aicgd_container').AIcgdContainer
    Child=importlib.import_module(package+'.aicgd_child').AIcgdChild
    instance=Container()
    value=Child()
    instance.setChild(value)
    assert instance.getChild() is value and instance.get_Child() is value

import json
from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import AIcSchemaContractBindingsGenerator

def test_schema_nested_reference_passes_mutable_contract_to_sdo(tmp_path, monkeypatch):
    import importlib
    from eu.algites.tool.codegen.sdo.impl.standard.aic_sdo_codegen_service import AIcSdoCodegenService
    package = 'sdopackage_' + tmp_path.name.replace('-', '_')
    schema = tmp_path / 'intf/src/product/jsondefs' / package
    schema.mkdir(parents=True)
    (schema/'child_1.jsondef.schema.json').write_text(json.dumps({
        'type':'object', 'properties':{'Name':{'type':'string'}}, 'required':['Name']}))
    (schema/'container_1.jsondef.schema.json').write_text(json.dumps({
        'type':'object', 'properties':{'Child':{'$ref':'child_1.jsondef.schema.json'}},
        'required':['Child']}))
    manifest = tmp_path/'bindings.json'
    manifest.write_text(json.dumps({'artifact':'intf','languages':['java','python'],'bindings':[]}))
    AIcSchemaContractBindingsGenerator().generate_repository(tmp_path, manifest)
    py = tmp_path/'intf/src/product/python.gen'
    monkeypatch.syspath_prepend(str(py))
    read_child = importlib.import_module(package+'.aiig_child_1').AIigChild_1
    read_container = importlib.import_module(package+'.aiig_container_1').AIigContainer_1
    assert read_container.getChild.__annotations__['return'] == 'AIigChild_1'
    generator = AIcSdoCodegenService()
    for contract in (read_child, read_container):
        generated = generator.generate(contract)
        for unit in (generated.mutable_interface, generated.implementation):
            output = py/unit.relative_path
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(unit.source)
    Container = importlib.import_module(package+'.aicgd_container_1').AIcgdContainer_1
    Child = importlib.import_module(package+'.aicgd_child_1').AIcgdChild_1
    instance, nested = Container(), Child()
    instance.setChild(nested)
    nested.setName('Nested')
    assert instance.getChild() is nested
    assert instance.get_Child().getName() == 'Nested'
    generated = generator.generate(read_container)
    assert 'def getChild(self) -> AIigdChild_1' in generated.mutable_interface.source
    assert 'def setChild(self, value: AIigdChild_1)' in generated.mutable_interface.source


def test_nullable_nested_contract_uses_nullable_mutable_return(contracts):
    _, parent, child = contracts
    from eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField
    module = importlib.import_module(parent.__module__)
    class AIigNullable(parent.__bases__[0]):
        __data_object_fields__ = (AIcdDataObjectField('Child', allows_null=True, getter_name='getChild'),)
        def getChild(self) -> child | None: raise NotImplementedError
    AIigNullable.__data_object__ = AIcdDataObject(schema_id='tests.nullable', schema_version=1)
    AIigNullable.__module__ = parent.__module__
    setattr(module, 'AIigNullable', AIigNullable)
    result = AIcSdoCodegenService().generate(AIigNullable)
    assert 'def getChild(self) -> AIigdChild | None' in result.mutable_interface.source
    assert 'def setChild(self, value: AIigdChild | None)' in result.mutable_interface.source
    assert 'def get_Child(self) -> AIigdChild | None' in result.mutable_interface.source


def test_yaml_named_sdo_setter_parameter_follows_python_profile(contracts):
    from eu.algites.lib.naming.convention.impl.algites.aic_name_convention_catalog_1 import AIcNameConventionCatalog_1
    _, parent, _ = contracts
    catalog = AIcNameConventionCatalog_1.standard('python')
    # The naming-backed path requires versioned DO contracts.
    parent.__name__ = 'AIigParent_1'
    generated = AIcSdoCodegenService().generate(parent, naming=(catalog, catalog, catalog))
    assert 'def setName(self, a_value: object)' in generated.mutable_interface.source
    assert 'def setName(self, a_value)' in generated.implementation.source
    assert "self.set_RawField('Name', a_value)" in generated.implementation.source
    assert catalog.recognize_filename(Path(generated.mutable_interface.relative_path).name,
                                     {'algites-python-gen-data-intf-versioned'}) is not None
    assert catalog.recognize_filename(Path(generated.implementation.relative_path).name,
                                     {'algites-python-gen-data-class-versioned'}) is not None


def test_generated_smartdo_policy_on_interface_and_getter(tmp_path, monkeypatch):
    import importlib
    package = 'policy_contracts'
    folder = tmp_path / package
    folder.mkdir()
    (folder / '__init__.py').write_text('')
    (folder / 'aiig_policy.py').write_text(
        "from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject\n"
        "from eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField\n"
        "from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject\n"
        "from eu.algites.lib.data.smartdataobject.smart_data_object_policy import smart_data_object, smart_data_object_field\n"
        "@smart_data_object(allow_non_present_read=True)\n"
        "class AIigPolicy(AIiDataObject):\n"
        "    __data_object__ = AIcdDataObject(schema_id='tests.policy', schema_version=1)\n"
        "    __data_object_fields__ = (AIcdDataObjectField('Soft', presence_required=True, getter_name='getSoft'), AIcdDataObjectField('Strict', presence_required=True, getter_name='getStrict'))\n"
        "    def getSoft(self): raise NotImplementedError\n"
        "    @smart_data_object_field(allow_non_present_read=False)\n"
        "    def getStrict(self): raise NotImplementedError\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    read_contract = importlib.import_module(package + '.aiig_policy').AIigPolicy
    emit(AIcSdoCodegenService().generate(read_contract), tmp_path)
    generated = importlib.import_module(package + '.aicgd_policy').AIcgdPolicy()
    assert generated.getSoft() is None
    assert generated.get_Soft() is None
    assert not generated.isPresent_Soft()
    assert not generated.is_ByRawValuesValid()
    with pytest.raises(ValueError, match='Required property is absent'):
        generated.getStrict()
