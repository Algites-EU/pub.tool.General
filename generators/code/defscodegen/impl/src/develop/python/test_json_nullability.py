"""Regression checks for null/absence semantics in schema-driven Python DTO generation."""
import json
from pathlib import Path
import types

import pytest

from eu.algites.lib.naming.convention.aic_algites_naming_profiles import AIcAlgitesNamingProfiles
from eu.algites.tool.codegen.defs._json_nullability import _accepts_null
from eu.algites.tool.codegen.defs.aic_default_defs_codegen_service import AIcDefaultDefsCodegenService
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.aicd_code_generation_request import AIcdCodeGenerationRequest
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget


@pytest.mark.parametrize("schema,expected", [
    ({}, True), ({"type": "string"}, False), ({"type": ["null", "string"]}, True),
    ({"type": ["null", "string"], "enum": ["x"]}, False),
    ({"enum": ["success", "error", None]}, True),
    ({"enum": ["success", "error"]}, False),
    ({"const": None}, True), ({"const": "x"}, False),
    ({"anyOf": [{"type": "string"}, {"type": "null"}]}, True),
    ({"oneOf": [{"type": "string"}, {"type": "null"}]}, True),
    ({"oneOf": [{}, {}]}, False),
    ({"allOf": [{}, {"type": "string"}]}, False),
    ({"not": {"type": "null"}}, False),
    ({"if": {"type": "null"}, "then": {"type": "string"}}, False),
])
def test_json_null_acceptance(schema, expected):
    assert _accepts_null(schema) is expected


def test_generated_nullable_dto_round_trip(tmp_path: Path):
    doc = {
        "$id": "urn:test:nullable-input:1", "type": "object", "description": "Nullable input",
        "properties": {
            "Outcome": {"enum": ["success", "error", None]},
            "Result": {"description": "Any value including null."},
            "Parent": {"type": ["string", "null"]},
            "Strict": {"type": "string"},
            "Limited": {"type": ["string", "null"], "enum": ["allowed"]},
            "Constant": {"type": "string", "const": "exact"},
        },
        "required": ["Constant"]
    }
    path = tmp_path / "nullable-input_1.jsondef.schema.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    profile = AIcAlgitesNamingProfiles.python_profile()
    service = AIcDefaultDefsCodegenService()
    definition = service.load(AIcdDefinitionLoadRequest(path, AInDefinitionSourceKind.JSONDEFS, profile))
    props = {p.source_name:p for p in definition.properties}
    assert props['Outcome'].nullable
    assert props['Result'].nullable
    assert props['Parent'].nullable
    assert not props['Strict'].nullable
    assert not props['Limited'].nullable
    assert props['Outcome'].constraints.enum_values == ('success', 'error')
    assert props['Constant'].constraints.enum_values == ('exact',)
    generated = service.generate(AIcdCodeGenerationRequest(definition, AInCodeGenerationTarget.PYTHON, 'test.generated', profile))
    module = types.ModuleType('test_nullable_generated')
    module.__dict__['__name__'] = 'test_nullable_generated'
    import sys
    sys.modules[module.__name__] = module
    try:
        exec(generated.source, module.__dict__)
        cls = getattr(module, generated.type_name)
        obj = cls.from_mapping({'Outcome': None, 'Result': None, 'Parent': None, 'Constant': 'exact'})
        assert obj.to_mapping() == {'Outcome': None, 'Result': None, 'Parent': None, 'Constant': 'exact'}
        assert cls.from_mapping(obj.to_mapping()) == obj
        assert cls.from_mapping({'Constant': 'exact'}).to_mapping() == {'Constant': 'exact'}
        with pytest.raises(ValueError, match='null is not permitted'):
            cls.from_mapping({'Constant': 'exact', 'Limited': None})
        with pytest.raises(ValueError, match='null is not permitted'):
            cls.from_mapping({'Constant': 'exact', 'Strict': None})
        with pytest.raises(ValueError, match='invalid enum value'):
            cls.from_mapping({'Constant': 'exact', 'Outcome': 'null'})
        with pytest.raises(ValueError, match='invalid enum value'):
            cls.from_mapping({'Constant': 'other'})
    finally:
        sys.modules.pop(module.__name__, None)
