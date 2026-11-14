"""Ensure profile distributions use the current Common/Defs/SDO split."""
from email.message import EmailMessage
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from zipfile import ZipFile
import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / 'generators/code/bootstrap-python-dist.py'
spec = spec_from_file_location('local_profile_dist', SCRIPT)
assert spec and spec.loader
packaging = module_from_spec(spec)
spec.loader.exec_module(packaging)


@pytest.mark.parametrize('profile', ('algites', 'standardprefix', 'standardpostfix'))
def test_live_catalogs_packaged_not_retired_catalogs(tmp_path, profile):
    name = f'eu-algites-pub-tool-general-generators-code-profile-{profile}'
    version = '1.1.dev202611140001'
    config = REPO / 'generators/code/profile' / profile / 'src/product/config'
    metadata = EmailMessage()
    metadata['Metadata-Version'] = '2.3'
    metadata['Name'] = name
    metadata['Version'] = version
    wheel = tmp_path / 'current.whl'
    with ZipFile(wheel, 'w') as archive:
        archive.writestr(f'{name.replace("-", "_")}-{version}.dist-info/METADATA', metadata.as_string())
        archive.writestr('eu/algites/tool/codegen/sdo/package.py', '"""Test module."""\n')
        for item in config.rglob('*'):
            if item.is_file():
                archive.write(item, item.relative_to(config).as_posix())
    packaging.verify_wheel(wheel, name, 'profile', profile, version)
    with ZipFile(wheel) as archive:
        names = archive.namelist()
    assert not any(file.endswith(('-dataobject-conventions.yml', '-smartdataobject-conventions.yml'))
                   for file in names)
    for language in ('java', 'python'):
        for domain in ('common', 'defs', 'sdo'):
            missing = (f'eu/algites/lib/naming/convention/sourcecode/'
                       f'{profile}-{language}-{domain}-codegen-conventions.yml')
            broken = tmp_path / f'missing-{language}-{domain}.whl'
            with ZipFile(wheel) as source, ZipFile(broken, 'w') as out:
                for info in source.infolist():
                    if info.filename != missing:
                        out.writestr(info, source.read(info.filename))
            with pytest.raises(ValueError, match='Missing .* naming catalog'):
                packaging.verify_wheel(broken, name, 'profile', profile, version)
