"""Stable reference-documentation policy for the two independent generators."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = next(parent for parent in Path(__file__).resolve().parents
            if parent.name == 'pub.tool.General')
CODE = ROOT / 'generators/code'


class TestGeneratorDocumentation:
    """A generator has one introduction and one maintained feature reference."""

    @pytest.mark.parametrize('name,manual', (
        ('defscodegen', 'DEFS-CODEGEN-REFERENCE.md'),
        ('sdocodegen', 'SDO-CODEGEN-REFERENCE.md'),
    ))
    def test_only_current_prose_manuals_remain(self, name, manual):
        """Historical status/transition documents may not proliferate again."""
        base = CODE / name
        documentation = {str(p.relative_to(base)) for p in base.rglob('*.md')}
        expected = {'README.md', manual}
        if name == 'defscodegen':
            # This is a public JSON Schema dialect resource with a stable URI.
            # It is machine-referenced; moving it would break schema publishing.
            expected.add('dialect/src/product/jsonmetadefs/eu/algites/tool/codegen/'
                         'defs/jsonmetadef/vocabulary_1.md')
        assert documentation == expected
        intro = (base / 'README.md').read_text(encoding='utf-8')
        assert f']({manual})' in intro
        reference = (base / manual).read_text(encoding='utf-8')
        assert 'Java' in reference and 'Python' in reference
        assert '.old' in reference and 'bootstrap' in reference

    @pytest.mark.parametrize('file', (
        CODE / 'defscodegen/DEFS-CODEGEN-REFERENCE.md',
        CODE / 'sdocodegen/SDO-CODEGEN-REFERENCE.md',
        CODE / 'CODEGEN-REFERENCE.md',
    ))
    def test_relative_markdown_links_point_to_existing_resources(self, file):
        """Removing obsolete notes must not leave broken cross-references."""
        content = file.read_text(encoding='utf-8')
        for match in re.finditer(r'\]\(([^)]+)\)', content):
            uri = match.group(1)
            if uri.startswith(('https:', 'http:', 'mailto:', '#')):
                continue
            path = uri.split('#', 1)[0]
            if not path or '\n' in path:
                continue
            assert (file.parent / path).exists(), (file, path)
