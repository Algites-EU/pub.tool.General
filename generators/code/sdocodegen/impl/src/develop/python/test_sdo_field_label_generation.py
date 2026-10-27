"""Regression checks for localized metadata in handwritten SmartDO read contracts."""
from eu.algites.lib.common.object.props.labels.aia_field_label import AIaFieldLabel
from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject
from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject
from eu.algites.lib.data.dataobject.aicd_data_object_field import AIcdDataObjectField
from explicit_sdo_fixture import configured_service, explicit_generic_manifest


class AIiTestDocument_1(AIiDataObject):
    """Simulates a manually maintained, importable read-only contract."""
    __module__ = 'test.documents.contract'
    __data_object__ = AIcdDataObject(schema_id='test:document', schema_version=1)
    __data_object_fields__ = (
        AIcdDataObjectField(field_name='CertificatePrivateKey',
                            getter_name='getCertificatePrivateKey'),
        AIcdDataObjectField(field_name='Password', getter_name='getPassword'),
    )

    def getCertificatePrivateKey(self):
        """Return the signing key."""

    @AIaFieldLabel(label='User-specified password label')
    def getPassword(self):
        """Return the password."""


def test_sdo_fallback_labels_and_explicit_inheritance():
    generated = configured_service().generate(AIiTestDocument_1, 'd')
    source = generated.mutable_interface.source
    assert "'CertificatePrivateKey': AIaFieldLabel(label='Certificate private key'" in source
    assert "'Password': AIaFieldLabel" not in source
    compile(source, '<generated-sdo-interface>', 'exec')


def test_sdo_preserves_contract_level_labels_alongside_generated_defaults():
    class AIiMixedAnnotations_1(AIiDataObject):
        __module__ = 'test.documents.contract'
        __data_object__ = AIcdDataObject(schema_id='test:mixed', schema_version=1)
        __data_object_fields__ = (
            AIcdDataObjectField(field_name='PrivateKey', getter_name='getPrivateKey'),
            AIcdDataObjectField(field_name='Certificate', getter_name='getCertificate'),
        )
        __field_labels__ = {
            'PrivateKey': AIaFieldLabel(label='Explicit private key',
                labels=(AIaFieldLabel.Entry(label='Explicit hint', roleCode='field.description'),))
        }
        def getPrivateKey(self): ...
        def getCertificate(self): ...

    source = configured_service().generate(AIiMixedAnnotations_1, 'd').mutable_interface.source
    assert "**getattr(AIiMixedAnnotations_1, '__field_labels__', {})" in source
    assert "'Certificate': AIaFieldLabel" in source
    assert "'PrivateKey': AIaFieldLabel" not in source
    compile(source, '<generated-mixed-SDO>', 'exec')
