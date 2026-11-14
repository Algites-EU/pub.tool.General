package eu.algites.tool.codegen.defs.impl.cli;

import java.io.ByteArrayInputStream;
import java.io.DataInputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;

/**
 * Inspects JVM class-file metadata of published read-only Defs interfaces.
 *
 * <p>This reader does not load dependency classes, initialize Java types, or
 * require their transitive classpath. It reads only directly declared interfaces,
 * method names and the runtime annotations carrying JSON/YAML schema URLs or
 * XML TYPE QNames. A writable SDO contract is never a candidate.</p>
 *
 * @author linhart1
 */
public final class AIcDefsCodegenCompiledContractReader {
    /** Java class-file magic number. */
    private static final int MAGIC = 0xCAFEBABE;
    /** The class access flag denoting an interface. */
    private static final int INTERFACE = 0x0200;
    /** Maximum class-file size accepted for metadata indexing. */
    private static final long MAX_BYTES = 8_000_000L;

    /** Stateless class-file utility; cannot be constructed. */
    private AIcDefsCodegenCompiledContractReader() { }

    /**
     * An indexed read-only interface and the associated public schema identity.
     *
     * @param identity full JSON/YAML public URL or XML QName
     * @param symbol fully qualified Java interface name
     * @param parents directly implemented/extended Java interface names
     */
    public record Contract(String identity, String symbol, Set<String> parents) { }

    /**
     * Read a compiled interface without executing any dependency bytecode.
     *
     * @param path the local class-file path from a declared dependency
     * @return contract metadata, or {@code null} for an unrelated or mutable type
     * @throws IOException if the class file is unreadable or structurally invalid
     */
    public static Contract read(Path path) throws IOException {
        var all = readAll(path);
        return all.isEmpty() ? null : all.get(0);
    }

    /**
     * Index every independently declared schema identity of a compiled
     * unified DataObject, not just the first JSON/XML/YAML annotation.
     * @param path compiled read-only interface
     * @return zero or more identities on the same Java symbol
     * @throws IOException on malformed or unreadable class metadata
     */
    public static java.util.List<Contract> readAll(Path path) throws IOException {
        if (Files.size(path) > MAX_BYTES) {
            throw new IOException(path + ": class-file metadata exceeds size limit");
        }
        try {
            return parseAll(path, Files.readAllBytes(path));
        } catch (RuntimeException exception) {
            throw new IOException(path + ": invalid compiled Defs contract at class-file byte offset: "
                    + exception.getMessage(), exception);
        }
    }

    /**
     * Parse JVM structural data and directly attached class annotations.
     *
     * @param path source of any diagnostics
     * @param bytes complete class-file payload
     * @return decoded read-only contract, or null when inapplicable
     * @throws IOException on an incomplete or invalid class file
     */
    private static java.util.List<Contract> parseAll(Path path, byte[] bytes) throws IOException {
        var in = new DataInputStream(new ByteArrayInputStream(bytes));
        if (in.readInt() != MAGIC) throw new IOException(path + ": invalid class-file magic");
        in.readUnsignedShort(); // minor version
        in.readUnsignedShort(); // major version
        int count = in.readUnsignedShort();
        Object[] pool = new Object[count];
        for (int entry = 1; entry < count; entry++) {
            int tag = in.readUnsignedByte();
            switch (tag) {
                case 1 -> pool[entry] = in.readUTF();
                case 3, 4 -> pool[entry] = in.readInt();
                case 5, 6 -> { in.readLong(); entry++; }
                case 7, 8, 16, 19, 20 -> pool[entry] = in.readUnsignedShort();
                case 9, 10, 11, 12, 17, 18 -> in.skipNBytes(4);
                case 15 -> in.skipNBytes(3);
                default -> throw new IOException(path + ": invalid JVM constant-pool tag " + tag);
            }
        }
        int access = in.readUnsignedShort();
        String symbol = className(in.readUnsignedShort(), pool);
        in.readUnsignedShort(); // superclass
        Set<String> parents = new LinkedHashSet<>();
        int interfaces = in.readUnsignedShort();
        for (int index = 0; index < interfaces; index++) {
            parents.add(className(in.readUnsignedShort(), pool));
        }
        for (int i = in.readUnsignedShort(); i > 0; i--) {
            in.skipNBytes(6); // field flags, name and descriptor
            skipAttributes(in);
        }
        boolean mutation = false;
        for (int i = in.readUnsignedShort(); i > 0; i--) {
            in.readUnsignedShort();
            String method = utf8(in.readUnsignedShort(), pool);
            in.readUnsignedShort();
            if ((method.startsWith("set") && method.length() > 3
                    && Character.isUpperCase(method.charAt(3))) || method.startsWith("_unset")) {
                mutation = true;
            }
            skipAttributes(in);
        }
        Map<String, Map<String, Object>> annotations = new LinkedHashMap<>();
        for (int i = in.readUnsignedShort(); i > 0; i--) {
            String attribute = utf8(in.readUnsignedShort(), pool);
            int size = in.readInt();
            if (size < 0) throw new IOException(path + ": negative attribute length");
            if (attribute.equals("RuntimeVisibleAnnotations")
                    || attribute.equals("RuntimeInvisibleAnnotations")) {
                byte[] content = new byte[size];
                in.readFully(content);
                var annotationStream = new DataInputStream(new ByteArrayInputStream(content));
                for (int j = annotationStream.readUnsignedShort(); j > 0; j--) {
                    var decoded = readAnnotation(annotationStream, pool);
                    String descriptor = decoded.getKey();
                    String name = descriptor.substring(descriptor.lastIndexOf('/') + 1)
                            .replace(";", "");
                    // Class descriptors begin with 'L'; for default-package
                    // annotations it remains after the last slash lookup.
                    if (!descriptor.contains("/") && name.startsWith("L")) name = name.substring(1);
                    annotations.put(name, decoded.getValue());
                }
                if (annotationStream.available() != 0) {
                    throw new IOException(path + ": annotation size mismatch");
                }
            } else {
                in.skipNBytes(size);
            }
        }
        if (in.available() != 0) throw new IOException(path + ": trailing JVM class-file data");
        if ((access & INTERFACE) == 0 || mutation || parents.stream()
                .anyMatch(name -> name.endsWith(".AIiSmartDataObject"))) {
            return java.util.List.of();
        }
        Set<String> identities = new LinkedHashSet<>();
        Map<String, Object> xml = annotations.get("AIaDataObjectXmlSchema");
        if (xml == null) xml = annotations.get("AIaXmlDataObject");
        if (xml != null && "TYPE".equals(xml.getOrDefault("definitionKind", "TYPE"))) {
            String local = String.valueOf(xml.getOrDefault("namespaceLocalName", ""));
            if (!local.isBlank()) {
                identities.add("{" + xml.getOrDefault("namespace", "") + "}" + local);
            }
        }
        for (String[] names : new String[][] {
                {"AIaDataObjectJsonSchema", "AIaJsonDataObject"},
                {"AIaYamlDataObject"}}) {
            Map<String, Object> format = null;
            for (String name : names) if (annotations.containsKey(name)) {
                format = annotations.get(name);
                break;
            }
            if (format == null || String.valueOf(format.getOrDefault("schemaId", "")).isBlank()) {
                continue;
            }
            String uri = String.valueOf(format.getOrDefault("schemaUrl", ""));
            if (uri.startsWith("https://")) identities.add(uri);
        }
        java.util.List<Contract> result = new java.util.ArrayList<>();
        for (String identity : identities) result.add(new Contract(identity, symbol, Set.copyOf(parents)));
        return java.util.List.copyOf(result);
    }

