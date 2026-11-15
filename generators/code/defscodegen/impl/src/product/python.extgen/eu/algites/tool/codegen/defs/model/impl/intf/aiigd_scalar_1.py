"""Generated mutable contract for AIigScalar_1."""
from __future__ import annotations
from abc import abstractmethod
from eu.algites.tool.codegen.defs.model.aiig_scalar_1 import AIigScalar_1
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_field_xml_schema import AIaDataObjectFieldXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_xml_schema import AIaDataObjectXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind
from eu.algites.lib.data.dataobject.yamldefs.aia_data_object_yaml_schema import AIaDataObjectYamlSchema
from eu.algites.lib.data.dataobject.jsondefs.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.common.object.props.labels.aia_field_label import AIaFieldLabel
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.lib.data.smartdataobject.aii_smart_data_object import AIiSmartDataObject


class AIigdScalar_1(AIigScalar_1, AIiSmartDataObject):
    __data_object__ = AIcdDataObject(title='', description='Canonical scalar value', setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Presence-aware setters, raw getters and unsetters."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Scalar', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Scalar', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='Scalar')
    __xml_schema_fields__ = {
        'ScalarKind': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='scalar_kind', value_kind=AInXmlValueKind.ELEMENT),
        'Format': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='format', value_kind=AInXmlValueKind.ELEMENT),
        'MinLength': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='min_length', value_kind=AInXmlValueKind.ELEMENT),
        'MaxLength': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='max_length', value_kind=AInXmlValueKind.ELEMENT),
        'Pattern': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='pattern', value_kind=AInXmlValueKind.ELEMENT),
        'Minimum': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='minimum', value_kind=AInXmlValueKind.ELEMENT),
        'Maximum': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='maximum', value_kind=AInXmlValueKind.ELEMENT),
        'ExclusiveMinimum': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='exclusive_minimum', value_kind=AInXmlValueKind.ELEMENT),
        'ExclusiveMaximum': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='exclusive_maximum', value_kind=AInXmlValueKind.ELEMENT),
        'MultipleOf': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='multiple_of', value_kind=AInXmlValueKind.ELEMENT),
    }
    __field_labels__ = {**getattr(AIigScalar_1, '__field_labels__', {}),
        'ScalarKind': AIaFieldLabel(label='Scalar kind', roleCode='field.name', labels=()),
        'Format': AIaFieldLabel(label='Format', roleCode='field.name', labels=()),
        'MinLength': AIaFieldLabel(label='Min length', roleCode='field.name', labels=()),
        'MaxLength': AIaFieldLabel(label='Max length', roleCode='field.name', labels=()),
        'Pattern': AIaFieldLabel(label='Pattern', roleCode='field.name', labels=()),
        'Minimum': AIaFieldLabel(label='Minimum', roleCode='field.name', labels=()),
        'Maximum': AIaFieldLabel(label='Maximum', roleCode='field.name', labels=()),
        'ExclusiveMinimum': AIaFieldLabel(label='Exclusive minimum', roleCode='field.name', labels=()),
        'ExclusiveMaximum': AIaFieldLabel(label='Exclusive maximum', roleCode='field.name', labels=()),
        'MultipleOf': AIaFieldLabel(label='Multiple of', roleCode='field.name', labels=()),
    }

    @abstractmethod
    def setScalarKind(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_ScalarKind(self) -> object: ...

    @abstractmethod
    def _isPresent_ScalarKind(self) -> bool: ...

    @abstractmethod
    def _unset_ScalarKind(self) -> None: ...

    @abstractmethod
    def setFormat(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_Format(self) -> object: ...

    @abstractmethod
    def _isPresent_Format(self) -> bool: ...

    @abstractmethod
    def _unset_Format(self) -> None: ...

    @abstractmethod
    def _setEmpty_Format(self) -> None: ...

    @abstractmethod
    def _isEmpty_Format(self) -> bool: ...

    @abstractmethod
    def setMinLength(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_MinLength(self) -> object: ...

    @abstractmethod
    def _isPresent_MinLength(self) -> bool: ...

    @abstractmethod
    def _unset_MinLength(self) -> None: ...

    @abstractmethod
    def setMaxLength(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_MaxLength(self) -> object: ...

    @abstractmethod
    def _isPresent_MaxLength(self) -> bool: ...

    @abstractmethod
    def _unset_MaxLength(self) -> None: ...

    @abstractmethod
    def setPattern(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_Pattern(self) -> object: ...

    @abstractmethod
    def _isPresent_Pattern(self) -> bool: ...

    @abstractmethod
    def _unset_Pattern(self) -> None: ...

    @abstractmethod
    def _setEmpty_Pattern(self) -> None: ...

    @abstractmethod
    def _isEmpty_Pattern(self) -> bool: ...

    @abstractmethod
    def setMinimum(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_Minimum(self) -> object: ...

    @abstractmethod
    def _isPresent_Minimum(self) -> bool: ...

    @abstractmethod
    def _unset_Minimum(self) -> None: ...

    @abstractmethod
    def _setEmpty_Minimum(self) -> None: ...

    @abstractmethod
    def _isEmpty_Minimum(self) -> bool: ...

    @abstractmethod
    def setMaximum(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_Maximum(self) -> object: ...

    @abstractmethod
    def _isPresent_Maximum(self) -> bool: ...

    @abstractmethod
    def _unset_Maximum(self) -> None: ...

    @abstractmethod
    def _setEmpty_Maximum(self) -> None: ...

    @abstractmethod
    def _isEmpty_Maximum(self) -> bool: ...

    @abstractmethod
    def setExclusiveMinimum(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_ExclusiveMinimum(self) -> object: ...

    @abstractmethod
    def _isPresent_ExclusiveMinimum(self) -> bool: ...

    @abstractmethod
    def _unset_ExclusiveMinimum(self) -> None: ...

    @abstractmethod
    def setExclusiveMaximum(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_ExclusiveMaximum(self) -> object: ...

    @abstractmethod
    def _isPresent_ExclusiveMaximum(self) -> bool: ...

    @abstractmethod
    def _unset_ExclusiveMaximum(self) -> None: ...

    @abstractmethod
    def setMultipleOf(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_MultipleOf(self) -> object: ...

    @abstractmethod
    def _isPresent_MultipleOf(self) -> bool: ...

    @abstractmethod
    def _unset_MultipleOf(self) -> None: ...

    @abstractmethod
    def _setEmpty_MultipleOf(self) -> None: ...

    @abstractmethod
    def _isEmpty_MultipleOf(self) -> bool: ...
