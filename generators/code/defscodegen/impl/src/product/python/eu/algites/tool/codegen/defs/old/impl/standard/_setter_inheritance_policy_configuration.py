"""Native fallback for Defs setter policy when invoked directly without CLI settings."""
from __future__ import annotations

from eu.algites.tool.codegen.common.aix_codegen_validation_exception import AIxCodegenValidationException
import os
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy


def effective_default() -> AInFieldSetterInheritancePolicy:
    """Return explicit CLI policy or the library's stable generics-preserving fallback."""
    value = os.environ.get('ALGITES_DEFS_CODEGEN_SETTER_INHERITANCE_POLICY',
                           'INHERIT_AS_GENERIC_PARAMETER')
    try:
        policy = AInFieldSetterInheritancePolicy(value)
    except ValueError as exc:
        raise AIxCodegenValidationException(f'Invalid setterInheritancePolicy: {value}', 'Check the inherited type and its parent contract. Preserve required setter parameter types, method signatures and valid inheritance relations.') from exc
    if policy is AInFieldSetterInheritancePolicy.DEFAULT:
        raise AIxCodegenValidationException('Unresolved setterInheritancePolicy: DEFAULT', 'Verify that the referenced type, schema or artifact exists, is included in explicit inputs, and uses the expected namespace/version. Check import and classpath configuration.')
    return policy
