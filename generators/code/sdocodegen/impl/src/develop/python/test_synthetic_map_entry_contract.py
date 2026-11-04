"""Regression coverage for JSON/YAML virtual map-entry values in the independent SDO engine."""
from __future__ import annotations

from abc import abstractmethod
from pathlib import Path
import pytest

from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.jsondefs.aii_json_data_object import AIiJsonDataObject
from eu.algites.lib.data.dataobject.yamldefs.aii_yaml_data_object import AIiYamlDataObject
from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import AIcNameConventionCatalog
from eu.algites.tool.codegen.sdo.impl.standard.aic_sdo_codegen_service import AIcSdoCodegenService
from eu.algites.tool.codegen.sdo.old.impl.standard.aic_sdo_codegen_service import AIcSdoCodegenService as AIcLegacySdoCodegenService


def _naming(legacy=False):
    """Resolve Common and SDO profiles from the checked-in catalog files."""
    checkout = Path(__file__).resolve().parents[8]
    catalog = AIcNameConventionCatalog.load_many([
        checkout / 'pub.lib.General/naming/convention/intf/src/product/config/eu/algites/lib/naming/convention/standard-conventions.yml',
        checkout / 'pub.lib.General/naming/convention/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode/algites-python-name-conventions.yml',
        *([checkout / 'pub.tool.General/generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode/algites-python-codegen-method-conventions.yml'] if legacy else [
            checkout / 'pub.tool.General/generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode/algites-python-common-codegen-conventions.yml',
            checkout / 'pub.tool.General/generators/code/profile/algites/src/product/config/eu/algites/lib/naming/convention/sourcecode/algites-python-sdo-codegen-conventions.yml']),
    ])
    catalog = (catalog.with_generated_method_profile('algites-python-codegen-standard_1') if legacy else
               catalog.with_codegen_naming_profiles('algites-python-codegen-common_1',
                                    'algites-python-sdocodegen-standard_1', 'sdo'))
    read = {kind: 'algites-python-gen-intf-versioned_1' for kind in ('jsondefs', 'yamldefs')}
    mutable = {kind: 'algites-python-gen-data-' + ('json' if kind == 'jsondefs' else 'yaml') + '-intf-versioned_1'
               for kind in ('jsondefs', 'yamldefs')}
    implementation = {kind: 'algites-python-gen-data-' + ('json' if kind == 'jsondefs' else 'yaml') + '-class-versioned_1'
                      for kind in ('jsondefs', 'yamldefs')}
    return read, mutable, implementation, catalog


class TestSyntheticMapEntryContract:
    """Functional tests grouped by the business contract, not a snapshot number."""

    @staticmethod
    @pytest.mark.parametrize('legacy', (False, True), ids=('independent-sdo', 'bootstrap-sdo'))
    @pytest.mark.parametrize('parent', (AIiJsonDataObject, AIiYamlDataObject))
    def test_virtual_key_and_value_are_not_serialized_fields(parent, legacy):
        """Generate both virtual accessors; retain a ctor-supplied value without a duplicate serialized field."""
        class AIigMapEntry_1(parent):
            __data_object__ = AIcdDataObject(schema_id='test.virtual.entry', schema_version=1,
                                            naming_convention='algites-python-gen-intf-versioned_1')

            @abstractmethod
            def _getKey(self) -> str:
                """The real property name in the containing object."""

            @abstractmethod
            def _getValue(self) -> tuple[str, ...]:
                """The typed property value in the containing object."""

        AIigMapEntry_1.__module__ = 'test.virtual.aiig_map_entry_1'
        result = (AIcLegacySdoCodegenService() if legacy else AIcSdoCodegenService()).generate(
            AIigMapEntry_1, naming=_naming(legacy))
        code = result.implementation.source
        compile(code, '<synthetic-entry>', 'exec')
        assert 'def _getKey(self)' in code
        assert 'def _getValue(self)' in code
        assert 'self._parent_property_value = parent_property_value' in code
        assert 'return self._parent_property_value' in code
        assert "self.get_EffectiveField('_getValue')" not in code
        assert "self.set_RawField('_getValue'" not in code
        assert 'def setValue(' not in result.mutable_interface.source

    @staticmethod
    def test_map_value_without_key_is_rejected():
        """A stand-alone value accessor cannot represent an additional-property entry."""
        class AIigInvalidEntry_1(AIiJsonDataObject):
            __data_object__ = AIcdDataObject(schema_id='test.virtual.invalid', schema_version=1)

            def _getValue(self) -> tuple[str, ...]:
                """This contract is invalid because it loses the parent key."""

        AIigInvalidEntry_1.__module__ = 'test.virtual.aiig_invalid_entry_1'
        with pytest.raises(ValueError, match='requires a virtual key getter'):
            AIcSdoCodegenService().generate(AIigInvalidEntry_1, naming=_naming())
