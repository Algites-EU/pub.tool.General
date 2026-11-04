"""Fail-closed Java/Python contract emitter for the validated canonical Defs graph.

This emitter is independent of ``defs.old``. Output identities and file stems are
provided by the caller's selected naming catalog, rather than inferred from the
source spelling. The caller owns writing to *.gen and the generated-file manifest.

Only explicitly handled canonical structures can be emitted. An unsupported
shape raises an error *before* any source files are returned, preventing partial
or misleading contracts. This is the first native production-emission slice,
not a replacement for all supported shapes in the historical Defs Codegen.
"""
from __future__ import annotations

from dataclasses import dataclass
import keyword
import re
from collections.abc import Mapping, Sequence

from eu.algites.tool.codegen.common.naming_profiles import AIcdCodegenNamingProfile
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIcgd_jElement_1 as Element,
    AIcgd_jElementList_1 as ElementList,
    AIcgd_jList_1 as ListNode,
    AIcgd_jMap_1 as MapNode,
    AIcgd_jScalar_1 as Scalar,
    AIcgd_jEnum_1 as EnumNode,
    AIcgd_jType_1 as TypeNode,
    AIigComposition_1 as Composition,
    AIigResolutionState_1 as Resolution,
    AIigScalarKind_1 as ScalarKind,
    AIigMapKind_1 as MapKind,
    AIigSourceInputKind_1 as SourceKind,
)

_JAVA_IDENTIFIER = re.compile(r'[A-Za-z_$][A-Za-z0-9_$]*\Z')
_PY_IDENTIFIER = re.compile(r'[A-Za-z_][A-Za-z0-9_]*\Z')
_JAVA_RESERVED = frozenset('abstract assert boolean break byte case catch char class const continue default do double else enum extends final finally float for goto if implements import instanceof int interface long native new package private protected public return short static strictfp super switch synchronized this throw throws transient try void volatile while true false null record sealed permits var yield'.split())
_PY_RESERVED = frozenset(keyword.kwlist)
_JAVA_SCALAR = {ScalarKind.STRING: 'String', ScalarKind.INTEGER: 'Long',
                ScalarKind.NUMBER: 'Double', ScalarKind.BOOLEAN: 'Boolean'}
_PY_SCALAR = {ScalarKind.STRING: 'str', ScalarKind.INTEGER: 'int',
              ScalarKind.NUMBER: 'float', ScalarKind.BOOLEAN: 'bool'}


def _identifier(value: str, target: str) -> str:
    """Check a catalog-derived identifier rather than silently rewriting it."""
    regex, reserved = (_JAVA_IDENTIFIER, _JAVA_RESERVED) if target == 'java' else (_PY_IDENTIFIER, _PY_RESERVED)
    if not isinstance(value, str) or not regex.fullmatch(value) or value in reserved:
        raise ValueError(f'Invalid {target} naming-catalog identifier: {value!r}')
    return value


def _java_doc(value: str) -> str:
    """Escape schema documentation for safe Javadoc text nodes."""
    escaped = (value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
               .replace('*/', '* /').replace('\n', ' ').replace('\r', ' '))
    return ''.join(f'[U+{ord(char):04X}]' if ord(char) < 32 and char != '\t'
                   else char for char in escaped)


def _py_doc(value: str) -> str:
    """Escape source documentation embedded inside Python docstrings."""
    return ' '.join(value.replace('\\', '\\\\').replace('"""', '\\"\\"\\"').split())


def _enum_literal(wire: str, kind: ScalarKind, target: str) -> str:
    """Return a lossless, strictly validated scalar enum constant literal.

    Arbitrary-precision integers use BigInteger/int rather than Java Long.
    Floating enum values remain unsupported until exact decimal parsing is
    available throughout both source frontends.
    """
    if kind is ScalarKind.STRING:
        return _java_string(wire) if target == 'java' else repr(wire)
    if kind is ScalarKind.INTEGER:
        if not re.fullmatch(r'0|-?[1-9][0-9]*', wire):
            raise ValueError(f'Invalid integer enum lexical value: {wire!r}')
        return (f'new java.math.BigInteger({_java_string(wire)})' if target == 'java'
                else wire)
    if kind is ScalarKind.BOOLEAN:
        if wire not in ('true', 'false'):
            raise ValueError(f'Invalid boolean enum lexical value: {wire!r}')
        return wire if target == 'java' else wire.title()
    raise NotImplementedError(f'Exact numeric enum representation unsupported: {kind.value}')


def _java_string(value: str) -> str:
    """Emit a Java quoted string without permitting control-character injection."""
    escaped = []
    for char in value:
        code = ord(char)
        if char == '\\': escaped.append('\\\\')
        elif char == '"': escaped.append('\\"')
        elif char == '\n': escaped.append('\\n')
        elif char == '\r': escaped.append('\\r')
        elif char == '\t': escaped.append('\\t')
        elif code < 32: escaped.append(f'\\{code:03o}')
        else: escaped.append(char)
    return '"' + ''.join(escaped) + '"'


_XML_NAME = re.compile(r'[A-Za-z_][A-Za-z0-9_-]*\Z')


