from __future__ import annotations

import re
from eu.algites.tool.codegen.defs.aicd_parsed_versioned_name import AIcdParsedVersionedName
from eu.algites.tool.codegen.defs.impl.standard._support import _strip_extensions


class AIcDefinitionIdentityResolver:
    """Separates canonical definition identity from an optional positive version."""

    @staticmethod
    def parse_versioned_stem(stem: str, explicit_version: int | None):
        found = re.fullmatch(r'(.*)_([0-9]+)', stem)
        file_version = int(found.group(2)) if found else None
        logical_name = found.group(1) if found else stem
        if file_version is not None and explicit_version is not None and file_version != explicit_version:
            raise ValueError(f'Definition version metadata {explicit_version} does not match file-name version {file_version} for {stem}')
        version = explicit_version if explicit_version is not None else file_version
        if version is not None and version < 1:
            raise ValueError(f'Definition version must be positive for {stem}')
        return AIcdParsedVersionedName(logical_name, version)

    def from_file(self, request, explicit_version: int | None):
        return self.parse_versioned_stem(_strip_extensions(request.path.name), explicit_version)
