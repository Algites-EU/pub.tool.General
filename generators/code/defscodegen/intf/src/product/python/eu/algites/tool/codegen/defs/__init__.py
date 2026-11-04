"""Canonical Defs Codegen contract shared by the separately packaged implementations.

Extend the namespace search path so the interface and implementation distributions
can coexist without imposing a dependency from the interface on the implementation.
"""

from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)
