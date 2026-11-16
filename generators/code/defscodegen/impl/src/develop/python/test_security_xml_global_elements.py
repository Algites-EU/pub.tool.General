"""Security production XSDs must support global-element identity constraints."""
from pathlib import Path

import pytest

from eu.algites.tool.codegen.defs.impl.standard.canonical_generated_model import (
    AIcgdList_1 as ListNode,
    AIngSourceInputKind_1 as Kind,
)
from eu.algites.tool.codegen.defs.impl.standard.canonical_pipeline import (
    AIcdDefsCodegenSourceDocument as Document,
)
from test_canonical_source_emitter import _pipeline

SECURITY = next(p for p in Path(__file__).resolve().parents if p.name == 'pub.tool.General').parent / 'pub.lib.Security'
ROOT = SECURITY / 'credentials/core/intf/src/product/xmldefs/eu/algites/lib/security/credentials/core'


@pytest.mark.skipif(not ROOT.is_dir(), reason='pub.lib.Security checkout not present alongside pub.tool.General')
def test_credentials_xsd_roots_and_keys():
    for filename, root_name in (( 'credential-profiles_1.xsd', 'CredentialProfiles'),
                                ('credentials_1.xsd', 'CredentialDocument')):
        doc = Document(Kind.XMLDEFS, filename, (ROOT / filename).read_bytes())
        linked = _pipeline().process((doc,))
        root = next(node for node in linked.types if node.name == root_name)
        assert next(iter(root.source_bindings[Kind.XMLDEFS])).representation_kind == 'xs:element'
        profiles = next(field for field in root.structure.children if field.name == 'Profile')
        assert isinstance(profiles, ListNode)
        assert [(key.identifier, key.fields) for key in profiles.key_definitions] == [
            ('UniqueProfileId', ('@Id',))]
