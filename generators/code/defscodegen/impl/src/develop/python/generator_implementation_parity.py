"""Independent Python/JVM parity checks for the canonical first-stage API.

Only read contracts and enums are generated. Concrete SmartDataObject implementations
belong to the independent SDO Codegen test suite.
"""
from __future__ import annotations
import argparse
import ast
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import AIcSchemaContractBindingsGenerator
from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_interface_generator import AIcSchemaContractInterfaceGenerator

def create_fixture(root):
    """Exercise scalar types, nested objects, enums, unions and cross-package references."""
    manifest = root / 'bindings.json'
    override_schema = 'intf/src/product/jsondefs/example/contracts/root_1.jsondef.schema.json'
    manifest.write_text(json.dumps(dict(artifact='intf', implementation_artifact='impl', languages=['python', 'java'],
        bindings=[dict(schema=override_schema, pointer='/$defs/valueSource', name='shared-value-source', common_one_of_fields=True)])), encoding='utf-8')
    for kind, suffix in (('jsondefs', 'jsondef.schema.json'), ('yamldefs', 'yamldef.schema.json')):
        directory = root / 'intf/src/product' / kind / 'example'
        contracts = directory / 'contracts'; contracts.mkdir(parents=True)
        values = directory / 'values'; values.mkdir()
        child = dict(type='object', description='Child <value> & its documentation.',
            properties={'Id':dict(type='integer', minimum=-4, maximum=9), 'Text':dict(type='string', minLength=1)}, required=['Id'])
        state = dict(type='string', enum=['ready', 'done'], description='State documentation.',
            oneOf=[dict(const='ready', description='Ready to process.'), dict(const='done', description='Finished.')])
        for name, schema in (('child', child), ('state', state)):
            (values / f'{name}_1.{suffix}').write_text(json.dumps(schema), encoding='utf-8')
        props = {
            'Name':dict(type='string', description='Display name.'),
            'Count':dict(type='integer'), 'Amount':dict(type='number'), 'Flag':dict(type='boolean'),
            'Nothing':dict(type=['string','null']), 'Anything':{}, 'Metadata':dict(type='object'),
            'Class':dict(type='string'), 'GetClass':dict(type='string'),
            'Items':dict(type='array', items=dict(type='object', properties={'Id':dict(type='integer')}, required=['Id'])),
            'Child':{'$ref':f'../values/child_1.{suffix}'},
            'Children':dict(type='array', items={'$ref':f'../values/child_1.{suffix}'}),
            'State':{'$ref':f'../values/state_1.{suffix}'},
            'States':dict(type='array', items={'$ref':f'../values/state_1.{suffix}'}),
            'InlineState':dict(type='string', enum=['open','closed']),
            'Thing':dict(type='object', properties={'PropertyValue':dict(type='string')}),
            'QuotedText':dict(type='string', description='Contains "quotes", """triple quotes""", a backslash \\ and a new\nline.', pattern='[A-Z]+'),
            'TextValues':dict(type='array', items=dict(type='string')),
            'RawArray':dict(type='array'),
            'MixedState':dict(enum=['success','error',None]),
            'BooleanState':dict(type='boolean', enum=[True,False]),
            'Binary':dict(type='string', **{'x-modustro-datatype':'hexBinary'}),
            'Date':dict(type='string', **{'x-modustro-datatype':'date'}),
            'Duration':dict(type='string', **{'x-modustro-datatype':'duration'}),
        }
        schema = dict(type='object', description='Root contract documentation.', properties=props,
            required=['Name','Count','Amount','Flag','Nothing','Child','Children','State','States'],
            **{'$defs':{'Thing':dict(type='object', properties={'DefinitionValue':dict(type='integer')}),
                'sourceA':dict(type='object', properties={'Source':dict(type='string', const='a'), 'Value':dict(type='string')}, required=['Source','Value']),
                'sourceB':dict(type='object', properties={'Source':dict(type='string', const='b'), 'Value':dict(type='string')}, required=['Source']),
                'valueSource':dict(oneOf=[{'$ref':'#/$defs/sourceA'},{'$ref':'#/$defs/sourceB'}])}})
        # The explicit shared union override has only one representation; leave equivalent
        # plain objects in the second format to verify the normal merger independently.
        if kind == 'yamldefs':
            del schema['$defs']['valueSource']
        (contracts / f'root_1.{suffix}').write_text(json.dumps(schema), encoding='utf-8')
        (values / f'scalar_1.{suffix}').write_text('{"type":"number","minimum":0.12345678901234567890123456789}', encoding='utf-8')
        (contracts / 'ignored.meta.yml').write_text('GlobalPublicationPathId: fixture\n', encoding='utf-8')
    return manifest

def normalized_python(source):
    """Compare executable Python exactly while ignoring whitespace in documentation literals.

    Generated DataObject classes can place a standalone documentation string
    after canonical metadata assignments, not necessarily as their first member.
    The expression has no executable effect there; normalizing only the first
    statement would report false implementation mismatches.
    """
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for statement in node.body:
            if (isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant)
                    and isinstance(statement.value.value, str)):
                statement.value.value = ' '.join(statement.value.value.split())
    return ast.dump(tree, include_attributes=False)


