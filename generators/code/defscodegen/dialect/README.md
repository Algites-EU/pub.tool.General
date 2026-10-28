# Defs Codegen dialect artifact (initial staged resources)

This is the new independent, data-only `jsonmetadefs` SourceKind proposed for Modustro Builder 1.1. It contains two versions of the syntax meta-schema and dialect, and one shared vocabulary specification. The standard JSON Schema `$schema` keyword is reused, not redeclared.

Important: the v15 bootstrap and current Builder do not yet discover or publish `jsonmetadefs`; inclusion of these files does not imply deployment, or that the Defs Java/Python frontends have switched to explicit-only inheritance/choice generation. Do not assume this artifact is production-integrated until SourceKind support, source distribution packaging, and frontend migration tests pass.
