"""Generate one sealed Java choice and stable value-record variants per alternative."""
from __future__ import annotations

from eu.algites.tool.codegen.common.aix_codegen_validation_exception import AIxCodegenValidationException
import hashlib
import json
import re
from collections import Counter
from eu.algites.tool.codegen.defs.ain_data_type_kind import AInDataTypeKind
from eu.algites.tool.codegen.defs.ain_defs_name_role import AInDefsNameRole
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.aicd_canonical_definition import AIcdCanonicalDefinition
from eu.algites.tool.codegen.defs.aicd_code_generation_request import AIcdCodeGenerationRequest
from eu.algites.tool.codegen.defs.aicd_generated_source import AIcdGeneratedSource
from eu.algites.tool.codegen.defs.aicd_generated_type_identity import AIcdGeneratedTypeIdentity
from .aic_generation_names import AIcGenerationNames


def json_quote(value: str) -> str:
    """Render an escaped Java string literal for the generated annotation."""
    return json.dumps(value, ensure_ascii=False)


def choice_branch_name(model, alternative, index, kind):
    """Derive a stable, convention-compatible branch identity.

    Named JSON/YAML choice alternatives are structural properties, so their
    identity must not depend on the order of the properties. XML alternatives
    likewise carry an explicit XML field name. Unnamed historical choices
    retain an indexed fallback, independently of the owning schema's name.

    Args:
        model: Owning canonical definition with a declared logical name.
        alternative: One canonical variant, possibly with named properties.
        index: Zero-based index used only if no alternative name is available.
        kind: Semantic choice kind, oneOf or anyOf.

    Returns:
        A lower-kebab identifier suitable for the selected naming conventions.

    Raises:
        AIxCodegenValidationException: If no valid identifier can be formed.
    """
    def kebab(text):
        value = re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', str(text))
        value = re.sub(r'[^A-Za-z0-9]+', '-', value).strip('-').lower()
        return value

    base = kebab(model.logical_name)
    named = (alternative.properties[0].source_name
             if alternative.kind is AInDataTypeKind.OBJECT and len(alternative.properties) == 1
             else None)
    suffix = kebab(named) if named else ('one-of-' if kind == 'oneOf' else 'any-of-') + str(index)
    result = base + '-' + suffix
    if not base or not suffix or not base[0].isalpha():
        raise AIxCodegenValidationException('Invalid named Choice alternative',
                                            'Give every Choice alternative a valid structural property name.')
    return result


