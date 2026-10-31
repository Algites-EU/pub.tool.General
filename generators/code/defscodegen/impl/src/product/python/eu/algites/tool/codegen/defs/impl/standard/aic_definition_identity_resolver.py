from __future__ import annotations

from eu.algites.tool.codegen.defs.aicd_parsed_versioned_name import AIcdParsedVersionedName


class AIcDefinitionIdentityResolver:
    """Read canonical identifiers and versions through the selected source naming catalog.

    The filename is always parsed with a configured ``file_name_stem`` composition.
    Neither a trailing underscore nor numeric digits carry built-in semantics.
    """

    @staticmethod
    def from_file(request, explicit_version: int | None):
        """Parse the actual filename, then verify any declared schema version.

        Args:
            request: Source path and naming catalog/profile selection.
            explicit_version: Version declared by the schema, if present.
        Returns:
            Canonical logical identifier and optional version.
        Raises:
            ValueError: If the source name does not match its profile, a version
                is invalid, or metadata conflicts with the filename.
        """
        catalog = request.naming_profile
        profile = request.source_naming_profile
        if not profile:
            match = catalog.recognize_filename(request.path.name)
            if match is None:
                raise ValueError(f'No source filename naming convention matches {request.path}')
            profile = match.convention_name
            values = match.variables
        else:
            if profile not in catalog.names:
                raise ValueError(f'Unknown source filename naming convention: {profile}')
            # Parse the whole filename, not an extension guessed from a hard-coded list.
            match = catalog.recognize_filename(request.path.name, {profile})
            if match is None:
                raise ValueError(f'{request.path.name!r} does not match source filename profile {profile}')
            values = match.variables
        logical_name = values.get('identifier')
        if not logical_name:
            raise ValueError(f'Source filename profile has no identifier segment: {profile}')
        lexical_version = values.get('version')
        file_version = int(lexical_version) if lexical_version is not None else None
        if file_version is not None and file_version < 1:
            raise ValueError(f'File version must be positive: {request.path}')
        if explicit_version is not None and (not isinstance(explicit_version, int) or explicit_version < 1):
            raise ValueError(f'Declared schema version must be positive: {request.path}')
        if file_version is not None and explicit_version is not None and file_version != explicit_version:
            raise ValueError(f'Schema version {explicit_version} disagrees with filename version {file_version}: {request.path}')
        return AIcdParsedVersionedName(logical_name, explicit_version if explicit_version is not None else file_version)
