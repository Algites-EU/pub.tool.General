"""Generated mutable contract for AIigSchemaFieldBindings_1."""
from __future__ import annotations
from typing import TypeVar, Generic
from abc import abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.lib.common.list.aii_bounded_list import AIiBoundedList
    from eu.algites.tool.codegen.defs.impl.intf.aiigd_field_binding_type_1 import AIigdFieldBindingType_1
from eu.algites.lib.data.dataobject.yamldefs.aia_data_object_yaml_schema import AIaDataObjectYamlSchema
from eu.algites.lib.data.dataobject.jsondefs.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.common.object.props.labels.aia_field_label import AIaFieldLabel
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.tool.codegen.defs.aiig_schema_field_bindings_1 import AIigSchemaFieldBindings_1
from eu.algites.lib.data.smartdataobject.aii_smart_data_object import AIiSmartDataObject

TBindingsList = TypeVar('TBindingsList', bound='AIigdFieldBindingType_1')


class AIigdSchemaFieldBindings_1(AIigSchemaFieldBindings_1, AIiSmartDataObject, Generic[TBindingsList]):
    __data_object__ = AIcdDataObject(title='', description='Generator instructions identifying canonical JSON Schema resources and optional field-binding projections.', setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Presence-aware setters, raw getters and unsetters."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.schema-field-bindings', schema_version=1, schema_url='https://defs.dev.algites.eu/api/jsondefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.jsondef.schema.json', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.schema-field-bindings', schema_version=1, schema_url='https://defs.dev.algites.eu/api/yamldefs/eu/algites/tool/codegen/defs/schema-field-bindings_1.yamldef.schema.json', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __field_labels__ = {**getattr(AIigSchemaFieldBindings_1, '__field_labels__', {}),
        'Artifact': AIaFieldLabel(label='Artifact', roleCode='field.name', labels=()),
        'ImplementationArtifact': AIaFieldLabel(label='Implementation artifact', roleCode='field.name', labels=()),
        'LanguagesList': AIaFieldLabel(label='Languages list', roleCode='field.name', labels=()),
        'BindingsList': AIaFieldLabel(label='Bindings list', roleCode='field.name', labels=()),
    }

    @abstractmethod
    def setArtifact(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_Artifact(self) -> object: ...

    @abstractmethod
    def _isPresent_Artifact(self) -> bool: ...

    @abstractmethod
    def _unset_Artifact(self) -> None: ...

    @abstractmethod
    def setImplementationArtifact(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_ImplementationArtifact(self) -> object: ...

    @abstractmethod
    def _isPresent_ImplementationArtifact(self) -> bool: ...

    @abstractmethod
    def _unset_ImplementationArtifact(self) -> None: ...

    @abstractmethod
    def _getRaw_LanguagesList(self) -> object: ...

    @abstractmethod
    def _isPresent_LanguagesList(self) -> bool: ...

    @abstractmethod
    def _unset_LanguagesList(self) -> None: ...

    @abstractmethod
    def getBindingsList(self) -> AIiBoundedList[TBindingsList]: ...

    @abstractmethod
    def _getRaw_BindingsList(self) -> AIiBoundedList[TBindingsList]: ...

    @abstractmethod
    def _isPresent_BindingsList(self) -> bool: ...

    @abstractmethod
    def _unset_BindingsList(self) -> None: ...
