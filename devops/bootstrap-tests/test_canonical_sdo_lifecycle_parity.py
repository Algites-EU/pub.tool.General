"""Run the same mutable SDO field lifecycle in both language runtimes.

Java compilation uses the checked-out sources, not fabricated DataObject
interfaces. External dependency jars must be supplied by the successful build
(or explicitly with ALGITES_PARITY_JAVA_CLASSPATH). Missing jars are reported as
an explicit skip rather than being mistaken for a passing Java test.

@author linhart1
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

TOOL = Path(__file__).resolve().parents[2]
LIB = TOOL.parent / 'pub.lib.General'
JAVA_HARNESS = '''\
import eu.algites.tool.codegen.defs.bootstrap.model.impl.AIcgdSourceBindingGroup_1;
import eu.algites.tool.codegen.defs.bootstrap.model.AIngSourceInputKind_1;
public class CanonicalGroupLifecycleCheck {
 public static void main(String[] args) {
  var value = new AIcgdSourceBindingGroup_1();
  if (value._isPresent_InputKind()) throw new AssertionError("Presence before set");
  value.setInputKind(AIngSourceInputKind_1.JSONDEFS);
  if (!value._isPresent_InputKind() ||
      value.getInputKind() != AIngSourceInputKind_1.JSONDEFS)
    throw new AssertionError("Wrong value after set");
  value._unset_InputKind();
  if (value._isPresent_InputKind()) throw new AssertionError("Presence after unset");
 }
}
'''
PYTHON_HARNESS = '''\
import sys
from eu.algites.tool.codegen.defs.bootstrap.model.impl.aicgd_source_binding_group_1 import AIcgdSourceBindingGroup_1
from eu.algites.tool.codegen.defs.bootstrap.model.aing_source_input_kind_1 import AIngSourceInputKind_1
value = AIcgdSourceBindingGroup_1()
assert not value._isPresent_InputKind()
value.setInputKind(AIngSourceInputKind_1.JSONDEFS)
assert value._isPresent_InputKind() and value.getInputKind() == AIngSourceInputKind_1.JSONDEFS
value._unset_InputKind()
assert not value._isPresent_InputKind()
'''


def _source_roots(language):
    """Find production source trees without touching tracked generated outputs."""
    roots = []
    for repo in (LIB, TOOL):
        for branch in (language, f'{language}.gen', f'{language}.extgen'):
            roots.extend(p / branch for p in repo.rglob('src/product')
                         if (p / branch).is_dir() and 'build' not in p.parts)
    return sorted(set(roots))


def test_python_generated_group_lifecycle():
    """Generated Python SDO supports presence, typed setter and unsetter."""
    roots = [str(p) for p in _source_roots('python')]
    result = subprocess.run([sys.executable, '-c', PYTHON_HARNESS],
                            text=True, capture_output=True, cwd=TOOL,
                            env={**os.environ, 'PYTHONPATH': os.pathsep.join(roots),
                                 'PYTHONDONTWRITEBYTECODE': '1'}, timeout=45)
    assert result.returncode == 0, result.stderr


def test_java_generated_group_lifecycle(tmp_path):
    """Compile actual Java SDO from sources and exercise the same lifecycle."""
    if not shutil.which('javac') or not shutil.which('java'):
        pytest.skip('JDK is unavailable: Java lifecycle NOT verified')
    classpath = os.environ.get('ALGITES_PARITY_JAVA_CLASSPATH', '')
    if not classpath:
        pytest.skip('ALGITES_PARITY_JAVA_CLASSPATH not configured: Java lifecycle NOT verified')
    expected = [Path(path) for path in classpath.split(os.pathsep)]
    assert all(path.exists() for path in expected), 'Java test classpath contains nonexistent dependencies'
    source = tmp_path / 'CanonicalGroupLifecycleCheck.java'
    source.write_text(JAVA_HARNESS)
    # JetBrains @NotNull is a compile-only signature dependency of common/util.
    # Use a test-local declaration when the standalone test classpath lacks it;
    # neither the test stub nor any compiled class is published to source trees.
    annotation = tmp_path / 'org/jetbrains/annotations/NotNull.java'
    annotation.parent.mkdir(parents=True)
    annotation.write_text('''package org.jetbrains.annotations;
@java.lang.annotation.Retention(java.lang.annotation.RetentionPolicy.CLASS)
@java.lang.annotation.Target({java.lang.annotation.ElementType.METHOD,
 java.lang.annotation.ElementType.PARAMETER, java.lang.annotation.ElementType.FIELD,
 java.lang.annotation.ElementType.TYPE_USE})
public @interface NotNull {}
''')
    cp = os.pathsep.join((str(tmp_path), classpath))
    roots = os.pathsep.join(map(str, _source_roots('java')))
    result = subprocess.run(['javac', '--release', '17', '-d', str(tmp_path),
                             str(annotation)], text=True, capture_output=True, timeout=45)
    assert result.returncode == 0, result.stderr
    result = subprocess.run(['javac', '--release', '17', '-d', str(tmp_path),
                             '-cp', cp, '-sourcepath', roots, str(source)],
                            text=True, capture_output=True, timeout=90)
    assert result.returncode == 0, result.stderr
    result = subprocess.run(['java', '-cp', cp, 'CanonicalGroupLifecycleCheck'],
                            text=True, capture_output=True, timeout=45)
    assert result.returncode == 0, result.stderr
