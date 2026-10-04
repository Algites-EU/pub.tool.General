from __future__ import annotations

import xml.etree.ElementTree as ET

from eu.algites.tool.codegen.defs._support import _xsd_kind
from eu.algites.tool.codegen.defs.aic_definition_identity_resolver import AIcDefinitionIdentityResolver
from eu.algites.tool.codegen.defs.aicd_canonical_definition import AIcdCanonicalDefinition
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.aicd_definition_reference import AIcdDefinitionReference
from eu.algites.tool.codegen.defs.aicd_enum_value_definition import AIcdEnumValueDefinition
from eu.algites.tool.codegen.defs.aicd_property_definition import AIcdPropertyDefinition
from eu.algites.tool.codegen.defs.ain_definition_kind import AInDefinitionKind
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.ain_value_kind import AInValueKind


class AIcXmlDefsFrontend:
    """Loads canonical definitions expressed as XML Schema definitions."""

    source_kind = AInDefinitionSourceKind.XMLDEFS
    _xs = "{http://www.w3.org/2001/XMLSchema}"

    def __init__(self) -> None:
        """Create the frontend with the default definition-identity resolver."""
        self._identities = AIcDefinitionIdentityResolver()

    def load(self, request: AIcdDefinitionLoadRequest) -> AIcdCanonicalDefinition:
        """Load one XSD resource into the format-neutral canonical-definition model."""
        root = ET.parse(request.path).getroot()
        explicit = int(root.attrib["version"]) if root.attrib.get("version", "").isdigit() else None
        parsed = self._identities.from_file(request, explicit)
        identity = root.attrib.get("targetNamespace") or parsed.logical_name
        schema_description = self._documentation(root)
        simple = root.find(f"{self._xs}simpleType")
        if simple is not None:
            values = tuple(
                AIcdEnumValueDefinition(node.attrib["value"], self._documentation(node))
                for node in simple.findall(f".//{self._xs}enumeration")
                if "value" in node.attrib
            )
            if values:
                return AIcdCanonicalDefinition(
                    identity,
                    parsed.version,
                    parsed.logical_name,
                    AInDefinitionKind.ENUM,
                    self.source_kind,
                    str(request.path),
                    self._documentation(simple) or schema_description,
                    enum_values=values,
                )
        complex_type = root.find(f".//{self._xs}complexType")
        if complex_type is not None:
            props = []
            for node in complex_type.findall(f".//{self._xs}element"):
                xsd_type = node.attrib.get("type", "")
                value_kind = _xsd_kind(xsd_type)
                repeated = node.attrib.get("maxOccurs", "1") != "1"
                props.append(
                    AIcdPropertyDefinition(
                        node.attrib.get("name", "Value"),
                        AInValueKind.ARRAY if repeated else value_kind,
                        node.attrib.get("minOccurs") != "0",
                        node.attrib.get("nillable") == "true",
                        item_value_kind=value_kind if repeated else None,
                        description=self._documentation(node),
                    )
                )
            return AIcdCanonicalDefinition(
                identity,
                parsed.version,
                parsed.logical_name,
                AInDefinitionKind.OBJECT,
                self.source_kind,
                str(request.path),
                self._documentation(complex_type) or schema_description,
                properties=tuple(props),
            )
        return AIcdCanonicalDefinition(
            identity,
            parsed.version,
            parsed.logical_name,
            AInDefinitionKind.SCALAR,
            self.source_kind,
            str(request.path),
            schema_description,
        )

    @classmethod
    def _documentation(cls, element: ET.Element) -> str | None:
        """Return normalized XSD documentation attached directly to an element."""
        annotation = element.find(f"{cls._xs}annotation")
        if annotation is None:
            return None
        documentation = annotation.find(f"{cls._xs}documentation")
        if documentation is None or documentation.text is None:
            return None
        value = " ".join(documentation.text.split())
        return value or None
