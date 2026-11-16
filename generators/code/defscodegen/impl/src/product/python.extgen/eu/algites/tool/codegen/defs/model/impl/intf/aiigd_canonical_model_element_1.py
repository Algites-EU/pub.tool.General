"""Generated mutable contract for AIigCanonicalModelElement_1."""
from __future__ import annotations
from typing import TypeVar, Generic
from abc import abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.lib.common.list.aii_bounded_list import AIiBoundedList
    from eu.algites.tool.codegen.defs.model.impl.intf.aiigd_type_1 import AIigdType_1
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_field_xml_schema import AIaDataObjectFieldXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_xml_schema import AIaDataObjectXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.common.object.props.labels.aia_field_label import AIaFieldLabel
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.tool.codegen.defs.model.aiig_canonical_model_element_1 import AIigCanonicalModelElement_1
from eu.algites.lib.data.smartdataobject.aii_smart_data_object import AIiSmartDataObject

TTypesList = TypeVar('TTypesList', bound='AIigdType_1')


class AIigdCanonicalModelElement_1(AIigCanonicalModelElement_1, AIiSmartDataObject, Generic[TTypesList]):
    __data_object__ = AIcdDataObject(title='', description='CanonicalModelElement', setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Presence-aware setters, raw getters and unsetters."""
    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.ELEMENT, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='CanonicalModel')
    __xml_schema_fields__ = {
        'TypesList': AIaDataObjectFieldXmlSchema(namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd', namespace_local_name='types', value_kind=AInXmlValueKind.ELEMENT),
    }
    __field_labels__ = {**getattr(AIigCanonicalModelElement_1, '__field_labels__', {}),
        'TypesList': AIaFieldLabel(label='Types list', roleCode='field.name', labels=()),
    }

    @abstractmethod
    def getTypesList(self) -> AIiBoundedList[TTypesList]: ...

    @abstractmethod
    def _getRaw_TypesList(self) -> AIiBoundedList[TTypesList]: ...

    @abstractmethod
    def _isPresent_TypesList(self) -> bool: ...

    @abstractmethod
    def _unset_TypesList(self) -> None: ...
