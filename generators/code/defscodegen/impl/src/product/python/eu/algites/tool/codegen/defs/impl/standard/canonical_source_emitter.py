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
    replace,
    AIcgdElement_1 as Element,
    AIcgdElementList_1 as ElementList,
    AIcgdList_1 as ListNode,
    AIcgdMap_1 as MapNode,
    AIcgdScalar_1 as Scalar,
    AIcgdEnum_1 as EnumNode,
    AIcgdType_1 as TypeNode,
    AIngComposition_1 as Composition,
    AIngResolutionState_1 as Resolution,
    AIngScalarKind_1 as ScalarKind,
    AIngMapKind_1 as MapKind,
    AIngElementKind_1 as ElementKind,
    AIngSourceInputKind_1 as SourceKind,
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
    if (collection.min_item_count, collection.max_item_count) != (0, -1):
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

    def validate(path, *, attribute_field=False):
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
                wire = matches[0].xml_wire
                if attribute_field:
                    if wire is None or wire.value_kind != 'ATTRIBUTE':
                        raise ValueError('XPath attribute path does not select an XML attribute: ' + path)
                elif wire is not None and wire.value_kind == 'ATTRIBUTE':
                    raise ValueError('XPath element path must use @ for an XML attribute: ' + path)
                leaf = resolve(current)
                if not isinstance(leaf, (Scalar, EnumNode)) or (
                    isinstance(leaf, Scalar) and leaf.scalar_kind in (ScalarKind.ANY, ScalarKind.NULL)):
                    raise NotImplementedError('Indexed LIST key must resolve to a typed scalar: ' + path)
                virtual_map_key = any(
                    binding.representation_kind == 'synthetic_map_key'
                    for bindings in matches[0].source_bindings.values()
                    for binding in bindings)
                if virtual_map_key and (
                    isinstance(leaf, Scalar) and leaf.scalar_kind is not ScalarKind.STRING or
                    isinstance(leaf, EnumNode) and leaf.base_scalar_type is not ScalarKind.STRING
                ):
                    raise NotImplementedError(
                        'JSON/YAML propertyNames keys must resolve to string or string enum: ' + path)

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
            attribute_field = False
            for index, fragment in enumerate(fragments):
                if fragment.startswith('@'):
                    if index != len(fragments) - 1:
                        raise NotImplementedError('XML attribute XPath must be terminal: ' + path)
                    attribute_field = True
                    fragment = fragment[1:]
                if not _XML_NAME.fullmatch(fragment):
                    raise NotImplementedError('Namespace/predicate/axis in indexed LIST XPath requires '
                                              'a dedicated resolver: ' + path)
                names.append(fragment)
            normalized_path = '.'.join(names)
            validate(normalized_path, attribute_field=attribute_field)
            normalized.append(normalized_path)
        if len(set(normalized)) != len(normalized):
            raise ValueError('Duplicate normalized key field in ' + key.identifier)
        indexed.append((key.identifier, tuple(normalized), key.required))
    return tuple(indexed)


def _scoped_index_paths(element: Element, types: Mapping[str, TypeNode]
                        ) -> tuple[tuple[str, str, tuple[str, ...], bool], ...]:
    """Validate an occurrence-scoped index against its referenced nominal TYPE.

    Key metadata stays on the referencing ELEMENT, never on a clone or a
    mutation of the shared TYPE. The selected LIST is inspected without
    changing the canonical model; field XPath is normalized using the same
    strict rules as an ordinary indexed LIST.
    """
    if not element.key_definitions:
        return ()
    if not isinstance(element.structure, TypeNode):
        raise ValueError('Scoped XSD indexes require an object type: ' + element.name)
    identity = element.structure.target_identity or element.structure.identity
    if identity not in types:
        raise ValueError('Unresolved indexed XSD container TYPE ' + identity
                         + ' at ' + element.name)
    group = types[identity].structure
    if not isinstance(group, ElementList):
        raise ValueError('Scoped XSD index owner is not an object TYPE: ' + identity)
    entries = []
    for key in element.key_definitions:
        selector = key.selector.removeprefix('./')
        candidates = [c for c in group.children if isinstance(c, ListNode)
                      and c.name == selector]
        if len(candidates) != 1:
            raise ValueError('Unresolved scoped XSD key selector ' + key.selector
                             + ' in ' + identity)
        candidate = replace(candidates[0], key_definitions=(key,))
        for name, fields, required in _indexed_paths(candidate, types):
            entries.append((selector, name, fields, required))
    return tuple(entries)


