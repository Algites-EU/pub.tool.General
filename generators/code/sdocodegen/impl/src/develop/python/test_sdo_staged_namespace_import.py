"""Fresh Defs contracts must be importable by the independent SDO generator."""
from __future__ import annotations

import sys
from pathlib import Path

from eu.algites.tool.codegen.sdo.impl.standard.aic_sdo_codegen_service import (
    AIcSdoCodegenService,
)


def test_transient_staged_contract_precedes_cached_pkgutil_package(tmp_path, monkeypatch):
    """A cached Algites namespace must not redirect source imports to old *.gen."""
    import eu.algites.tool.codegen.defs as defs_namespace

    relative = Path('eu/algites/tool/codegen/defs/aiig_staged_source_probe.py')
    source = tmp_path / relative
    source.parent.mkdir(parents=True)
    source.write_text('from eu.algites.lib.data.dataobject.aii_data_object import AIiDataObject\n'
                      'from eu.algites.lib.data.dataobject.aicd_data_object import AIcdDataObject\n'
                      'class AIigStagedSourceProbe(AIiDataObject):\n'
                      '    __data_object__ = AIcdDataObject()\n', encoding='utf-8')
    before = defs_namespace.__path__
    assert str(source.parent) not in before
    marker = object()
    service = AIcSdoCodegenService()
    monkeypatch.setattr(service, 'generate', lambda contract, *args, **kwargs: marker)
    try:
        actual = service.generate_from_sources(
            tmp_path, {relative: 'AIigStagedSourceProbe'})
        assert actual == {source: marker}
        assert defs_namespace.__path__ is before
    finally:
        sys.modules.pop('eu.algites.tool.codegen.defs.aiig_staged_source_probe', None)
