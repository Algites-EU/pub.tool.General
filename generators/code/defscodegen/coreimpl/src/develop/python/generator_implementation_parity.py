"""Integration checks between the independent JVM and Python generator implementations.

Run with --java-classpath from a checkout with the generator/naming Python packages
installed. The Java TestNG suite invokes the same checks automatically.
"""
from __future__ import annotations

import argparse
import ast
from copy import deepcopy
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from eu.algites.tool.codegen.defs.aic_schema_object_bindings_generator import AIcSchemaObjectBindingsGenerator


def create_fixture(root):
    """Exercise scalar types, nested objects, enums, unions and cross-package references."""
    manifest = root / 'bindings.json'
    override_schema = 'coreintf/src/product/jsondefs/example/contracts/root_1.jsondef.schema.json'
    manifest.write_text(json.dumps(dict(artifact='coreintf', implementation_artifact='coreimpl', languages=['python', 'java'],
        bindings=[dict(schema=override_schema, pointer='/$defs/valueSource', name='shared-value-source', common_one_of_fields=True)])), encoding='utf-8')
    for kind, suffix in (('jsondefs', 'jsondef.schema.json'), ('yamldefs', 'yamldef.schema.json')):
        directory = root / 'coreintf/src/product' / kind / 'example'
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
    """Ignore syntax formatting/quote style, retaining code, literals and documentation."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                first.value.value = ' '.join(first.value.value.split())
    return ast.dump(tree, include_attributes=False)


def normalized_java(source):
    """Ignore spacing outside literals and normalize comment whitespace only."""
    pattern = r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|/\*[\s\S]*?\*/|//[^\n]*|[A-Za-z_$][A-Za-z0-9_$]*|[0-9]+|[^\s]'
    tokens = re.findall(pattern, source)
    return tuple(' '.join(token.split()) if token.startswith(('/*','//')) else token for token in tokens)


class AItcGeneratorImplementationParityTest(unittest.TestCase):
    """Generate using both implementations; compare outputs and run their native code."""

    java_classpath = None

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='defs-implementation-parity-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repositories = {}
        for implementation in ('jvm','python'):
            root = self.root / implementation; root.mkdir()
            self.repositories[implementation] = (root, create_fixture(root))

    def generate(self, implementation, check=False, success=True):
        root, manifest = self.repositories[implementation]
        if implementation == 'python':
            if success:
                return AIcSchemaObjectBindingsGenerator().generate_repository(root, manifest, check)
            with self.assertRaises((ValueError, KeyError, TypeError)):
                AIcSchemaObjectBindingsGenerator().generate_repository(root, manifest, check)
            return None
        process = subprocess.run(['java','-cp',self.java_classpath,
            'eu.algites.tool.codegen.defs.AIcSchemaObjectBindingsGenerator',str(root),str(manifest),'--json',
            *(['--check'] if check else [])], text=True, capture_output=True)
        if success:
            self.assertEqual(process.returncode, 0, process.stderr)
            return json.loads(process.stdout)
        self.assertNotEqual(process.returncode, 0, process.stdout)

    def compare_outputs(self):
        roots = [item[0] for item in self.repositories.values()]
        owned = [json.loads((root / 'build/run/schema-bindings/generated-files.json').read_text()) for root in roots]
        self.assertEqual(owned[0], owned[1])
        for relative in owned[0]:
            sources = [(root / relative).read_text(encoding='utf-8') for root in roots]
            normalize = normalized_python if relative.endswith('.py') else normalized_java
            self.assertEqual(normalize(sources[0]), normalize(sources[1]), relative)

    def test_complete_outputs_and_native_runtime(self):
        results = [self.generate(kind) for kind in self.repositories]
        self.assertEqual(results[0], results[1])
        self.compare_outputs()
        for root, _ in self.repositories.values():
            env = dict(os.environ, PYTHONPATH=os.pathsep.join(str(root / artifact / 'src/product/python.gen') for artifact in ('coreintf','coreimpl')),
                PYTHONPYCACHEPREFIX=str(root / 'build/pycache'))
            runtime = '''
from decimal import Decimal
import dataclasses, importlib, inspect, pathlib, typing
for artifact in ('coreintf','coreimpl'):
    base = pathlib.Path(artifact) / 'src/product/python.gen'
    for path in base.rglob('*.py'):
        module = importlib.import_module('.'.join(path.relative_to(base).with_suffix('').parts))
        for cls in vars(module).values():
            if isinstance(cls,type) and cls.__module__ == module.__name__ and hasattr(cls,'__canonical_source_id__'):
                typing.get_type_hints(cls)
from example.contracts.aiig_root_1 import AIigRoot_1
from example.contracts.aicgd_root_1 import AIcgdRoot_1
assert inspect.isabstract(AIigRoot_1)
assert not inspect.isabstract(AIcgdRoot_1)
assert AIigRoot_1.SCHEMA_FIELD_NAME__NAME == 'Name'
assert all(not f.name.startswith('SCHEMA_FIELD_NAME__') for f in dataclasses.fields(AIcgdRoot_1))
wire = dict(Name='example',Count=10**80,Amount=Decimal('123456789.123456789'),Flag=True,Nothing=None,
    Child={'Id':7},Children=[{'Id':2}],State='ready',States=['done'],Items=[{'Id':4}],QuotedText='ABC',
    Date='2024-02-29Z',Duration='P1Y2M',Binary='01FF')
value = AIcgdRoot_1.from_mapping(wire)
assert isinstance(value,AIigRoot_1) and value.to_mapping() == wire
assert not hasattr(value,'__dict__') and 'TextValues' not in value.to_mapping()
assert value.child.id == 7
assert typing.get_type_hints(AIigRoot_1)['date'] is typing.get_type_hints(AIcgdRoot_1)['date']
try: AIcgdRoot_1.from_mapping(dict(wire,Child={'Id':10}))
except ValueError: pass
else: raise AssertionError('Invalid referenced scalar value accepted')
'''
            subprocess.run([sys.executable,'-c',runtime], cwd=root, env=env, check=True)
            java = [str(p) for artifact in ('coreintf','coreimpl') for p in (root / artifact / 'src/product/java.gen').rglob('*.java')]
            subprocess.run(['java','com.sun.tools.javac.Main','-d',str(root / 'build/classes'),*java], check=True)

    def test_paired_api_all_frontends_and_targets(self):
        from eu.algites.lib.naming.convention.aic_algites_naming_profiles import AIcAlgitesNamingProfiles
        from eu.algites.tool.codegen.defs.aic_default_defs_codegen_service import AIcDefaultDefsCodegenService
        from eu.algites.tool.codegen.defs.aic_schema_interface_generator import AIcSchemaInterfaceGenerator
        from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
        from eu.algites.tool.codegen.defs.aicd_code_generation_request import AIcdCodeGenerationRequest
        from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
        from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
        resources = Path(__file__).parents[1]
        for kind, suffix in ((AInDefinitionSourceKind.JSONDEFS,'jsondef.schema.json'),
                (AInDefinitionSourceKind.YAMLDEFS,'yamldef.schema.json'),(AInDefinitionSourceKind.XMLDEFS,'xsd')):
            for target in AInCodeGenerationTarget:
                profile = AIcAlgitesNamingProfiles.python_profile() if target is AInCodeGenerationTarget.PYTHON else AIcAlgitesNamingProfiles.java_profile()
                for stem in ('parity-root','parity-child','parity-leaf','parity-status','parity-builtins'):
                    with self.subTest(kind=kind, target=target, stem=stem):
                        source = resources / kind.value / (stem + '_1.' + suffix)
                        model = AIcDefaultDefsCodegenService().load(AIcdDefinitionLoadRequest(source,kind,profile))
                        pair = AIcSchemaInterfaceGenerator().generate(AIcdCodeGenerationRequest(model,target,'api_parity',profile))
                        output = self.root / 'api' / kind.value / target.value / stem
                        subprocess.run(['java','-cp',self.java_classpath,'eu.algites.tool.codegen.defs.AItcGeneratorImplementationParityTest',
                            kind.name,target.name,str(source),'api_parity',str(output)],check=True,capture_output=True)
                        expected = [item for item in (pair.contract,pair.implementation) if item is not None]
                        self.assertEqual({p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()}, {item.relative_path for item in expected})
                        for item in expected:
                            normalize = normalized_python if target is AInCodeGenerationTarget.PYTHON else normalized_java
                            self.assertEqual(normalize((output / item.relative_path).read_text()),normalize(item.source),item.relative_path)

    def test_check_and_owned_stale_pruning(self):
        for implementation, (root, _) in self.repositories.items():
            self.generate(implementation)
            base = root / 'coreintf/src/product/python.gen/example/contracts'
            other = base / 'other_generator.py'; other.write_text('# independent output\n')
            contract = base / 'aiig_root_1.py'; contract.unlink()
            before = {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
            self.generate(implementation, check=True, success=False)
            self.assertEqual(before, {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()})
            self.generate(implementation)
            for kind in ('jsondefs','yamldefs'):
                schema = next((root / 'coreintf/src/product' / kind / 'example/contracts').glob('root_1.*.json'))
                node = json.loads(schema.read_text()); del node['properties']['Items']
                schema.write_text(json.dumps(node))
            self.generate(implementation)
            self.assertFalse((base / 'aiig_root_items_items_1.py').exists())
            self.assertTrue(other.exists())
            self.generate(implementation, check=True)
        self.compare_outputs()

    def test_invalid_representations_and_paths_do_not_write(self):
        for implementation, (root, manifest) in self.repositories.items():
            self.generate(implementation)
            schema = root / 'coreintf/src/product/yamldefs/example/values/child_1.yamldef.schema.json'
            schema.write_text('{"type":"object","properties":{"Id":{"type":"string"}}}')
            def snapshot():
                return {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file() and any(part.endswith('.gen') for part in p.parts)}
            before = snapshot()
            self.generate(implementation, success=False); self.assertEqual(snapshot(),before)
            data = json.loads(manifest.read_text()); data['artifact'] = '../../escape'; manifest.write_text(json.dumps(data))
            self.generate(implementation, success=False); self.assertEqual(snapshot(),before)

    def test_distinct_objects_collisions_and_ignored_documentation(self):
        for implementation, (root, _) in self.repositories.items():
            self.generate(implementation)
            base = root / 'coreintf/src/product/python.gen/example/contracts'
            self.assertIn('SCHEMA_FIELD_NAME__PROPERTY_VALUE',(base / 'aiig_root_thing_1.py').read_text())
            self.assertIn('SCHEMA_FIELD_NAME__DEFINITION_VALUE',(base / 'aiig_root_definition_thing_1.py').read_text())
            schema = root / 'coreintf/src/product/jsondefs/example/contracts/root_1.jsondef.schema.json'
            node = json.loads(schema.read_text())
            node['examples'] = [dict(type='object',properties={'ShouldNotGenerate':dict(type='string')})]
            schema.write_text(json.dumps(node))
            before = set(base.glob('*.py')); self.generate(implementation); self.assertEqual(set(base.glob('*.py')),before)
            node['properties']['thing'] = deepcopy(node['properties']['Thing']); schema.write_text(json.dumps(node))
            self.generate(implementation,success=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--java-classpath', required=True)
    parsed = parser.parse_args()
    AItcGeneratorImplementationParityTest.java_classpath = parsed.java_classpath
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AItcGeneratorImplementationParityTest)
    return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
