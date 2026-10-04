package eu.algites.tool.codegen.defs;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.util.List;

/** Retains scalar families and basic facets without narrowing numeric boundaries. */
final class AIcScalarConstraints {
    private AIcScalarConstraints() { }
    static AIcdValueConstraints json(JsonNode aNode, AInValueKind aKind) {
        String locType = text(aNode, "x-modustro-datatype");
        if (locType == null) {
            String locEncoding = text(aNode, "contentEncoding");
            String locFormat = text(aNode, "format");
            if ("base64".equals(locEncoding)) locType = "base64Binary";
            else if ("base16".equals(locEncoding)) locType = "hexBinary";
            else if (List.of("date", "time", "date-time", "duration").contains(locFormat == null ? "" : locFormat)) locType = "date-time".equals(locFormat) ? "dateTime" : locFormat;
            else locType = switch (aKind) { case STRING -> "string"; case INTEGER -> "integer"; case NUMBER -> "decimal"; case BOOLEAN -> "boolean"; default -> null; };
        }
        if ("anyType".equals(locType)) locType = null;
        boolean locMinExclusive = aNode.has("exclusiveMinimum"), locMaxExclusive = aNode.has("exclusiveMaximum");
        var locBase = defaults(locType);
        List<String> locEnum = aNode.has("enum") ? java.util.stream.StreamSupport.stream(aNode.get("enum").spliterator(), false).map(JsonNode::asText).toList() : List.of();
        return new AIcdValueConstraints(locType,
                numeric(aNode, locMinExclusive ? "exclusiveMinimum" : "minimum", locBase.minimum()),
                numeric(aNode, locMaxExclusive ? "exclusiveMaximum" : "maximum", locBase.maximum()),
                locMinExclusive, locMaxExclusive, integer(aNode, "minLength"), integer(aNode, "maxLength"), text(aNode, "pattern"), locEnum);
    }
    static AIcdValueConstraints defaults(String aType) {
        String locMin = null, locMax = null;
        if (aType != null) {
            int locBits = switch (aType) { case "byte", "unsignedByte" -> 8; case "short", "unsignedShort" -> 16; case "int", "unsignedInt" -> 32; case "long", "unsignedLong" -> 64; default -> 0; };
            if (locBits != 0) {
                boolean locUnsigned = aType.startsWith("unsigned");
                locMin = locUnsigned ? "0" : BigInteger.ONE.shiftLeft(locBits - 1).negate().toString();
                locMax = BigInteger.ONE.shiftLeft(locUnsigned ? locBits : locBits - 1).subtract(BigInteger.ONE).toString();
            } else if (aType.equals("nonNegativeInteger")) locMin = "0";
            else if (aType.equals("positiveInteger")) locMin = "1";
            else if (aType.equals("nonPositiveInteger")) locMax = "0";
            else if (aType.equals("negativeInteger")) locMax = "-1";
        }
        return new AIcdValueConstraints(aType, locMin, locMax, false, false, null, null, null, List.of());
    }
    static String decimal(String aValue) { return new BigDecimal(aValue).stripTrailingZeros().toPlainString(); }
    private static String numeric(JsonNode aNode, String aName, String aDefault) { return aNode.has(aName) ? decimal(aNode.get(aName).asText()) : aDefault; }
    private static String text(JsonNode aNode, String aName) { return aNode.hasNonNull(aName) ? aNode.get(aName).asText() : null; }
    private static Integer integer(JsonNode aNode, String aName) { return aNode.has(aName) ? aNode.get(aName).intValue() : null; }
}
