"""Generated mutable contract for AIigDefscodegenNamingConventionsPropertyDefsCodegenNameConventions_1."""
from __future__ import annotations
from typing import TypeVar, Generic
from abc import abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.tool.codegen.defs.naming.impl.intf.aiigd_defscodegen_naming_conventions_property_name_conventions_1 import AIigdDefscodegenNamingConventionsPropertyNameConventions_1
from eu.algites.lib.data.dataobject.yamldefs.aia_data_object_yaml_schema import AIaDataObjectYamlSchema
from eu.algites.lib.data.dataobject.jsondefs.aia_data_object_json_schema import AIaDataObjectJsonSchema
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.common.object.props.labels.aia_field_label import AIaFieldLabel
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.tool.codegen.defs.naming.aiig_defscodegen_naming_conventions_property_defs_codegen_name_conventions_1 import AIigDefscodegenNamingConventionsPropertyDefsCodegenNameConventions_1
from eu.algites.lib.data.smartdataobject.aii_smart_data_object import AIiSmartDataObject

TNameConventions = TypeVar('TNameConventions', bound='AIigdDefscodegenNamingConventionsPropertyNameConventions_1')


class AIigdDefscodegenNamingConventionsPropertyDefsCodegenNameConventions_1(AIigDefscodegenNamingConventionsPropertyDefsCodegenNameConventions_1, AIiSmartDataObject, Generic[TNameConventions]):
    __data_object__ = AIcdDataObject(title='', description='DefscodegenNamingConventionsPropertyDefsCodegenNameConventions', setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Presence-aware setters, raw getters and unsetters."""
    __json_schema__ = AIaDataObjectJsonSchema(schema_id='generators/code/defscodegen/intf/src/product/jsondefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.jsondef.schema.json#/properties/DefsCodegenNameConventions#synthetic:synthetic_property_type', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __yaml_schema__ = AIaDataObjectYamlSchema(schema_id='generators/code/defscodegen/intf/src/product/yamldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.yamldef.schema.json#/properties/DefsCodegenNameConventions#synthetic:synthetic_property_type', schema_version=1, schema_url='', data_source_schema_url_field='', data_source_schema_identifier_field='', data_source_schema_version_field='')
    __field_labels__ = {**getattr(AIigDefscodegenNamingConventionsPropertyDefsCodegenNameConventions_1, '__field_labels__', {}),
        'NameConventions': AIaFieldLabel(label='Name conventions', roleCode='field.name', labels=()),
    }

    @abstractmethod
    def getNameConventions(self) -> TNameConventions: ...

    @abstractmethod
    def setNameConventions(self, a_value: TNameConventions) -> None: ...

    @abstractmethod
    def _getRaw_NameConventions(self) -> TNameConventions: ...

    @abstractmethod
    def _isPresent_NameConventions(self) -> bool: ...

    @abstractmethod
    def _unset_NameConventions(self) -> None: ...
