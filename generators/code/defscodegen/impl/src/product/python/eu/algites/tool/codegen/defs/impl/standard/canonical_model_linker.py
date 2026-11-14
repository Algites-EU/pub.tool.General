"""Resolve canonical TYPE links and validate the complete graph before normalizing.

The canonical contract is a finite tree of definitions with symbolic TYPE edges.
A resolved edge carries ``target_identity`` instead of recursively copying a
referenced declaration. This makes self-recursion and mutual recursion safe and
is equal in meaning to the Java canonical linker.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import replace
from typing import Any
from urllib.parse import urljoin

from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIcgdType_1 as TypeNode,
    AIcgdElement_1 as Element, AIcgdElementList_1 as ElementList,
    AIcgdList_1 as ListNode, AIcgdMap_1 as MapNode,
    AIngResolutionState_1 as State, normalize_structure,
)
from eu.algites.tool.codegen.defs.impl.standard.canonical_contract_payload import (
    AIcDefsCodegenCanonicalContractPayload,
)


class AIcDefsCodegenCanonicalModelLinker:
    """Links local or registered external schema refs while collecting diagnostics."""

    @staticmethod
    def link(types: Iterable[TypeNode], *, schema: Mapping[str, Any] | None = None,
             external_parents: Iterable[str] = (),
             document_uris: Mapping[str, str] | None = None
             ) -> tuple[TypeNode, ...]:
        """Resolve references, validate all outputs, then normalize, in that order.

        Args:
            types: All named definitions collected from the selected source inputs.
            schema: Optional generated canonical-model JSON Schema contract to
                validate prior to normalization, including closed choices and maps.
            external_parents: Verified external base-type identities.
            document_uris: Declared `$id` URL for each input source resource;
                permits qualified local or cross-document `$ref` while preserving
                the logical `x-algites-schema-id` as canonical TYPE identity.

        Returns:
            Finalized roots; any recursive usage is a resolved symbolic TYPE edge.

        Raises:
            ValueError: Missing/ambiguous declarations, unresolved references,
                invalid shapes, or contract incompatibility. Diagnostics include
                exact schema source locations where available.
        """
        candidates = tuple(types)
        external = frozenset(external_parents)
        uris = document_uris or {}
        declarations: dict[str, TypeNode] = {}
        aliases: dict[str, set[str]] = {}
        problems: list[str] = []
        for root in candidates:
            if not isinstance(root, TypeNode) or root.resolution_state is not State.RESOLVED \
                    or root.structure is None or root.target_identity:
                problems.append(f'Invalid top-level TYPE declaration: {root!r}')
                continue
            if root.identity in declarations:
                problems.append(f'Duplicate canonical TYPE declaration: {root.identity}')
                continue
            declarations[root.identity] = root
            aliases.setdefault(root.identity, set()).add(root.identity)
            aliases.setdefault(root.name, set()).add(root.identity)
            for values in root.source_bindings.values():
                for b in values:
                    aliases.setdefault(b.source_resource + '::' + root.name, set()).add(root.identity)
                    if b.source_pointer.startswith('#'):
                        aliases.setdefault(b.source_resource + b.source_pointer, set()).add(root.identity)
                        declared_uri = uris.get(b.source_resource)
                        if declared_uri:
                            # `#` is the root, not a separate URI fragment.
                            qualified = declared_uri.rstrip('#') + (
                                '' if b.source_pointer == '#' else b.source_pointer)
                            aliases.setdefault(qualified, set()).add(root.identity)
                        if b.source_pointer == '#':
                            aliases.setdefault(b.source_resource, set()).add(root.identity)
        if problems:
            raise ValueError('Canonical model declaration errors:\n' + '\n'.join(problems))

        def find_target(identity: str, bindings) -> str | None:
            """Prefer a local declaration, then a qualified URI, then an unqualified name."""
            location = next((f'{b.source_resource}{b.source_pointer}'
                             for values in bindings.values() for b in values), '(no location)')
            resource = next((b.source_resource for values in bindings.values()
                             for b in values), '')
            names: list[str] = []
            if identity.startswith('#') and resource:
                names.append(resource + identity)
            elif resource:
                names.extend((resource + '::' + identity, urljoin(resource, identity)))
            names.append(identity)
            for name in names:
                matches = aliases.get(name)
                if matches:
                    if len(matches) > 1:
                        problems.append(f'{location}: ambiguous reference {identity!r}: '
                                        + ', '.join(sorted(matches)))
                        return None
                    return next(iter(matches))
            if identity in external:
                return identity
            problems.append(f'{location}: unresolved reference {identity!r}; '
                            'supply its declared TYPE or a supported local schema dependency')
            return None

        def resolve(ref: TypeNode) -> TypeNode:
            identity = find_target(ref.identity, ref.source_bindings)
            if identity is None:
                return ref
            if identity in external:
                problems.append(f'External type {identity!r} is only supported as an inherited parent, not as a field reference')
                return ref
            target = declarations[identity]
            return replace(ref, identity=target.identity, name=target.name,
                           origin=target.origin, inherited_from_types=(),
                           schema_version=target.schema_version, description=target.description,
                           structure=None, resolution_state=State.RESOLVED,
                           target_identity=target.identity)

        def visit(node):
            if isinstance(node, TypeNode):
                if node.resolution_state is State.REFERENCE:
                    return resolve(node)
                if node.resolution_state is State.UNDEFINED:
                    problems.append(f'Undefined canonical TYPE: {node.identity}')
                    return node
                if node.target_identity:
                    if node.target_identity not in declarations:
                        problems.append(f'Unknown linked TYPE: {node.target_identity}')
                    return node
                inherited = tuple(find_target(base, node.source_bindings) or base
                                  for base in node.inherited_from_types)
                return replace(node, inherited_from_types=inherited,
                               structure=visit(node.structure))
            if isinstance(node, ElementList):
                return replace(node, children=tuple(visit(child) for child in node.children))
            if isinstance(node, Element):
                return replace(node, structure=visit(node.structure))
            if isinstance(node, ListNode):
                return replace(node, item=visit(node.item))
            if isinstance(node, MapNode):
                return replace(node, key_type=visit(node.key_type),
                               value_type=visit(node.value_type))
            return node

        linked = tuple(visit(node) for node in candidates)
        def check_inheritance(identity: str, chain: list[str], complete: set[str]):
            if identity in complete:
                return
            if identity in chain:
                problems.append('Cyclic TYPE inheritance: ' + ' -> '.join(chain + [identity]))
                return
            node = declarations.get(identity)
            if node is not None:
                chain.append(identity)
                linked_node = next(item for item in linked if item.identity == identity)
                for parent in linked_node.inherited_from_types:
                    check_inheritance(parent, chain, complete)
                chain.pop()
            complete.add(identity)

        completed: set[str] = set()
        for root in linked:
            check_inheritance(root.identity, [], completed)
        if problems:
            raise ValueError('Canonical model reference resolution failed:\n' + '\n'.join(problems))
        # A generated interface contract describes the graph *before* normalization.
        if schema is not None:
            try:
                from jsonschema import Draft202012Validator
            except ImportError as error:
                raise RuntimeError(
                    'Defs Codegen requires the Python runtime dependency '
                    'jsonschema>=4.18,<5.0 for canonical model validation. '
                    'Install it into the bootstrap Python environment '
                    '(e.g. python3 -m pip install "jsonschema>=4.18,<5.0"), '
                    'then rerun the bootstrap; validation must not be skipped.'
                ) from error
            errors = sorted(Draft202012Validator(schema).iter_errors(
                AIcDefsCodegenCanonicalContractPayload.emit(linked)), key=lambda e: str(e.path))
            if errors:
                raise ValueError('Canonical model validation failed:\n' + '\n'.join(
                    f'{error.json_path}: {error.message}' for error in errors))
        return tuple(normalize_structure(node) for node in linked)
