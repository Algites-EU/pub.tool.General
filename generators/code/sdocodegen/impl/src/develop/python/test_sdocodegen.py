from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind
"""Generated Python SmartDataObject types are independent of schema formats."""
import importlib
import sys
from pathlib import Path
import pytest

from eu.algites.tool.codegen.sdo.impl.standard.aic_sdo_codegen_service import AIcSdoCodegenService
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject


class AItcConfiguredSdoGenerator:
    """Test-only adapter that supplies an explicit legacy naming profile.

    Production generators deliberately reject missing profiles; old fixture
    contracts use the Algites names, so their tests must select that profile.
    """
    def __init__(self):
        self.service = AIcSdoCodegenService()

    @staticmethod
    def _naming(read_contract, configured=None):
        from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import (
            AIcNameConventionCatalog)
        from eu.algites.lib.data.dataobject.jsondefs.aii_json_data_object import AIiJsonDataObject
        from eu.algites.lib.data.dataobject.yamldefs.aii_yaml_data_object import AIiYamlDataObject
        from eu.algites.lib.data.dataobject.xmldefs.aii_xml_data_object import AIiXmlDataObject
        from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind
        if configured is None:
            common = Path(__file__).resolve().parents[8]
            library = common/'pub.lib.General/naming/convention/profile/algites/src/product/config/eu/algites/lib/naming/convention'
            tool = common/'pub.tool.General/generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention'
            catalog = AIcNameConventionCatalog.load_many([
                library/'algites-python-name-conventions.yml',
                tool/'algites-python-codegen-method-conventions.yml',
            ]).with_generated_method_profile('algites-python-codegen-standard_1')
        else:
            catalog = configured[-1]
        if issubclass(read_contract, AIiXmlDataObject):
            kind = getattr(getattr(read_contract, '__xml_data_object__', None), 'definition_kind', None)
            role = 'xmldefs_element' if kind is AInXmlObjectDefinitionKind.ELEMENT else 'xmldefs_type'
        elif issubclass(read_contract, AIiJsonDataObject):
            role = 'jsondefs'
        elif issubclass(read_contract, AIiYamlDataObject):
            role = 'yamldefs'
        else:
            role = 'common'
        versioned = bool(__import__('re').search(r'_[1-9][0-9]*$', read_contract.__name__))
        suffix = '-versioned_1' if versioned else '_1'
        input_kind = 'intf'
        source_name = read_contract.__name__
        if source_name.startswith('AIi') and not source_name.startswith('AIig'):
            input_kind = 'intf'  # Non-generated handwritten contracts use a distinct prefix.
            input_profile = 'algites-python-intf' + suffix
        else:
            input_profile = 'algites-python-gen-intf' + suffix
        source_annotation = getattr(read_contract, '__data_object__', None)
        specific = getattr(source_annotation, 'naming_convention', '')
        if specific:
            input_profile = specific
        mutable_profile = 'algites-python-gen-data-intf' + suffix
        concrete_profile = 'algites-python-gen-data-class' + suffix
        if configured is not None:
            selected_catalog = configured[0]
        else:
            selected_catalog = catalog
        input_roles = {role: input_profile}
        mutable_roles = {role: mutable_profile}
        concrete_roles = {role: concrete_profile}
        if role == 'xmldefs_element':
            # XML substitution heads and generated elements can inherit from
            # a named XML type, so both roles are required by this fixture.
            input_roles['xmldefs_type'] = 'algites-python-gen-intf' + suffix
            mutable_roles['xmldefs_type'] = mutable_profile
            concrete_roles['xmldefs_type'] = concrete_profile
        return (input_roles, mutable_roles, concrete_roles, selected_catalog)

    def generate(self, read_contract, marker='d', naming=None,
                 mutable_subpackage='', concrete_subpackage=''):
        return self.service.generate(read_contract, marker,
            self._naming(read_contract, naming), mutable_subpackage, concrete_subpackage)

    def generate_from_sources(self, source_root, contract_sources, marker='d',
                              dependency_classpath=(), naming=None, mutable_subpackage='',
                              concrete_subpackage='', enabled_roles=None):
        if naming is None:
            # The source API accepts one profile for a set of contracts, and
            # handwritten test source trees use the unversioned naming family.
            from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
            class AIigTest(AIiDataObject):
                pass
            naming = self._naming(AIigTest)
        return self.service.generate_from_sources(source_root, contract_sources,
            marker, naming, mutable_subpackage, concrete_subpackage, enabled_roles)


