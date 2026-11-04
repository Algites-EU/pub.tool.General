"""Aggregate DataObject CLI diagnostics without publishing partial SDO output."""
from __future__ import annotations

from pathlib import Path
import pytest

from eu.algites.tool.codegen.common.validation_batch import AIxCodegenBatchValidationException
from eu.algites.tool.codegen.sdo.old.impl.cli.aic_sdo_codegen_cli import main as historical_main
from eu.algites.tool.codegen.sdo.impl.cli.aic_sdo_codegen_cli import main as current_main
from test_handwritten_naming_cli import test_handwritten_contract_uses_annotated_convention_not_filename


@pytest.mark.parametrize('invoke', (historical_main, current_main))
def test_two_invalid_python_input_files_reported_together(tmp_path: Path, invoke):
    """Both independent SDO CLIs gather input errors before touching outputs."""
    test_handwritten_contract_uses_annotated_convention_not_filename(tmp_path)
    generated = tmp_path/'generated'
    baseline = {p.relative_to(generated):p.read_bytes() for p in generated.rglob('*.py')}
    for name in ('first_broken.py','second_broken.py'):
        (tmp_path/'source/exampleinvoice'/name).write_text('class Invalid(:\n',encoding='utf-8')
    with pytest.raises(AIxCodegenBatchValidationException) as failure:
        invoke([f'--settings-file={tmp_path / "custom.settings"}',
                '--codegen-validate-one-input-at-a-time-only=false'])
    assert len(failure.value.errors) == 2
    assert {'first_broken.py','second_broken.py'} == {Path(error.source).name for error in failure.value.errors}
    assert {p.relative_to(generated):p.read_bytes() for p in generated.rglob('*.py')} == baseline


@pytest.mark.parametrize('invoke', (historical_main, current_main))
def test_invalid_boolean_is_rejected_before_generation(tmp_path: Path, invoke):
    """Invalid settings never silently switch the requested validation mode."""
    with pytest.raises(ValueError, match='true or false'):
        invoke(['--codegen-validate-one-input-at-a-time-only=maybe'])
