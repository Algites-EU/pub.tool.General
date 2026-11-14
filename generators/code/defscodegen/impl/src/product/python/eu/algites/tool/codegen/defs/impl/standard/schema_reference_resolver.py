"""Offline-first HTTPS reference resolver for canonical Defs Codegen.

The original public URI is always retained as the schema's identity. Local
copies and cache entries are storage optimizations, never URI rewrites. The
resolver does not synthesize or publish a DataObject for a referenced schema.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from typing import Callable
from urllib.parse import urldefrag, urlsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

_XS = '{http://www.w3.org/2001/XMLSchema}'
_SUFFIXES = ('.jsondef.schema.json', '.yamldef.schema.json', '.xsd')


@dataclass(frozen=True)
class ResolvedSchema:
    """Immutable public URI, bytes and physical origin for a resolved schema.

    Args:
        uri: Exact absolute URI without a fragment.
        content: Original schema bytes, unmodified by local/cache resolution.
        origin: Local source path, cache path or public URI used for retrieval.
    """
    uri: str
    content: bytes
    origin: str


class SchemaReferenceResolver:
    """Resolve public HTTPS schema identifiers from source, cache, or HTTPS.

    The caller supplies explicit trusted local source directories. On a cache
    miss the resolver downloads only HTTPS and enforces response-size and time
    limits; requests never follow a redirect to a non-HTTPS protocol. Cached
    schema bytes are validated again before use. No XML DTD processing occurs.
    """

    def __init__(self, source_roots: tuple[Path, ...] = (), cache_dir: Path | None = None,
                 *, max_bytes: int = 4 * 1024 * 1024, timeout: float = 8,
                 attempts: int = 2, fetch: Callable[[str, float], bytes] | None = None,
                 locations_file: Path | None = None):
        """Configure source lookup and bounded HTTPS transport.

        Args:
            source_roots: Declared checkout roots for offline schema lookup.
            cache_dir: Cache directory; defaults to a dedicated Modustro path.
            max_bytes: Maximum schema size, inclusive, in bytes.
            timeout: Timeout of each network attempt, in seconds.
            attempts: Maximum number of bounded HTTPS attempts.
            fetch: Optional injected transport for deterministic unit tests.
            locations_file: Optional strict URL-to-path property file. When set,
                every HTTPS lookup must be present in that file; no cache or
                network fallback is allowed.
        Raises:
            ValueError: Invalid resource limits or cache directory.
        """
        if max_bytes < 1 or timeout <= 0 or attempts < 1:
            raise ValueError('Invalid schema reference resource limits')
        self.source_roots = tuple(Path(p).resolve(strict=True) for p in source_roots)
        self.cache_dir = Path(cache_dir or Path.home() / '.modustro/cache/defs-schemas').expanduser()
        self.max_bytes = max_bytes
        self.timeout = timeout
        self.attempts = attempts
        self._fetch = fetch or self._download
        self._indexed: dict[str, Path] | None = None
        self._locations = self._load_locations(locations_file) if locations_file is not None else None

    @classmethod
    def _load_locations(cls, filename: Path) -> dict[str, Path]:
        """Read the documented ``URL=absolute-path`` properties subset.

        A literal HTTPS colon is not a key separator: only the first ``=``
        separates a record. Reject duplicate keys, invalid paths and broken
        mappings instead of silently reaching the live schema server.
        """
        location = Path(filename).expanduser().resolve(strict=True)
        if not location.is_file():
            raise ValueError(f'Not a schema locations property file: {location}')
        result: dict[str, Path] = {}
        for number, raw in enumerate(location.read_text(encoding='utf-8').splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith(('#', '!')):
                continue
            if '=' not in line:
                raise ValueError(f'{location}:{number}: expected HTTPS_URL=absolute_local_path')
            uri, value = (piece.strip() for piece in line.split('=', 1))
            if cls._validate_uri(uri) != uri:
                raise ValueError(f'{location}:{number}: schema location key must omit fragments')
            target = Path(value).expanduser()
            if not target.is_absolute() or not target.is_file() or target.is_symlink():
                raise ValueError(f'{location}:{number}: missing or unsafe local schema: {value}')
            if uri in result:
                raise ValueError(f'{location}:{number}: duplicate schema URL {uri}')
            result[uri] = target.resolve(strict=True)
        return result

    @staticmethod
    def _validate_uri(uri: str) -> str:
        """Accept only absolute HTTPS schema URIs without userinfo or query."""
        document, fragment = urldefrag(uri)
        parsed = urlsplit(document)
        if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
                or parsed.query or not any(parsed.path.endswith(s) for s in _SUFFIXES)):
            raise ValueError('Schema reference requires an absolute HTTPS schema URI: ' + uri)
        if fragment and not fragment.startswith('/'):
            raise ValueError('Unsupported non-JSON-Pointer schema fragment: ' + uri)
        return document

    @staticmethod
    def _schema_identity(blob: bytes, suffix: str) -> str:
        """Read the published JSON $id or XSD targetNamespace, without fetching imports."""
        if suffix == '.xsd':
            if b'<!DOCTYPE' in blob.upper() or b'<!ENTITY' in blob.upper():
                raise ValueError('DTD/entity declarations forbidden in XSD references')
            root = ET.fromstring(blob)
            if root.tag != _XS + 'schema':
                raise ValueError('Referenced document is not an XSD schema')
            return root.attrib.get('targetNamespace', '')
        doc = json.loads(blob.decode('utf-8'))
        if not isinstance(doc, dict) or not isinstance(doc.get('$id'), str):
            raise ValueError('Referenced JSON/YAMLDEFS schema requires an explicit $id')
        return doc['$id']

    @staticmethod
    def _suffix(uri: str) -> str:
        return next(s for s in _SUFFIXES if uri.endswith(s))

    def _verify(self, uri: str, data: bytes, namespace: str | None = None) -> bytes:
        if not data or len(data) > self.max_bytes:
            raise ValueError('Referenced schema is empty or exceeds configured limit: ' + uri)
        identity = self._schema_identity(data, self._suffix(uri))
        if uri.endswith('.xsd'):
            if namespace is not None and identity != namespace:
                raise ValueError(f'Imported XSD targetNamespace mismatch for {uri}: {identity!r} != {namespace!r}')
        elif identity != uri:
            raise ValueError(f'Referenced schema $id mismatch: requested {uri!r}, got {identity!r}')
        return data

    def _local_index(self) -> dict[str, Path]:
        if self._indexed is not None:
            return self._indexed
        result: dict[str, Path] = {}
        for root in self.source_roots:
            for source in sorted(root.rglob('*')):
                if (not source.is_file() or source.is_symlink() or
                        any(p in {'build', '.git', 'node_modules', '__pycache__', '.venv'}
                            for p in source.relative_to(root).parts)):
                    continue
                # A dependency may be a source checkout with src/product,
                # or the unpacked content of a JAR/wheel with schema resources
                # at its package root. In both cases only verified published
                # schema IDs are indexed; develop fixtures are excluded.
                relative_parts = source.relative_to(root).parts
                if any(relative_parts[i:i + 2] == ('src', 'develop')
                       for i in range(len(relative_parts) - 1)):
                    continue
                if not any(source.name.endswith(s) for s in _SUFFIXES):
                    continue
                if source.stat().st_size > self.max_bytes:
                    continue
                try:
                    blob = source.read_bytes()
                    if source.name.endswith('.xsd'):
                        # A published URI-shaped XSD namespace identifies the
                        # exact schema even after its src/product prefix is
                        # stripped during JAR packaging. For other namespaces,
                        # only the original checkout path supplies the URL.
                        declared = self._schema_identity(blob, '.xsd')
                        relative = source.as_posix()
                        if declared.startswith('https://') and declared.endswith('.xsd'):
                            uri = declared
                        elif '/src/product/xmldefs/' in relative:
                            uri = ('https://defs.dev.algites.eu/api/xmldefs/' +
                                   relative.split('/src/product/xmldefs/', 1)[1])
                        else:
                            continue
                        self._verify(uri, blob, namespace=declared)
                    else:
                        uri = self._schema_identity(blob, self._suffix(source.name))
                        if not uri.startswith('https://'):
                            continue
                        self._verify(uri, blob)
                except (ValueError, ET.ParseError, UnicodeError, OSError):
                    continue
                if uri in result and result[uri].read_bytes() != blob:
                    raise ValueError('Conflicting published local schema declarations for '
                                     + uri + ': ' + str(result[uri]) + ' and ' + str(source))
                result[uri] = source
        self._indexed = result
        return result

    def _download(self, uri: str, timeout: float) -> bytes:
        class HTTPSOnlyRedirect(__import__('urllib.request', fromlist=['HTTPRedirectHandler']).HTTPRedirectHandler):
            def redirect_request(self, request, fp, code, message, headers, newurl):
                if urlsplit(newurl).scheme != 'https':
                    raise ValueError('Schema redirect to non-HTTPS URL refused')
                return super().redirect_request(request, fp, code, message, headers, newurl)
        from urllib.request import build_opener
        opener = build_opener(HTTPSOnlyRedirect)
        with opener.open(Request(uri, headers={'Accept': 'application/schema+json, application/xml, */*'}),
                         timeout=timeout) as response:
            return response.read(self.max_bytes + 1)

    def resolve(self, uri: str, *, namespace: str | None = None) -> ResolvedSchema:
        """Return verified source bytes, resolving locally, cached, then remotely.

        Args:
            uri: Absolute HTTPS $id/schemaLocation, optional JSON Pointer suffix.
            namespace: For an XSD import, required targetNamespace if known.
        Returns:
            Schema bytes and exact provenance; fragment is not part of bytes.
        Raises:
            ValueError: Invalid URI, mismatched identity, or invalid schema.
            RuntimeError: HTTPS attempts exhausted or cache content invalid.
        """
        document = self._validate_uri(uri)
        if self._locations is not None:
            source = self._locations.get(document)
            if source is None:
                raise FileNotFoundError(
                    f'Schema URL {document} is absent from --schema-locations-property-file; '
                    'bootstrap must provide its declaring dependency (network fallback disabled)')
            return ResolvedSchema(document,
                                  self._verify(document, source.read_bytes(), namespace),
                                  str(source))
        local = self._local_index().get(document)
        if local is not None:
            return ResolvedSchema(document, self._verify(document, local.read_bytes(), namespace), str(local))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache = self.cache_dir / (hashlib.sha256(document.encode('utf-8')).hexdigest() + self._suffix(document))
        if cache.exists():
            if cache.is_symlink():
                raise ValueError('Refusing symlinked schema cache entry: ' + str(cache))
            return ResolvedSchema(document, self._verify(document, cache.read_bytes(), namespace), str(cache))
        last: Exception | None = None
        for number in range(self.attempts):
            try:
                payload = self._verify(document, self._fetch(document, self.timeout), namespace)
                with tempfile.NamedTemporaryFile(dir=self.cache_dir, delete=False) as stream:
                    staged = Path(stream.name)
                    stream.write(payload)
                try:
                    os.replace(staged, cache)
                finally:
                    staged.unlink(missing_ok=True)
                return ResolvedSchema(document, payload, document)
            except (OSError, TimeoutError) as error:
                last = error
                if number + 1 < self.attempts:
                    time.sleep(0.2)
        raise RuntimeError(f'Cannot resolve HTTPS schema {document} after {self.attempts} attempts: {last}') from last
