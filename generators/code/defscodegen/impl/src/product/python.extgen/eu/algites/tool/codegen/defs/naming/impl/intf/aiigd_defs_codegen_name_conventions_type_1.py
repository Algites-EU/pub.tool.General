"""Generated mutable contract for AIigDefsCodegenNameConventionsType_1."""
from __future__ import annotations
from typing import TypeVar, Generic
from abc import abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eu.algites.lib.naming.convention.impl.intf.aiigd_identifier_conventions_1 import AIigdIdentifierConventions_1
    from eu.algites.lib.naming.convention.impl.intf.aiigd_name_compositions_1 import AIigdNameCompositions_1
    from eu.algites.lib.naming.convention.impl.intf.aiigd_name_fragments_1 import AIigdNameFragments_1
    from eu.algites.lib.naming.convention.impl.intf.aiigd_version_conventions_1 import AIigdVersionConventions_1
    from eu.algites.tool.codegen.defs.naming.impl.intf.aiigd_defs_codegen_name_conventions_type_property_defs_codegen_name_conventions_1 import AIigdDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_field_xml_schema import AIaDataObjectFieldXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind
from eu.algites.lib.data.dataobject.xmldefs.aia_data_object_xml_schema import AIaDataObjectXmlSchema
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.common.object.props.labels.aia_field_label import AIaFieldLabel
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy
from eu.algites.tool.codegen.defs.naming.aiig_defs_codegen_name_conventions_type_1 import AIigDefsCodegenNameConventionsType_1
from eu.algites.lib.data.smartdataobject.aii_smart_data_object import AIiSmartDataObject
from eu.algites.lib.naming.convention.impl.intf.aiigd_common_naming_conventions_1 import AIigdCommonNamingConventions_1

TIdentifierConventions = TypeVar('TIdentifierConventions', bound='AIigdIdentifierConventions_1')
TVersionConventions = TypeVar('TVersionConventions', bound='AIigdVersionConventions_1')
TNameFragments = TypeVar('TNameFragments', bound='AIigdNameFragments_1')
TNameCompositions = TypeVar('TNameCompositions', bound='AIigdNameCompositions_1')
TDefsCodegenNameConventions = TypeVar('TDefsCodegenNameConventions', bound='AIigdDefsCodegenNameConventionsTypePropertyDefsCodegenNameConventions_1')


class AIigdDefsCodegenNameConventionsType_1(AIigDefsCodegenNameConventionsType_1, AIigdCommonNamingConventions_1[TIdentifierConventions, TVersionConventions, TNameFragments, TNameCompositions], AIiSmartDataObject, Generic[TIdentifierConventions, TVersionConventions, TNameFragments, TNameCompositions, TDefsCodegenNameConventions]):
    __data_object__ = AIcdDataObject(title='', description='DefsCodegenNameConventionsType', setter_inheritance_policy=AInFieldSetterInheritancePolicy.INHERIT_AS_GENERIC_PARAMETER)
    """Presence-aware setters, raw getters and unsetters."""
    __xml_schema__ = AIaDataObjectXmlSchema(definition_kind=AInXmlObjectDefinitionKind.TYPE, namespace='https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/naming/defscodegen-naming-conventions_1.xsd', namespace_local_name='DefsCodegenNameConventionsType')
    __xml_schema_fields__ = {
        'DefsCodegenNameConventions': AIaDataObjectFieldXmlSchema(namespace='', namespace_local_name='DefsCodegenNameConventions', value_kind=AInXmlValueKind.ELEMENT),
    }
    __field_labels__ = {**getattr(AIigDefsCodegenNameConventionsType_1, '__field_labels__', {}),
        'StandardConventionsFile': AIaFieldLabel(label='Standard conventions file', roleCode='field.name', labels=()),
        'IdentifierConventions': AIaFieldLabel(label='Identifier conventions', roleCode='field.name', labels=()),
        'VersionConventions': AIaFieldLabel(label='Version conventions', roleCode='field.name', labels=()),
        'NameFragments': AIaFieldLabel(label='Name fragments', roleCode='field.name', labels=()),
        'NameCompositions': AIaFieldLabel(label='Name compositions', roleCode='field.name', labels=()),
        'DefsCodegenNameConventions': AIaFieldLabel(label='Defs codegen name conventions', roleCode='field.name', labels=()),
    }

    @abstractmethod
    def setStandardConventionsFile(self, a_value: object) -> None: ...

    @abstractmethod
    def _getRaw_StandardConventionsFile(self) -> object: ...

    @abstractmethod
    def _isPresent_StandardConventionsFile(self) -> bool: ...

    @abstractmethod
    def _unset_StandardConventionsFile(self) -> None: ...

    @abstractmethod
    def _setEmpty_StandardConventionsFile(self) -> None: ...

    @abstractmethod
    def _isEmpty_StandardConventionsFile(self) -> bool: ...

    @abstractmethod
    def getIdentifierConventions(self) -> TIdentifierConventions: ...

    @abstractmethod
    def setIdentifierConventions(self, a_value: TIdentifierConventions) -> None: ...

    @abstractmethod
    def _getRaw_IdentifierConventions(self) -> TIdentifierConventions: ...

    @abstractmethod
    def _isPresent_IdentifierConventions(self) -> bool: ...

    @abstractmethod
    def _unset_IdentifierConventions(self) -> None: ...

    @abstractmethod
    def getVersionConventions(self) -> TVersionConventions: ...

    @abstractmethod
    def setVersionConventions(self, a_value: TVersionConventions) -> None: ...

    @abstractmethod
    def _getRaw_VersionConventions(self) -> TVersionConventions: ...

    @abstractmethod
    def _isPresent_VersionConventions(self) -> bool: ...

    @abstractmethod
    def _unset_VersionConventions(self) -> None: ...

    @abstractmethod
    def getNameFragments(self) -> TNameFragments: ...

    @abstractmethod
    def setNameFragments(self, a_value: TNameFragments) -> None: ...

    @abstractmethod
    def _getRaw_NameFragments(self) -> TNameFragments: ...

    @abstractmethod
    def _isPresent_NameFragments(self) -> bool: ...

    @abstractmethod
    def _unset_NameFragments(self) -> None: ...

    @abstractmethod
    def getNameCompositions(self) -> TNameCompositions: ...

    @abstractmethod
    def setNameCompositions(self, a_value: TNameCompositions) -> None: ...

    @abstractmethod
    def _getRaw_NameCompositions(self) -> TNameCompositions: ...

    @abstractmethod
    def _isPresent_NameCompositions(self) -> bool: ...

    @abstractmethod
    def _unset_NameCompositions(self) -> None: ...

    @abstractmethod
    def getDefsCodegenNameConventions(self) -> TDefsCodegenNameConventions: ...

    @abstractmethod
    def setDefsCodegenNameConventions(self, a_value: TDefsCodegenNameConventions) -> None: ...

    @abstractmethod
    def _getRaw_DefsCodegenNameConventions(self) -> TDefsCodegenNameConventions: ...

    @abstractmethod
    def _isPresent_DefsCodegenNameConventions(self) -> bool: ...

    @abstractmethod
    def _unset_DefsCodegenNameConventions(self) -> None: ...
