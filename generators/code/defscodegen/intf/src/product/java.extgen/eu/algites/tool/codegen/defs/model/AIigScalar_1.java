package eu.algites.tool.codegen.defs.model;

/**
 * Canonical scalar value
 *
 * <p>Canonical identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}Scalar; version: 1.</p>
 */
@eu.algites.lib.data.dataobject.jsondefs.AIaDataObjectJsonSchema(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Scalar", schemaVersion = 1)
@eu.algites.lib.data.dataobject.yamldefs.AIaDataObjectYamlSchema(schemaId = "eu.algites.tool.codegen.defs.model.canonical-model#/$defs/Scalar", schemaVersion = 1)
@eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectXmlSchema(definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "Scalar")
@eu.algites.lib.data.dataobject.AIaDataObject(description = "Canonical scalar value")
public interface AIigScalar_1 extends eu.algites.lib.data.dataobject.AIiDataObject {
    /** Canonical key IDs and field names for this DataObject. */
    interface CONSTScalar {
        /** Source identifier scalar_kind. */
        String FIELD_NAME__SCALAR_KIND = "scalar_kind";
        /** Source identifier format. */
        String FIELD_NAME__FORMAT = "format";
        /** Source identifier min_length. */
        String FIELD_NAME__MIN_LENGTH = "min_length";
        /** Source identifier max_length. */
        String FIELD_NAME__MAX_LENGTH = "max_length";
        /** Source identifier pattern. */
        String FIELD_NAME__PATTERN = "pattern";
        /** Source identifier minimum. */
        String FIELD_NAME__MINIMUM = "minimum";
        /** Source identifier maximum. */
        String FIELD_NAME__MAXIMUM = "maximum";
        /** Source identifier exclusive_minimum. */
        String FIELD_NAME__EXCLUSIVE_MINIMUM = "exclusive_minimum";
        /** Source identifier exclusive_maximum. */
        String FIELD_NAME__EXCLUSIVE_MAXIMUM = "exclusive_maximum";
        /** Source identifier multiple_of. */
        String FIELD_NAME__MULTIPLE_OF = "multiple_of";
    }

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "scalar_kind", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "scalar_kind", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED, allowsNull = false, order = 0, minItemCount = 1, maxItemCount = 1, isEmptyAllowed = false)
    /** Value of schema field scalar_kind. Field is required; cardinality 1..1.
     * @return field value in its canonical representation
     */
    AIngScalarKind_1 getScalarKind();

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "format", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "format", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 1, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = true)
    /** Value of schema field format. Field is optional; cardinality 0..1.
     * @return field value in its canonical representation
     */
    String getFormat();

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "min_length", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "min_length", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 2, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = false)
    /** Value of schema field min_length. Field is optional; cardinality 0..1.
     * @return field value in its canonical representation
     */
    Long getMinLength();

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "max_length", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "max_length", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 3, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = false)
    /** Value of schema field max_length. Field is optional; cardinality 0..1.
     * @return field value in its canonical representation
     */
    Long getMaxLength();

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "pattern", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "pattern", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 4, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = true)
    /** Value of schema field pattern. Field is optional; cardinality 0..1.
     * @return field value in its canonical representation
     */
    String getPattern();

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "minimum", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "minimum", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 5, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = true)
    /** Value of schema field minimum. Field is optional; cardinality 0..1.
     * @return field value in its canonical representation
     */
    String getMinimum();

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "maximum", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "maximum", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 6, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = true)
    /** Value of schema field maximum. Field is optional; cardinality 0..1.
     * @return field value in its canonical representation
     */
    String getMaximum();

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "exclusive_minimum", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "exclusive_minimum", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 7, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = false)
    /** Value of schema field exclusive_minimum. Field is optional; cardinality 0..1.
     * @return field value in its canonical representation
     */
    Boolean getExclusiveMinimum();

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "exclusive_maximum", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "exclusive_maximum", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 8, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = false)
    /** Value of schema field exclusive_maximum. Field is optional; cardinality 0..1.
     * @return field value in its canonical representation
     */
    Boolean getExclusiveMaximum();

    @eu.algites.lib.data.dataobject.xmldefs.AIaDataObjectFieldXmlSchema(namespace = "https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd", namespaceLocalName = "multiple_of", valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.ELEMENT)
    @eu.algites.lib.data.dataobject.AIaDataObjectField(dataFieldName = "multiple_of", presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED, allowsNull = false, order = 9, minItemCount = 0, maxItemCount = 1, isEmptyAllowed = true)
    /** Value of schema field multiple_of. Field is optional; cardinality 0..1.
     * @return field value in its canonical representation
     */
    String getMultipleOf();

}