def _key_constant_identifier(field: str, key: str) -> str:
    """Produce a normalized KEY_ID__ constant from a canonical index identifier.

    The supplied member is retained for caller compatibility; the index ID alone
    determines the constant name across XMLDEFS, JSONDEFS and YAMLDEFS.
    """
    def words(value: str) -> list[str]:
        value = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', value)
        value = re.sub(r'([A-Z])([A-Z][a-z])', r'\1_\2', value)
        parts = re.findall(r'[A-Za-z0-9]+', value)
        if not parts:
            raise ValueError(f'Cannot form a key constant from {value!r}')
        return [part.upper() for part in parts]
    return _identifier('KEY_ID__' + '_'.join(words(key)), 'java')


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
                 output_naming_convention: str = '',
                 external_parents: Mapping[str, Mapping[str, str]] | None = None,
                 schema_urls: Mapping[tuple[SourceKind, str], str] | None = None,
                 common_output_names: Mapping[str, AIcdDefsCodegenEmissionName] | None = None,
                 common_projection: bool = False,
                 source_representations: Mapping[SourceKind, TypeNode] | None = None):
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
        self.external_parents = dict(external_parents or {})
        self.schema_urls = dict(schema_urls or {})
        self.common_output_names = dict(common_output_names or {})
        self.common_projection = common_projection
        self.source_representations = dict(source_representations or {})
        self._scoped_index_targets: frozenset[tuple[str, str]] = frozenset()

    def with_source_representations(self, sources: Mapping[SourceKind, TypeNode],
                                    schema_urls: Mapping[tuple[SourceKind, str], str]):
        """Return an isolated emitter with the dialects contributing one contract."""
        result = AIcDefsCodegenCanonicalSourceEmitter(
            self.naming, self.output_names, self.package_name,
            output_naming_convention=self.output_naming_convention,
            external_parents=self.external_parents,
            schema_urls=schema_urls,
            common_output_names=self.common_output_names,
            common_projection=self.common_projection,
            source_representations=sources)
        # Shared type rendering must retain indexes discovered on referencing
        # elements during render().  Rebinding the format metadata must not
        # erase the selected list signatures (AIiMultiMappedList in Java/Python).
        result._scoped_index_targets = self._scoped_index_targets
        return result

    def _representation(self, node: TypeNode, kind: SourceKind) -> TypeNode:
        """Select the original source TYPE for its independent schema identity."""
        return self.source_representations.get(kind, node)

    def _published_schema_url(self, node: TypeNode, kind: SourceKind) -> str:
        """Find a declaration's own published document URL, not its logical ID.

        Only a document-root binding (``#``) may advertise the document URL.
        Synthetic and $defs contracts must not all masquerade as the document
        root when external inheritance resolves a published schema $id.
        """
        urls = {self.schema_urls.get((kind, binding.source_resource), '')
                for binding in node.source_bindings.get(kind, ())
                if binding.source_pointer == '#'}
        urls.discard('')
        if len(urls) > 1:
            raise ValueError('Conflicting published schema URLs for ' + node.identity)
        return next(iter(urls), '')

    def render(self, types: Sequence[TypeNode]) -> tuple[AIcdDefsCodegenEmittedFile, ...]:
        """Render all declarations or raise before returning any partial outputs.

        ``types`` must be the normalized result of a validated canonical
        pipeline. No unresolved symbols, unknown parents, unsupported group
        cardinalities, inline enum, or unhandled union constructs are accepted.
        """
        ordered = self._collect(types)
        selected = set()
        for definition in ordered.values():
            if isinstance(definition.structure, ElementList):
                for child in definition.structure.children:
                    if isinstance(child, Element) and child.key_definitions:
                        identity = (child.structure.target_identity or child.structure.identity)
                        for selector, _, _, _ in _scoped_index_paths(child, ordered):
                            selected.add((identity, selector))
        self._scoped_index_targets = frozenset(selected)
        self._validate_names(ordered)
        if self.common_output_names:
            if set(self.common_output_names) != set(ordered):
                raise ValueError('Common names must cover every canonical declaration')
            if any(((not self.output_names[key].java_type.startswith('AIxUnused') and
                     self.common_output_names[key].java_type == self.output_names[key].java_type) or
                    (not self.output_names[key].python_module.startswith('aix_unused_') and
                     self.common_output_names[key].python_module == self.output_names[key].python_module))
                   for key, node in ordered.items() if not isinstance(node.structure, EnumNode)):
                raise ValueError('Common and source-specific interfaces must use different catalog names')
            shared_emitter = AIcDefsCodegenCanonicalSourceEmitter(
                self.naming, self.common_output_names, self.package_name,
                external_parents=self.external_parents,
                common_projection=True)
            shared = shared_emitter.render(types)
        else:
            shared = ()
        choice_parents = self._choice_parents(ordered)
        outputs = []
        for node in ordered.values():
            if self.common_projection and isinstance(node.structure, EnumNode):
                continue  # Enums are shared value types, not nominal DataObjects.
            # A named JSON/YAML array or object-keyed collection is a TYPE
            # alias for a list-valued field, not a standalone DataObject.
            # Keep the alias in the linker registry to resolve $ref, but do
            # not emit a misleading interface extending a collection.
            if isinstance(node.structure, ListNode):
                if node.inherited_from_types:
                    raise ValueError('List alias cannot have DataObject parents: ' + node.identity)
                continue
            names = self.output_names[node.identity]
            outputs.append(AIcdDefsCodegenEmittedFile('java',
                self.package_name.replace('.', '/') + '/' + names.java_type + '.java',
                self._java_source(node, ordered, choice_parents), node.identity))
            outputs.append(AIcdDefsCodegenEmittedFile('python',
                self.package_name.replace('.', '/') + '/' + names.python_module + '.py',
                self._python_source(node, ordered, choice_parents), node.identity))
        return tuple(shared) + tuple(outputs)

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
            if (structure.min_item_count, structure.max_item_count) != (1, 1):
                raise NotImplementedError(f'CHOICE group cardinality unsupported: {node.identity}')
            if node.inherited_from_types:
                raise NotImplementedError(f'CHOICE inheritance unsupported: {node.identity}')
            if not structure.children:
                raise ValueError(f'Empty CHOICE: {node.identity}')
            for child in structure.children:
                if (not isinstance(child, Element) or not isinstance(child.structure, TypeNode)
                        or child.structure.target_identity or child.min_item_count != 0 or child.max_item_count != 1):
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
                if parent not in types and parent not in self.external_parents:
                    raise ValueError(f'Unresolved parent {parent!r} of {node.identity!r}')

    @staticmethod
    def _constraint_decorators(value, types: Mapping[str, TypeNode], target: str):
        """Resolve canonical facets without guessing method names or losing references."""
        visited = set()
        while isinstance(value, TypeNode):
            identity = value.target_identity or value.identity
            if identity in visited:
                raise ValueError('Recursive constrained value: ' + identity)
            visited.add(identity)
            if value.target_identity:
                if identity not in types:
                    raise ValueError('Unresolved constrained value: ' + identity)
                value = types[identity].structure
            else:
                value = value.structure
        result = []
        if isinstance(value, Scalar):
            if value.scalar_kind is ScalarKind.STRING:
                arguments = []
                if value.min_length >= 0: arguments.append(('minLength', 'min_length', value.min_length))
                if value.max_length >= 0: arguments.append(('maxLength', 'max_length', value.max_length))
                if value.pattern: arguments.append(('pattern', 'pattern', value.pattern))
                if value.format: arguments.append(('format', 'format', value.format))
                if arguments:
                    result.append(('String', arguments))
            if value.scalar_kind in (ScalarKind.INTEGER, ScalarKind.NUMBER):
                arguments = []
                for name, py_name in (('minimum', 'minimum'), ('maximum', 'maximum'),
                                      ('multipleOf', 'multiple_of')):
                    raw = getattr(value, py_name)
                    if raw: arguments.append((name, py_name, raw))
                for name, py_name in (('exclusiveMinimum', 'exclusive_minimum'),
                                      ('exclusiveMaximum', 'exclusive_maximum')):
                    if getattr(value, py_name): arguments.append((name, py_name, True))
                if value.format: arguments.append(('format', 'format', value.format))
                if arguments:
                    result.append(('Numeric', arguments))
        elif isinstance(value, ListNode):
            arguments = []
            if value.min_item_count > 0: arguments.append(('minItems', 'min_items', value.min_item_count))
            if value.max_item_count >= 0: arguments.append(('maxItems', 'max_items', value.max_item_count))
            if value.unique_items: arguments.append(('uniqueItems', 'unique_items', True))
            if arguments: result.append(('List', arguments))
        elif isinstance(value, ElementList):
            arguments = []
            if value.min_properties >= 0: arguments.append(('minProperties', 'min_properties', value.min_properties))
            if value.max_properties >= 0: arguments.append(('maxProperties', 'max_properties', value.max_properties))
            if arguments: result.append(('Object', arguments))
        output = []
        for category, arguments in result:
            stem = f'AIaDataObjectField{category}Constraints'
            if target == 'java':
                output.append('    @eu.algites.lib.data.dataobject.' + stem + '('
                    + ', '.join(f'{name} = ' + (_java_string(v) if isinstance(v, str)
                        else str(v).lower() if isinstance(v, bool) else str(v))
                        for name, _, v in arguments) + ')\n')
            else:
                output.append('    @' + stem + '('
                    + ', '.join(f'{name}=' + repr(v) for _, name, v in arguments) + ')\n')
        return tuple(output)

    @staticmethod
    def _choice_constraint_imports() -> str:
        """Import the same field constraint decorators used by normal contracts.

        Choice alternatives are immutable records rather than AIiDataObjects, but
        their getters must retain the original schema facet annotations too.

        Returns:
            Python imports for all supported scalar and collection restrictions.
        """
        return ''.join(
            'from eu.algites.lib.data.dataobject.aia_data_object_field_'
            + category.lower() + '_constraints import AIaDataObjectField'
            + category + 'Constraints\n'
            for category in ('String', 'Numeric', 'List', 'Object'))

    def _typed(self, node, target: str, types: Mapping[str, TypeNode],
               containing: str) -> str:
        """Resolve a concrete field type; never emit untyped Object/Any getters."""
        if isinstance(node, TypeNode):
            reference = node.target_identity or node.identity
            if reference not in types:
                raise ValueError(f'Unknown referenced TYPE {reference!r} inside {containing}')
            declaration = types[reference]
            if isinstance(declaration.structure, ListNode):
                # Resolve a named array/map to its actual collection value;
                # do not reference an artificial collection DataObject.
                return self._typed(declaration.structure, target, types, containing)
            symbol = self.output_names[reference]
            return symbol.java_type if target == 'java' else symbol.python_type
        if isinstance(node, Scalar):
            if node.scalar_kind is ScalarKind.ANY:
                raise ValueError(
                    f'{containing}: untyped ANY scalar cannot be emitted as a public '
                    f'{target} DataObject getter (Object/Any is forbidden); '
                    'supply a concrete scalar, enum, or named structured type in the schema')
            mapping = _JAVA_SCALAR if target == 'java' else _PY_SCALAR
            if node.scalar_kind not in mapping:
                raise NotImplementedError(f'No lossless {target} scalar for {node.scalar_kind.value} inside {containing}')
            if node.format and node.scalar_kind not in (ScalarKind.STRING, ScalarKind.INTEGER, ScalarKind.NUMBER):
                raise NotImplementedError(f'Unsupported {target} scalar format {node.format!r} inside {containing}')
            return mapping[node.scalar_kind]
        if isinstance(node, ListNode):
            _indexed_paths(node, types)
            item = self._typed(node.item, target, types, containing + '/items')
            if node.key_definitions:
                return (f'eu.algites.lib.common.list.AIiMultiMappedList<{'? extends ' if target == 'java' else ''}{item}>'
                        if target == 'java' else f'AIiMultiMappedList[{item}]')
            return f'java.util.List<? extends {item}>' if target == 'java' else f'list[{item}]'
        if isinstance(node, MapNode):
            if node.map_kind not in (MapKind.COMMON_MAP, MapKind.INTEGRATED_PROPERTY_MAP):
                raise ValueError(f'Unsupported map kind in {containing}')
            key = self._typed(node.key_type, target, types, containing + '/key')
            value = self._typed(node.value_type, target, types, containing + '/value')
            if target == 'java' and self.common_projection:
                return f'java.util.Map<? extends {key}, ? extends {value}>'
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
        if (structure.min_item_count, structure.max_item_count) != (1, 1):
            raise NotImplementedError(f'Group cardinality requires group-aware emission: {node.identity}')
        results = []
        used = set()
        for child in structure.children:
            if isinstance(child, Element):
                if child.max_item_count != 1:
                    raise NotImplementedError(f'Repeated field requires occurrence-preserving emitter: {node.identity}/{child.name}')
                name, value, minimum, maximum, description = (child.name, child.structure,
                    child.min_item_count, child.max_item_count, child.description)
            elif isinstance(child, ListNode):
                # XSD maxOccurs=unbounded produces a LIST directly in the
                # ELEMENTLIST, not an ELEMENT wrapping a LIST. Preserve the
                # collection type and its exact occurrence bounds. Only the
                # unconstrained 0..unbounded case is currently representable;
                # _typed() fails closed for all other bounds.
                if not child.name:
                    raise ValueError(f'Unnamed direct LIST inside {node.identity}')
                name, value, minimum, maximum, description = (
                    child.name, child, child.min_item_count, child.max_item_count, '')
            elif isinstance(child, MapNode) and child.map_kind is MapKind.INTEGRATED_PROPERTY_MAP:
                name, value, minimum, maximum, description = child.name, child, 0, -1, ''
            else:
                raise NotImplementedError(f'Unsupported {child.kind.value} in object {node.identity}')
            binding_kinds = ({binding.representation_kind
                              for bindings in child.source_bindings.values() for binding in bindings}
                             if isinstance(child, Element) else set())
            getter_role = ('multi_mapped_list_key_synthetic_getter' if 'synthetic_map_key' in binding_kinds
                           else 'multi_mapped_list_value_synthetic_getter' if 'synthetic_map_value' in binding_kinds
                           else 'list_getter' if isinstance(value, ListNode)
                           else 'standard_getter')
            getter = _identifier(self.naming.method_name(getter_role, name), target)
            setter = _identifier(self.naming.method_name('standard_setter', name), target)
            if getter == setter or getter in used or setter in used:
                raise ValueError(f'Conflicting member names in {node.identity}: {getter}/{setter}')
            used.update((getter, setter))
            value_type = self._typed(value, target, types, node.identity + '/' + name)
            if isinstance(value, ListNode) and (node.identity, name) in self._scoped_index_targets:
                item_type = self._typed(value.item, target, types, node.identity + '/' + name + '/items')
                value_type = (f'eu.algites.lib.common.list.AIiMultiMappedList<{'? extends ' if target == 'java' else ''}{item_type}>'
                              if target == 'java' else f'AIiMultiMappedList[{item_type}]')
            results.append((name, getter, setter, value_type, minimum, maximum, description))
        return results

    def _key_constants(self, node: TypeNode, types: Mapping[str, TypeNode],
                       target: str) -> tuple[str, dict[tuple[str, str], str]]:
        """Assign CONST identifiers for every object member and collection index.

        Preserve source spelling in values and use consistent normalized symbols
        in Java/Python. Collisions of different source spellings fail closed.
        """
        if not isinstance(node.structure, ElementList):
            return '', {}
        result: dict[tuple[str, str], str] = {}
        symbols: dict[str, str] = {}

        def register(source: str, identifier: str, symbol: str) -> None:
            existing = symbols.setdefault(symbol, identifier)
            if existing != identifier:
                raise ValueError(
                    f'Conflicting key or field constant in {node.identity}: '
                    f'{symbol} maps to both {existing!r} and {identifier!r}')
            result[source, identifier] = symbol

        # Every direct DataObject field, not only fields selected by xs:key,
        # has a public, stable logical field-name constant. In particular this
        # includes ordinary JSONDEFS/YAMLDEFS properties and MAP members.
        for child in node.structure.children:
            if not isinstance(child, (Element, ListNode, MapNode)):
                continue
            if not child.name:
                raise ValueError(f'Unnamed object member in {node.identity}')
            parts = re.findall(r'[A-Za-z0-9]+',
                re.sub(r'([A-Z])([A-Z][a-z])', r'\1_\2',
                       re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', child.name)))
            if not parts:
                raise ValueError(f'Invalid DataObject field name: {child.name!r}')
            symbol = _identifier('FIELD_NAME__' + '_'.join(part.upper() for part in parts), target)
            register('__field__', child.name, symbol)

        for child in node.structure.children:
            if isinstance(child, ListNode):
                key_rows = ((child.name, key_name, fields) for key_name, fields, _
                            in _indexed_paths(child, types))
            elif isinstance(child, Element) and child.key_definitions:
                key_rows = ((child.name, name, fields) for _, name, fields, _
                            in _scoped_index_paths(child, types))
            else:
                continue
            for owner_name, key_name, field_names in key_rows:
                symbol = _key_constant_identifier(owner_name, key_name)
                if (owner_name, key_name) in result:
                    raise ValueError(f'Duplicate key identifier in {node.identity}: {key_name}')
                register(owner_name, key_name, symbol)
                for field_name in field_names:
                    parts = re.findall(r'[A-Za-z0-9]+',
                        re.sub(r'([A-Z])([A-Z][a-z])', r'\1_\2',
                               re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', field_name)))
                    if not parts:
                        raise ValueError(f'Invalid key field name: {field_name!r}')
                    field_symbol = _identifier(
                        'FIELD_NAME__' + '_'.join(part.upper() for part in parts), target)
                    register('__field__', field_name, field_symbol)
        if not result:
            return '', result
        container = _identifier(self.naming.method_name('const_container_interface', node.name), target)
        methods = {member[1] for member in self._fields(node, types, target)}
        methods.update(member[2] for member in self._fields(node, types, target))
        if container in methods:
            raise ValueError(f'CONST naming collides with a generated method: {container}')
        return container, result

    def _data_object_technology(self, node: TypeNode) -> str:
        """Use the source-specific marker only when all bindings agree.

        A merged cross-technology declaration must not falsely claim that the
        same instance has one particular wire encoding. The generic marker is
        still a valid SDO input and preserves source independence.
        """
        if self.common_projection:
            return ''
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
            # The old format-specific wrapper was sealed while its shared
            # base was empty. With one nominal contract the shared type must
            # itself retain the exclusive (sealed) variant hierarchy.
            if self.common_projection and not self.source_representations:
                return header + f'public interface {name} {{\n}}\n'
            parent = (f' extends {self.common_output_names[node.identity].java_type}'
                      if self.common_output_names and not self.common_projection else
                      ' extends eu.algites.lib.data.dataobject.AIiDataObject')
            return (header + f'public sealed interface {name}{parent} '
                    f'permits {", ".join(variants)} {{\n}}\n')
        if node.identity in choice_parents:
            parent_type = self.output_names[choice_parents[node.identity]].java_type
            if node.inherited_from_types:
                raise NotImplementedError(f'CHOICE variant inheritance unsupported: {node.identity}')
            if isinstance(node.structure, Scalar):
                scalar_type = self._typed(node.structure, 'java', types, node.identity + '/value')
                getter = _identifier(self.naming.method_name('standard_getter', 'value'), 'java')
                constraints = ''.join(self._constraint_decorators(node.structure, types, 'java'))
                return (header + f'public record {name}({scalar_type} value) implements {parent_type} {{\n'
                        + constraints
                        + f'    /** @return exact typed value of this exclusive alternative */\n'
                        + f'    public {scalar_type} {getter}() {{ return value; }}\n}}\n')
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
            if SourceKind.XMLDEFS in node.source_bindings:
                first_qnames = self._xml_first_qnames(node, types)
                if first_qnames:
                    serialized_names = ', '.join(_java_string(qname) for qname in first_qnames)
                    lines.append('    /**\n'
                                 '     * Return the possible first XML QNames of this variant.\n'
                                 '     * @return immutable set of expanded names without synthetic wrappers\n'
                                 '     */\n'
                                 '    public static java.util.Set<String> xmlFirstQNames() {\n'
                                 f'        return java.util.Set.of({serialized_names});\n'
                                 '    }\n\n')
            required = [(field, component) for field, component in zip(fields, components)
                        if field[4] > 0]
            if required:
                lines.append(f'    /** Validate required fields on construction. */\n'
                             f'    public {name} {{\n')
                for field, component in required:
                    lines.append(f'        java.util.Objects.requireNonNull({component}, '
                                 f'{_java_string(field[0])});\n')
                lines.append('    }\n\n')
            for position, (field, component) in enumerate(zip(fields, components)):
                original, getter, _, typ, minimum, _, description = field
                member = next((child for child in node.structure.children
                               if getattr(child, 'name', None) == original), None)
                constraint_value = member.structure if isinstance(member, Element) else member
                wire = member.xml_wire if isinstance(member, (Element, ListNode)) else None
                if wire is not None:
                    lines.append('    @eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObjectField('
                                 f'namespace = {_java_string(wire.namespace_uri)}, '
                                 f'namespaceLocalName = {_java_string(wire.local_name)}, '
                                 f'valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.{wire.value_kind}'
                                 ')\n')
                # A sealed record is not an SDO, but its canonical getter
                # still needs a stable semantic position and a transparent
                # embedding flag for generic XML choice materialization.
                lines.append('    @eu.algites.lib.data.dataobject.AIaDataObjectField('
                             + ('embedded = true' if wire is None else
                                'dataFieldName = ' + _java_string(original))
                             + f', order = {position})\n')
                lines.extend(self._constraint_decorators(constraint_value, types, 'java'))
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
            used_identifiers = set()
            for index, value in enumerate(node.structure.values):
                wire = value.wire_value
                literal = _enum_literal(wire, kind, 'java')
                if wire in seen:
                    raise ValueError(f'Duplicate enum wire code in {node.identity}: {wire!r}')
                seen.add(wire)
                role = 'string_enum_item' if kind is ScalarKind.STRING else 'non_string_enum_item'
                member = _identifier(self.naming.method_name(role, wire), 'java')
                if member in used_identifiers:
                    raise ValueError(f'Enum name collision {member!r} at {node.identity}')
                used_identifiers.add(member)
                members.append(f'    /** Exact wire value {_java_doc(wire)}. */\n'
                               f'    {member}({literal})')
            return (header + f'public enum {name} {{\n' + ',\n'.join(members) + ';\n\n'
                    f'    private final {code_type} wireCode;\n\n'
                    f'    /** @param aWireCode original typed schema code */\n'
                    f'    {name}({code_type} aWireCode) {{ wireCode = aWireCode; }}\n\n'
                    '    /** @return the exact typed schema wire value */\n'
                    f'    public {code_type} code() {{ return wireCode; }}\n}}\n')
        if isinstance(node.structure, ListNode):
            # A named, keyed JSON/YAML object is a collection DataObject,
            # not an artificial object with a persisted `items` property.
            # Preserve the established SDO ABI: a named read-only collection
            # directly extends the typed AIiMultiMappedList contract.
            item = self._typed(node.structure.item, 'java', types, node.identity + '/items')
            parent_types = [self.output_names[x].java_type if x in self.output_names
                            else self.external_parents[x]['java']
                            for x in node.inherited_from_types]
            if self.common_projection:
                parent_types = ['eu.algites.lib.data.dataobject.AIiDataObject']
            elif self.common_output_names:
                parent_types = [self.common_output_names[node.identity].java_type] + parent_types
            if not parent_types:
                parent_types.append('eu.algites.lib.data.dataobject.AIiDataObject')
            parent_types.append('eu.algites.lib.common.list.AIiMultiMappedList<' + item + '>')
            for source, technology in ((SourceKind.JSONDEFS, 'json'), (SourceKind.YAMLDEFS, 'yaml')):
                if source in node.source_bindings and not self.common_projection:
                    header += (f'@eu.algites.lib.data.dataobject.{technology}defs.AIa{technology.title()}DataObject('
                               f'schemaId = {_java_string(node.identity)}, '
                               f'schemaVersion = {self._schema_version_number(node)}'
                               + (f', schemaUrl = {_java_string(url)}' if (url := self._published_schema_url(node, source)) else '')
                               + ')\n')
                    header += ('@eu.algites.lib.data.dataobject.jsonschema.AIaDataObjectJsonSchema('
                               f'schemaId = {_java_string(node.identity)}, '
                               f'schemaVersion = {self._schema_version_number(node)}'
                               + (f', schemaUrl = {_java_string(url)}' if (url := self._published_schema_url(node, source)) else '')
                               + ')\n')
            return (header + ('@eu.algites.lib.data.dataobject.AIaDataObject('
                    + 'description = ' + _java_string(node.description or node.name)
                    + ')\n' if self.common_projection or not self.common_output_names else '') + 'public interface ' + name + ' extends '
                    + ', '.join(parent_types) + ' {\n}\n')
        fields = self._fields(node, types, 'java')
        technology = self._data_object_technology(node)
        marker = ('eu.algites.lib.data.dataobject.' +
                  (technology + 'defs.AIi' + technology.title() + 'DataObject'
                   if technology else 'AIiDataObject'))
        parent_types = [self.output_names[x].java_type if x in self.output_names
                        else self.external_parents[x]['java']
                        for x in node.inherited_from_types]
        if self.common_projection:
            parent_types = parent_types or ['eu.algites.lib.data.dataobject.AIiDataObject']
        elif self.common_output_names:
            parent_types.insert(0, self.common_output_names[node.identity].java_type)
        if marker not in parent_types and not self.common_projection:
            parent_types.append(marker)
        if not parent_types:
            parent_types.append(marker)
        parents = ' extends ' + ', '.join(parent_types)
        schema_version = self._schema_version_number(node)
        for source, format_name in ((SourceKind.JSONDEFS, 'json'), (SourceKind.YAMLDEFS, 'yaml')):
            if source in node.source_bindings and (not self.common_projection or self.source_representations):
                source_node = self._representation(node, source)
                header += (f'@eu.algites.lib.data.dataobject.{format_name}defs.AIa{format_name.title()}DataObject('
                           f'schemaId = {_java_string(source_node.identity)}, '
                           f'schemaVersion = {schema_version}'
                           + (f', schemaUrl = {_java_string(url)}' if (url := self._published_schema_url(source_node, source)) else '')
                           + ')\n')
                if source == SourceKind.YAMLDEFS and SourceKind.JSONDEFS in node.source_bindings:
                    continue  # one modern schema annotation; both legacy dialect annotations remain
                header += ('@eu.algites.lib.data.dataobject.jsonschema.AIaDataObjectJsonSchema('
                           f'schemaId = {_java_string(source_node.identity)}, '
                           f'schemaVersion = {schema_version}'
                           + (f', schemaUrl = {_java_string(url)}' if (url := self._published_schema_url(source_node, source)) else '')
                           + ')\n')
        if SourceKind.XMLDEFS in node.source_bindings and (not self.common_projection or self.source_representations):
            match = re.fullmatch(r'\{([^}]*)\}([^/]+)',
                                 self._representation(node, SourceKind.XMLDEFS).identity)
            if match:
                header += ('@eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObject(' +
                           'definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, ' +
                           f'namespace = {_java_string(match.group(1))}, ' +
                           f'namespaceLocalName = {_java_string(match.group(2))})\n')
                header += ('@eu.algites.lib.data.dataobject.xmlschema.AIaDataObjectXmlSchema(' +
                           'definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, ' +
                           f'namespace = {_java_string(match.group(1))}, ' +
                           f'namespaceLocalName = {_java_string(match.group(2))})\n')
        if self.common_projection or not self.common_output_names:
            header += ('@eu.algites.lib.data.dataobject.AIaDataObject('
                       f'description = {_java_string(node.description or node.name)})\n')
        rows = [header, f'public interface {name}{parents} {{\n']
        const_container, key_constants = self._key_constants(node, types, 'java')
        if key_constants:
            rows.append(f'    /** Canonical key IDs and field names for this DataObject. */\n'
                        f'    interface {const_container} {{\n')
            emitted_constants: set[str] = set()
            for (_, original_name), const_name in key_constants.items():
                if const_name in emitted_constants:
                    continue
                emitted_constants.add(const_name)
                rows.append(f'        /** Source identifier {_java_doc(original_name)}. */\n'
                            f'        String {const_name} = {_java_string(original_name)};\n')
            rows.append('    }\n\n')
        for position, (original, getter, setter, typ, minimum, maximum, description) in enumerate(fields):
            xml_member = next((child for child in node.structure.children
                               if isinstance(child, (Element, ListNode)) and child.name == original), None)
            # Indexed-map entry key/value accessors are synthetic views, not
            # persisted fields. SDO Codegen recognizes their configured names
            # and implements them without a writable DataObject field.
            binding_kinds = ({binding.representation_kind
                              for bindings in xml_member.source_bindings.values() for binding in bindings}
                             if isinstance(xml_member, Element) else set())
            if {'synthetic_map_key', 'synthetic_map_value'} & binding_kinds:
                rows.append('    /** @return virtual indexed-map entry ' +
                            ('key' if 'synthetic_map_key' in binding_kinds else 'value') +
                            ', supplied by the SDO collection implementation. */\n'
                            + f'    {typ} {getter}();\n\n')
                continue
            wire = xml_member.xml_wire if xml_member is not None and (
                not self.common_projection or self.source_representations) else None
            if wire is not None:
                rows.append('    @eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObjectField('
                            f'namespace = {_java_string(wire.namespace_uri)}, '
                            f'namespaceLocalName = {_java_string(wire.local_name)}, '
                            f'valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.{wire.value_kind}'
                            ')\n')
                rows.append('    @eu.algites.lib.data.dataobject.xmlschema.AIaDataObjectFieldXmlSchema('
                            f'namespace = {_java_string(wire.namespace_uri)}, '
                            f'namespaceLocalName = {_java_string(wire.local_name)}, '
                            f'valueKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind.{wire.value_kind}'
                            ')\n')
            member = next((child for child in node.structure.children
                           if isinstance(child, ListNode) and child.name == original), None)
            for key_name, paths, required_key in _indexed_paths(member, types) if member else ():
                path_literals = ', '.join(const_container + '.' + key_constants[('__field__', path)] for path in paths)
                rows.append('    @eu.algites.lib.data.dataobject.AIaKeyDefinition('
                            f'name = {const_container}.{key_constants[(original, key_name)]}, '
                            f'fields = {{{path_literals}}}, '
                            f'required = {str(required_key).lower()})\n')
            scoped = _scoped_index_paths(xml_member, types) if isinstance(xml_member, Element) else ()
            for selector, key_name, paths, required_key in scoped:
                path_literals = ', '.join(const_container + '.' + key_constants[('__field__', path)]
                                          for path in paths)
                rows.append('    @eu.algites.lib.data.dataobject.AIaKeyDefinition('
                            f'name = {const_container}.{key_constants[(original, key_name)]}, '
                            f'selector = {_java_string(selector)}, fields = {{{path_literals}}}, '
                            f'required = {str(required_key).lower()})\n')
            is_embedded = (isinstance(xml_member, Element)
                           and xml_member.element_kind is ElementKind.EMBEDDED)
            field_value = xml_member.structure if isinstance(xml_member, Element) else xml_member
            # A list-valued property has two independent bounds: whether the
            # property itself is present, and how many items it contains. Keep
            # presence based on the ELEMENT, but publish collection limits in
            # the common schema-neutral field-count metadata for all formats.
            count_min, count_max = ((field_value.min_item_count, field_value.max_item_count)
                                    if isinstance(field_value, ListNode) else (minimum, maximum))
            annotation_fields = (["embedded = true"] if is_embedded else
                                 [f'dataFieldName = {_java_string(original)}']) + [
                f'presence = eu.algites.lib.data.dataobject.AInFieldPresenceKind.{"REQUIRED" if minimum else "ALLOWED"}',
                'allowsNull = false', f'order = {position}',
                f'minItemCount = {count_min}', f'maxItemCount = {count_max}',
            ]
            if isinstance(xml_member, Element):
                annotation_fields.append('isEmptyAllowed = ' + str(xml_member.is_empty_allowed).lower())
                if xml_member.default_kind:
                    annotation_fields.append('defaultValue = @eu.algites.lib.data.dataobject.AIaDataObjectFieldDefault('
                        'kind = eu.algites.lib.data.dataobject.AInDataObjectFieldDefaultKind.'
                        + xml_member.default_kind + ', defined = true, value = '
                        + _java_string(xml_member.default_value) + ')')
            if self.common_projection or not self.common_output_names:
                rows.extend(self._constraint_decorators(field_value, types, 'java'))
                rows.append('    @eu.algites.lib.data.dataobject.AIaDataObjectField('
                            + ', '.join(annotation_fields) + ')\n')
            documented = _java_doc(description or f'Value of schema field {original}.')
            required = 'required' if minimum else 'optional'
            rows.extend((
                f'    /** {documented} Field is {required}; cardinality {minimum}..{maximum}.\n'
                f'     * @return field value in its canonical representation\n     */\n'
                f'    {typ} {getter}();\n\n'))
        rows.append('}\n')
        return ''.join(rows)

    def _xml_enum_imports(self, node: TypeNode, types: Mapping[str, TypeNode]) -> dict[str, str]:
        """Describe generated XML enum member types with explicit lazy imports.

        Naming profiles, not Python runtime guesses, determine the exact module
        and class name. Only XML-bound, nominal enum members are included.

        Args:
            node: Canonical object or closed choice variant.
            types: Complete linked canonical type map.

        Returns:
            Semantic XML field names mapped to qualified enum class symbols.
        """
        if not isinstance(node.structure, ElementList) or SourceKind.XMLDEFS not in node.source_bindings:
            return {}
        result = {}
        for child in node.structure.children:
            if (not isinstance(child, Element) or child.xml_wire is None
                    or not isinstance(child.structure, TypeNode)):
                continue
            target_id = child.structure.target_identity or child.structure.identity
            nominal = types.get(target_id)
            if nominal is None or not isinstance(nominal.structure, EnumNode):
                continue
            symbol = self.output_names[target_id]
            result[child.name] = (self.package_name + '.' + symbol.python_module
                                  + ':' + symbol.python_type)
        return result

    @staticmethod
    def _xml_first_qnames(node: TypeNode, types: Mapping[str, TypeNode]) -> tuple[str, ...]:
        """Find leading XML element QNames of an exclusive variant.

        Resolve transparent embedded structures through their nominal TYPE
        references. This is a structural hint for XML parsing, not an extra
        field or an XML wrapper. Every lexical QName comes from an XML wire
        declaration, never from a synthetic Java/Python getter name.

        Args:
            node: Canonical variant whose first XML member is to be found.
            types: Linked canonical type definitions.

        Returns:
            Ordered distinct expanded XML QNames that may begin the variant.

        Raises:
            ValueError: A recursive reference prevents determining the prefix.
        """
        def first(value, visiting: frozenset[str]) -> tuple[str, ...]:
            if isinstance(value, Element):
                wire = value.xml_wire
                if wire is not None:
                    if wire.value_kind != 'ELEMENT' or not wire.local_name:
                        return ()
                    return ('{' + wire.namespace_uri + '}' + wire.local_name
                            if wire.namespace_uri else wire.local_name,)
                return first(value.structure, visiting)
            if isinstance(value, TypeNode):
                identity = value.target_identity or value.identity
                if identity in visiting:
                    raise ValueError('Recursive XML CHOICE prefix: ' + identity)
                definition = types.get(identity, value)
                return first(definition.structure, visiting | {identity})
            if isinstance(value, ElementList):
                result = []
                for child in value.children:
                    result.extend(first(child, visiting))
                    if (value.composition == Composition.SEQUENCE and
                            getattr(child, 'min_item_count', 1) != 0):
                        break
                return tuple(dict.fromkeys(result))
            if isinstance(value, ListNode):
                # Repeated XML particles retain their own element QName. The
                # item's nominal type may have a different inner wire shape.
                wire = value.xml_wire
                if wire is not None and wire.value_kind == 'ELEMENT' and wire.local_name:
                    return ('{' + wire.namespace_uri + '}' + wire.local_name
                            if wire.namespace_uri else wire.local_name,)
                return first(value.item, visiting)
            return ()
        return first(node, frozenset())

    def _python_source(self, node: TypeNode, types: Mapping[str, TypeNode],
                       choice_parents: Mapping[str, str]) -> str:
        """Render one Python ABC or enum with equivalent typed method contracts."""
        name = self.output_names[node.identity].python_type
        header = 'from __future__ import annotations\nfrom typing import Any\n\n'
        if isinstance(node.structure, ElementList) and node.structure.composition == Composition.CHOICE:
            # A CHOICE is not a mutable SDO, but the XML runtime needs an
            # explicit variant registry. Python modules are imported lazily;
            # __subclasses__() alone would silently omit unloaded alternatives.
            variants = tuple(self.package_name + '.'
                             + self.output_names[child.structure.identity].python_module + ':'
                             + self.output_names[child.structure.identity].python_type
                             for child in node.structure.children)
            common = self.common_output_names.get(node.identity)
            import_common = (f'from .{common.python_module} import {common.python_type}\n'
                             if common else '')
            base = common.python_type if common else 'ABC'
            return (header + 'from abc import ABC\n' + import_common + '\n\n'
                    f'class {name}({base}):\n'
                    f'    """{_py_doc(node.description or "Exclusive canonical choice")}"""\n'
                    f'    __xml_choice_variant_imports__ = {variants!r}\n')
        if node.identity in choice_parents:
            if node.inherited_from_types:
                raise NotImplementedError(f'CHOICE variant inheritance unsupported: {node.identity}')
            base = self.output_names[choice_parents[node.identity]]
            if isinstance(node.structure, Scalar):
                scalar_type = self._typed(node.structure, 'python', types, node.identity + '/value')
                getter = _identifier(self.naming.method_name('standard_getter', 'value'), 'python')
                constraints = ''.join(self._constraint_decorators(node.structure, types, 'python'))
                constraint_imports = self._choice_constraint_imports()
                return (header + 'from dataclasses import dataclass\nfrom typing import final\n'
                        + constraint_imports
                        + f'from .{base.python_module} import {base.python_type}\n\n\n'
                        + '@final\n@dataclass(frozen=True)\n'
                        + f'class {name}({base.python_type}):\n'
                        + f'    """{_py_doc(node.description or "Exclusive canonical variant")}"""\n'
                        + f'    value: {scalar_type}\n\n'
                        + constraints
                        + f'    def {getter}(self) -> {scalar_type}:\n'
                        + '        """Return the exact typed alternative value."""\n'
                        + '        return self.value\n')
            fields = self._fields(node, types, 'python')
            components = [f'field{i}' for i in range(1, len(fields) + 1)]
            if any(field[1] in components for field in fields):
                raise ValueError(f'CHOICE getter conflicts with dataclass component: {node.identity}')
            lines = [header, 'from dataclasses import dataclass\nfrom typing import final\n',
                     self._choice_constraint_imports(),
                     f'from .{base.python_module} import {base.python_type}\n\n\n',
                     '@final\n@dataclass(frozen=True)\n',
                     f'class {name}({base.python_type}):\n',
                     f'    """{_py_doc(node.description or "Exclusive canonical object variant")}"""\n',
                     f'    __xml_choice_component_names__ = '
                     f'{tuple(field[0] for field in fields)!r}\n']
            # Read-only enum types are imported under TYPE_CHECKING by the
            # generated contract. Give the XML runtime an exact lazy symbol
            # rather than degrading the wire value to an untyped string.
            enum_types = self._xml_enum_imports(node, types)
            if enum_types:
                lines.append(f'    __xml_scalar_type_imports__ = {enum_types!r}\n')
            # A nested EMBEDDED branch has no XML QName of its own. Its
            # first serialized child must still select the correct CHOICE
            # alternative before requiring that branch's concrete SDO class.
            if SourceKind.XMLDEFS in node.source_bindings:
                first_qnames = self._xml_first_qnames(node, types)
                if first_qnames:
                    lines.append(f'    __xml_choice_first_qnames__ = {first_qnames!r}\n')
            if not fields:
                # Empty variants still carry their own distinct, nominal type.
                lines.append('    pass\n')
            xml_members = [(index, child) for index, child in enumerate(node.structure.children)
                           if isinstance(child, (Element, ListNode)) and child.xml_wire is not None
                       and (not self.common_projection or self.source_representations)]
            if xml_members:
                lines.insert(1, 'from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object_field '
                             'import AIaXmlDataObjectField\n'
                             'from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind '
                             'import AInXmlValueKind\n')
                lines.append('    __xml_data_object_fields__ = {\n')
                for position, child in xml_members:
                    wire = child.xml_wire
                    lines.append(f'        {child.name!r}: AIaXmlDataObjectField('
                                 f'namespace={wire.namespace_uri!r}, '
                                 f'namespace_local_name={wire.local_name!r}, '
                                 f'value_kind=AInXmlValueKind.{wire.value_kind}, '
                                 '),\n')
                lines.append('    }\n\n')
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
                member = next((child for child in node.structure.children
                               if getattr(child, 'name', None) == original), None)
                constraint_value = member.structure if isinstance(member, Element) else member
                lines.append('\n')
                lines.extend(self._constraint_decorators(constraint_value, types, 'python'))
                lines.append(f'    def {getter}(self) -> {annotation}:\n'
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
                    f'    """{_py_doc(node.description or "Schema enum")}\n\n'
                    f'    Canonical identity: {_py_doc(node.identity)}; '
                    f'version: {self._schema_version_number(node)}."""\n\n']
            seen = set()
            used_identifiers = set()
            for index, val in enumerate(node.structure.values):
                literal = _enum_literal(val.wire_value, kind, 'python')
                if val.wire_value in seen:
                    raise ValueError(f'Duplicate enum wire code in {node.identity}: {val.wire_value!r}')
                seen.add(val.wire_value)
                role = 'string_enum_item' if kind is ScalarKind.STRING else 'non_string_enum_item'
                member = _identifier(self.naming.method_name(role, val.wire_value), 'python')
                if member in used_identifiers:
                    raise ValueError(f'Enum name collision {member!r} at {node.identity}')
                used_identifiers.add(member)
                body.append(f'    {member} = {literal}\n')
            body.extend((f'\n    def code(self) -> {code_type}:\n',
                         '        """Return the exact typed wire code."""\n',
                         '        return self.value\n'))
            return header + ''.join(body)
        if isinstance(node.structure, ListNode):
            item_type = self._typed(node.structure.item, 'python', types, node.identity + '/items')
            parent_imports = []
            for parent in node.inherited_from_types:
                if parent in self.external_parents:
                    spec = self.external_parents[parent]
                    parent_imports.append(f"from {spec['python_module']} import {spec['python_type']}\n")
                else:
                    symbol = self.output_names[parent]
                    parent_imports.append(f'from .{symbol.python_module} import {symbol.python_type}\n')
            for identity, symbol in self.output_names.items():
                if identity != node.identity and identity not in node.inherited_from_types and \
                        re.search(r'\b' + re.escape(symbol.python_type) + r'\b', item_type):
                    parent_imports.append(f'from .{symbol.python_module} import {symbol.python_type}\n')
            parents = ([self.output_names[x].python_type if x in self.output_names
                        else self.external_parents[x]['python_type']
                        for x in node.inherited_from_types]
                       or ['AIiDataObject'])
            if self.common_projection:
                parents = ['AIiDataObject']
            elif self.common_output_names:
                if parents == ['AIiDataObject']:
                    parents = []
                parents.insert(0, self.common_output_names[node.identity].python_type)
                common = self.common_output_names[node.identity]
                parent_imports.append(f'from .{common.python_module} import {common.python_type}\n')
            parents.append('AIiMultiMappedList[' + item_type + ']')
            return (header + 'from abc import ABC\n'
                    + 'from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject\n'
                    + 'from eu.algites.lib.common.list.aii_multi_mapped_list import AIiMultiMappedList\n'
                    + 'from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject\n'
                    + ('from eu.algites.lib.data.dataobject.jsonschema.aia_data_object_json_schema import AIaDataObjectJsonSchema\n' if not self.common_projection else '')
                    + ''.join(f'from eu.algites.lib.data.dataobject.{fmt}defs.aia_{fmt}_data_object '
                        f'import AIa{fmt.title()}DataObject\n' for kind, fmt in
                        ((SourceKind.JSONDEFS, 'json'), (SourceKind.YAMLDEFS, 'yaml'))
                        if kind in node.source_bindings and not self.common_projection)
                    + ''.join(dict.fromkeys(parent_imports)) + '\n\n'
                    + f'class {name}({", ".join(parents)}, ABC):\n'
                    + f'    """{_py_doc(node.description or "Named schema collection")}"""\n'
                    + (f'    __data_object__ = AIcdDataObject(description={node.description or node.name!r})\n'
                       if self.common_projection or not self.common_output_names else '')
                    + ''.join(
                        f'    __{fmt}_data_object__ = AIa{fmt.title()}DataObject('
                        f'schema_id={node.identity!r}, schema_version={self._schema_version_number(node)}'
                        + (f', schema_url={url!r}' if (url := self._published_schema_url(node, kind)) else '')
                        + ')\n'
                        for kind, fmt in ((SourceKind.JSONDEFS, 'json'), (SourceKind.YAMLDEFS, 'yaml'))
                        if kind in node.source_bindings and not self.common_projection)
                    + ''.join(
                        f'    __json_schema__ = AIaDataObjectJsonSchema('
                        f'schema_id={node.identity!r}, schema_version={self._schema_version_number(node)}'
                        + (f', schema_url={url!r}' if (url := self._published_schema_url(node, kind)) else '')
                        + ')\n'
                        for kind in (SourceKind.JSONDEFS, SourceKind.YAMLDEFS)
                        if kind in node.source_bindings and not self.common_projection)
                    + '    __slots__ = ()\n')
        fields = self._fields(node, types, 'python')
        parent_imports = []
        for parent in node.inherited_from_types:
            if parent in self.external_parents:
                specification = self.external_parents[parent]
                parent_imports.append(f"from {specification['python_module']} import {specification['python_type']}\n")
            else:
                symbols = self.output_names[parent]
                parent_imports.append(f'from .{symbols.python_module} import {symbols.python_type}\n')
        technology = self._data_object_technology(node)
        marker_name = 'AIi' + technology.title() + 'DataObject' if technology else 'AIiDataObject'
        marker_module = (f'{technology}defs.aii_{technology}_data_object'
                         if technology else 'aii_data_object')
        parent_names = [self.output_names[x].python_type if x in self.output_names
                        else self.external_parents[x]['python_type']
                        for x in node.inherited_from_types]
        if self.common_projection:
            parent_names = parent_names or ['AIiDataObject']
        elif self.common_output_names:
            parent_names.insert(0, self.common_output_names[node.identity].python_type)
            parent_imports.append(
                f'from .{self.common_output_names[node.identity].python_module} import ' +
                self.common_output_names[node.identity].python_type + '\n')
        if not self.common_projection and marker_name not in parent_names:
            parent_names.append(marker_name)
        parent_list = ', '.join(parent_names)
        header += ('from abc import ABC, abstractmethod\nfrom typing import TYPE_CHECKING\n'
                   'from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject\n'
                   'from eu.algites.lib.data.dataobject.aia_data_object_field import AIaDataObjectField\n'
                   'from eu.algites.lib.data.dataobject.ain_field_presence_kind import AInFieldPresenceKind\n'
                   'from eu.algites.lib.data.dataobject.aia_data_object_field_default import AIaDataObjectFieldDefault\n'
                   'from eu.algites.lib.data.dataobject.ain_data_object_field_default_kind import AInDataObjectFieldDefaultKind\n')
        if self.common_projection or not node.inherited_from_types or self.common_output_names:
            header += ('from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject\n'
                       if self.common_projection else
                       f'from eu.algites.lib.data.dataobject.{marker_module} import {marker_name}\n')
        for kind, fmt in ((SourceKind.JSONDEFS, 'json'), (SourceKind.YAMLDEFS, 'yaml')):
            if kind in node.source_bindings:
                header += (f'from eu.algites.lib.data.dataobject.{fmt}defs.'
                           f'aia_{fmt}_data_object import AIa{fmt.title()}DataObject\n')
        if (not self.common_projection or self.source_representations) and any(
                kind in node.source_bindings for kind in (SourceKind.JSONDEFS, SourceKind.YAMLDEFS)):
            header += ('from eu.algites.lib.data.dataobject.jsonschema.aia_data_object_json_schema '
                       'import AIaDataObjectJsonSchema\n')
        indexed_fields = [(child.name, _indexed_paths(child, types)) for child in node.structure.children
                          if isinstance(child, ListNode) and child.key_definitions]
        if (indexed_fields or any(identity == node.identity for identity, _ in self._scoped_index_targets)
                or any('AIiMultiMappedList[' in value_type for _, _, _, value_type, _, _, _ in fields)):
            header += 'from eu.algites.lib.common.list.aii_multi_mapped_list import AIiMultiMappedList\n'
        xml_members = [(position, child) for position, child in enumerate(node.structure.children)
                       if isinstance(child, (Element, ListNode)) and child.xml_wire is not None
                       and (not self.common_projection or self.source_representations)]
        if xml_members:
            header += ('from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object_field '
                       'import AIaXmlDataObjectField\n'
                       'from eu.algites.lib.data.dataobject.xmlschema.aia_data_object_field_xml_schema '
                       'import AIaDataObjectFieldXmlSchema\n'
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
                (f'    __data_object__ = AIcdDataObject(description={node.description or node.name!r})\n'
                 if self.common_projection or not self.common_output_names else '')
                + ''.join(
                    f'    __{fmt}_data_object__ = AIa{fmt.title()}DataObject('
                    f'schema_id={self._representation(node, kind).identity!r}, schema_version={self._schema_version_number(node)}'
                    + (f', schema_url={url!r}' if (url := self._published_schema_url(self._representation(node, kind), kind)) else '')
                    + ')\n'
                    for kind, fmt in ((SourceKind.JSONDEFS, 'json'), (SourceKind.YAMLDEFS, 'yaml'))
                    if kind in node.source_bindings and (not self.common_projection or self.source_representations))
                + ''.join(
                    f'    __json_schema__ = AIaDataObjectJsonSchema('
                    f'schema_id={self._representation(node, kind).identity!r}, schema_version={self._schema_version_number(node)}'
                    + (f', schema_url={url!r}' if (url := self._published_schema_url(self._representation(node, kind), kind)) else '')
                    + ')\n'
                    for kind in (SourceKind.JSONDEFS, SourceKind.YAMLDEFS)
                    if kind in node.source_bindings
                    and (kind != SourceKind.YAMLDEFS or SourceKind.JSONDEFS not in node.source_bindings)
                    and (not self.common_projection or self.source_representations)) + '\n']
        if SourceKind.XMLDEFS in node.source_bindings and (not self.common_projection or self.source_representations):
            match = re.fullmatch(r'\{([^}]*)\}([^/]+)',
                                 self._representation(node, SourceKind.XMLDEFS).identity)
            if match:
                rows.insert(1, 'from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object '
                            'import AIaXmlDataObject\n'
                            'from eu.algites.lib.data.dataobject.xmlschema.aia_data_object_xml_schema '
                            'import AIaDataObjectXmlSchema\n'
                            'from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind '
                            'import AInXmlObjectDefinitionKind\n')
                rows.append('    __xml_data_object__ = AIaXmlDataObject('
                            'definition_kind=AInXmlObjectDefinitionKind.TYPE, '
                            f'namespace={match.group(1)!r}, '
                            f'namespace_local_name={match.group(2)!r})\n\n')
                rows.append('    __xml_schema__ = AIaDataObjectXmlSchema('
                            'definition_kind=AInXmlObjectDefinitionKind.TYPE, '
                            f'namespace={match.group(1)!r}, '
                            f'namespace_local_name={match.group(2)!r})\n\n')
        enum_imports = self._xml_enum_imports(node, types) if (
            not self.common_projection or self.source_representations) else {}
        if enum_imports:
            rows.append(f'    __xml_scalar_type_imports__ = {enum_imports!r}\n\n')
        if SourceKind.XMLDEFS in node.source_bindings and (
                not self.common_projection or self.source_representations):
            # Logical embedded getters have no XML name. Supply their nominal
            # read-only target identity without assuming any SDO naming profile
            # or importing a generated implementation at module import time.
            embedded_read_types = {}
            for child in node.structure.children:
                if (isinstance(child, Element) and child.element_kind is ElementKind.EMBEDDED
                        and isinstance(child.structure, TypeNode)):
                    target_identity = child.structure.target_identity or child.structure.identity
                    symbols = self.output_names.get(target_identity)
                    if symbols is not None:
                        embedded_read_types[child.name] = (self.package_name + '.'
                            + symbols.python_module + ':' + symbols.python_type)
            if embedded_read_types:
                rows.append(f'    __xml_embedded_read_types__ = {embedded_read_types!r}\n\n')
        if xml_members:
            rows.append('    __xml_data_object_fields__ = {\n')
            for position, child in xml_members:
                wire = child.xml_wire
                rows.append(f'        {child.name!r}: AIaXmlDataObjectField('
                            f'namespace={wire.namespace_uri!r}, '
                            f'namespace_local_name={wire.local_name!r}, '
                            f'value_kind=AInXmlValueKind.{wire.value_kind}, '
                            '),\n')
            rows.append('    }\n\n')
            rows.append('    __xml_schema_fields__ = {\n')
            for position, child in xml_members:
                wire = child.xml_wire
                rows.append(f'        {child.name!r}: AIaDataObjectFieldXmlSchema('
                            f'namespace={wire.namespace_uri!r}, '
                            f'namespace_local_name={wire.local_name!r}, '
                            f'value_kind=AInXmlValueKind.{wire.value_kind}),\n')
            rows.append('    }\n\n')
        # Python's XML SDO parser cannot infer repeated fields from the
        # AIiMultiMappedList generic alone. Preserve direct XSD LIST members
        # in the generated read contract so the runtime can materialize each
        # collection (including empty and indexed collections) correctly.
        # JSONDEFS/YAMLDEFS contracts must not gain XML-specific metadata.
        if SourceKind.XMLDEFS in node.source_bindings and (
                not self.common_projection or self.source_representations):
            xml_repeated = tuple(child.name for child in node.structure.children
                                 if isinstance(child, ListNode))
            if xml_repeated:
                rows.append(f'    __xml_repeated_fields__ = {xml_repeated!r}\n\n')
        const_container, key_constants = self._key_constants(node, types, 'python')
        if key_constants:
            rows.append(f'    class {const_container}:\n'
                        '        """Stable key IDs and field names for this DataObject."""\n')
            emitted_constants = set()
            for (member_name, key_name), const_name in key_constants.items():
                if const_name in emitted_constants:
                    continue
                emitted_constants.add(const_name)
                rows.append(f'        {const_name} = {key_name!r}\n')
            rows.append('\n')
        if indexed_fields:
            rows.append('    __key_definitions__ = {\n')
            for member_name, key_rows in indexed_fields:
                # Keep Python index metadata in sync with Java annotations:
                # reference the generated CONST symbols rather than embedding
                # a second independent copy of the key-field names.
                def field_tuple(paths):
                    fields = ', '.join(const_container + '.' + key_constants[('__field__', path)]
                                       for path in paths)
                    return '(' + fields + (',' if len(paths) == 1 else '') + ')'
                literal_rows = ', '.join(
                    '(' + const_container + '.' + key_constants[(member_name, key_name)]
                    + ', ' + field_tuple(paths) + ', ' + repr(required_key) + ')'
                    for key_name, paths, required_key in key_rows)
                rows.append(f'        {member_name!r}: ({literal_rows},),\n')
            rows.append('    }\n\n')
        for category in ('String', 'Numeric', 'List', 'Object'):
            module = 'aia_data_object_field_' + category.lower() + '_constraints'
            symbol = 'AIaDataObjectField' + category + 'Constraints'
            # Imports are harmless for schemas without facets and keep decorators
            # independent from user-chosen method names.
            rows.insert(1, f'from eu.algites.lib.data.dataobject.{module} import {symbol}\n')
        scoped_fields = [(child.name, _scoped_index_paths(child, types))
                         for child in node.structure.children
                         if isinstance(child, Element) and child.key_definitions]
        if scoped_fields:
            rows.append('    __scoped_key_definitions__ = {\n')
            for member_name, entries in scoped_fields:
                rows.append(f'        {member_name!r}: (\n')
                for selector, key_id, paths, required in entries:
                    path_literals = repr(tuple(paths))
                    rows.append(f'            ({selector!r}, {key_id!r}, {path_literals}, {required!r}),\n')
                rows.append('        ),\n')
            rows.append('    }\n\n')
        if not fields:
            rows.append('    pass\n')
        for original, getter, setter, typ, minimum, maximum, description in fields:
            metadata = next((child for child in node.structure.children
                             if isinstance(child, Element) and child.name == original), None)
            binding_kinds = ({binding.representation_kind
                              for bindings in metadata.source_bindings.values() for binding in bindings}
                             if metadata is not None else set())
            if {'synthetic_map_key', 'synthetic_map_value'} & binding_kinds:
                virtual_role = 'key' if 'synthetic_map_key' in binding_kinds else 'value'
                rows.extend(('    @abstractmethod\n', f'    def {getter}(self) -> {typ}:\n',
                             f'        """Return the virtual indexed-map entry {virtual_role}."""\n',
                             '        raise NotImplementedError\n\n'))
                continue
            required = 'required' if minimum else 'optional'
            doc = _py_doc(description or f'Canonical field {original}.')
            runtime_type = (typ if typ in ('str', 'int', 'float', 'bool') else
                            'AIiMultiMappedList' if typ.startswith('AIiMultiMappedList[') else
                            'list' if typ.startswith('list[') else
                            'dict' if typ.startswith('dict[') else None)
            metadata = next((child for child in node.structure.children
                             if isinstance(child, Element) and child.name == original), None)
            default_expression = ''
            if metadata is not None and metadata.default_kind:
                default_expression = (', default_value=AIaDataObjectFieldDefault('
                    'kind=AInDataObjectFieldDefaultKind.' + metadata.default_kind
                    + ', defined=True, value=' + repr(metadata.default_value) + ')')
            field_order = next((i for i, child in enumerate(node.structure.children)
                                if getattr(child, 'name', None) == original), -1)
            field_member = next((child for child in node.structure.children
                                 if isinstance(child, (Element, ListNode)) and child.name == original), None)
            field_value = field_member.structure if isinstance(field_member, Element) else field_member
            count_min, count_max = ((field_value.min_item_count, field_value.max_item_count)
                                    if isinstance(field_value, ListNode) else (minimum, maximum))
            if self.common_projection or not self.common_output_names:
                rows.extend(self._constraint_decorators(field_value, types, 'python'))
            embedded = bool(metadata and metadata.element_kind is ElementKind.EMBEDDED)
            if self.common_projection or not self.common_output_names:
                rows.append(f'    @AIaDataObjectField('
                         + ('embedded=True, ' if embedded else f'dataFieldName={original!r}, ')
                         + f'presence=AInFieldPresenceKind.{"REQUIRED" if minimum else "ALLOWED"}, '
                         'allows_null=False'
                         + (f', expected_type={runtime_type}' if runtime_type else '')
                         + f', order={field_order}, min_item_count={count_min}, max_item_count={count_max}'
                         + f', is_empty_allowed={bool(metadata and metadata.is_empty_allowed)!r}'
                         + default_expression + ')\n')
            rows.extend(('    @abstractmethod\n', f'    def {getter}(self) -> {typ}:\n',
                         f'        """Return {doc} ({required}, cardinality {minimum}..{maximum})."""\n',
                         '        raise NotImplementedError\n\n'))
        return ''.join(rows)
