# Code generator standardpostfix profile

This artifact selects naming conventions for BOTH Java and Python native technology kinds and for Defs/SDO generators via classpath/sys.path settings overlays.

It depends on `pub.lib.General_naming.convention.profile.standardpostfix`. Treat it as a build-time dependency; it is not an API or runtime dependency of generated products.

For current Builder 1.0, the Algites bootstrap explicitly stages only the algites profile. Once Builder 1.1 supports build-source-processor dependency usages, declare it through `Dependencies` at repository scope instead.