class AIcClosedChoiceGenerator:
    """Generate a contract and separately importable records in its owning package."""

    def __init__(self):
        self.names = AIcGenerationNames()

    def generate(self, request):
        model = request.definition
        choice = model.data_type
        if choice.kind not in (AInDataTypeKind.ONE_OF, AInDataTypeKind.ANY_OF):
            raise AIxCodegenValidationException('Definition is not a closed choice', 'Check that each choice/enum branch is declared once with a supported, resolvable type and that any required choice annotation is present.')
        kind = 'oneOf' if choice.kind is AInDataTypeKind.ONE_OF else 'anyOf'
        target = request.target
        cls = self.names.type_name(model, request.naming_profile, AInDefsNameRole.INTERFACE_TYPE)
        stem = self.names.file_stem(model, request.naming_profile, AInDefsNameRole.INTERFACE_TYPE_FILE_STEM)
        ext = '.java' if target is AInCodeGenerationTarget.JAVA else '.py'
        path_prefix = request.package_name.replace('.', '/') + '/'
        variants = []
        resolved = []
        for index, alternative in enumerate(choice.alternatives):
            reference = alternative.reference
            if alternative.kind is AInDataTypeKind.REFERENCE and reference is not None:
                label = reference.logical_name
                role = AInDefsNameRole.ENUM_TYPE if reference.targets_enum else AInDefsNameRole.INTERFACE_TYPE
                type_name = self.names.render(reference.logical_name, reference.version, request.naming_profile, role)
                file_role = AInDefsNameRole.ENUM_TYPE_FILE_STEM if role is AInDefsNameRole.ENUM_TYPE else AInDefsNameRole.INTERFACE_TYPE_FILE_STEM
                file_stem = self.names.render(reference.logical_name, reference.version, request.naming_profile, file_role)
                identity = reference.identity
            elif alternative.kind in (AInDataTypeKind.STRING, AInDataTypeKind.INTEGER,
                    AInDataTypeKind.NUMBER, AInDataTypeKind.BOOLEAN, AInDataTypeKind.ANY):
                scalar = {AInDataTypeKind.STRING: ('String', 'str'),
                    AInDataTypeKind.INTEGER: ('Long', 'int'),
                    AInDataTypeKind.NUMBER: ('java.math.BigDecimal', 'Decimal'),
                    AInDataTypeKind.BOOLEAN: ('Boolean', 'bool'),
                    AInDataTypeKind.ANY: ('Object', 'object')}
                types = scalar[alternative.kind]
                type_name = types[0] if target is AInCodeGenerationTarget.JAVA else types[1]
                label, file_stem = f'Alternative{index + 1}', None
                identity = model.identity + '#/' + kind + '/' + str(index)
            elif alternative.kind is AInDataTypeKind.ARRAY:
                item_type = {
                    AInDataTypeKind.STRING: ('String', 'str'),
                    AInDataTypeKind.INTEGER: ('Long', 'int'),
                    AInDataTypeKind.NUMBER: ('java.math.BigDecimal', 'Decimal'),
                    AInDataTypeKind.BOOLEAN: ('Boolean', 'bool'),
                }.get(alternative.element_type.kind)
                if item_type is None:
                    raise AIxCodegenValidationException('Closed choice array requires a supported scalar item kind', 'Check that each choice/enum branch is declared once with a supported, resolvable type and that any required choice annotation is present.')
                label, file_stem = f'Alternative{index + 1}', None
                type_name = ('java.util.List<' + item_type[0] + '>' if target is AInCodeGenerationTarget.JAVA
                    else 'list[' + item_type[1] + ']')
                identity = model.identity + '#/' + kind + '/' + str(index)
            elif alternative.kind is AInDataTypeKind.OBJECT:
                # Batch discovery emits each inline branch as a separate contract.
                label = (alternative.properties[0].source_name if len(alternative.properties) == 1
                         else f'Alternative{index + 1}')
                name = choice_branch_name(model, alternative, index, kind)
                type_name = self.names.render(name, model.version, request.naming_profile, AInDefsNameRole.INTERFACE_TYPE)
                file_stem = self.names.render(name, model.version, request.naming_profile, AInDefsNameRole.INTERFACE_TYPE_FILE_STEM)
                identity = model.identity + '#/' + kind + '/' + str(index)
            else:
                raise AIxCodegenValidationException(f'Closed choice variant {index} requires a named or inline object type; got {alternative.kind.value}', 'Check that each choice/enum branch is declared once with a supported, resolvable type and that any required choice annotation is present.')
            resolved.append((label, type_name, file_stem, identity))
        if len({identity for _, _, _, identity in resolved}) != len(resolved):
            raise AIxCodegenValidationException('Closed choice contains repeated alternatives', 'Check that each choice/enum branch is declared once with a supported, resolvable type and that any required choice annotation is present.')
        counts = Counter(label.lower() for label, *_ in resolved)
        for label, typ, file, identity in resolved:
            short = 'h' + hashlib.sha256(identity.encode()).hexdigest()[:8] if counts[label.lower()] > 1 else ''
            # Suffix ordering stays outside the canonical logical identifier.
            fragment = re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', label)
            fragment = re.sub(r'[^A-Za-z0-9]+', '-', fragment).strip('-').lower()
            if not fragment:
                raise AIxCodegenValidationException('Empty named Choice alternative',
                    'Declare a nonempty structural name for every choice variant.')
            if short:
                fragment += '-' + short
            # The selected-variant record and the payload object are distinct
            # public types. A separated role suffix prevents case-insensitive
            # collisions in Python modules and Java class names.
            logical = model.logical_name + '-selected-' + fragment
            wrapper = self.names.render(logical, model.version, request.naming_profile, AInDefsNameRole.DATA_TYPE)
            wrapper_file = self.names.render(logical, model.version, request.naming_profile, AInDefsNameRole.DATA_TYPE_FILE_STEM)
            variants.append((wrapper, wrapper_file, typ, file))
        if target is AInCodeGenerationTarget.JAVA:
            xml_annotation = ''
            if request.xml_type_qname and request.contract_role != 'common':
                namespace, local = request.xml_type_qname[1:].split('}', 1)
                xml_annotation = ('@eu.algites.lib.data.dataobject.xmldefs.AIaXmlDataObject('
                    'definitionKind = eu.algites.lib.data.dataobject.xmldefs.AInXmlObjectDefinitionKind.TYPE, '
                    f'namespace = {json_quote(namespace)}, namespaceLocalName = {json_quote(local)})\n')
            main = ('package ' + request.package_name + ';\n\n'
                '/** Generated closed ' + kind + ' schema contract.\n * @author linhart1\n */\n'
                + xml_annotation
                + ('public interface ' if request.contract_role == 'common' else 'public sealed interface ') + cls
                + (' extends eu.algites.lib.data.dataobject.xmldefs.AIiXmlDataObject' if (model.source_kind is AInDefinitionSourceKind.XMLDEFS and request.contract_role != 'common') else '')
                + ('' if request.contract_role == 'common' else ' permits ' + ', '.join(wrapper for wrapper, *_ in variants)) + ' {\n}\n')
        else:
            xml_import = ('from eu.algites.lib.data.dataobject.xmldefs.aii_xml_data_object import AIiXmlDataObject\n'
                if model.source_kind is AInDefinitionSourceKind.XMLDEFS and request.contract_role != 'common' else '')
            xml_annotation = ''
            if request.xml_type_qname and request.contract_role != 'common':
                namespace, local = request.xml_type_qname[1:].split('}', 1)
                xml_import += ('from eu.algites.lib.data.dataobject.xmldefs.aia_xml_data_object import AIaXmlDataObject\n'
                    'from eu.algites.lib.data.dataobject.xmldefs.ain_xml_object_definition_kind import AInXmlObjectDefinitionKind\n')
                xml_annotation = ('    __xml_data_object__ = AIaXmlDataObject('
                    'definition_kind=AInXmlObjectDefinitionKind.TYPE, '
                    f'namespace={namespace!r}, namespace_local_name={local!r})\n')
            main = ('from __future__ import annotations\n' + xml_import + '\n'
                'class ' + cls + ('(AIiXmlDataObject)' if model.source_kind is AInDefinitionSourceKind.XMLDEFS else '') + ':\n'
                + xml_annotation
                + '    """Generated closed ' + kind + ' choice; use a declared value wrapper.\n\n    Author: linhart1.\n    """\n'
                + '    __closed_choice_mode__ = ' + repr(kind) + '\n'
                + '    __slots__ = ()\n')
        primary = AIcdGeneratedSource(cls, path_prefix + stem + ext, main,
            (AIcdGeneratedTypeIdentity.from_request(request, cls, path_prefix + stem + ext,
                AInDefsNameRole.INTERFACE_TYPE),))
        generated = [primary]
        if any(option.kind is AInDataTypeKind.OBJECT for option in choice.alternatives):
            # Inline named alternatives need payload contracts in every source
            # representation (including JSON/YAML); a wrapper's imported
            # branch class must exist before SDO can import it. Referenced
            # alternatives already have their own nominal definitions.
            from .aic_schema_contract_interface_generator import AIcSchemaContractInterfaceGenerator
            for index, alternative in enumerate(choice.alternatives):
                if alternative.kind is AInDataTypeKind.REFERENCE:
                    continue
                if alternative.kind is not AInDataTypeKind.OBJECT:
                    continue  # Scalar/array alternatives use built-in Java/Python value types.
                logical = choice_branch_name(model, alternative, index, kind)
                branch = AIcdCanonicalDefinition(model.identity + '#/' + kind + '/' + str(index), model.version, logical, model.source_kind, model.source_resource, model.description, alternative, (), None)
                subrequest = AIcdCodeGenerationRequest(
                    branch, target, request.package_name, request.naming_profile,
                    naming_convention=request.naming_convention,
                    contract_role=request.contract_role,
                    common_naming_profile=request.common_naming_profile)
                generated.append(AIcSchemaContractInterfaceGenerator().generate(subrequest))
        for wrapper, wrapper_file, typ, typ_file in variants:
            if target is AInCodeGenerationTarget.JAVA:
                body = ('package ' + request.package_name + ';\n\n'
                    '/** One explicitly selected, statically typed closed-choice alternative. */\n'
                    'public record ' + wrapper + '(' + typ + ' value) implements ' + cls + ' {\n'
                    '    /** Require a non-null selected alternative. */\n'
                    '    public ' + wrapper + ' { java.util.Objects.requireNonNull(value, "value"); }\n'
                    '}\n')
            else:
                body = ('from __future__ import annotations\n'
                    'from dataclasses import dataclass\n'
                    f'from .{stem} import {cls}\n'
                    + (f'from .{typ_file} import {typ}\n' if typ_file else
                       'from decimal import Decimal\n' if typ == 'Decimal' else '') + '\n'
                    '@dataclass(frozen=True, slots=True)\n'
                    f'class {wrapper}({cls}):\n'
                    '    """One explicitly selected closed-choice alternative."""\n'
                    f'    value: {typ}\n\n'
                    '    def __post_init__(self):\n'
                    f'        if not isinstance(self.value, {"list" if typ.startswith("list[") else typ}):\n'
                    f'            raise TypeError("Expected {typ} choice value")\n')
            rel = path_prefix + wrapper_file + ext
            generated.append(AIcdGeneratedSource(wrapper, rel, body,
                (AIcdGeneratedTypeIdentity.from_request(request, wrapper, rel,
                    AInDefsNameRole.DATA_TYPE),)))
        return tuple(generated)
