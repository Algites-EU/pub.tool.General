"""Generated mutable contract for AIigDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1."""
from __future__ import annotations
from typing import TypeVar, Generic
from abc import abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.tool.codegen.defs.naming.impl.intf.aiigd_defs_codegen_name_conventions_type_property_name_conventions_1 import AIigdDefsCodegenNameConventionsTypePropertyNameConventions_1
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_field_xml_schema import AIaDataObjectFieldXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_xml_schema import AIaDataObjectXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.common.object.props.labels.aia_field_label import AIaFieldLabel
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.tool.codegen.defs.naming.aiig_defs_codegen_name_conventions_type_property_defs_codegen_name_conventions_1 import AIigDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1
from eu.algites.lib.data.smartdataobject.aii_smart_data_object import AIiSmartDataObject

TNameConventions = TypeVar('TNameConventions', bound='AIigdDefsCodegenNameConventionsTypePropertyNameConventions_1')


class AIigdDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1(AIigDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1, AIiSmartDataObject, Generic[TNameConventions]):
    __data_object__ = AIcdDataObject(title='', description='DefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions', setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Presence-aware setters, raw getters and unsetters."""
    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='', namespace_local_name='generators/code/defscodegen/intf/src/product/xmldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.xsd/schema/DefsCodegenNameConventionsType/complexContent/extension/sequence/sequence/0#synthetic:synthetic_property_type')
    __xml_schema_fields__ = {
        'NameConventions': AIaDataObjectFieldXmlSchema(namespace='', namespace_local_name='NameConventions', value_kind=AInXmlValueKind.ELEMENT),
    }
    __field_labels__ = {**getattr(AIigDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1, '__field_labels__', {}),
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
