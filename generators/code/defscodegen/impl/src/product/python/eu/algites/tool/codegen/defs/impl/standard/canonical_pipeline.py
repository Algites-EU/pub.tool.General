"""Native source-to-validated-canonical-model service for new Defs Codegen.

Input sources retain their technology and resource identity. The pipeline collects
all declarations before cross-source merging and reference resolution, validates
the linked generated schema contract, and only then normalizes structural groups.
The deprecated generator has no runtime dependency on or from this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable, Mapping
from typing import Any

from eu.algites.tool.codegen.common.naming_profiles import AIcdCodegenNamingProfile
from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIngSourceInputKind_1 as SourceKind,
    AIcgdType_1 as TypeNode,
)
from eu.algites.tool.codegen.defs.impl.standard.canonical_schema_frontend import (
    AIcDefsCodegenCanonicalSchemaFrontend,
)
from eu.algites.tool.codegen.defs.impl.standard.canonical_model_merger import (
    AIcDefsCodegenCanonicalModelMerger,
)
from eu.algites.tool.codegen.defs.impl.standard.canonical_model_linker import (
    AIcDefsCodegenCanonicalModelLinker,
)
from eu.algites.tool.codegen.defs.impl.standard.canonical_contract_payload import (
    AIcDefsCodegenCanonicalContractPayload,
)


@dataclass(frozen=True)
class AIcdDefsCodegenSourceDocument:
    """One input document with technology-specific parsed content and source URI.

    JSONDEFS/YAMLDEFS use a parsed object Mapping; XMLDEFS uses the XSD source
    text. The parser fails closed for unsupported node structures and references.
    """
    kind: SourceKind
    resource: str
    content: Mapping[str, Any] | str | bytes
    root_name: str = ""
    source_version: str = ""

    def __post_init__(self) -> None:
        if not self.resource or not isinstance(self.kind, SourceKind):
            raise ValueError('Each source requires a typed input kind and nonempty resource')
        if self.kind is SourceKind.XMLDEFS and not isinstance(self.content, (str, bytes)):
            raise TypeError('XMLDEFS input requires XSD text or bytes')
        if self.kind is not SourceKind.XMLDEFS and not isinstance(self.content, Mapping):
            raise TypeError('JSONDEFS/YAMLDEFS input requires a parsed schema mapping')


@dataclass(frozen=True)
class AIcdDefsCodegenCanonicalPipelineResult:
    """Fully linked and normalized graph and its exact validated generated payload."""
    types: tuple[TypeNode, ...]
    payload: Mapping[str, Any]


class AIcDefsCodegenCanonicalPipeline:
    """Coordinates source frontends, merging, linking, validation, normalization."""

    def __init__(self, naming: AIcdCodegenNamingProfile, schema: Mapping[str, Any],
                 *, external_xsd_types: frozenset[str] = frozenset(),
                 external_xsd_documents: Mapping[str, bytes] | None = None):
        """Require an explicit resolved naming profile and a generated contract schema."""
        if not isinstance(schema, Mapping) or not schema:
            raise ValueError('Canonical contract JSON Schema is mandatory')
        self.frontend = AIcDefsCodegenCanonicalSchemaFrontend(
            naming, external_xsd_types=external_xsd_types,
            external_xsd_documents=external_xsd_documents)
        self.schema = schema

    def process(self, documents: Iterable[AIcdDefsCodegenSourceDocument],
                *, external_parents: Iterable[str] = ()
                ) -> AIcdDefsCodegenCanonicalPipelineResult:
        """Return validated canonical types with stable cross-technology provenance.

        Raises:
            ValueError: Empty inputs, incompatible declarations, missing references
                or invalid generated contract (the first failure is diagnostic).
        """
        source_types: list[TypeNode] = []
        document_uris: dict[str, str] = {}
        for source in documents:
            if not isinstance(source, AIcdDefsCodegenSourceDocument):
                raise TypeError('Every input must be a typed source document')
            try:
                if source.kind is SourceKind.XMLDEFS:
                    source_types.extend(self.frontend.load_xsd(source.content, source.resource, source_version=source.source_version))
                else:
                    declared_uri = source.content.get('$id')
                    if isinstance(declared_uri, str) and declared_uri:
                        document_uris[source.resource] = declared_uri
                    source_types.extend(self.frontend.load_json_or_yaml_types(
                        source.content, source.resource, source.kind,
                        root_name=source.root_name, source_version=source.source_version))
            except (ValueError, TypeError, KeyError, NotImplementedError) as exc:
                # Preserve any JSON Pointer / XML position reported by the frontend.
                # A diagnostic without its input resource is not actionable when a
                # bootstrap batch contains many different schema documents.
                raise ValueError(f'{source.resource}: {exc}') from exc
        if not source_types:
            raise ValueError('No canonical TYPE declarations were found in the supplied sources')
        merged = AIcDefsCodegenCanonicalModelMerger.merge(source_types)
        linked = AIcDefsCodegenCanonicalModelLinker.link(
            merged, schema=self.schema, external_parents=external_parents,
            document_uris=document_uris)
        return AIcdDefsCodegenCanonicalPipelineResult(
            linked, AIcDefsCodegenCanonicalContractPayload.emit(linked))
