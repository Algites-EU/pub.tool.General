"""Native Defs parsing errors identify the original source in a multi-file batch."""

import pytest

from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIngSourceInputKind_1 as Kind,
)
from eu.algites.tool.codegen.defs.impl.standard.canonical_pipeline import (
    AIcdDefsCodegenSourceDocument as Document,
)
from test_canonical_source_emitter import _pipeline


@pytest.mark.parametrize('kind,resource', [
    (Kind.JSONDEFS, 'schemas/broken.jsondef.schema.json'),
    (Kind.YAMLDEFS, 'schemas/broken.yamldef.schema.json'),
])
def test_invalid_named_definitions_include_source_resource(kind, resource):
    """Keep the actual input resource and the original parser message together."""
    with pytest.raises(ValueError) as error:
        _pipeline().process((Document(kind, resource, {'$defs': ['not', 'a', 'map']}),))
    assert resource in str(error.value)
    assert '$defs' in str(error.value) or 'definitions' in str(error.value)


def test_invalid_choice_in_validation_branch_identifies_source_and_pointer():
    """A JSON Pointer is useful only together with its source document path."""
    resource = 'schemas/invalid-choice.jsondef.schema.json'
    source = {'type': 'object', 'properties': {
        'example': {'oneOf': [{'x-algites-defscodegen-choice': 'CHOICE'}]}}}
    with pytest.raises(ValueError) as error:
        _pipeline().process((Document(Kind.JSONDEFS, resource, source),))
    assert resource in str(error.value)
    assert '#/properties/example/oneOf/0' in str(error.value)


def test_conflicting_canonical_sources_report_both_origin_documents():
    """Reconciliation errors include both files and source pointers."""
    from eu.algites.tool.codegen.defs.impl.standard.canonical_model_merger import (
        AIcDefsCodegenCanonicalModelMerger as Merger,
    )
    from eu.algites.tool.codegen.defs.impl.standard.canonical_schema_frontend import (
        AIcDefsCodegenCanonicalSchemaFrontend,
    )
    from test_canonical_source_emitter import _profile

    frontend = AIcDefsCodegenCanonicalSchemaFrontend(_profile())
    first = frontend.load_json_or_yaml(
        {'$id': 'urn:example', 'type': 'string'}, 'a.json', Kind.JSONDEFS)
    second = frontend.load_json_or_yaml(
        {'$id': 'urn:example', 'type': 'integer'}, 'b.yaml', Kind.YAMLDEFS)
    with pytest.raises(ValueError) as error:
        Merger.merge((first, second))
    assert 'a.json#' in str(error.value)
    assert 'b.yaml#' in str(error.value)


def test_optional_xml_wildcard_warning_reports_original_resource():
    """An intentionally ignored optional XML node still needs an actionable location."""
    from eu.algites.tool.codegen.defs.impl.standard.canonical_schema_frontend import (
        AIcDefsCodegenCanonicalSchemaFrontend,
    )
    from test_canonical_source_emitter import _profile

    xml = ('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
           '<xs:complexType name="Doc"><xs:sequence>'
           '<xs:any minOccurs="0" processContents="lax"/>'
           '</xs:sequence></xs:complexType></xs:schema>')
    resource = 'schemas/optional-any.xsd'
    with pytest.warns(UserWarning) as caught:
        AIcDefsCodegenCanonicalSchemaFrontend(_profile()).load_xsd(xml, resource)
    assert any(resource in str(item.message) and '/schema/Doc/' in str(item.message)
               and 'Hint:' in str(item.message) for item in caught)