def _indexed_paths(collection: ListNode, types: Mapping[str, TypeNode]) -> tuple[tuple[str, tuple[str, ...], bool], ...]:
    """Resolve the safe direct-selector / child-axis subset of xs:key and xs:unique.

    The runtime consumes *semantic* dot-separated field paths, not XPath. Do
    not guess namespace bindings, descendant selectors, wildcards or predicates.
    Those require a namespace-aware resolver before emitting a runtime index.
    """
    if not collection.key_definitions:
        return ()
    if (collection.min_occurs, collection.max_occurs) != (0, -1):
        raise NotImplementedError('Indexed LIST cardinality is not yet enforceable: ' + collection.name)
    if not isinstance(collection.item, TypeNode):
        raise NotImplementedError('Indexed LIST elements must be named TYPEs: ' + collection.name)
    def resolve(structure):
        seen = set()
        while isinstance(structure, TypeNode):
            if structure.target_identity:
                identity = structure.target_identity
                if identity in seen or identity not in types:
                    raise ValueError('Unresolved indexed LIST item reference: ' + identity)
                seen.add(identity)
                structure = types[identity].structure
            else:
                structure = structure.structure
        return structure

    def validate(path):
        current = collection.item
        for index, segment in enumerate(path.split('.')):
            group = resolve(current)
            if not isinstance(group, ElementList) or group.composition == Composition.CHOICE:
                raise NotImplementedError('Indexed LIST field path traverses a non-object: ' + path)
            matches = [node for node in group.children
                       if isinstance(node, Element) and node.name == segment]
            if len(matches) != 1:
                raise ValueError('Unresolved or ambiguous indexed LIST field path: ' + path)
            current = matches[0].structure
            if index == len(path.split('.')) - 1:
                leaf = resolve(current)
                if not isinstance(leaf, (Scalar, EnumNode)) or (
                    isinstance(leaf, Scalar) and leaf.scalar_kind in (ScalarKind.ANY, ScalarKind.NULL)):
                    raise NotImplementedError('Indexed LIST key must resolve to a typed scalar: ' + path)

    indexed = []
    for key in collection.key_definitions:
        if key.selector.removeprefix('./') != collection.name:
            raise NotImplementedError('Indexed LIST selector must target exactly its own direct child: '
                                      + key.selector)
        if not key.fields:
            raise ValueError('Indexed LIST key requires at least one field: ' + key.identifier)
        normalized = []
        for path in key.fields:
            raw = path.removeprefix('./')
            fragments = raw.split('/')
            if not fragments or any(not fragment for fragment in fragments):
                raise NotImplementedError('Unsupported indexed LIST XPath: ' + path)
            names = []
            for index, fragment in enumerate(fragments):
                if fragment.startswith('@'):
                    # The canonical XML frontend does not yet retain attribute
                    # declarations. Do not silently index an element instead.
                    raise NotImplementedError('Attribute XPath requires an attribute-aware canonical model: ' + path)
                if not _XML_NAME.fullmatch(fragment):
                    raise NotImplementedError('Namespace/predicate/axis in indexed LIST XPath requires '
                                              'a dedicated resolver: ' + path)
                names.append(fragment)
            normalized_path = '.'.join(names)
            validate(normalized_path)
            normalized.append(normalized_path)
        if len(set(normalized)) != len(normalized):
            raise ValueError('Duplicate normalized key field in ' + key.identifier)
        indexed.append((key.identifier, tuple(normalized), key.required))
    return tuple(indexed)


def _key_constant_identifier(field: str, key: str) -> str:
    """Produce a stable, collision-checked key symbol from XML member and key IDs.

    The CONST container name itself always comes from the naming catalog.
    Key symbols are scoped by their repeated member to distinguish locally named
    xs:key/xs:unique constraints on independent lists in the same TYPE.
    """
    def words(value: str) -> list[str]:
        value = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', value)
        value = re.sub(r'([A-Z])([A-Z][a-z])', r'\1_\2', value)
        parts = re.findall(r'[A-Za-z0-9]+', value)
        if not parts:
            raise ValueError(f'Cannot form a key constant from {value!r}')
        return [part.upper() for part in parts]
    return _identifier('KEY_' + '_'.join(words(field) + words(key)), 'java')


@dataclass(frozen=True)
class AIcdDefsCodegenEmissionName:
    """Catalog-resolved output names for one canonical declaration.

    ``java_type`` and ``python_type`` must be valid unique identifiers.
    ``python_module`` is an explicit module stem, excluding the ``.py`` suffix.
    """
    java_type: str
    python_type: str
    python_module: str


@dataclass(frozen=True)
class AIcdDefsCodegenEmittedFile:
    """One complete generated source with repository-relative destination."""
    language: str
    relative_path: str
    content: str
    type_identity: str


