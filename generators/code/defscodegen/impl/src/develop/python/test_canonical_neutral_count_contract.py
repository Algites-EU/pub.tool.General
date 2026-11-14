"""Regressions for technology-neutral canonical multiplicity vocabulary."""

import json
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[4] / 'intf/src/product'


def test_canonical_count_contract_in_all_schema_formats():
    """Canonical schema declarations have equal neutral count metadata."""
    for kind, suffix in (('jsondefs', 'jsondef'), ('yamldefs', 'yamldef')):
        source = ROOT / kind / 'eu/algites/tool/codegen/defs/model' / (
            f'canonical-model_1.{suffix}.schema.json')
        definitions = json.loads(source.read_text(encoding='utf-8'))['$defs']
        for name in ('Element', 'ElementList', 'List'):
            fields = definitions[name]['properties']
            assert 'min_item_count' in fields and 'max_item_count' in fields
            assert 'min_occurs' not in fields and 'max_occurs' not in fields
            assert {'min_item_count', 'max_item_count'} <= set(definitions[name]['required'])
    source = ROOT / 'xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd'
    namespace = {'xs': 'http://www.w3.org/2001/XMLSchema'}
    xml = ET.parse(source)
    for name in ('Element', 'ElementList', 'List'):
        declaration = xml.find(f".//xs:complexType[@name='{name}']", namespace)
        assert declaration is not None
        fields = {field.attrib['name'] for field in declaration.findall('xs:sequence/xs:element', namespace)}
        assert {'min_item_count', 'max_item_count'} <= fields
        assert not {'min_occurs', 'max_occurs'} & fields
