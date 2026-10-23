"""Native fallback for Defs setter policy when invoked directly without CLI settings."""
from __future__ import annotations
import os
from eu.algites.lib.data.dataobject.ain_field_setter_inheritance_policy import AInFieldSetterInheritancePolicy


def effective_default() -> AInFieldSetterInheritancePolicy:
    """Return explicit CLI policy or the library's stable generics-preserving fallback."""
    value = os.environ.get('ALGITES_DEFS_CODEGEN_SETTER_INHERITANCE_POLICY',
                           'INHERIT_AS_GENERIC_PARAMETER')
    try:
        policy = AInFieldSetterInheritancePolicy(value)
    except ValueError as exc:
        raise ValueError(f'Invalid setterInheritancePolicy: {value}') from exc
    if policy is AInFieldSetterInheritancePolicy.DEFAULT:
        raise ValueError('Unresolved setterInheritancePolicy: DEFAULT')
    return policy
