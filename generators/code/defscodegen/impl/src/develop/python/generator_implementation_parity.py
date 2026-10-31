"""Independent Python/JVM parity checks for the canonical first-stage API.

Only read contracts and enums are generated. Concrete SmartDataObject implementations
belong to the independent SDO Codegen test suite.
"""
from __future__ import annotations
import argparse
import ast
import json
import difflib
import io
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import tokenize
import unittest

from explicit_naming_fixture import explicit_algites_manifest
from explicit_legacy_naming import configured_load, rendering_catalog
from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_bindings_generator import AIcSchemaContractBindingsGenerator
from eu.algites.tool.codegen.defs.impl.standard.aic_schema_contract_interface_generator import AIcSchemaContractInterfaceGenerator

def create_fixture(root):
    """Exercise scalar types, nested objects, enums, unions and cross-package references."""
    manifest = root / 'bindings.json'
    override_schema = 'intf/src/product/jsondefs/example/contracts/root_1.jsondef.schema.json'
    manifest.write_text(json.dumps(explicit_algites_manifest(dict(artifact='intf', implementation_artifact='impl', languages=['python', 'java'],
        bindings=[dict(schema=override_schema, pointer='/$defs/ValueSource', name='shared-value-source')]))), encoding='utf-8')
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
                'SourceA':dict(type='object', properties={'Source':dict(type='string', const='a'), 'Value':dict(type='string')}, required=['Source','Value']),
                'SourceB':dict(type='object', properties={'Source':dict(type='string', const='b'), 'Value':dict(type='string')}, required=['Source']),
                'ValueSource':dict(type='object', properties={'Source': dict(type='string'), 'Value': dict(type='string')}, oneOf=[{'$ref':'#/$defs/SourceA'},{'$ref':'#/$defs/SourceB'}])}})
        # The explicit shared union override has only one representation; leave equivalent
        # plain objects in the second format to verify the normal merger independently.
        if kind == 'yamldefs':
            del schema['$defs']['ValueSource']
        (contracts / f'root_1.{suffix}').write_text(json.dumps(schema), encoding='utf-8')
        (values / f'scalar_1.{suffix}').write_text('{"type":"number","minimum":0.12345678901234567890123456789}', encoding='utf-8')
        (contracts / 'ignored.meta.yml').write_text('GlobalPublicationPathId: fixture\n', encoding='utf-8')
    return manifest

def normalized_python(source):
    """Ignore only lexical whitespace while preserving Python syntax and literals.

    INDENT/DEDENT and logical NEWLINE tokens remain visible: changing the block
    hierarchy or statement boundaries cannot accidentally pass as formatting.
    Comments keep their wording but ignore the spacing within the comment.
    Unlike comparing ASTs this rejects alternative implementations, parentheses,
    changed literals, and reordered declarations even when their meaning matches.
    """
    tokens = []
    reader = io.BytesIO(source.encode('utf-8')).readline
    for item in tokenize.tokenize(reader):
        if item.type in (tokenize.ENCODING, tokenize.ENDMARKER, tokenize.NL):
            continue
        if item.type in (tokenize.INDENT, tokenize.DEDENT):
            tokens.append((item.type, ''))
        elif item.type == tokenize.COMMENT:
            tokens.append((item.type, ' '.join(item.string.split())))
        else:
            tokens.append((item.type, item.string if item.type != tokenize.NEWLINE else ''))
    return tuple(tokens)


def normalized_java(source):
    """Ignore spacing outside literals and normalize comment whitespace only."""
    pattern = r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|/\*[\s\S]*?\*/|//[^\n]*|[A-Za-z_$][A-Za-z0-9_$]*|[0-9]+|>>>=|<<=|>>=|>>>|\.\.\.|::|->|==|!=|<=|>=|&&|\|\||\+\+|--|<<|>>|[+*/%&|^!=<>-]=|[^\s]'
    tokens = re.findall(pattern, source)
    return tuple(' '.join(token.split()) if token.startswith(('/*','//')) else token for token in tokens)



