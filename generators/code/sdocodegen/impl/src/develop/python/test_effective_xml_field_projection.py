"""XML wire overlays must join inherited semantic fields without invented QNames."""
import pytest

from eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField
from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object_field import AIaXmlDataObjectField
from eu.algites.tool.codegen.sdo.impl.standard.aic_sdo_codegen_service import _effective_xml_fields
from eu.algites.tool.codegen.common.aix_codegen_validation_exception import AIxCodegenValidationException


class Common:
    """Shared schema-neutral shape, including a non-XML nested field."""
    __data_object_fields__ = (
        AIcdDataObjectField('Child'),
        AIcdDataObjectField('SourceBindings'),
    )


class Xml(Common):
    """XML projection of only the explicitly mapped child."""
    __xml_schema_fields__ = {
        'Child': AIaXmlDataObjectField(namespace_local_name='Child'),
    }


def test_explicit_xml_child_is_joined_without_mapping_shared_fields():
    fields = {field.name: field for field in Common.__data_object_fields__}
    effective = _effective_xml_fields(Xml, fields)
    assert list(effective) == ['Child', 'SourceBindings']
    assert effective['Child'].wire.namespace_local_name == 'Child'
    assert effective['SourceBindings'].wire is None
    assert effective['SourceBindings'].descriptor is fields['SourceBindings']


def test_orphan_xml_mapping_is_not_silently_ignored():
    class Invalid(Common):
        __xml_schema_fields__ = {'Other': AIaXmlDataObjectField(namespace_local_name='Other')}
    with pytest.raises(AIxCodegenValidationException, match='no inherited DataObject field'):
        _effective_xml_fields(Invalid, {field.name: field for field in Common.__data_object_fields__})