def configured_service():
    """Select fixture-specific naming without altering production defaults."""
    return AItcConfiguredSdoGenerator()


@pytest.fixture
def contracts(tmp_path, monkeypatch):
    package = 'contracts_' + tmp_path.name.replace('-', '_')
    loc = tmp_path / package
    loc.mkdir()
    (loc / '__init__.py').write_text('')
    (loc / 'aiig_parent.py').write_text("from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject\nfrom eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField\nfrom eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject\nfrom eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind\nclass AIigParent(AIiDataObject):\n    __data_object__ = AIcdDataObject(schema_id='tests.parent', schema_version=1)\n    __data_object_fields__ = (AIcdDataObjectField('Name', presence=AInFieldPresenceKind.REQUIRED, getter_name='getName'),)\n    def getName(self): raise NotImplementedError\n")
    (loc / 'aiig_child.py').write_text("from .aiig_parent import AIigParent\nfrom eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField\nfrom eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject\nfrom eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind\nclass AIigChild(AIigParent):\n    __data_object__ = AIcdDataObject(schema_id='tests.child', schema_version=1)\n    __data_object_fields__ = (AIcdDataObjectField('Amount', getter_name='getAmount'),)\n    def getAmount(self): raise NotImplementedError\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    return tmp_path, importlib.import_module(package + '.aiig_parent').AIigParent, importlib.import_module(package + '.aiig_child').AIigChild


def emit(result, root: Path):
    for item in (result.mutable_interface, result.implementation):
        output = root / item.relative_path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(item.source, encoding='utf-8')


def test_inherited_generated_implementations_and_runtime(contracts):
    root, parent, child = contracts
    generator = configured_service()
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
    assert c._getRaw_Name() == 'item'
    assert c._getRaw_Amount() == 42
    assert c._isPresent_Name()
    c._unset_Name()
    assert not c._isPresent_Name()


def test_handwritten_contract_and_marker(contracts):
    _, parent, _ = contracts
    result = configured_service().generate(parent, 'sdo')
    assert result.mutable_interface.type_name == 'AIigdParent'
    assert result.implementation.type_name == 'AIcgdParent'
    assert 'aiigd_parent.py' in result.mutable_interface.relative_path
    with pytest.raises(ValueError, match='Invalid'):
        configured_service().generate(parent, '../')


def test_conflicting_inherited_fields(contracts):
    _, parent, _ = contracts
    from eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField
    class AIigBad(parent):
        __data_object_fields__ = (AIcdDataObjectField('Name', allows_null=True, getter_name='getName'),)
    AIigBad.__module__ = parent.__module__
    with pytest.raises(ValueError, match='Invalid inherited presence restriction'):
        configured_service().generate(AIigBad)


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
    generator=configured_service()
    for contract in (parent, child):
        emit(generator.generate(contract), root)
    generated=generator.generate(AIigContainer)
    assert 'def getChild(self) -> TChild' in generated.mutable_interface.source
    assert 'def setChild(self, a_value: TChild)' in generated.mutable_interface.source
    assert 'def _getRaw_Child(self) -> TChild' in generated.mutable_interface.source
    emit(generated, root)
    Container=importlib.import_module(package+'.aicgd_container').AIcgdContainer
    Child=importlib.import_module(package+'.aicgd_child').AIcgdChild
    instance=Container()
    value=Child()
    instance.setChild(value)
    assert instance.getChild() is value and instance._getRaw_Child() is value

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
    from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import AIcSchemaContractBindingsGenerator
    from importlib.util import spec_from_file_location, module_from_spec
    fixture_path = Path(__file__).resolve().parents[5] / 'defscodegen/impl/src/develop/python/explicit_naming_fixture.py'
    fixture_spec = spec_from_file_location('explicit_naming_fixture_sdo', fixture_path)
    fixture_module = module_from_spec(fixture_spec)
    fixture_spec.loader.exec_module(fixture_module)
    manifest.write_text(json.dumps(fixture_module.explicit_algites_manifest(json.loads(manifest.read_text()))))
    AIcSchemaContractBindingsGenerator().generate_repository(tmp_path, manifest)
    py = tmp_path/'intf/src/product/python.gen'
    monkeypatch.syspath_prepend(str(py))
    read_child = importlib.import_module(package+'.aiig_child_1').AIigChild_1
    read_container = importlib.import_module(package+'.aiig_container_1').AIigContainer_1
    assert read_container.getChild.__annotations__['return'] == 'AIigChild_1'
    generator = configured_service()
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
    assert instance._getRaw_Child().getName() == 'Nested'
    generated = generator.generate(read_container)
    assert 'def getChild(self) -> TChild' in generated.mutable_interface.source
    assert 'def setChild(self, a_value: TChild)' in generated.mutable_interface.source


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
    result = configured_service().generate(AIigNullable)
    assert 'def getChild(self) -> TChild | None' in result.mutable_interface.source
    assert 'def setChild(self, a_value: TChild | None)' in result.mutable_interface.source
    assert 'def _getRaw_Child(self) -> TChild | None' in result.mutable_interface.source


def test_yaml_named_sdo_setter_parameter_follows_python_profile(contracts):
    from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import AIcNameConventionCatalog
    _, parent, _ = contracts
    catalog = AIcNameConventionCatalog.load_resource('algites-python-name-conventions.yml')
    # The naming-backed path requires versioned DO contracts.
    parent.__name__ = 'AIigParent_1'
    generated = configured_service().generate(parent, naming=(catalog, catalog, catalog))
    assert 'def setName(self, a_value: object)' in generated.mutable_interface.source
    assert 'def setName(self, a_value)' in generated.implementation.source
    assert "self.set_RawField('Name', a_value)" in generated.implementation.source
    assert catalog.recognize_filename(Path(generated.mutable_interface.relative_path).name,
                                     {'algites-python-gen-data-intf-versioned_1'}) is not None
    assert catalog.recognize_filename(Path(generated.implementation.relative_path).name,
                                     {'algites-python-gen-data-class-versioned_1'}) is not None


def test_generated_smartdo_policy_on_interface_and_getter(tmp_path, monkeypatch):
    import importlib
    package = 'policy_contracts'
    folder = tmp_path / package
    folder.mkdir()
    (folder / '__init__.py').write_text('')
    (folder / 'aiig_policy.py').write_text(
        "from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject\n"
        "from eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField\n"
        "from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject\nfrom eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind\n"
        "from eu.algites.lib.data.smartdataobject.smart_data_object_policy import smart_data_object, smart_data_object_field\n"
        "@smart_data_object(allow_non_present_read=True)\n"
        "class AIigPolicy(AIiDataObject):\n"
        "    __data_object__ = AIcdDataObject(schema_id='tests.policy', schema_version=1)\n"
        "    __data_object_fields__ = (AIcdDataObjectField('Soft', presence=AInFieldPresenceKind.REQUIRED, getter_name='getSoft'), AIcdDataObjectField('Strict', presence=AInFieldPresenceKind.REQUIRED, getter_name='getStrict'))\n"
        "    def getSoft(self): raise NotImplementedError\n"
        "    @smart_data_object_field(allow_non_present_read=False)\n"
        "    def getStrict(self): raise NotImplementedError\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    read_contract = importlib.import_module(package + '.aiig_policy').AIigPolicy
    emit(configured_service().generate(read_contract), tmp_path)
    generated = importlib.import_module(package + '.aicgd_policy').AIcgdPolicy()
    assert generated.getSoft() is None
    assert generated._getRaw_Soft() is None
    assert not generated._isPresent_Soft()
    assert not generated.is_ByRawValuesValid()
    with pytest.raises(ValueError, match='Required property is absent'):
        generated.getStrict()


def test_generate_from_uncompiled_source_tree(contracts):
    root, parent, child = contracts
    package = parent.__module__.split('.')[0]
    src_base = root / package / 'aiig_parent.py'
    src_child = root / package / 'aiig_child.py'
    output = configured_service().generate_from_sources(root, {
        src_base: 'AIigParent', src_child: 'AIigChild'})
    assert output[src_base.resolve()].mutable_interface.type_name == 'AIigdParent'
    assert 'AIigdParent' in output[src_child.resolve()].mutable_interface.source
    assert 'AIcgdParent' in output[src_child.resolve()].implementation.source


def test_source_loader_rejects_path_escape(contracts, tmp_path):
    root, _, _ = contracts
    outside = root.parent / 'outside_contract.py'
    outside.write_text('class AIigOutside: pass')
    with pytest.raises(ValueError, match='Invalid DO contract source'):
        configured_service().generate_from_sources(root, {outside: 'AIigOutside'})


def test_user_defined_setter_method_composition_is_used_by_sdo():
    """A custom setter syntax must not be derived from the read getter prefix."""
    from copy import deepcopy
    from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
    from eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField
    from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import AIcNameConventionCatalog

    class AIigInvoice_1(AIiDataObject):
        __data_object__ = AIcdDataObject(schema_id='test.invoice', schema_version=1,
            naming_convention='algites-python-gen-intf-versioned_1')
        __data_object_fields__ = (AIcdDataObjectField(field_name='Name', getter_name='getName'),)
        def getName(self):
            raise NotImplementedError

    AIigInvoice_1.__module__ = 'example.contracts.aiig_invoice_1'
    source = AIcNameConventionCatalog.load_resource('algites-python-name-conventions.yml')
    config = deepcopy(source._config)
    config['NameCompositions']['python-setter-method-name_1']['Segments'][0]['Value'] = 'write'
    catalog = AIcNameConventionCatalog(config)
    result = configured_service().generate(AIigInvoice_1, naming=(catalog, catalog, catalog))
    assert 'def writeName(self' in result.mutable_interface.source
    assert 'def writeName(self' in result.implementation.source
    assert 'def setName(self' not in result.mutable_interface.source
    assert 'def get_Name(self' in result.mutable_interface.source
    assert 'def get_ReadName(self' not in result.mutable_interface.source
    assert 'def getName(self' in result.implementation.source


def test_custom_getter_without_explicit_getter_metadata_uses_selected_convention():
    """SDO resolves implicit read getters from the selected profile, not a built-in prefix."""
    from copy import deepcopy
    from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
    from eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField
    from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import AIcNameConventionCatalog

    from eu.algites.lib.data.dataobject.aia_data_object_field import AIaDataObjectField
    class AIigInvoice_1(AIiDataObject):
        __data_object__ = AIcdDataObject(schema_id='test.invoice', schema_version=1,
            naming_convention='algites-python-gen-intf-versioned_1')
        @AIaDataObjectField(field_name='Name')
        def readName(self):
            raise NotImplementedError

    AIigInvoice_1.__module__ = 'example.contracts.aiig_invoice_1'
    source = AIcNameConventionCatalog.load_resource('algites-python-name-conventions.yml')
    config = deepcopy(source._config)
    config['NameCompositions']['python-getter-method-name_1']['Segments'][0]['Value'] = 'read'
    config['NameCompositions']['python-setter-method-name_1']['Segments'][0]['Value'] = 'write'
    catalog = AIcNameConventionCatalog(config)
    result = configured_service().generate(AIigInvoice_1, naming=(catalog, catalog, catalog))
    # Scalar read methods are inherited from the input contract rather than redeclared.
    assert 'def readName(self' in result.implementation.source
    assert 'def writeName(self' in result.mutable_interface.source
    assert 'def writeName(self' in result.implementation.source
    assert 'def getName(self' not in result.implementation.source
    assert 'def setName(self' not in result.implementation.source
    assert 'def get_Name(self' in result.mutable_interface.source
    assert 'def isPresent_Name(self' in result.mutable_interface.source
    assert 'def unset_Name(self' in result.mutable_interface.source


def test_shared_generated_method_profile_controls_real_sdo_emission(contracts, tmp_path):
    """Custom naming composition must change emitted field methods without implicit prefixes."""
    import yaml
    from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import AIcNameConventionCatalog

    _, parent, _ = contracts
    root = Path(__file__).resolve().parents[8]
    library = root / 'pub.lib.General/naming/convention/profile/algites/src/product/config/eu/algites/lib/naming/convention'
    tool = root / 'pub.tool.General/generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention'
    config = yaml.safe_load((tool / 'algites-python-codegen-method-conventions.yml').read_text())
    config['NameCompositions']['custom-sdo-raw-getter'] = {'Segments': [
        {'Kind': 'constant_string', 'Value': 'rawValue'},
        {'Kind': 'identifier', 'Convention': 'upper_camel_case_1'},
    ]}
    config['GeneratedDataObjectMethodNameConventions']['NameConventions'][
        'algites-python-codegen-standard_1']['StructureNaming'][
        'raw_getter'] = 'custom-sdo-raw-getter'
    custom_file = tmp_path / 'custom-sdo-methods.yml'
    custom_file.write_text(yaml.safe_dump(config), encoding='utf-8')
    catalog = AIcNameConventionCatalog.load_many([
        library / 'algites-python-name-conventions.yml', custom_file,
    ]).with_generated_method_profile('algites-python-codegen-standard_1')
    parent.__name__ = 'AIigParent_1'
    generated = configured_service().generate(parent, naming=(catalog, catalog, catalog, catalog))
    assert 'def rawValueName(self)' in generated.mutable_interface.source
    assert 'def rawValueName(self)' in generated.implementation.source
    assert 'def _isPresent_Name(self)' in generated.mutable_interface.source
    assert 'def _unset_Name(self)' in generated.mutable_interface.source
    assert 'def _getRaw_Name(self)' not in generated.implementation.source

@pytest.mark.parametrize('disabled', ('raw_getter', 'raw_presence_checker_method',
                                     'raw_unsetter', 'all'))
def test_unconfigured_raw_methods_are_not_emitted(contracts, tmp_path, disabled):
    """Absent or empty raw compositions omit both the abstract and concrete method."""
    import yaml
    from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import AIcNameConventionCatalog

    _, parent, _ = contracts
    repository = Path(__file__).resolve().parents[8]
    lib = repository / 'pub.lib.General/naming/convention/profile/algites/src/product/config/eu/algites/lib/naming/convention'
    shared = repository / 'pub.tool.General/generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention'
    source = yaml.safe_load((shared / 'algites-python-codegen-method-conventions.yml').read_text())
    rules = source['GeneratedDataObjectMethodNameConventions']['NameConventions'][
        'algites-python-codegen-standard_1']['StructureNaming']
    keys = ('raw_getter', 'raw_presence_checker_method', 'raw_unsetter')
    if disabled == 'all':
        for key in keys:
            rules.pop(key)
    else:
        rules[disabled] = ''
    filename = tmp_path / 'optional-raw.yml'
    filename.write_text(yaml.safe_dump(source), encoding='utf-8')
    catalog = AIcNameConventionCatalog.load_many([
        lib / 'algites-python-name-conventions.yml', filename,
    ]).with_generated_method_profile('algites-python-codegen-standard_1')
    parent.__name__ = 'AIigParent_1'
    result = configured_service().generate(parent, naming=(catalog, catalog, catalog, catalog))
    for key, name in zip(keys, ('_getRaw_Name', '_isPresent_Name', '_unset_Name')):
        active = disabled != 'all' and key != disabled
        for output in (result.mutable_interface.source, result.implementation.source):
            assert (f'def {name}(' in output) == active
    assert 'def setName(' in result.mutable_interface.source
    assert 'def getName(' in result.implementation.source


def test_decorated_getter_semantic_identity_is_independent_of_field_name():
    """A Python getter defines one canonical SDO field; the wire key is opaque."""
    from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
    from eu.algites.lib.data.dataobject.aia_data_object_field import AIaDataObjectField

    class AIigCustomer(AIiDataObject):
        __data_object__ = AIcdDataObject(schema_id='test.customer', schema_version=1)
        @AIaDataObjectField(field_name='external_customer_id')
        def getCustomerId(self): ...

    AIigCustomer.__module__ = 'example.contracts.aiig_customer'
    result = configured_service().generate(AIigCustomer)
    source = result.implementation.source
    assert "self.set_RawField('CustomerId'" in source
    assert "self.get_EffectiveField('CustomerId'" in source
    assert 'def setCustomerId(' in source
    assert 'def setExternalCustomerId(' not in source
