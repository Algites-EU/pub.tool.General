"""Deterministically layer packaged, classpath and invocation settings for one Codegen."""
from __future__ import annotations

from eu.algites.tool.codegen.common.aix_codegen_validation_exception import AIxCodegenValidationException
import importlib.resources
from pathlib import Path
import sys


def expand(arguments: list[str], generator: str, technology: str, package: str) -> list[str]:
    """Merge settings by complete qualified option name before parsing values.

    Args:
        arguments: Explicit CLI options, with at most one settings-file selector.
        generator: Generator identity, such as defscodegen or sdocodegen.
        technology: Native target language, java or python.
        package: Implementation resource package, optionally ending in .old.
            Built-in defaults follow this package; public profile overlays use
            the unsuffixed package and retain their external resource identity.

    Returns:
        Effective CLI options after defaults, profiles, invocation file and
        explicit options have been merged; empty assignments remove a value.

    Raises:
        FileNotFoundError: If required defaults or the invocation file are absent.
        OSError: If a settings resource cannot be read.
        AIxCodegenValidationException: If options or settings content are invalid.
    """
    file_options = [value.partition('=')[2] for value in arguments if value.startswith('--settings-file=')]
    if len(file_options) > 1:
        raise AIxCodegenValidationException('Only one --settings-file is permitted', 'Check the configured source, output and artifact paths; ensure inputs exist, paths stay inside their allowed roots and required dependencies are present.')
    remainder = [value for value in arguments if not value.startswith('--settings-file=')]
    name = f'{generator}-{technology}-default.settings'
    base = Path(f'generators/code/{generator}/intf/src/product/config/eu/algites/tool/codegen') / package.replace('.', '/')
    def resource_text(name: str, required: bool) -> str | None:
        resource_path = Path('eu/algites/tool/codegen') / package.replace('.', '/') / name
        try:
            candidate = importlib.resources.files(f'eu.algites.tool.codegen.{package}').joinpath(name)
            if candidate.is_file():
                return candidate.read_text(encoding='utf-8')
        except (ModuleNotFoundError, FileNotFoundError, TypeError):
            pass
        for prefix in sys.path:
            candidate = Path(prefix) / resource_path
            if candidate.is_file():
                return candidate.read_text(encoding='utf-8')
        candidate = base / name
        if candidate.is_file():
            return candidate.read_text(encoding='utf-8')
        if required:
            raise FileNotFoundError(f'Missing packaged Codegen defaults: {name}')
        return None

    sources: list[tuple[str, str]] = [(name, resource_text(name, True) or '')]
    override_name = f'{generator}-{technology}.settings'
    # Profile resource identities stay public when implementation defaults move.
    profile_package = package.removesuffix('.old')
    profile_base = Path(f'generators/code/{generator}/intf/src/product/config/eu/algites/tool/codegen') / profile_package.replace('.', '/')
    override_path = Path('eu/algites/tool/codegen') / profile_package.replace('.', '/') / override_name
    seen_files: set[Path] = set()
    overrides: list[tuple[str, str]] = []

    def append_file(candidate: Path, *, package_resource: bool = False) -> None:
        if candidate.is_file():
            resolved = candidate.resolve()
            if package_resource or resolved not in seen_files:
                if not package_resource:
                    seen_files.add(resolved)
                overrides.append((str(resolved), candidate.read_text(encoding='utf-8')))

    try:
        packaged = importlib.resources.files(f'eu.algites.tool.codegen.{profile_package}').joinpath(override_name)
        if packaged.is_file():
            # Importlib can use non-filesystem Traversables (e.g. ZIP resources).
            # A physical sys.path copy of the same file must only be read once.
            try:
                append_file(Path(packaged), package_resource=True)
            except TypeError:
                overrides.append((f'importlib.resources:{override_name}',
                                  packaged.read_text(encoding='utf-8')))
    except (ModuleNotFoundError, FileNotFoundError, TypeError):
        pass
    append_file(profile_base / override_name)
    # sys.path[0] has the highest import precedence. Apply its files last,
    # so every discovered file contributes without losing that priority.
    for prefix in reversed(sys.path):
        directory = Path(prefix or '.')
        append_file(directory / override_path)
        append_file(directory / override_name)
    invocation = None
    if file_options:
        path = Path(file_options[0])
        invocation = (str(path), path.read_text(encoding='utf-8'))

    # Profile resources may be installed simultaneously (Algites, Standard
    # Prefix and Standard Postfix).  They are *alternatives*, not successive
    # configuration layers.  In particular, combining a Standard Prefix source
    # filename catalog with an explicitly selected Algites catalog would leave
    # multiple conventions matching the same schema filename.
    #
    # Choose a single profile family using the caller's qualified profile IDs.
    # The selection is driven by settings data, never by a vendor-specific path
    # or by arbitrary sys.path precedence. Within the selected family, multiple
    # identical resource copies may still layer as before.
    def profile_selections(content: str) -> dict[str, str]:
        """Extract explicitly named profile identities from CLI/settings text.

        Naming catalog file paths are deliberately excluded: their resources
        can be shared, whereas profile IDs determine the intended family.
        """
        keys = (
            '--input-schema-naming-convention:',
            '--common-codegen-naming-convention:',
            '--defs-codegen-naming-convention:',
            '--sdo-codegen-naming-convention:',
            '--output-interface-technology-naming-convention:',
            '--output-enum-technology-naming-convention:',
            '--input-technology-naming-convention:',
            '--output-technology-naming-convention:',
        )
        selected: dict[str, str] = {}
        for line in content.splitlines():
            token = line.strip()
            if token.startswith(keys) and '=' in token:
                key, value = token.split('=', 1)
                if value:
                    selected[key] = value
        return selected

    requested = profile_selections('\n'.join(remainder))
    if file_options:
        requested.update(profile_selections(invocation[1]))

    families: dict[tuple[tuple[str, str], ...], list[tuple[str, str]]] = {}
    for candidate in overrides:
        signature = tuple(sorted(profile_selections(candidate[1]).items()))
        if signature:
            families.setdefault(signature, []).append(candidate)
    if families:
        if requested:
            # Caller-specific overrides (for example a handwritten input
            # contract) may intentionally use an ID not present in *any*
            # installed overlay. Those custom IDs must not invalidate an
            # otherwise unambiguous installed family. Conversely, referring
            # to IDs belonging to two different installed families is an error.
            matching = [signature for signature in families
                        if any(requested.get(key) == value for key, value in signature)
                        and not any(key in requested and requested[key] != value
                                    and not key.startswith('--input-technology-naming-convention:')
                                    for key, value in signature)]
            if not matching and any(any(requested.get(key) == value
                                        for key, value in signature)
                                    for signature in families):
                raise AIxCodegenValidationException(
                    'Conflicting naming profile selection: no single installed profile '
                    'matches the explicitly selected profile IDs',
                    'Select one Common/Defs/SDO naming family. A custom input '
                    'interface convention may override the selected family.')
            if len(matching) > 1:
                raise AIxCodegenValidationException(
                    'Conflicting naming profile selection: multiple installed '
                    'families match the explicitly selected profile IDs',
                    'Choose only one installed naming profile family.')
        else:
            matching = list(families)
        if len(matching) > 1:
            origins = sorted({source for signature in matching
                              for source, _ in families[signature]})
            raise AIxCodegenValidationException(
                'Ambiguous Codegen naming profile overlays: ' + ', '.join(origins),
                'Select one profile family explicitly with qualified naming '
                'profile arguments or --settings-file; profiles are alternatives.')
        selected = set(families[matching[0]]) if matching else set()
    else:
        selected = set()
    # Unqualified settings are independent additions, not competing profile
    # families. Keep their original ordering (including sys.path precedence).
    # Explicit profile families are mutually exclusive, but ordinary settings
    # files from multiple source roots must accumulate.
    sources.extend(candidate for candidate in overrides
                   if not profile_selections(candidate[1]) or candidate in selected)
    # Invocation settings and direct CLI arguments have precedence over all
    # packaged and classpath defaults; no profile may shadow explicit settings.
    if invocation is not None:
        sources.append(invocation)
    # Do not silently append an unrelated packaged profile. This also allows
    # calls with fully custom profiles and explicit catalogs.

    # Qualified option names are the stable configuration identity. Do not
    # translate them into the obsolete kind:value parser representation.
    merged: dict[str, str] = {}

    def push(token: str) -> None:
        if token in {'--check', '--clean-only', '--allow-unversioned-schemas'}:
            token += '=true'
        if not token.startswith('--') or '=' not in token:
            raise AIxCodegenValidationException(f'Invalid settings argument: {token}', 'Check the qualified CLI option and the active layered settings. Supply the required value, role and technology and remove conflicting options.')
        key, value = token.split('=', 1)
        if key == '--settings-file':
            raise AIxCodegenValidationException('Nested settings-file is not supported', 'Check the configured source, output and artifact paths; ensure inputs exist, paths stay inside their allowed roots and required dependencies are present.')
        if value == '':
            merged.pop(key, None)
        else:
            merged[key] = value

    for source, content in sources:
        for no, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            if any(ch.isspace() for ch in stripped):
                raise AIxCodegenValidationException(f'Malformed settings at {source}:{no}: {line}', 'Check the configured source, output and artifact paths; ensure inputs exist, paths stay inside their allowed roots and required dependencies are present.')
            push(stripped)
    for arg in remainder:
        push(arg)

    expanded: list[str] = []
    for key, value in merged.items():
        if key in {'--check', '--clean-only', '--allow-unversioned-schemas'}:
            if value.lower() not in {'true', 'false'}:
                raise AIxCodegenValidationException(f'Expected boolean for {key}: {value}', 'Check the collection shape, entry type, key definition and key field paths. Use a complete, resolvable key or declare the intended virtual map property key explicitly.')
            if value.lower() == 'true':
                expanded.append(key)
        else:
            expanded.append(f'{key}={value}')
    return expanded
