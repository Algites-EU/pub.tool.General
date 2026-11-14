"""Read-only, no-classloading index of compiled Java Defs interface metadata.

Class files are inspected as data. Only class and runtime annotation metadata are
needed; no dependency classes are loaded and no arbitrary class initializer runs.

@author linhart1
"""
from __future__ import annotations

from pathlib import Path
import struct


class _Reader:
    """Bounds-checked JVM class-file reader."""

    def __init__(self, data: bytes, source: Path):
        self.data, self.source, self.pos = data, source, 0

    def take(self, size: int) -> bytes:
        if size < 0 or self.pos + size > len(self.data):
            raise ValueError(f'{self.source}: truncated class file at byte {self.pos}')
        result = self.data[self.pos:self.pos + size]
        self.pos += size
        return result

    def u1(self):
        return self.take(1)[0]

    def u2(self):
        return struct.unpack('>H', self.take(2))[0]

    def u4(self):
        return struct.unpack('>I', self.take(4))[0]


def read_class_contracts(path: Path) -> tuple[tuple[str, str, frozenset[str]], ...]:
    """Return (public schema identity, fully-qualified interface, direct parents).

    Ignore compiled SDO contracts and unrelated classes. Reject malformed
    class files rather than silently accepting a possibly misleading identity.
    """
    if path.stat().st_size > 8_000_000:
        raise ValueError(f'{path}: oversized class-file metadata')
    reader = _Reader(path.read_bytes(), path)
    if reader.u4() != 0xCAFEBABE:
        raise ValueError(f'{path}: invalid Java class-file magic')
    reader.u2(); reader.u2()  # minor and major version
    count = reader.u2()
    cp: list[tuple[int, object] | None] = [None] * count
    index = 1
    while index < count:
        tag = reader.u1()
        if tag == 1:
            length = reader.u2()
            cp[index] = (tag, reader.take(length).decode('utf-8', errors='replace'))
        elif tag in (3, 4):
            cp[index] = (tag, reader.u4())
        elif tag in (5, 6):
            reader.take(8)
            index += 1
        elif tag in (7, 8, 16, 19, 20):
            cp[index] = (tag, reader.u2())
        elif tag in (9, 10, 11, 12, 17, 18):
            reader.take(4)
        elif tag == 15:
            reader.take(3)
        else:
            raise ValueError(f'{path}: unsupported JVM constant-pool tag {tag}')
        index += 1

    def utf8(i):
        value = cp[i] if 0 < i < len(cp) else None
        if value is None or value[0] != 1:
            raise ValueError(f'{path}: invalid JVM UTF8 constant {i}')
        return value[1]

    def class_name(i):
        value = cp[i] if 0 < i < len(cp) else None
        if value is None or value[0] != 7:
            raise ValueError(f'{path}: invalid JVM class constant {i}')
        return utf8(value[1]).replace('/', '.')

    def element_value():
        tag = chr(reader.u1())
        if tag in 'BCDFIJSZs':
            i = reader.u2()
            if tag == 's':
                return utf8(i)
            return cp[i][1] if cp[i] else None
        if tag == 'e':
            reader.u2()
            return utf8(reader.u2())
        if tag == 'c':
            return utf8(reader.u2())
        if tag == '@':
            return annotation()[1]
        if tag == '[':
            return [element_value() for _ in range(reader.u2())]
        raise ValueError(f'{path}: invalid annotation element tag {tag}')

    def annotation():
        typ = utf8(reader.u2())
        return typ, {utf8(reader.u2()): element_value() for _ in range(reader.u2())}

    def skip_attributes():
        for _ in range(reader.u2()):
            reader.u2()
            reader.take(reader.u4())

    access = reader.u2()
    this_class = class_name(reader.u2())
    reader.u2()  # superclass
    parents = frozenset(class_name(reader.u2()) for _ in range(reader.u2()))
    for _ in range(reader.u2()):
        reader.take(6)
        skip_attributes()
    mutations = False
    for _ in range(reader.u2()):
        reader.u2()
        name = utf8(reader.u2())
        reader.u2()
        if (name.startswith('set') and len(name) > 3 and name[3].isupper()) or name.startswith('_unset'):
            mutations = True
        skip_attributes()
    attributes: dict[str, dict] = {}
    for _ in range(reader.u2()):
        name = utf8(reader.u2())
        length = reader.u4()
        end = reader.pos + length
        if name in ('RuntimeVisibleAnnotations', 'RuntimeInvisibleAnnotations'):
            for _ in range(reader.u2()):
                descriptor, values = annotation()
                attributes[descriptor.rsplit('/', 1)[-1].removesuffix(';').removeprefix('L')] = values
            if reader.pos != end:
                raise ValueError(f'{path}: unexpected annotation-attribute length')
        else:
            reader.take(length)
    if reader.pos != len(reader.data):
        raise ValueError(f'{path}: unexpected trailing class-file data')
    if not access & 0x0200 or mutations or any(name.endswith('.AIiSmartDataObject') for name in parents):
        return ()
    # One unified read-only interface can provide independent identities for
    # all three formats. Never select only XML because its annotation appears.
    identities: set[str] = set()
    xml = attributes.get('AIaDataObjectXmlSchema') or attributes.get('AIaXmlDataObject')
    if xml and xml.get('definitionKind', 'TYPE') == 'TYPE':
        local = xml.get('namespaceLocalName', '')
        if local:
            identities.add('{' + str(xml.get('namespace', '')) + '}' + str(local))
    for names in (('AIaDataObjectJsonSchema', 'AIaJsonDataObject'),
                  ('AIaYamlDataObject',)):
        form = next((attributes[n] for n in names if n in attributes), None)
        if form and form.get('schemaId') and str(form.get('schemaUrl', '')).startswith('https://'):
            identities.add(str(form['schemaUrl']))
    return tuple((identity, this_class, parents) for identity in sorted(identities))


def read_class_contract(path: Path) -> tuple[str, str, frozenset[str]] | None:
    """Legacy single-identity adapter; new indexers use read_class_contracts."""
    contracts = read_class_contracts(path)
    return contracts[0] if contracts else None
