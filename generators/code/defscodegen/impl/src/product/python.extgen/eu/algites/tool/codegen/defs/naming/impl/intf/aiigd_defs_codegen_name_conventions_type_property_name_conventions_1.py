"""Generated mutable contract for AIigDefsCodegenNameConventionsTypePropertyNameConventions_1."""
from __future__ import annotations
from typing import TypeVar, Generic
from abc import abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.lib.common.list.aii_multi_mapped_list import AIiMultiMappedList
    from eu.algites.tool.codegen.defs.naming.impl.intf.aiigd_defs_codegen_name_convention_1 import AIigdDefsCodegenNameConvention_1
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_field_xml_schema import AIaDataObjectFieldXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.common.object.props.labels.aia_field_label import AIaFieldLabel
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.tool.codegen.defs.naming.aiig_defs_codegen_name_conventions_type_property_name_conventions_1 import AIigDefsCodegenNameConventionsTypePropertyNameConventions_1
from eu.algites.lib.data.smartdataobject.aii_smart_data_object import AIiSmartDataObject

TNameConventionList = TypeVar('TNameConventionList', bound='AIigdDefsCodegenNameConvention_1')


class AIigdDefsCodegenNameConventionsTypePropertyNameConventions_1(AIigDefsCodegenNameConventionsTypePropertyNameConventions_1, AIiSmartDataObject, Generic[TNameConventionList]):
    __data_object__ = AIcdDataObject(title='', description='DefsCodegenNameConventionsTypePropertyNameConventions', setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Presence-aware setters, raw getters and unsetters."""
    __xml_schema_fields__ = {
        'NameConventionList': AIaDataObjectFieldXmlSchema(namespace='', namespace_local_name='NameConvention', value_kind=AInXmlValueKind.ELEMENT),
    }
    __field_labels__ = {**getattr(AIigDefsCodegenNameConventionsTypePropertyNameConventions_1, '__field_labels__', {}),
        'NameConventionList': AIaFieldLabel(label='Name convention list', roleCode='field.name', labels=()),
    }

    @abstractmethod
    def getNameConventionList(self) -> AIiMultiMappedList[TNameConventionList]: ...

    @abstractmethod
    def _getRaw_NameConventionList(self) -> AIiMultiMappedList[TNameConventionList]: ...

    @abstractmethod
    def _isPresent_NameConventionList(self) -> bool: ...

    @abstractmethod
    def _unset_NameConventionList(self) -> None: ...
