"""Executable, source-level contracts for generated Defs interfaces.

The audit deliberately reads *delivered* .gen/.extgen files, not handcrafted
fixtures.  It catches a stale generated tree as well as defects in the emitter.
Sources in a multi-generator tree may share an output directory; only read-only
AIig contracts belong to this audit, not generated writable SDO classes.

Run with PYTHONDONTWRITEBYTECODE=1 python -m pytest -q \
    devops/bootstrap-tests/test_contract_architecture_audit.py

@author linhart1
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import re

import pytest

TOOL = Path(__file__).resolve().parents[2]
LIB = TOOL.parent / 'pub.lib.General'
REPOS = (TOOL, LIB)
SPECIAL = re.compile(r'^AIig_([xjy])')
JAVA_METHOD = re.compile(r'(?m)^\s*(?:public\s+)?([\w.$?<>\[\],\s]+?)\s+(get\w+|is\w+)\s*\(\s*\)\s*;')
JAVA_CLASS = re.compile(r'\bpublic\s+interface\s+(AIig\w+)\s+extends\s+([^\{]+)\{')
PACKAGE = re.compile(r'(?m)^package\s+([\w.]+);')


@dataclass(frozen=True)
class Contract:
    """One read-only interface definition from one generated technology tree."""
    name: str
    package: str
    language: str
    stage: str
    path: Path
    parents: tuple[str, ...]
    methods: dict[str, str]
    semantic: frozenset[str]
    general_annotation: bool
    technology_annotation: bool

    @property
    def key(self):
        """Stable identity shared by corresponding Java and Python types."""
        return (self.stage, self.package, self.name)


def _stage(path: Path) -> str:
    """Separate persistently shipped extgen bootstrap seed from generated sources."""
    return 'extgen' if '.extgen' in path.parts else 'gen'


def _read_java(path: Path) -> Contract | None:
    """Parse generated Java read-interface signatures without compiling dependencies."""
    value = path.read_text(encoding='utf8')
    found = JAVA_CLASS.search(value)
    package = PACKAGE.search(value)
    if not found or not package:
        return None
    name, inherited = found.groups()
    parents = tuple(s.strip() for s in inherited.split(','))
    methods: dict[str, str] = {}
    semantic = set()
    for match in JAVA_METHOD.finditer(value):
        method = match.group(2)
        methods[method] = re.sub(r'\s+', ' ', match.group(1)).strip()
        # Annotation must be attached to THIS getter, not just present elsewhere.
        prev = value.rfind(';', 0, match.start())
        prev = max(prev, value.rfind('}', 0, match.start()))
        vicinity = value[prev + 1:match.start()]
        if re.search(r'@(?:[\w.]+\.)?AIaDataObjectField\s*\(', vicinity):
            semantic.add(method)
    return Contract(name, package.group(1), 'java', _stage(path), path,
                    parents, methods, frozenset(semantic),
                    '@eu.algites.lib.data.dataobject.AIaDataObject(' in value,
                    bool(re.search(r'@[^\s(]*AIa(?:Xml|Json|Yaml)DataObject\(', value)))


def _read_python(path: Path) -> Contract | None:
    """Use AST so decorator checks are scoped to each declared getter."""
    value = path.read_text(encoding='utf8')
    tree = ast.parse(value, filename=str(path))
    cls = next((n for n in tree.body if isinstance(n, ast.ClassDef)
                and n.name.startswith('AIig')), None)
    if cls is None:
        return None
    import_path = path.as_posix().split('/src/product/', 1)[-1].split('/', 1)[-1]
    package = '.'.join(import_path.split('/')[:-1])
    aliases = {}
    for top in tree.body:
        if isinstance(top, ast.ImportFrom) and top.module:
            for imported in top.names:
                aliases[imported.asname or imported.name] = (package if top.level else top.module.rpartition('.')[0]) + '.' + imported.name
    parents = tuple(aliases.get(ast.unparse(n), ast.unparse(n)) for n in cls.bases)
    methods: dict[str, str] = {}
    semantic = set()
    for field in cls.body:
        if isinstance(field, (ast.FunctionDef, ast.AsyncFunctionDef)) and re.match(r'^(get|is)[A-Z]', field.name):
            methods[field.name] = ast.unparse(field.returns) if field.returns else 'Any'
            if any(ast.unparse(decorator).startswith('AIaDataObjectField(')
                   for decorator in field.decorator_list):
                semantic.add(field.name)
    general = any(isinstance(n, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == '__data_object__' for t in n.targets)
        for n in cls.body)
    technology = any(isinstance(n, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id in {'__xml_data_object__', '__json_data_object__', '__yaml_data_object__'}
        for t in n.targets) for n in cls.body)
    return Contract(cls.name, package, 'python', _stage(path), path,
                    parents, methods, frozenset(semantic), general, technology)


def _contracts():
    """Collect all generated read-only interfaces from both repositories."""
    rows = []
    for repo in REPOS:
        if not repo.is_dir():
            continue
        for language, ext, reader in (('java', '*.java', _read_java),
                                       ('python', '*.py', _read_python)):
            for path in repo.rglob(ext):
                if 'build' in path.parts or '.pytest_cache' in path.parts:
                    continue
                if f'/src/product/{language}.gen/' not in path.as_posix() and \
                        f'/src/product/{language}.extgen/' not in path.as_posix():
                    continue
                if not path.name.startswith(('AIig', 'aiig')):
                    continue
                obj = reader(path)
                if obj:
                    rows.append(obj)
    return rows


@pytest.fixture(scope='module')
def contracts():
    """Parse the same immutable contracts for all five architecture checks."""
    found = _contracts()
    assert found, 'No shipped read-only Defs contracts discovered'
    return found


def _parents(index: dict, obj: Contract):
    """Traverse ancestors through both local and cross-package interface edges."""
    visited = {obj.package + '.' + obj.name}
    pending = [obj]
    while pending:
        current = pending.pop()
        for parent in current.parents:
            full_name = parent if '.' in parent else current.package + '.' + parent
            if full_name in visited:
                continue
            visited.add(full_name)
            candidate = index.get((current.stage, full_name))
            if candidate:
                yield candidate
                pending.append(candidate)


def _failure(errors, limit=16):
    """Show actionable source locations without hiding the number of violations."""
    if errors:
        pytest.fail(f'{len(errors)} violations:\n' + '\n'.join(errors[:limit]) +
                    (f'\n... {len(errors) - limit} more' if len(errors) > limit else ''))


@pytest.mark.parametrize('language', ['java', 'python'])
def test_only_neutral_interfaces_declare_semantic_fields(contracts, language):
    """Technology projections must not redeclare @AIaDataObjectField metadata."""
    issues = []
    for obj in contracts:
        if obj.language != language or not SPECIAL.match(obj.name):
            continue
        if obj.semantic or obj.general_annotation:
            issues.append(f'{obj.path}: technology {obj.name} has general annotations '
                          f'(getters={sorted(obj.semantic)}, class={obj.general_annotation})')
    _failure(issues)


@pytest.mark.parametrize('language', ['java', 'python'])
def test_every_technology_getter_overrides_neutral_semantics(contracts, language):
    """No XML/JSON/YAML-only business field; neutral ancestor owns its getter."""
    index = {(c.stage, c.package + '.' + c.name): c for c in contracts if c.language == language}
    issues = []
    for obj in contracts:
        if obj.language != language or not SPECIAL.match(obj.name):
            continue
        ancestors = tuple(_parents(index, obj))
        for method in obj.methods:
            if not any(method in parent.semantic for parent in ancestors
                       if not SPECIAL.match(parent.name)):
                issues.append(f'{obj.path}: {obj.name}.{method} has no annotated neutral ancestor')
    _failure(issues)


def test_java_collection_getters_keep_covariance_through_every_level(contracts):
    """List and multi-mapped list read getters must preserve '? extends T'."""
    issues = []
    for obj in contracts:
        if obj.language != 'java':
            continue
        for name, return_type in obj.methods.items():
            if re.search(r'\b(?:List|AIiMultiMappedList)\s*<', return_type) and \
                    not re.search(r'<\s*\?\s+extends\s+', return_type):
                issues.append(f'{obj.path}: {name}() returns {return_type!r} without covariance')
    _failure(issues)


def test_java_python_declared_read_contract_structures_match(contracts):
    """Verify matched read interfaces expose the same methods and semantic metadata."""
    indexed = {(obj.key, obj.language): obj for obj in contracts}
    issues = []
    for (key, lang), java in indexed.items():
        if lang != 'java':
            continue
        python = indexed.get((key, 'python'))
        if python is None:
            issues.append(f'{java.path}: missing Python interface {java.name}')
            continue
        java_methods = set(java.methods)
        python_methods = set(python.methods)
        if java_methods != python_methods:
            issues.append(f'{java.path} vs {python.path}: Java-only {sorted(java_methods - python_methods)} '
                          f'Python-only {sorted(python_methods - java_methods)}')
        if java.semantic != python.semantic:
            issues.append(f'{java.path} vs {python.path}: semantic annotations differ: '
                          f'Java {sorted(java.semantic)} vs Python {sorted(python.semantic)}')
    for (key, lang), python in indexed.items():
        if lang == 'python' and (key, 'java') not in indexed:
            issues.append(f'{python.path}: missing Java interface {python.name}')
    _failure(issues)


def _field_shape(source_type: str, language: str):
    """Compare typed field shapes while preserving technology-specific element names."""
    if 'AIiMultiMappedList' in source_type:
        container = 'multi_mapped_list'
    elif (re.search(r'\bList\s*<', source_type) if language == 'java' else
          re.search(r'\b(?:tuple|list)\s*\[', source_type)):
        container = 'list'
    elif (re.search(r'\bMap\s*<', source_type) if language == 'java' else
          re.search(r'\b(?:Mapping|dict)\s*\[', source_type)):
        container = 'map'
    else:
        container = 'scalar'
    symbols = tuple(re.findall(r'\b(?:AIig|AIng)\w+_1\b', source_type))
    return container, symbols


def test_java_python_field_value_shapes_match(contracts):
    """A matching getter must have the same list/map semantics and named item type."""
    indexed = {(obj.key, obj.language): obj for obj in contracts}
    issues = []
    for (key, language), java in indexed.items():
        if language != 'java':
            continue
        python = indexed.get((key, 'python'))
        if not python:
            continue  # Absence is reported by the structural parity test.
        for name in java.methods.keys() & python.methods.keys():
            jshape = _field_shape(java.methods[name], 'java')
            pshape = _field_shape(python.methods[name], 'python')
            if jshape != pshape:
                issues.append(f'{java.path}:{name}: Java {java.methods[name]!r} != '
                              f'{python.path}: Python {python.methods[name]!r} '
                              f'(shape {jshape} vs {pshape})')
    _failure(issues)


def test_technology_interfaces_inherit_neutral_type(contracts):
    """Technology-specific contracts must directly or transitively extend a neutral type."""
    issues = []
    for language in ('java', 'python'):
        index = {(c.stage, c.package + '.' + c.name): c for c in contracts if c.language == language}
        for obj in contracts:
            if obj.language != language or not SPECIAL.match(obj.name):
                continue
            ancestors = tuple(_parents(index, obj))
            if not any(not SPECIAL.match(parent.name) for parent in ancestors):
                issues.append(f'{obj.path}: {obj.name} has no neutral ancestor; '
                              f'parents={obj.parents}')
    _failure(issues)
