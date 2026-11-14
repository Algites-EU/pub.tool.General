"""Generated mutable contract for AIigType_1."""
from __future__ import annotations
from typing import TypeVar, Generic
from abc import abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.tool.codegen.defs.bootstrap.model.aiig_type_content_1 import AIigTypeContent_1
    from eu.algites.tool.codegen.defs.bootstrap.model.impl.intf.aiigd_source_bindings_1 import AIigdSourceBindings_1
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
from eu.algites.tool.codegen.defs.bootstrap.model.aiig_type_1 import AIigType_1
from eu.algites.lib.data.smartdataobject.aii_smart_data_object import AIiSmartDataObject

TSourceBindings = TypeVar('TSourceBindings', bound='AIigdSourceBindings_1')


class AIigdType_1(AIigType_1, AIiSmartDataObject, Generic[TSourceBindings]):
    __data_object__ = AIcdDataObject(title='', description='Declared or synthetic named type', setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Presence-aware setters, raw getters and unsetters."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Type', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __json_data_object__ = AIaJsonDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Type', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_data_object__ = AIaYamlDataObject(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Type', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __xml_data_object__ = AIaXmlDataObject(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='Type')
    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='Type')
    __xml_data_object_fields__ = {
        'identity': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='identity', value_kind=AInXmlValueKind.ELEMENT),
        'name': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='name', value_kind=AInXmlValueKind.ELEMENT),
        'origin': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='origin', value_kind=AInXmlValueKind.ELEMENT),
        'schema_version': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='schema_version', value_kind=AInXmlValueKind.ELEMENT),
        'description': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='description', value_kind=AInXmlValueKind.ELEMENT),
        'path_segments': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='path_segments', value_kind=AInXmlValueKind.ELEMENT),
        'inherited_from_types': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='inherited_from_types', value_kind=AInXmlValueKind.ELEMENT),
        'content': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='content', value_kind=AInXmlValueKind.ELEMENT),
        'resolution_state': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='resolution_state', value_kind=AInXmlValueKind.ELEMENT),
        'source_bindings': AIaXmlDataObjectField(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='source_bindings', value_kind=AInXmlValueKind.ELEMENT),
    }
    __xml_schema_fields__ = {
        'identity': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='identity', value_kind=AInXmlValueKind.ELEMENT),
        'name': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='name', value_kind=AInXmlValueKind.ELEMENT),
        'origin': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='origin', value_kind=AInXmlValueKind.ELEMENT),
        'schema_version': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='schema_version', value_kind=AInXmlValueKind.ELEMENT),
        'description': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='description', value_kind=AInXmlValueKind.ELEMENT),
        'path_segments': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='path_segments', value_kind=AInXmlValueKind.ELEMENT),
        'inherited_from_types': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='inherited_from_types', value_kind=AInXmlValueKind.ELEMENT),
        'content': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='content', value_kind=AInXmlValueKind.ELEMENT),
        'resolution_state': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='resolution_state', value_kind=AInXmlValueKind.ELEMENT),
        'source_bindings': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='source_bindings', value_kind=AInXmlValueKind.ELEMENT),
    }
    __field_labels__ = {**getattr(AIigType_1, '__field_labels__', {}),
        'Identity': AIaFieldLabel(label='Identity', roleCode='field.name', labels=()),
        'Name': AIaFieldLabel(label='Name', roleCode='field.name', labels=()),
        'Origin': AIaFieldLabel(label='Origin', roleCode='field.name', labels=()),
        'SchemaVersion': AIaFieldLabel(label='Schema version', roleCode='field.name', labels=()),
        'Description': AIaFieldLabel(label='Description', roleCode='field.name', labels=()),
        'PathSegmentsList': AIaFieldLabel(label='Path segments list', roleCode='field.name', labels=()),
        'InheritedFromTypesList': AIaFieldLabel(label='Inherited from types list', roleCode='field.name', labels=()),
        'Content': AIaFieldLabel(label='Content', roleCode='field.name', labels=()),
        'ResolutionState': AIaFieldLabel(label='Resolution state', roleCode='field.name', labels=()),
        'SourceBindings': AIaFieldLabel(label='Source bindings', roleCode='field.name', labels=()),
    }

    @abstractmethod
    def setIdentity(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_Identity(self) -> object: ...

    @abstractmethod
    def _isPresent_Identity(self) -> bool: ...

    @abstractmethod
    def _unset_Identity(self) -> None: ...

    @abstractmethod
    def _setEmpty_Identity(self) -> None: ...

    @abstractmethod
    def _isEmpty_Identity(self) -> bool: ...

    @abstractmethod
    def setName(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_Name(self) -> object: ...

    @abstractmethod
    def _isPresent_Name(self) -> bool: ...

    @abstractmethod
    def _unset_Name(self) -> None: ...

    @abstractmethod
    def _setEmpty_Name(self) -> None: ...

    @abstractmethod
    def _isEmpty_Name(self) -> bool: ...

    @abstractmethod
    def setOrigin(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_Origin(self) -> object: ...

    @abstractmethod
    def _isPresent_Origin(self) -> bool: ...

    @abstractmethod
    def _unset_Origin(self) -> None: ...

    @abstractmethod
    def setSchemaVersion(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_SchemaVersion(self) -> object: ...

    @abstractmethod
    def _isPresent_SchemaVersion(self) -> bool: ...

    @abstractmethod
    def _unset_SchemaVersion(self) -> None: ...

    @abstractmethod
    def _setEmpty_SchemaVersion(self) -> None: ...

    @abstractmethod
    def _isEmpty_SchemaVersion(self) -> bool: ...

    @abstractmethod
    def setDescription(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_Description(self) -> object: ...

    @abstractmethod
    def _isPresent_Description(self) -> bool: ...

    @abstractmethod
    def _unset_Description(self) -> None: ...

    @abstractmethod
    def _setEmpty_Description(self) -> None: ...

    @abstractmethod
    def _isEmpty_Description(self) -> bool: ...

    @abstractmethod
    def _getRaw_PathSegmentsList(self) -> object: ...

    @abstractmethod
    def _isPresent_PathSegmentsList(self) -> bool: ...

    @abstractmethod
    def _unset_PathSegmentsList(self) -> None: ...

    @abstractmethod
    def _getRaw_InheritedFromTypesList(self) -> object: ...

    @abstractmethod
    def _isPresent_InheritedFromTypesList(self) -> bool: ...

    @abstractmethod
    def _unset_InheritedFromTypesList(self) -> None: ...

    @abstractmethod
    def getContent(self) -> AIigTypeContent_1: ...

    @abstractmethod
    def setContent(self, a_value: AIigTypeContent_1) -> None: ...

    @abstractmethod
    def _getRaw_Content(self) -> AIigTypeContent_1: ...

    @abstractmethod
    def _isPresent_Content(self) -> bool: ...

    @abstractmethod
    def _unset_Content(self) -> None: ...

    @abstractmethod
    def setResolutionState(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_ResolutionState(self) -> object: ...

    @abstractmethod
    def _isPresent_ResolutionState(self) -> bool: ...

    @abstractmethod
    def _unset_ResolutionState(self) -> None: ...

    @abstractmethod
    def getSourceBindings(self) -> TSourceBindings: ...

    @abstractmethod
    def setSourceBindings(self, a_value: TSourceBindings) -> None: ...

    @abstractmethod
    def _getRaw_SourceBindings(self) -> TSourceBindings: ...

    @abstractmethod
    def _isPresent_SourceBindings(self) -> bool: ...

    @abstractmethod
    def _unset_SourceBindings(self) -> None: ...
