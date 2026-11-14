"""Regressions for the public contract schemas in every source format."""
import json
from pathlib import Path
from xml.etree import ElementTree as ET


def test_published_public_schema_families_are_symmetric():
    root = Path(__file__).resolve().parents[4] / 'intf/src/product'
    base = Path('eu/algites/tool/codegen/defs')
    for stem in ('input-profile', 'schema-field-bindings'):
        for kind, suffix in (('yamldefs', '.yamldef.schema.json'),
                             ('jsondefs', '.jsondef.schema.json'), ('xmldefs', '.xsd')):
            path = root / kind / base / f'{stem}_1{suffix}'
            assert path.is_file(), f'Missing {kind} definition for {stem}'
            sidecar = path.with_name(path.name + '.meta.yml')
            assert sidecar.is_file()
            assert f'GlobalPublicationPathId: {base.as_posix()}/{path.name}' in sidecar.read_text()
            if kind == 'xmldefs':
                schema = ET.parse(path).getroot()
                assert schema.tag == '{http://www.w3.org/2001/XMLSchema}schema'
                assert schema.attrib['version'] == '1'
            else:
                schema = json.loads(path.read_text())
                assert schema['$schema'] == 'https://json-schema.org/draft/2020-12/schema'
                assert schema['$id'].endswith('/' + kind + '/' + base.as_posix() + '/' + path.name)
                assert schema.get('x-algites-schema-id') == 'eu.algites.tool.codegen.defs.' + stem
                assert schema.get('x-algites-schema-version') == 1