def assert_identical_outputs(test, expected, actual, language):
    """Reject missing/extra sources and show a focused source-level parity diff.

    Args:
        test: active unittest instance
        expected: paths and emitted sources from the JVM generator
        actual: paths and emitted sources from the Python generator
        language: target technology name for the diagnostic
    Raises:
        AssertionError: For a missing, additional, or lexically unequal source
    """
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    test.assertFalse(missing or extra,
        f'{language}: generated file set differs\nMissing in Python: {missing}\nExtra in Python: {extra}')
    normalizer = normalized_python if language == 'python' else normalized_java
    for relative in sorted(expected):
        if normalizer(expected[relative]) != normalizer(actual[relative]):
            diff = ''.join(difflib.unified_diff(expected[relative].splitlines(True),
                actual[relative].splitlines(True), fromfile='java-generator/' + relative,
                tofile='python-generator/' + relative))
            raise AssertionError(f'{language}: non-whitespace output difference in {relative}\n{diff[:20000]}')


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

    def test_whitespace_normalizers_do_not_mask_semantic_differences(self):
        """Regress strict parity: only whitespace outside tokens may be ignored."""
        self.assertEqual(normalized_python('def f():\n    return 1\n'),
                         normalized_python('def f( ):\n        return 1\n'))
        self.assertNotEqual(normalized_python('def f():\n    return 1\n'),
                            normalized_python('def f():\n    return 2\n'))
        self.assertNotEqual(normalized_python('if ready:\n    return_value = 1\n'),
                            normalized_python('if ready:\n    pass\nreturn_value = 1\n'))
        self.assertEqual(normalized_java('class Test { int a=1; }'),
                         normalized_java('class  Test{int a = 1;}'))
        self.assertNotEqual(normalized_java('class Test { int a=1; }'),
                            normalized_java('class Test { int a=2; }'))
        self.assertNotEqual(normalized_java('int x = a + +b;'),
                            normalized_java('int x = a++b;'))

    def test_contract_repository_output_parity(self):
        result = {name: self.generate(name) for name in self.repositories}
        self.assertEqual(result['jvm'], result['python'])
        a, b = (self._outputs(name) for name in ('jvm', 'python'))
        self.assertTrue(a, 'No generated sources: parity test must never pass vacuously')
        self.assertFalse(any('/impl/' in path or 'aicgd_' in path for path in a))
        for language, extension in (('java', '.java'), ('python', '.py')):
            java_outputs = {path: source for path, source in a.items() if path.endswith(extension)}
            python_outputs = {path: source for path, source in b.items() if path.endswith(extension)}
            self.assertTrue(java_outputs, f'JVM generator emitted no {language} files')
            self.assertTrue(python_outputs, f'Python generator emitted no {language} files')
            assert_identical_outputs(self, java_outputs, python_outputs, language)
        for name in self.repositories:
            before = self._outputs(name)
            self.generate(name, check=True)
            self.assertEqual(before, self._outputs(name))

    def test_all_frontends_and_targets(self):
        from eu.algites.lib.naming.convention.impl.standard.aic_name_convention_catalog import AIcNameConventionCatalog
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
                language = 'python' if target is AInCodeGenerationTarget.PYTHON else 'java'
                profile = AIcNameConventionCatalog.load_many([
                    f'resource:algites-{family}-name-conventions.yml'
                    for family in (language, 'jsondef', 'yamldef', 'xmldef')])
                for stem in ('parity-supported', 'parity-child', 'parity-leaf', 'parity-status', 'parity-supported-builtins'):
                    with self.subTest(kind=kind, target=target, stem=stem):
                        source = resources / kind.value / (stem + '_1.' + suffix)
                        model = AIcDefaultDefsCodegenService().load(configured_load(source, kind, profile))
                        item = AIcSchemaContractInterfaceGenerator().generate(AIcdCodeGenerationRequest(
                            model, target, 'api_parity', rendering_catalog(profile, language)))
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
