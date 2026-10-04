from dataclasses import replace


class AIcCanonicalDefinitionMerger:
    """Merge compatible representations while retaining documentation and source provenance."""

    @staticmethod
    def merge(definitions):
        """Reject differing contracts and combine documentation for one logical type."""
        definitions = tuple(definitions)
        if not definitions:
            raise ValueError("No canonical definitions to merge.")
        first = definitions[0]
        def shape(definition):
            return (definition.logical_name, definition.version, definition.kind,
                sorted((prop.source_name, prop.value_kind, prop.required, prop.nullable,
                    prop.item_value_kind, None if prop.reference is None else
                    (prop.reference.logical_name, prop.reference.version, prop.reference.target_kind), prop.constraints, prop.item_constraints)
                    for prop in definition.properties),
                tuple(value.value for value in definition.enum_values))
        for definition in definitions:
            if shape(first) != shape(definition):
                raise ValueError(f"Incompatible canonical representations: {first.source_resource} and {definition.source_resource}")
        if len(definitions) == 1:
            return first
        def documentation(values):
            return "\n\n".join(dict.fromkeys(value.strip() for value in values if value and value.strip())) or None
        properties = tuple(replace(prop, description=documentation(candidate.description
            for definition in definitions for candidate in definition.properties if candidate.source_name == prop.source_name))
            for prop in first.properties)
        values = tuple(replace(value, description=documentation(candidate.description
            for definition in definitions for candidate in definition.enum_values if candidate.value == value.value))
            for value in first.enum_values)
        description = documentation(definition.description for definition in definitions)
        origins = "; ".join(dict.fromkeys(f"{definition.source_kind.name}: {definition.identity} ({definition.source_resource})"
            for definition in definitions))
        return replace(first, properties=properties, enum_values=values,
            description=(description + "\n\n" if description else "") + "Canonical representations: " + origins)