class AIcDefsCodegenCanonicalSourceEmitter:
    """Generates independent Java/Python Defs *interfaces* from linked model types.

    The generator does not create runtime SDO classes. It translates only a
    restricted, validated local-key subset to Java annotations and Python key
    metadata; more general identity constraints are rejected. Actual member
    methods are derived from the selected
    Common naming profile. Every output type name comes from the external
    catalog; collisions are errors. This function is pure: no files are written.
    """

    def __init__(self, naming: AIcdCodegenNamingProfile,
                 output_names: Mapping[str, AIcdDefsCodegenEmissionName], package_name: str,
                 output_naming_convention: str = ''):
        """Bind an explicitly resolved naming profile, type map, and Java package."""
        if not isinstance(naming, AIcdCodegenNamingProfile):
            raise TypeError('An explicit Common+Defs naming profile is required')
        if not package_name or not all(_JAVA_IDENTIFIER.fullmatch(segment)
                                       and segment not in _JAVA_RESERVED
                                       for segment in package_name.split('.')):
            raise ValueError('An explicit valid Java package name is required')
        self.naming = naming
        self.output_names = dict(output_names)
        self.package_name = package_name
        self.output_naming_convention = output_naming_convention

    def render(self, types: Sequence[TypeNode]) -> tuple[AIcdDefsCodegenEmittedFile, ...]:
        """Render all declarations or raise before returning any partial outputs.

        ``types`` must be the normalized result of a validated canonical
        pipeline. No unresolved symbols, unknown parents, unsupported group
        cardinalities, inline enum, or unhandled union constructs are accepted.
        """
        ordered = self._collect(types)
        self._validate_names(ordered)
        choice_parents = self._choice_parents(ordered)
        outputs = []
        for node in ordered.values():
            names = self.output_names[node.identity]
            outputs.append(AIcdDefsCodegenEmittedFile('java',
                self.package_name.replace('.', '/') + '/' + names.java_type + '.java',
                self._java_source(node, ordered, choice_parents), node.identity))
            outputs.append(AIcdDefsCodegenEmittedFile('python',
                self.package_name.replace('.', '/') + '/' + names.python_module + '.py',
                self._python_source(node, ordered, choice_parents), node.identity))
        return tuple(outputs)

    @staticmethod
    def declarations(roots: Sequence[TypeNode]) -> tuple[TypeNode, ...]:
        """Expose ordered declared/synthetic output identities to naming catalogs.

        The naming phase must cover every reachable synthetic TYPE exactly once;
        it must not guess names by inspecting the emitter's generated source text.
        """
        return tuple(AIcDefsCodegenCanonicalSourceEmitter._collect(roots).values())

    @staticmethod
    def _collect(roots: Sequence[TypeNode]) -> dict[str, TypeNode]:
        """Collect explicit and embedded synthetic declarations with cycle guards."""
        found: dict[str, TypeNode] = {}

        def visit(node):
            if isinstance(node, TypeNode):
                if node.resolution_state != Resolution.RESOLVED:
                    raise ValueError(f'Unresolved canonical type: {node.identity}')
                if node.target_identity:
                    return
                prior = found.get(node.identity)
                if prior is not None:
                    if prior != node:
                        raise ValueError(f'Conflicting nested type identity: {node.identity}')
                    return
                found[node.identity] = node
                visit(node.structure)
            elif isinstance(node, ElementList):
                for child in node.children: visit(child)
            elif isinstance(node, Element):
                visit(node.structure)
            elif isinstance(node, ListNode):
                visit(node.item)
            elif isinstance(node, MapNode):
                visit(node.key_type)
                visit(node.value_type)
            elif not isinstance(node, (Scalar, EnumNode)):
                raise TypeError(f'Unsupported canonical node: {type(node)!r}')

        for root in roots:
            if not isinstance(root, TypeNode):
                raise TypeError('Top-level declaration must be a TYPE')
            visit(root)
        if not found:
            raise ValueError('No canonical source types to emit')
        return found

    @staticmethod
    def _choice_parents(types: Mapping[str, TypeNode]) -> dict[str, str]:
        """Plan sealed variants before emission; reject non-exclusive/unknown branches.

        Each CHOICE branch must be an independently named synthetic TYPE with an
        unambiguous owner. Scalar alternatives and bounded single-occurrence
        object alternatives are represented by named, final record variants.
        Any unsupported nested structures fail before rendering.
        """
        parents = {}
        for node in types.values():
            structure = node.structure
            if not isinstance(structure, ElementList) or structure.composition != Composition.CHOICE:
                continue
            if (structure.min_occurs, structure.max_occurs) != (1, 1):
                raise NotImplementedError(f'CHOICE group cardinality unsupported: {node.identity}')
            if node.inherited_from_types:
                raise NotImplementedError(f'CHOICE inheritance unsupported: {node.identity}')
            if not structure.children:
                raise ValueError(f'Empty CHOICE: {node.identity}')
            for child in structure.children:
                if (not isinstance(child, Element) or not isinstance(child.structure, TypeNode)
                        or child.structure.target_identity or child.min_occurs != 0 or child.max_occurs != 1):
                    raise NotImplementedError(f'CHOICE requires named exclusive variant at {node.identity}')
                variant = child.structure
                if (not isinstance(variant.structure, (Scalar, ElementList)) or
                        (isinstance(variant.structure, ElementList) and
                         variant.structure.composition not in (Composition.SEQUENCE, Composition.ALL))):
                    raise NotImplementedError(f'Unsupported CHOICE variant at {variant.identity}')
                if variant.inherited_from_types or variant.identity not in types:
                    raise ValueError(f'Invalid CHOICE variant {variant.identity}')
                if variant.identity in parents:
                    raise ValueError(f'CHOICE variant has multiple owners: {variant.identity}')
                parents[variant.identity] = node.identity
        return parents

    def _validate_names(self, types: Mapping[str, TypeNode]) -> None:
        """Require exact external naming coverage and reject file collisions."""
        if set(self.output_names) != set(types):
            raise ValueError(f'Output naming identities differ from canonical declarations: '
                             f'missing={sorted(set(types)-set(self.output_names))}, '
                             f'extra={sorted(set(self.output_names)-set(types))}')
        paths = set()
        for node in types.values():
            names = self.output_names[node.identity]
            if not isinstance(names, AIcdDefsCodegenEmissionName):
                raise TypeError(f'Invalid resolved naming for {node.identity}')
            for target, name in (('java', names.java_type), ('python', names.python_type),
                                 ('python', names.python_module)):
                _identifier(name, target)
            for key in (('java', names.java_type.casefold()),
                        ('python', names.python_module.casefold())):
                if key in paths: raise ValueError(f'Output path collision for {node.identity}: {key}')
                paths.add(key)
            for parent in node.inherited_from_types:
                if parent not in types:
                    raise ValueError(f'Unresolved parent {parent!r} of {node.identity!r}')

    def _typed(self, node, target: str, types: Mapping[str, TypeNode],
               containing: str) -> str:
        """Resolve a field's language type without lossy ANY/null widening."""
        if isinstance(node, TypeNode):
            reference = node.target_identity or node.identity
            if reference not in types:
                raise ValueError(f'Unknown referenced TYPE {reference!r} inside {containing}')
            symbol = self.output_names[reference]
            return symbol.java_type if target == 'java' else symbol.python_type
        if isinstance(node, Scalar):
            mapping = _JAVA_SCALAR if target == 'java' else _PY_SCALAR
            if node.scalar_kind not in mapping:
                raise NotImplementedError(f'No lossless {target} scalar for {node.scalar_kind.value} inside {containing}')
            if node.format:
                raise NotImplementedError(f'Unsupported {target} scalar format {node.format!r} inside {containing}')
            return mapping[node.scalar_kind]
        if isinstance(node, ListNode):
            _indexed_paths(node, types)
            if (node.min_occurs, node.max_occurs) != (0, -1):
                raise NotImplementedError(f'Bounded LIST cannot be enforced by this emitter: {containing}')
            item = self._typed(node.item, target, types, containing + '/items')
            if node.key_definitions:
                return (f'eu.algites.lib.common.list.AIiMultiMappedList<{item}>'
                        if target == 'java' else f'AIiMultiMappedList[{item}]')
            return f'java.util.List<{item}>' if target == 'java' else f'list[{item}]'
        if isinstance(node, MapNode):
            if node.map_kind not in (MapKind.COMMON_MAP, MapKind.INTEGRATED_PROPERTY_MAP):
                raise ValueError(f'Unsupported map kind in {containing}')
            key = self._typed(node.key_type, target, types, containing + '/key')
            value = self._typed(node.value_type, target, types, containing + '/value')
            return f'java.util.Map<{key}, {value}>' if target == 'java' else f'dict[{key}, {value}]'
        raise NotImplementedError(f'Unsupported inline {node.kind.value} inside {containing}; '
                                  'lift the structure to a named TYPE before emission')

    def _fields(self, node: TypeNode, types: Mapping[str, TypeNode], target: str):
        """Lower a SEQUENCE/ALL into read-only typed getter contracts, preserving CHOICE."""
        structure = node.structure
        if not isinstance(structure, ElementList):
            raise NotImplementedError(f'Only object TYPE or top-level ENUM is currently emitted: {node.identity}')
        if structure.composition not in (Composition.SEQUENCE, Composition.ALL):
            raise NotImplementedError(f'CHOICE emission requires the sealed-variant backend: {node.identity}')
        if (structure.min_occurs, structure.max_occurs) != (1, 1):
            raise NotImplementedError(f'Group cardinality requires group-aware emission: {node.identity}')
        results = []
        used = set()
        for child in structure.children:
            if isinstance(child, Element):
                if child.key_definitions:
                    raise NotImplementedError(f'Identity constraints require specialized generator: {node.identity}/{child.name}')
                if child.max_occurs != 1:
                    raise NotImplementedError(f'Repeated field requires occurrence-preserving emitter: {node.identity}/{child.name}')
                name, value, minimum, maximum, description = (child.name, child.structure,
                    child.min_occurs, child.max_occurs, child.description)
            elif isinstance(child, ListNode):
                # XSD maxOccurs=unbounded produces a LIST directly in the
                # ELEMENTLIST, not an ELEMENT wrapping a LIST. Preserve the
                # collection type and its exact occurrence bounds. Only the
                # unconstrained 0..unbounded case is currently representable;
                # _typed() fails closed for all other bounds.
                if not child.name:
                    raise ValueError(f'Unnamed direct LIST inside {node.identity}')
                name, value, minimum, maximum, description = (
                    child.name, child, child.min_occurs, child.max_occurs, '')
            elif isinstance(child, MapNode) and child.map_kind is MapKind.INTEGRATED_PROPERTY_MAP:
                name, value, minimum, maximum, description = child.name, child, 0, -1, ''
            else:
                raise NotImplementedError(f'Unsupported {child.kind.value} in object {node.identity}')
            getter = _identifier(self.naming.method_name('standard_getter', name), target)
            setter = _identifier(self.naming.method_name('standard_setter', name), target)
            if getter == setter or getter in used or setter in used:
                raise ValueError(f'Conflicting member names in {node.identity}: {getter}/{setter}')
            used.update((getter, setter))
            value_type = self._typed(value, target, types, node.identity + '/' + name)
            results.append((name, getter, setter, value_type, minimum, maximum, description))
        return results

    def _key_constants(self, node: TypeNode, types: Mapping[str, TypeNode],
                       target: str) -> tuple[str, dict[tuple[str, str], str]]:
        """Assign all indexed members to validated constants under a catalog-named CONST.

        Symbol collisions (including camelCase vs underscore variants) fail the
        whole compilation rather than aliasing distinct XSD identity constraints.
        """
        if not isinstance(node.structure, ElementList):
            return '', {}
        result: dict[tuple[str, str], str] = {}
        used: set[str] = set()
        for child in node.structure.children:
            if not isinstance(child, ListNode) or not child.key_definitions:
                continue
            for key_name, _, _ in _indexed_paths(child, types):
                symbol = _key_constant_identifier(child.name, key_name)
                if symbol in used or (child.name, key_name) in result:
                    raise ValueError(f'Conflicting XSD key constant in {node.identity}: {symbol}')
                used.add(symbol)
                result[(child.name, key_name)] = symbol
        if not result:
            return '', result
        container = _identifier(self.naming.method_name('const_container_interface', node.name), target)
        methods = {member[1] for member in self._fields(node, types, target)}
        methods.update(member[2] for member in self._fields(node, types, target))
        if container in methods:
            raise ValueError(f'CONST naming collides with a generated method: {container}')
        return container, result

    @staticmethod
    def _data_object_technology(node: TypeNode) -> str:
        """Use the source-specific marker only when all bindings agree.

        A merged cross-technology declaration must not falsely claim that the
        same instance has one particular wire encoding. The generic marker is
        still a valid SDO input and preserves source independence.
        """
        source_kinds = set(node.source_bindings)
        names = {SourceKind.XMLDEFS: 'xml', SourceKind.JSONDEFS: 'json',
                 SourceKind.YAMLDEFS: 'yaml'}
        return names[next(iter(source_kinds))] if len(source_kinds) == 1 else ''

    @staticmethod
    def _schema_version_number(node: TypeNode) -> int:
        """Only represent integral positive schema versions in API metadata."""
        token = node.schema_version
        return int(token) if token and str(token).isdigit() and int(token) > 0 else -1

    def _java_source(self, node: TypeNode, types: Mapping[str, TypeNode],
                     choice_parents: Mapping[str, str]) -> str:
        """Render one Java interface or exact-code enum with complete public documentation."""
        name = self.output_names[node.identity].java_type
        header = f'package {self.package_name};\n\n'
        doc = _java_doc(node.description or f'Contract for {node.name}.')
        header += ('/**\n' + f' * {doc}\n' + ' *\n'
                   + f' * <p>Canonical identity: {_java_doc(node.identity)}; '
                   + f'version: {_java_doc(node.schema_version)}.</p>\n' + ' */\n')
        if isinstance(node.structure, ElementList) and node.structure.composition == Composition.CHOICE:
            variants = [self.output_names[child.structure.identity].java_type
                        for child in node.structure.children]
            return header + f'public sealed interface {name} permits {", ".join(variants)} {{\n}}\n'
        if node.identity in choice_parents:
            parent_type = self.output_names[choice_parents[node.identity]].java_type
            if node.inherited_from_types:
                raise NotImplementedError(f'CHOICE variant inheritance unsupported: {node.identity}')
            if isinstance(node.structure, Scalar):
                scalar_type = self._typed(node.structure, 'java', types, node.identity + '/value')
                getter = _identifier(self.naming.method_name('standard_getter', 'value'), 'java')
                return (header + f'public record {name}({scalar_type} value) implements {parent_type} {{\n'
                        f'    /** @return exact typed value of this exclusive alternative */\n'
                        f'    public {scalar_type} {getter}() {{ return value; }}\n}}\n')
            # Preserve every object member as an immutable, typed record component.
            # Internal fieldN storage names are deliberately independent of source
            # names, which may contain characters forbidden in Java identifiers.
            fields = self._fields(node, types, 'java')
            components = [f'field{i}' for i in range(1, len(fields) + 1)]
            if any(field[1] in components for field in fields):
                raise ValueError(f'CHOICE getter conflicts with record component: {node.identity}')
            signature = ', '.join(f'{field[3]} {component}'
                                  for field, component in zip(fields, components))
            header = header.replace(' */\n', ''.join(
                f' * @param {component} {_java_doc(field[6] or f"Schema field {field[0]}")}\n'
                for field, component in zip(fields, components)) + ' */\n')
            lines = [header, f'public record {name}({signature}) implements {parent_type} {{\n']
            required = [(field, component) for field, component in zip(fields, components)
                        if field[4] > 0]
            if required:
                lines.append(f'    /** Validate required fields on construction. */\n'
                             f'    public {name} {{\n')
                for field, component in required:
                    lines.append(f'        java.util.Objects.requireNonNull({component}, '
                                 f'{_java_string(field[0])});\n')
                lines.append('    }\n\n')
            for field, component in zip(fields, components):
                original, getter, _, typ, minimum, _, description = field
                lines.append(f'    /** @return {_java_doc(description or f"Value of {original}")}'
                             f' ({"required" if minimum else "optional"}) */\n'
                             f'    public {typ} {getter}() {{ return {component}; }}\n')
            return ''.join(lines) + '}\n'
        if isinstance(node.structure, EnumNode):
            kind = node.structure.base_scalar_type
            if kind is ScalarKind.NUMBER:
                raise NotImplementedError(f'Exact decimal enum parsing is unsupported: {node.identity}')
            if node.inherited_from_types:
                raise NotImplementedError(f'Enum inheritance is unsupported: {node.identity}')
            code_type = {ScalarKind.STRING: 'String', ScalarKind.INTEGER: 'java.math.BigInteger',
                         ScalarKind.BOOLEAN: 'Boolean'}.get(kind)
            if code_type is None:
                raise NotImplementedError(f'No wire-value type for enum: {node.identity}')
            members = []
            seen = set()
            for index, value in enumerate(node.structure.values):
                wire = value.wire_value
                literal = _enum_literal(wire, kind, 'java')
                if wire in seen:
                    raise ValueError(f'Duplicate enum wire code in {node.identity}: {wire!r}')
                seen.add(wire)
                members.append(f'    /** Exact wire value {_java_doc(wire)}. */\n'
                               f'    VALUE_{index + 1}({literal})')
            return (header + f'public enum {name} {{\n' + ',\n'.join(members) + ';\n\n'
                    f'    private final {code_type} wireCode;\n\n'
                    f'    /** @param aWireCode original typed schema code */\n'
                    f'    {name}({code_type} aWireCode) {{ wireCode = aWireCode; }}\n\n'
                    '    /** @return the exact typed schema wire value */\n'
                    f'    public {code_type} code() {{ return wireCode; }}\n}}\n')
        fields = self._fields(node, types, 'java')
        technology = self._data_object_technology(node)
        marker = ('eu.algites.lib.data.dataobject.' +
                  (technology + 'defs.AIi' + technology.title() + 'DataObject'
                   if technology else 'AIiDataObject'))
        parent_types = [self.output_names[x].java_type for x in node.inherited_from_types]
        if not parent_types:
            parent_types.append(marker)
        parents = ' extends ' + ', '.join(parent_types)
        schema_version = self._schema_version_number(node)
        header += ('@eu.algites.lib.data.dataobject.AIaDataObject('
                   f'schemaId = {_java_string(node.identity)}, '
                   f'schemaVersion = {schema_version}, '
                   f'description = {_java_string(node.description or node.name)}, '
                   f'namingConvention = {_java_string(self.output_naming_convention)})\n')
        rows = [header, f'public interface {name}{parents} {{\n']
        const_container, key_constants = self._key_constants(node, types, 'java')
        if key_constants:
            rows.append(f'    /** Canonical identifiers of the XML identity constraints for this TYPE. */\n'
                        f'    interface {const_container} {{\n')
            for (member_name, key_name), const_name in key_constants.items():
                rows.append(f'        /** XSD key or unique constraint {_java_doc(key_name)} '
                            f'on repeated member {_java_doc(member_name)}. */\n'
                            f'        String {const_name} = {_java_string(key_name)};\n')
            rows.append('    }\n\n')
        for position, (original, getter, setter, typ, minimum, maximum, description) in enumerate(fields):
            xml_member = next((child for child in node.structure.children
                               if isinstance(child, (Element, ListNode)) and child.name == original), None)
            wire = xml_member.xml_wire if xml_member is not None else None
            if wire is not None:
                rows.append('    @eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObjectField('
                            f'namespace = {_java_string(wire.namespace_uri)}, '
                            f'namespaceLocalName = {_java_string(wire.local_name)}, '
                            f'valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.{wire.value_kind}, '
                            f'order = {position}, minOccurs = {minimum}, maxOccurs = {maximum})\n')
            member = next((child for child in node.structure.children
                           if isinstance(child, ListNode) and child.name == original), None)
            for key_name, paths, required_key in _indexed_paths(member, types) if member else ():
                path_literals = ', '.join(_java_string(path) for path in paths)
                rows.append('    @eu.algites.lib.data.dataobject.xmldefs.AIaXmlKeyDefinition('
                            f'name = {const_container}.{key_constants[(original, key_name)]}, '
                            f'fields = {{{path_literals}}}, '
                            f'required = {str(required_key).lower()})\n')
            rows.append('    @eu.algites.lib.data.dataobject.AIaDataObjectField('
                        f'fieldName = {_java_string(original)}, '
                        f'presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.'
                        f'{"REQUIRED" if minimum else "ALLOWED"}, '
                        'allowsNull = false)\n')
            documented = _java_doc(description or f'Value of schema field {original}.')
            required = 'required' if minimum else 'optional'
            rows.extend((
                f'    /** {documented} Field is {required}; cardinality {minimum}..{maximum}.\n'
                f'     * @return field value in its canonical representation\n     */\n'
                f'    {typ} {getter}();\n\n'))
        rows.append('}\n')
        return ''.join(rows)

    def _python_source(self, node: TypeNode, types: Mapping[str, TypeNode],
                       choice_parents: Mapping[str, str]) -> str:
        """Render one Python ABC or enum with equivalent typed method contracts."""
        name = self.output_names[node.identity].python_type
        header = 'from __future__ import annotations\n\n'
        if isinstance(node.structure, ElementList) and node.structure.composition == Composition.CHOICE:
            return (header + 'from abc import ABC\n\n\n'
                    f'class {name}(ABC):\n'
                    f'    """{_py_doc(node.description or "Exclusive canonical choice")}"""\n'
                    '    pass\n')
        if node.identity in choice_parents:
            if node.inherited_from_types:
                raise NotImplementedError(f'CHOICE variant inheritance unsupported: {node.identity}')
            base = self.output_names[choice_parents[node.identity]]
            if isinstance(node.structure, Scalar):
                scalar_type = self._typed(node.structure, 'python', types, node.identity + '/value')
                getter = _identifier(self.naming.method_name('standard_getter', 'value'), 'python')
                return (header + 'from dataclasses import dataclass\nfrom typing import final\n'
                        f'from .{base.python_module} import {base.python_type}\n\n\n'
                        '@final\n@dataclass(frozen=True)\n'
                        f'class {name}({base.python_type}):\n'
                        f'    """{_py_doc(node.description or "Exclusive canonical variant")}"""\n'
                        f'    value: {scalar_type}\n\n'
                        f'    def {getter}(self) -> {scalar_type}:\n'
                        '        """Return the exact typed alternative value."""\n'
                        '        return self.value\n')
            fields = self._fields(node, types, 'python')
            components = [f'field{i}' for i in range(1, len(fields) + 1)]
            if any(field[1] in components for field in fields):
                raise ValueError(f'CHOICE getter conflicts with dataclass component: {node.identity}')
            lines = [header, 'from dataclasses import dataclass\nfrom typing import final\n',
                     f'from .{base.python_module} import {base.python_type}\n\n\n',
                     '@final\n@dataclass(frozen=True)\n',
                     f'class {name}({base.python_type}):\n',
                     f'    """{_py_doc(node.description or "Exclusive canonical object variant")}"""\n']
            if not fields:
                # Empty variants still carry their own distinct, nominal type.
                lines.append('    pass\n')
            for field, component in zip(fields, components):
                typ = field[3] if field[4] else field[3] + ' | None'
                lines.append(f'    {component}: {typ}\n')
            if any(field[4] for field in fields):
                lines.extend(('\n    def __post_init__(self) -> None:\n',
                              '        """Validate required fields of this exact alternative."""\n'))
                for field, component in zip(fields, components):
                    if field[4]:
                        lines.append(f'        if self.{component} is None:\n'
                                     f'            raise ValueError({field[0]!r} + " is required")\n')
            for field, component in zip(fields, components):
                original, getter, _, typ, minimum, _, description = field
                annotation = typ if minimum else typ + ' | None'
                lines.append(f'\n    def {getter}(self) -> {annotation}:\n'
                             f'        """Return {_py_doc(description or f"field {original}")}."""\n'
                             f'        return self.{component}\n')
            return ''.join(lines)
        if isinstance(node.structure, EnumNode):
            kind = node.structure.base_scalar_type
            if kind is ScalarKind.NUMBER:
                raise NotImplementedError(f'Exact decimal enum parsing is unsupported: {node.identity}')
            if node.inherited_from_types:
                raise NotImplementedError(f'Enum inheritance is unsupported: {node.identity}')
            if kind not in (ScalarKind.STRING, ScalarKind.INTEGER, ScalarKind.BOOLEAN):
                raise NotImplementedError(f'No wire-value type for enum: {node.identity}')
            header += 'from enum import Enum\n\n\n'
            bases = 'str, Enum' if kind is ScalarKind.STRING else 'int, Enum' if kind is ScalarKind.INTEGER else 'Enum'
            code_type = {ScalarKind.STRING: 'str', ScalarKind.INTEGER: 'int', ScalarKind.BOOLEAN: 'bool'}[kind]
            body = [f'class {name}({bases}):\n',
                    f'    """{_py_doc(node.description or "Schema enum")}"""\n\n']
            seen = set()
            for index, val in enumerate(node.structure.values):
                literal = _enum_literal(val.wire_value, kind, 'python')
                if val.wire_value in seen:
                    raise ValueError(f'Duplicate enum wire code in {node.identity}: {val.wire_value!r}')
                seen.add(val.wire_value)
                body.append(f'    VALUE_{index + 1} = {literal}\n')
            body.extend((f'\n    def code(self) -> {code_type}:\n',
                         '        """Return the exact typed wire code."""\n',
                         '        return self.value\n'))
            return header + ''.join(body)
        fields = self._fields(node, types, 'python')
        parent_imports = []
        for parent in node.inherited_from_types:
            symbols = self.output_names[parent]
            parent_imports.append(f'from .{symbols.python_module} import {symbols.python_type}\n')
        technology = self._data_object_technology(node)
        marker_name = 'AIi' + technology.title() + 'DataObject' if technology else 'AIiDataObject'
        marker_module = (f'{technology}defs.aii_{technology}_data_object'
                         if technology else 'aii_data_object')
        parent_list = ', '.join(self.output_names[x].python_type for x in node.inherited_from_types) or marker_name
        header += ('from abc import ABC, abstractmethod\nfrom typing import TYPE_CHECKING\n'
                   'from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject\n'
                   'from eu.algites.lib.data.dataobject.aia_data_object_field import AIaDataObjectField\n'
                   'from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind\n')
        if not node.inherited_from_types:
            header += f'from eu.algites.lib.data.dataobject.{marker_module} import {marker_name}\n'
        indexed_fields = [(child.name, _indexed_paths(child, types)) for child in node.structure.children
                          if isinstance(child, ListNode) and child.key_definitions]
        if indexed_fields:
            header += 'from eu.algites.lib.common.list.aii_multi_mapped_list import AIiMultiMappedList\n'
        xml_members = [(position, child) for position, child in enumerate(node.structure.children)
                       if isinstance(child, (Element, ListNode)) and child.xml_wire is not None]
        if xml_members:
            header += ('from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object_field '
                       'import AIaXmlDataObjectField\n'
                       'from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind '
                       'import AInXmlValueKind\n')
        header += ''.join(parent_imports)
        typed_references = []
        all_imported = set(node.inherited_from_types)
        for _, _, _, value_type, _, _, _ in fields:
            for identity, symbols in self.output_names.items():
                if (identity not in all_imported and identity != node.identity
                        and re.search(r'\b' + re.escape(symbols.python_type) + r'\b', value_type)):
                    typed_references.append(f'    from .{symbols.python_module} import {symbols.python_type}\n')
                    all_imported.add(identity)
        if typed_references:
            header += '\nif TYPE_CHECKING:\n' + ''.join(typed_references)
        header += '\n\n'
        rows = [header, f'class {name}({parent_list}):\n',
                f'    """{_py_doc(node.description or f"Contract for {node.name}.")}"""\n\n',
                f'    __data_object__ = AIcdDataObject(schema_id={node.identity!r}, '
                f'schema_version={self._schema_version_number(node)}, '
                f'description={node.description or node.name!r}, '
                f'naming_convention={self.output_naming_convention!r})\n\n']
        if xml_members:
            rows.append('    __xml_data_object_fields__ = {\n')
            for position, child in xml_members:
                wire = child.xml_wire
                rows.append(f'        {child.name!r}: AIaXmlDataObjectField('
                            f'namespace={wire.namespace_uri!r}, '
                            f'namespace_local_name={wire.local_name!r}, '
                            f'value_kind=AInXmlValueKind.{wire.value_kind}, '
                            f'order={position}, min_occurs={child.min_occurs}, '
                            f'max_occurs={child.max_occurs}),\n')
            rows.append('    }\n\n')
        # Python's XML SDO parser cannot infer repeated fields from the
        # AIiMultiMappedList generic alone. Preserve direct XSD LIST members
        # in the generated read contract so the runtime can materialize each
        # collection (including empty and indexed collections) correctly.
        # JSONDEFS/YAMLDEFS contracts must not gain XML-specific metadata.
        if SourceKind.XMLDEFS in node.source_bindings:
            xml_repeated = tuple(child.name for child in node.structure.children
                                 if isinstance(child, ListNode))
            if xml_repeated:
                rows.append(f'    __xml_repeated_fields__ = {xml_repeated!r}\n\n')
        const_container, key_constants = self._key_constants(node, types, 'python')
        if key_constants:
            rows.append(f'    class {const_container}:\n'
                        '        """Stable XML identity constraint identifiers for this type."""\n')
            for (member_name, key_name), const_name in key_constants.items():
                rows.append(f'        {const_name} = {key_name!r}\n')
            rows.append('\n')
        if indexed_fields:
            rows.append('    __xml_key_definitions__ = {\n')
            for member_name, key_rows in indexed_fields:
                literal_rows = ', '.join(
                    '(' + const_container + '.' + key_constants[(member_name, key_name)]
                    + ', ' + repr(paths) + ', ' + repr(required_key) + ')'
                    for key_name, paths, required_key in key_rows)
                rows.append(f'        {member_name!r}: ({literal_rows},),\n')
            rows.append('    }\n\n')
        if not fields:
            rows.append('    pass\n')
        for original, getter, setter, typ, minimum, maximum, description in fields:
            required = 'required' if minimum else 'optional'
            doc = _py_doc(description or f'Canonical field {original}.')
            runtime_type = (typ if typ in ('str', 'int', 'float', 'bool') else
                            'list' if typ.startswith('list[') else
                            'dict' if typ.startswith('dict[') else None)
            rows.extend((f'    @AIaDataObjectField(field_name={original!r}, '
                         f'presence=AInFieldPresenceKind.{"REQUIRED" if minimum else "ALLOWED"}, '
                         'allows_null=False'
                         + (f', expected_type={runtime_type}' if runtime_type else '') + ')\n',
                         '    @abstractmethod\n', f'    def {getter}(self) -> {typ}:\n',
                         f'        """Return {doc} ({required}, cardinality {minimum}..{maximum})."""\n',
                         '        raise NotImplementedError\n\n'))
        return ''.join(rows)