    /**
     * Retrieve an UTF8 constant with validated type.
     * @param index constant-pool index
     * @param pool previously parsed constant pool
     * @return decoded text
     * @throws IOException when the constant is invalid
     */
    private static String utf8(int index, Object[] pool) throws IOException {
        if (index <= 0 || index >= pool.length || !(pool[index] instanceof String value)) {
            throw new IOException("Invalid UTF8 pool reference " + index);
        }
        return value;
    }

    /**
     * Resolve a class constant to dotted binary class name.
     * @param index pool index for a CONSTANT_Class
     * @param pool constant pool
     * @return dotted class name
     * @throws IOException on invalid constant
     */
    private static String className(int index, Object[] pool) throws IOException {
        if (index <= 0 || index >= pool.length || !(pool[index] instanceof Integer offset)) {
            throw new IOException("Invalid class pool reference " + index);
        }
        return utf8(offset, pool).replace('/', '.');
    }

    /**
     * Skip all attributes on one field or method.
     * @param in class-file reader positioned at attributes_count
     * @throws IOException on malformed attributes
     */
    private static void skipAttributes(DataInputStream in) throws IOException {
        for (int i = in.readUnsignedShort(); i > 0; i--) {
            in.readUnsignedShort();
            int size = in.readInt();
            if (size < 0) throw new IOException("Negative class-file attribute size");
            in.skipNBytes(size);
        }
    }

    /**
     * Read one JVM annotation including its named element values.
     * @param in annotation byte stream
     * @param pool parsed constant pool
     * @return descriptor and direct element values
     * @throws IOException for invalid annotation content
     */
    private static Map.Entry<String, Map<String, Object>> readAnnotation(
            DataInputStream in, Object[] pool) throws IOException {
        String descriptor = utf8(in.readUnsignedShort(), pool);
        Map<String, Object> values = new LinkedHashMap<>();
        for (int i = in.readUnsignedShort(); i > 0; i--) {
            String key = utf8(in.readUnsignedShort(), pool);
            values.put(key, readElement(in, pool));
        }
        return Map.entry(descriptor, values);
    }

    /**
     * Decode or skip a JVM annotation element without loading its type.
     * @param in annotation byte stream
     * @param pool parsed constant pool
     * @return scalar, enum member, nested map or array of elements
     * @throws IOException on an invalid tag
     */
    private static Object readElement(DataInputStream in, Object[] pool) throws IOException {
        int tag = in.readUnsignedByte();
        return switch (tag) {
            case 's' -> utf8(in.readUnsignedShort(), pool);
            case 'B', 'C', 'D', 'F', 'I', 'J', 'S', 'Z' -> {
                int slot = in.readUnsignedShort();
                yield slot > 0 && slot < pool.length ? pool[slot] : null;
            }
            case 'e' -> {
                in.readUnsignedShort(); // enum type descriptor
                yield utf8(in.readUnsignedShort(), pool);
            }
            case 'c' -> utf8(in.readUnsignedShort(), pool);
            case '@' -> readAnnotation(in, pool).getValue();
            case '[' -> {
                var values = new java.util.ArrayList<>();
                for (int j = in.readUnsignedShort(); j > 0; j--) {
                    values.add(readElement(in, pool));
                }
                yield values;
            }
            default -> throw new IOException("Invalid annotation element tag " + tag);
        };
    }
}
