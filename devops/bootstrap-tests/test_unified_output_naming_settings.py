"""All codegen profile settings use only format-independent output type names."""
from pathlib import Path
import yaml
import pytest

TOOL_ROOT = Path(__file__).resolve().parents[2]
LIB_ROOT = TOOL_ROOT.parent / 'pub.lib.General'
FAMILIES = {'algites': 'algites', 'standardprefix': 'standard-prefix',
            'standardpostfix': 'standard-postfix'}


@pytest.mark.parametrize('family,prefix', FAMILIES.items())
@pytest.mark.parametrize('language', ('java', 'python'))
def test_both_generators_reference_the_same_defined_read_interface(family, prefix, language):
    """Defs' output naming is the same as SDO's input contract naming."""
    library = (LIB_ROOT / 'naming/convention/profile' / family
               / 'src/product/config/eu/algites/lib/naming/convention/sourcecode'
               / f'{prefix}-{language}-name-conventions.yml')
    declarations = yaml.safe_load(library.read_text())
    names = {item['name'] for item in declarations[
        'SourceStructureNameConventions']['NameConventions']['NameConvention']}

    settings = {}
    for generator, artifact in (('defs', 'defscodegen'), ('sdo', 'sdocodegen')):
        path = (TOOL_ROOT / 'generators/code/profile' / family
                / f'src/product/config/eu/algites/tool/codegen/{generator}'
                / f'{artifact}-{language}.settings')
        setting = {}
        for line in path.read_text().splitlines():
            if line.startswith('--') and '=' in line:
                key, value = line[2:].split('=', 1)
                setting[key] = value
        settings[generator] = setting

    do_option = f'dointf-naming-convention:{language}'
    sdo_options = (f'sdointf-naming-convention:{language}',
                   f'sdoimpl-naming-convention:{language}')
    assert settings['defs'][do_option] == settings['sdo'][do_option]
    for generator, values in settings.items():
        options = (do_option,) if generator == 'defs' else (do_option,) + sdo_options
        for option in options:
            assert values[option] in names, (family, language, generator, option)
            assert not any(token in values[option] for token in ('-xml-', '-json-', '-yaml-'))
    assert len({settings['sdo'][name] for name in (do_option,) + sdo_options}) == 3
