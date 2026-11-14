"""Generated mutable contract for AIigEnum_1."""
from __future__ import annotations
from typing import TypeVar, Generic
from abc import abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.lib.common.list.aii_bounded_list import AIiBoundedList
    from eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.aiigd_enum_value_1 import AIigdEnumValue_1
from eu.algites.lib.data.dataobject.xmlschema.aia_data_object_field_xml_schema import AIaDataObjectFieldXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object_field import AIaXmlDataObjectField
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind
from eu.algites.lib.data.dataobject.xmlschema.aia_data_object_xml_schema import AIaDataObjectXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object import AIaXmlDataObject
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind
from eu.algites.lib.data.dataobject.yamldefs.aia_yaml_data_object import AIaYamlDataObject
from eu.algites.lib.data.dataobject.jsondefs.aia_json_data_object import AIaJsonDataObject
from eu.algites.lib.data.dataobject.jsonschema.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.common.object.props.labels.aia_field_label import AIaFieldLabel
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.tool.codegen.defs.bootstrap.model.aiig_enum_1 import AIigEnum_1
from eu.algites.lib.data.smartdataobject.aii_smart_data_object import AIiSmartDataObject

TValuesList = TypeVar('TValuesList', bound='AIigdEnumValue_1')


class AIigdEnum_1(AIigEnum_1, AIiSmartDataObject, Generic[TValuesList]):
    __data_object__ = AIcdDataObject(title='', description='Canonical enumeration', setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Presence-aware setters, raw getters and unsetters."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Enum', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __json_data_object__ = AIaJsonDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Enum', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_data_object__ = AIaYamlDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Enum', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __xml_data_object__ = AIaXmlDataObject(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='Enum')
    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='Enum')
    __xml_data_object_fields__ = {
        'base_scalar_type': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='base_scalar_type', value_kind=AInXmlValueKind.ELEMENT),
        'values': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='values', value_kind=AInXmlValueKind.ELEMENT),
    }
    __xml_schema_fields__ = {
        'base_scalar_type': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='base_scalar_type', value_kind=AInXmlValueKind.ELEMENT),
        'values': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='values', value_kind=AInXmlValueKind.ELEMENT),
    }
    __field_labels__ = {**getattr(AIigEnum_1, '__field_labels__', {}),
        'BaseScalarType': AIaFieldLabel(label='Base scalar type', roleCode='field.name', labels=()),
        'ValuesList': AIaFieldLabel(label='Values list', roleCode='field.name', labels=()),
    }

    @abstractmethod
    def setBaseScalarType(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_BaseScalarType(self) -> object: ...

    @abstractmethod
    def _isPresent_BaseScalarType(self) -> bool: ...

    @abstractmethod
    def _unset_BaseScalarType(self) -> None: ...

    @abstractmethod
    def getValuesList(self) -> AIiBoundedList[TValuesList]: ...

    @abstractmethod
    def _getRaw_ValuesList(self) -> AIiBoundedList[TValuesList]: ...

    @abstractmethod
    def _isPresent_ValuesList(self) -> bool: ...

    @abstractmethod
    def _unset_ValuesList(self) -> None: ...
