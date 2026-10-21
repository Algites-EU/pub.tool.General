package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.AIcdCodeGenerationRequest;
import eu.algites.tool.codegen.defs.AIcdPropertyDefinition;
import eu.algites.tool.codegen.defs.AInCodeGenerationTarget;
import eu.algites.tool.codegen.defs.AInDefsNameRole;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Generates XML-only namespace marker contracts and projects xs:any to XML object interfaces. */
final class AIcXmlNamespaceContracts {
    private AIcXmlNamespaceContracts() { }

    /** A generated namespace compilation unit and its fully qualified type name. */
    record Generated(String typeName, String relativePath, String source, String qualifiedName) { }

    /** Convert a complete namespace URI to a deterministic XML namespace contract suffix. */
    static String identifier(String namespace) {
        Matcher matcher = Pattern.compile("[A-Za-z0-9]+").matcher(namespace);
        StringBuilder result = new StringBuilder();
        while (matcher.find()) {
            String token = matcher.group();
            result.append(Character.toUpperCase(token.charAt(0))).append(token.substring(1));
        }
        return result.isEmpty() ? "Local" : result.toString();
    }

    /** Resolve one explicitly selected namespace from a wildcard constraint. */
    static String selectedNamespace(String constraint, String target) {
        String[] parts = constraint.trim().split("\\s+");
        if (parts.length != 1) return null;
        if (parts[0].equals("##targetNamespace")) return target;
        return parts[0].startsWith("##") ? null : parts[0];
    }

    /** Generate names through XML namespace roles, with no XML element prefix manipulation. */
    static Generated generate(AIcdCodeGenerationRequest request, String namespace) {
        AIcGenerationNames names = new AIcGenerationNames();
        String logical = identifier(namespace)
                .replaceAll("([a-z0-9])([A-Z])", "$1-$2")
                .replaceAll("([A-Z]+)([A-Z][a-z])", "$1-$2")
                .toLowerCase(java.util.Locale.ROOT);
        String name = names.referenceTypeName(logical, null, request.namingProfile(),
                AInDefsNameRole.XML_NAMESPACE_INTERFACE_TYPE);
        String stem = names.referenceTypeName(logical, null, request.namingProfile(),
                AInDefsNameRole.XML_NAMESPACE_INTERFACE_TYPE_FILE_STEM);
        boolean java = request.target() == AInCodeGenerationTarget.JAVA;
        String packageName = request.packageName();
        String source = java
                ? "package " + packageName + ";\n\n"
                    + "/** XML namespace " + namespace.replace("*/", "* /")
                    + "; all generated XML objects in this namespace extend this contract. */\n"
                    + "@eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObject(namespace = "
                    + AIcScalarGeneration.jquote(namespace) + ")\n"
                    + "public interface " + name + " extends "
                    + "eu.algites.lib.data.dataobject.xmldefs.AIiXmlDataObjectNamespace {\n}\n"
                : "from __future__ import annotations\n"
                    + "from eu.algites.lib.data.dataobject.xmldefs.aii_xml_data_object_namespace import AIiXmlDataObjectNamespace\n"
                    + "from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object import AIaXmlDataObject\n\n"
                    + "class " + name + "(AIiXmlDataObjectNamespace):\n"
                    + "    \"\"\"Namespace marker for XML data objects.\"\"\"\n"
                    + "    __xml_data_object__ = AIaXmlDataObject(namespace=" + pythonQuote(namespace) + ")\n"
                    + "    __slots__ = ()\n";
        String filename = stem + (java ? ".java" : ".py");
        String qualified = packageName + "." + (java ? "" : stem + ".") + name;
        return new Generated(name, packageName.replace('.', '/') + "/" + filename, source, qualified);
    }

    /** Escape XML namespace URIs in generated Python source. */
    private static String pythonQuote(String value) {
        return "'" + value.replace("\\", "\\\\").replace("'", "\\'")
                .replace("\n", "\\n").replace("\r", "\\r") + "'";
    }

    /** Attach the namespace parent and replace xs:any string-fragment signatures with XML object signatures. */
    static String decorate(String source, AIcdCodeGenerationRequest request, String marker,
            Map<String, String> wildcardFields) {
        boolean python = request.target() == AInCodeGenerationTarget.PYTHON;
        String result = source;
        if (python) {
            String name = marker.substring(marker.lastIndexOf('.') + 1);
            String module = marker.substring(0, marker.lastIndexOf('.'));
            result = result.replace("from __future__ import annotations\n",
                    "from __future__ import annotations\nfrom " + module + " import " + name + "\n");
            Pattern pattern = Pattern.compile("(?m)^(class [A-Za-z_][A-Za-z_0-9]*\\()([^)]*)(\\):)");
            Matcher matcher = pattern.matcher(result);
            if (matcher.find()) {
                String existing = matcher.group(2).replace("AIiXmlDataObject, ", "").replace("AIiXmlDataObject", "");
                if (existing.equals("ABC")) existing = name + ", " + existing;
                else existing += ", " + name;
                String declaration = matcher.group(1) + existing + matcher.group(3);
                result = result.substring(0, matcher.start()) + declaration + result.substring(matcher.end());
            }
        } else {
            Pattern pattern = Pattern.compile("(?m)^(public (?:sealed )?interface [A-Za-z_][A-Za-z_0-9]* extends )([^\\n{]*?)(?= permits | \\{)");
            Matcher matcher = pattern.matcher(result);
            if (matcher.find() && !matcher.group(2).contains(marker)) {
                result = result.substring(0, matcher.end(2)) + ", " + marker
                        + result.substring(matcher.end(2));
            }
        }
        AIcGenerationNames names = new AIcGenerationNames();
        for (var entry : wildcardFields.entrySet()) {
            String propertyName = names.propertyName(entry.getKey(), request.namingProfile());
            String target = entry.getValue();
            if (python) {
                String type = target.substring(target.lastIndexOf('.') + 1);
                String module = target.substring(0, target.lastIndexOf('.'));
                result = result.replace("from __future__ import annotations\n",
                        "from __future__ import annotations\nfrom " + module + " import " + type + "\n");
                Pattern field = Pattern.compile("(?m)^    " + Pattern.quote(propertyName) + ": ([^\n]+)$");
                Matcher matcher = field.matcher(result);
                String annotated = type;
                if (matcher.find()) {
                    annotated = matcher.group(1).contains("tuple[") ? "tuple[" + type + ", ...]" : type;
                    result = result.substring(0, matcher.start(1)) + annotated + result.substring(matcher.end(1));
                }
                String method = names.getterName(entry.getKey(), request.namingProfile());
                Pattern getter = Pattern.compile("(    def " + Pattern.quote(method) + "\\(self\\))(?: -> [^:]+)?(:)");
                result = getter.matcher(result).replaceFirst(Matcher.quoteReplacement("    def " + method
                        + "(self) -> " + annotated + ":"));
            } else {
                Pattern method = Pattern.compile("(?m)^(    )[^\n]*?(" + Pattern.quote(names.getterName(entry.getKey(), request.namingProfile())) + "\\(\\);)$");
                Matcher matcher = method.matcher(result);
                if (!matcher.find()) throw new IllegalArgumentException("Missing XML wildcard getter " + propertyName);
                String original = matcher.group(0);
                String type = original.contains("java.util.List<")
                        ? "java.util.List<? extends " + target + ">" : target;
                result = result.substring(0, matcher.start()) + matcher.group(1) + type
                        + " " + matcher.group(2) + result.substring(matcher.end());
            }
        }
        return result;
    }
}
