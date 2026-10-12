# Naming validator CLI

Validates structural names directly with the 1.1 YAML convention catalog.

`<catalog.yml> <name-convention> <source-structure-kind> <name>`

Returns exit code 0 for a match and exit code 2 for a mismatch. Both Java and
Python implementations consume the same declarative patterns.
