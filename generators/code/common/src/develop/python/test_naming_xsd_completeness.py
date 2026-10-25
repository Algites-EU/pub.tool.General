"""Keep native XSD alongside the JSON/YAML generated-method naming definitions."""
from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

import yaml

MODULE = Path(__file__).resolve().parents[3]


def test_xsd_parity_and_publication_metadata():
    xsd_root = MODULE / 'src/product/xmldefs/eu/algites/tool/codegen/common/naming'
    json_root = MODULE / 'src/product/jsondefs/eu/algites/tool/codegen/common/naming'
    yaml_root = MODULE / 'src/product/yamldefs/eu/algites/tool/codegen/common/naming'
    for name in ('generated-dataobject-method-kind_1', 'data-object-naming-conventions_1'):
        xsd = xsd_root / (name + '.xsd')
        assert xsd.is_file()
        assert (json_root / (name + '.jsondef.schema.json')).is_file()
        assert (yaml_root / (name + '.yamldef.schema.json')).is_file()
        metadata = yaml.safe_load((xsd_root / (name + '.xsd.meta.yml')).read_text())
        assert metadata['GlobalPublicationPathId'].endswith(xsd.name)
        assert ET.parse(xsd).getroot().tag.endswith('schema')


def test_xsd_method_roles_and_common_base():
    root = MODULE / 'src/product/xmldefs/eu/algites/tool/codegen/common/naming'
    roles = (root / 'generated-dataobject-method-kind_1.xsd').read_text()
    for role in ('standard_getter_name', 'standard_setter_name', 'raw_getter_name',
                 'raw_presence_checker_method_name', 'raw_unsetter_name'):
        assert role in roles
    profiles = (root / 'data-object-naming-conventions_1.xsd').read_text()
    assert 'GeneratedDataObjectMethodNameConventions' in profiles
    assert 'NameConventions' in profiles
    assert 'common-naming-conventions_1.xsd' in profiles


def test_method_catalogs_contain_declared_schema_identifiers():
    """Both shipped DO/SDO catalogs keep the complete three-line schema header."""
    catalog_root = MODULE / 'src/product/config/eu/algites/lib/naming/convention'
    for technology in ('java', 'python'):
        path = catalog_root / f'algites-{technology}-codegen-method-conventions.yml'
        lines = path.read_text(encoding='utf-8').splitlines()
        uri = lines[0].removeprefix('# yaml-language-server: $schema=')
        assert lines[0] == f'# yaml-language-server: $schema={uri}'
        assert lines[1] == f'# $schema: {uri}'
        assert lines[2] == f'$schema: {uri}'
        assert yaml.safe_load(path.read_text(encoding='utf-8'))['$schema'] == uri
