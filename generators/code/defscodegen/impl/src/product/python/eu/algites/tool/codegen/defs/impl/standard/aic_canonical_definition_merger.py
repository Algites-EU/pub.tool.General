from dataclasses import replace
from urllib.parse import urlsplit
from pathlib import Path


class AIcCanonicalDefinitionMerger:
    """Merge compatible representations while retaining documentation and source provenance."""

    @staticmethod
    def merge(definitions):
        """Reject differing contracts and combine documentation for one logical type."""
        definitions = tuple(definitions)
        if not definitions:
            raise ValueError("No canonical definitions to merge.")
        first = definitions[0]
        def constraints(prop, definition):
            """Ignore only a $schema constant pointing to this representation's own publication."""
            c = prop.data_type.constraints
            if prop.source_name != '$schema' or prop.data_type.kind.value != 'STRING' or len(c.enum_values) != 1:
                return c
            kind = definition.source_kind.value
            if kind not in ('jsondefs', 'yamldefs'):
                return c
            source = str(definition.source_resource).replace('\\', '/')
            marker = 'src/product/' + kind + '/'
            index = source.find(marker)
            if index < 0 or (index > 0 and source[index - 1] != '/'):
                return c
            resource = urlsplit(c.enum_values[0])
            if (resource.scheme == 'https' and resource.netloc and not resource.fragment
                    and resource.path.endswith('/api/' + kind + '/' + source[index + len(marker):])):
                return replace(c, enum_values=())
            return c

        AIcCanonicalDefinitionMerger.validate(definitions, documentation=False)
        if len(definitions) == 1:
            return first
        def documentation(values):
            return "\n\n".join(dict.fromkeys(value.strip() for value in values if value and value.strip())) or None
        properties = tuple(replace(prop, data_type=replace(prop.data_type, constraints=constraints(prop, first)), title=prop.title or next((candidate.title for definition in definitions
            for candidate in definition.data_type.properties if candidate.source_name == prop.source_name and candidate.title), None),
            description=documentation(candidate.description
            for definition in definitions for candidate in definition.data_type.properties if candidate.source_name == prop.source_name))
            for prop in first.data_type.properties)
        values = tuple(replace(value, title=value.title or next((candidate.title for definition in definitions
            for candidate in definition.enum_values if candidate.value == value.value and candidate.title), None),
            description=documentation(candidate.description
            for definition in definitions for candidate in definition.enum_values if candidate.value == value.value))
            for value in first.enum_values)
        description = documentation(definition.description for definition in definitions)
        origins = "; ".join(dict.fromkeys(f"{definition.source_kind.name}: {definition.identity} ({definition.source_resource})"
            for definition in definitions))
        return replace(first, data_type=first.data_type.with_properties(properties) if first.data_type.kind.name == "OBJECT" else first.data_type, enum_values=values,
            title=first.title or next((definition.title for definition in definitions if definition.title), None),
            description=(description + "\n\n" if description else "") + "Canonical representations: " + origins)

    @staticmethod
    def merge_strict(definitions, source_root=None):
        """Merge multi-format publications with structural and documentation parity."""
        definitions = tuple(definitions)
        AIcCanonicalDefinitionMerger.validate(definitions, documentation=True, source_root=source_root)
        return AIcCanonicalDefinitionMerger.merge(definitions)

    @staticmethod
    def validate(definitions, documentation=False, source_root=None):
        """Report every incompatible pair with source filenames and best-effort source lines."""
        definitions = tuple(definitions)
        if not definitions:
            raise ValueError('No canonical definitions to merge.')
        if len(definitions) == 1:
            return
        source_root = Path(source_root or '.').resolve()
        def path(definition):
            source = Path(str(definition.source_resource).split('#', 1)[0])
            return source.resolve() if source.is_absolute() else (source_root / source).resolve()

        def position(definition, field=None, member=None):
            location = path(definition)
            try:
                lines = location.read_text(encoding='utf-8').splitlines()
            except OSError:
                return str(location) + ' (line unknown)'
            xml = location.suffix == '.xsd'
            start = next((i for i, line in enumerate(lines) if
                ((f'name="{field}"' in line and '<xs:element' in line) if xml else (f'"{field}"' in line))), 0) if field else 0
            if xml and field is None:
                start = next((i for i, line in enumerate(lines) if '<xs:complexType' in line), 0)
            if member:
                component = member.split('/')[-1]
                xml_terms = {'description':'<xs:documentation', 'title':'<algdoc:title',
                    'minLength':'<xs:minLength', 'type':'type=', 'required':'minOccurs='}
                token = xml_terms.get(component, component) if xml else '"' + component + '"'
                for i in range(start, len(lines) if field is None else min(len(lines), start + 24)):
                    if token in lines[i]:
                        return f'{location}:{i+1}'
            return f'{location}:{start+1}'

        def self_schema(property, definition):
            if property is None or property.source_name != '$schema' or property.data_type.kind.value != 'STRING':
                return False
            vals = property.data_type.constraints.enum_values
            if len(vals) != 1:
                return False
            kind = definition.source_kind.value
            if kind not in ('yamldefs','jsondefs'):
                return False
            src = str(definition.source_resource).replace('\\','/')
            marker = 'src/product/' + kind + '/'
            if marker not in src:
                return False
            u = urlsplit(vals[0])
            return u.scheme == 'https' and bool(u.netloc) and not u.fragment and u.path.endswith('/api/' + kind + '/' + src.split(marker, 1)[1])

        def diff(a, b):
            found = []
            def compare(label, field, member, left, right):
                if left != right:
                    found.append((label, field, member, left, right))
            for key in ('logical_name','version'):
                compare(key, None, None, getattr(a,key), getattr(b,key))
            if documentation:
                for key in ('title','description'):
                    compare(key, None, key, getattr(a,key), getattr(b,key))
            ap = {p.source_name:p for p in a.data_type.properties}
            bp = {p.source_name:p for p in b.data_type.properties}
            # A source reference identifies a representation-specific resource, not
            # a distinct canonical target. Mirror Java AIcReference(): compare the
            # resolved logical target rather than .jsondef/.yamldef/.xsd paths.
            # Do not discard version or target kind: those are semantic differences.
            def reference_target(reference):
                if reference is None:
                    return None
                return (reference.logical_name, reference.version, reference.target_data_type)

            fields = ('presence','nullable')
            cfields = ('data_type','minimum','maximum','exclusive_minimum','exclusive_maximum',
                       'min_length','max_length','pattern','enum_values','min_items','max_items')
            def compare_data_type(prefix, field, left, right):
                """Compare the complete recursive shape, never its legacy one-level projection."""
                if left is None or right is None:
                    compare(prefix, field, 'dataType', left, right)
                    return
                compare(prefix + '.kind', field, 'dataType/kind', left.kind, right.kind)
                if left.kind != right.kind:
                    return
                if left.kind.name == 'REFERENCE':
                    compare(prefix + '.reference', field, 'dataType/reference',
                            reference_target(left.reference), reference_target(right.reference))
                elif left.kind.name == 'ARRAY':
                    compare_data_type(prefix + '.items', field, left.element_type, right.element_type)
                elif left.kind.name in ('ONE_OF', 'ANY_OF'):
                    compare(prefix + '.alternativeCount', field, 'dataType/alternatives',
                            len(left.alternatives), len(right.alternatives))
                    for index, (first, second) in enumerate(zip(left.alternatives, right.alternatives)):
                        compare_data_type(prefix + f'.alternatives[{index}]', field, first, second)
                elif left.kind.name == 'OBJECT':
                    left_props = {p.source_name: p for p in left.properties}
                    right_props = {p.source_name: p for p in right.properties}
                    for nested_name in sorted(left_props.keys() | right_props.keys()):
                        first, second = left_props.get(nested_name), right_props.get(nested_name)
                        key = prefix + '.properties[' + nested_name + ']'
                        if first is None or second is None:
                            compare(key + '.presence', field, 'dataType/properties/' + nested_name,
                                    bool(first), bool(second))
                            continue
                        for member in ('presence', 'nullable'):
                            compare(key + '.' + member, field, member,
                                    getattr(first, member), getattr(second, member))
                        if documentation:
                            for member in ('title', 'description'):
                                compare(key + '.' + member, field, member,
                                        getattr(first, member), getattr(second, member))
                        compare_data_type(key + '.dataType', field, first.data_type, second.data_type)
                # Scalar constraints on nested nodes are not represented by the old
                # valueKind/itemValueKind fields and must be compared separately.
                if left.kind.name not in ('OBJECT', 'REFERENCE'):
                    for member in cfields:
                        compare(prefix + '.constraints.' + member, field, 'dataType/constraints/' + member,
                                getattr(left.constraints, member), getattr(right.constraints, member))

            def scalar_array_shape(data_type):
                """True only when both formats can fully describe each nested scalar dimension."""
                if data_type.kind.name == 'ARRAY':
                    return scalar_array_shape(data_type.element_type)
                return data_type.kind.name in ('STRING', 'INTEGER', 'NUMBER', 'BOOLEAN', 'ANY', 'ENUM')

            def compare_structural_type(prefix, field, left, right):
                """Compare all nested kinds across XML/JSON/YAML without equating lexical facets."""
                compare(prefix + '.kind', field, 'dataType/kind', left.kind, right.kind)
                if left.kind != right.kind:
                    return
                if left.kind.name == 'ARRAY':
                    compare_structural_type(prefix + '.items', field, left.element_type, right.element_type)
                elif left.kind.name == 'REFERENCE':
                    compare(prefix + '.reference', field, 'dataType/reference',
                        reference_target(left.reference), reference_target(right.reference))
                elif left.kind.name in ('ONE_OF', 'ANY_OF'):
                    compare(prefix + '.alternativeCount', field, 'dataType/alternatives',
                        len(left.alternatives), len(right.alternatives))
                    for index, (first, second) in enumerate(zip(left.alternatives, right.alternatives)):
                        compare_structural_type(prefix + f'.alternatives[{index}]', field, first, second)
                elif left.kind.name == 'OBJECT':
                    first = {p.source_name: p for p in left.properties}
                    second = {p.source_name: p for p in right.properties}
                    for name in sorted(first.keys() | second.keys()):
                        x, y = first.get(name), second.get(name)
                        key = prefix + '.properties[' + name + ']'
                        if x is None or y is None:
                            compare(key + '.presence', field, 'dataType/properties/' + name,
                                x is not None, y is not None)
                        else:
                            compare(key + '.presence', field, 'presence', x.presence, y.presence)
                            compare(key + '.nullable', field, 'nullable', x.nullable, y.nullable)
                            compare_structural_type(key + '.dataType', field, x.data_type, y.data_type)

            if ((a.source_kind.value == 'xmldefs' and b.source_kind.value == 'xmldefs' and
                    (a.data_type.kind.name in ('ONE_OF', 'ANY_OF') or b.data_type.kind.name in ('ONE_OF', 'ANY_OF'))) or
                    (a.source_kind.value != 'xmldefs' and b.source_kind.value != 'xmldefs' and
                     (a.data_type.kind.name != 'OBJECT' or b.data_type.kind.name != 'OBJECT'))):
                compare_data_type('root.dataType', None, a.data_type, b.data_type)
            for name in sorted(ap.keys() | bp.keys()):
                x, y = ap.get(name), bp.get(name)
                if x is None and b.source_kind.value == 'xmldefs' and self_schema(y, b):
                    continue
                if y is None and a.source_kind.value == 'xmldefs' and self_schema(x, a):
                    continue
                if x is None and y is not None and a.source_kind.value == 'xmldefs' and self_schema(y,b):
                    continue
                if y is None and x is not None and b.source_kind.value == 'xmldefs' and self_schema(x,a):
                    continue
                if x is None or y is None:
                    compare(f"field '{name}' presence", name, None, 'present' if x else '<missing>', 'present' if y else '<missing>')
                    continue
                if a.source_kind.value == 'xmldefs' and b.source_kind.value == 'xmldefs':
                    compare(f"field '{name}'.xmlField", name, 'xmlField', x.xml_field, y.xml_field)
                for key in fields:
                    compare(f"field '{name}'.{key}", name, key, getattr(x,key), getattr(y,key))
                compare(f"field '{name}'.reference", name, '$ref',
                        reference_target(x.data_type.referenced_definition()), reference_target(y.data_type.referenced_definition()))
                # Structural child constraints are compared recursively below. For
                # the schema self-link, compare normalized constraints only.
                if self_schema(x, a) or self_schema(y, b):
                    cx = replace(x.data_type.constraints, enum_values=()) if self_schema(x, a) else x.data_type.constraints
                    cy = replace(y.data_type.constraints, enum_values=()) if self_schema(y, b) else y.data_type.constraints
                    for key in cfields:
                        compare(f"field '{name}'.constraints.{key}", name, key, getattr(cx,key),getattr(cy,key))
                def literal_oneof_matches_enum(choice, values):
                    if choice.kind.name != 'ONE_OF' or not values or len(choice.alternatives) != len(values):
                        return False
                    literals = []
                    for alternative in choice.alternatives:
                        if alternative.kind.name != 'ENUM' or len(alternative.constraints.enum_values) != 1:
                            return False
                        literals.extend(alternative.constraints.enum_values)
                    return len(set(literals)) == len(literals) and set(literals) == set(values)

                # The published JSON/YAML schema may spell a finite scalar enum
                # as enum + oneOf(const) solely to carry per-value documentation;
                # XSD expresses the same restriction with xs:enumeration facets.
                loc_literal_enum_projection = (x.data_type.kind == y.data_type.kind and
                    x.data_type.kind.name in ('STRING', 'INTEGER', 'NUMBER', 'BOOLEAN') and
                    x.data_type.constraints.enum_values == y.data_type.constraints.enum_values and
                    (literal_oneof_matches_enum(x.data_type, x.data_type.constraints.enum_values)
                     and y.data_type.kind.name in ('STRING', 'INTEGER', 'NUMBER', 'BOOLEAN') or
                     literal_oneof_matches_enum(y.data_type, y.data_type.constraints.enum_values)
                     and x.data_type.kind.name in ('STRING', 'INTEGER', 'NUMBER', 'BOOLEAN')))
                # The current XML frontend does not yet project all nested named
                # complexTypes into recursive DataType nodes. Keep the established
                # flat canonical comparison for XML until both readers can produce
                # equivalent structural models; never claim deep XML parity here.
                if (not loc_literal_enum_projection and a.source_kind.value != 'xmldefs'
                        and b.source_kind.value != 'xmldefs' and not (self_schema(x, a) and self_schema(y, b))):
                    compare_data_type(f"field '{name}'.dataType", name, x.data_type, y.data_type)
                if (not loc_literal_enum_projection and (a.source_kind.value == 'xmldefs') != (b.source_kind.value == 'xmldefs')
                        and scalar_array_shape(x.data_type) and scalar_array_shape(y.data_type)):
                    compare_structural_type(f"field '{name}'.dataType", name, x.data_type, y.data_type)
                if documentation:
                    for key in ('title','description'):
                        compare(f"field '{name}'.{key}", name, key, getattr(x,key), getattr(y,key))
            ae={e.value:e for e in a.enum_values};be={e.value:e for e in b.enum_values}
            for key in sorted(ae.keys() | be.keys()):
                x,y=ae.get(key),be.get(key)
                if x is None or y is None:
                    compare(f"enum '{key}' presence", None, 'enum', 'present' if x else '<missing>', 'present' if y else '<missing>')
                elif documentation:
                    for member in ('title','description'):
                        compare(f"enum '{key}'.{member}", None, member, getattr(x,member),getattr(y,member))
            return found

        checks=[]; failure=False
        for i, a in enumerate(definitions):
            for j in range(i+1,len(definitions)):
                b=definitions[j]; differences=diff(a,b)
                checks.append(f'  [{i+1}] {a.source_kind.name} vs [{j+1}] {b.source_kind.name}: ' +
                    ('INCONSISTENT' if differences else 'CONSISTENT'))
                if differences:
                    failure=True
                    for label,field,member,left,right in differences:
                        checks.append(f'    - {label}: [{i+1}] {left!r} ({position(a,field,member)}) vs '
                            f'[{j+1}] {right!r} ({position(b,field,member)})')
        if failure:
            files='\n'.join(f'  [{i+1}] {d.source_kind.name}: {position(d)}' for i,d in enumerate(definitions))
            raise ValueError(f'Incompatible canonical definitions ({len(definitions)} representations):\nSources:\n'
                +files+'\nPairwise comparison:\n'+'\n'.join(checks))