def normalized_java(source):
    """Ignore spacing outside literals and normalize comment whitespace only."""
    pattern = r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|/\*[\s\S]*?\*/|//[^\n]*|[A-Za-z_$][A-Za-z0-9_$]*|[0-9]+|[^\s]'
    tokens = re.findall(pattern, source)
    return tuple(' '.join(token.split()) if token.startswith(('/*','//')) else token for token in tokens)



class AItcGeneratorImplementationParityTest(unittest.TestCase):
    """Compare independent renderers and verify first-stage repository ownership."""

    java_classpath = None
    java_fixture_directory = None

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='defs-contract-parity-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repositories = {}
        for name in ('jvm', 'python'):
            root = self.root / name
            root.mkdir()
            self.repositories[name] = root, create_fixture(root)

    def generate(self, name, check=False, success=True):
        root, manifest = self.repositories[name]
        if name == 'python':
            if success:
                return AIcSchemaContractBindingsGenerator().generate_repository(root, manifest, check)
            with self.assertRaises((ValueError, KeyError, TypeError)):
                AIcSchemaContractBindingsGenerator().generate_repository(root, manifest, check)
            return None
        proc = subprocess.run(['java', '-cp', self.java_classpath,
            'eu.algites.tool.codegen.defs.impl.standard.AIcSchemaContractBindingsGenerator',
            str(root), str(manifest), '--json', *(['--check'] if check else [])],
            text=True, capture_output=True)
        if not success:
            self.assertNotEqual(proc.returncode, 0, proc.stdout)
            return None
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout)

    def _outputs(self, name):
        root = self.repositories[name][0]
        result = {}
        for output in root.rglob('*'):
            if output.is_file() and any(p.endswith('.gen') for p in output.parts):
                result[output.relative_to(root).as_posix()] = output.read_text()
        return result

    def test_contract_repository_output_parity(self):
        result = {name: self.generate(name) for name in self.repositories}
        self.assertEqual(result['jvm'], result['python'])
        a, b = (self._outputs(name) for name in ('jvm', 'python'))
        self.assertEqual(set(a), set(b))
        self.assertTrue(a)
        self.assertFalse(any('/impl/' in path or 'aicgd_' in path for path in a))
        for path in a:
            normalize = normalized_python if path.endswith('.py') else normalized_java
            self.assertEqual(normalize(a[path]), normalize(b[path]), path)
        for name in self.repositories:
            before = self._outputs(name)
            self.generate(name, check=True)
            self.assertEqual(before, self._outputs(name))

    def test_all_frontends_and_targets(self):
        from eu.algites.lib.naming.convention.impl.algites.aic_algites_naming_profiles_1 import AIcAlgitesNamingProfiles_1
        from eu.algites.tool.codegen.defs.impl.standard.aic_default_defs_codegen_service import AIcDefaultDefsCodegenService
        from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
        from eu.algites.tool.codegen.defs.aicd_code_generation_request import AIcdCodeGenerationRequest
        from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
        from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
        resources = Path(__file__).parents[1]
        for kind, suffix in ((AInDefinitionSourceKind.JSONDEFS, 'jsondef.schema.json'),
                             (AInDefinitionSourceKind.YAMLDEFS, 'yamldef.schema.json'),
                             (AInDefinitionSourceKind.XMLDEFS, 'xsd')):
            for target in AInCodeGenerationTarget:
                profile = (AIcAlgitesNamingProfiles_1.python_profile() if target is AInCodeGenerationTarget.PYTHON
                    else AIcAlgitesNamingProfiles_1.java_profile())
                for stem in ('parity-root', 'parity-child', 'parity-leaf', 'parity-status', 'parity-builtins'):
                    with self.subTest(kind=kind, target=target, stem=stem):
                        source = resources / kind.value / (stem + '_1.' + suffix)
                        model = AIcDefaultDefsCodegenService().load(AIcdDefinitionLoadRequest(source, kind, profile))
                        item = AIcSchemaContractInterfaceGenerator().generate(AIcdCodeGenerationRequest(
                            model, target, 'api_parity', profile))
                        location = Path(self.java_fixture_directory) / kind.value / target.value / stem
                        files = [p for p in location.rglob('*') if p.is_file()]
                        self.assertEqual(len(files), 1)
                        self.assertEqual(files[0].relative_to(location).as_posix(), item.relative_path)
                        normalize = normalized_python if target is AInCodeGenerationTarget.PYTHON else normalized_java
                        self.assertEqual(normalize(files[0].read_text()), normalize(item.source), item.relative_path)
                        self.assertNotIn('aicgd', item.relative_path.lower())

    def test_read_only_check_detects_missing_outputs(self):
        for name in self.repositories:
            self.generate(name)
            root = self.repositories[name][0]
            output = next(p for p in root.rglob('*.py') if any(x.endswith('.gen') for x in p.parts))
            output.unlink()
            self.generate(name, check=True, success=False)
            self.generate(name)
            self.assertTrue(output.exists())


if __name__ == '__main__':
    cli = argparse.ArgumentParser()
    cli.add_argument('--java-classpath', required=True)
    cli.add_argument('--java-fixture-directory', required=True)
    args = cli.parse_args()
    AItcGeneratorImplementationParityTest.java_classpath = args.java_classpath
    AItcGeneratorImplementationParityTest.java_fixture_directory = args.java_fixture_directory
    unittest.main(argv=[sys.argv[0]])
