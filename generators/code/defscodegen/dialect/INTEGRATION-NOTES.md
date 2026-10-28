# Integration status and ordering

This checkpoint intentionally adds **only** the independent dialect/vocabulary contract. It is not yet a finished implementation of explicit-only Defs Codegen, nor a runnable end-to-end bootstrap for this newly introduced SourceKind.

## Prerequisites for activating these resources

1. Add generic `jsonmetadefs` SourceKind support to Modustro Builder **1.1 in `pub.pltf.Modustro`** (including its Gradle plugin and local bootstrap regression tests), rather than editing the existing Builder 1.0 scripts as a permanent substitute.
2. Implement the same explicit `x-algites-defscodegen-extends` and `x-algites-defscodegen-choice` semantics in **both** Java and Python Defs frontends and canonical merger. Never infer fields, generated inheritance or choice types from the standard validation combinators. Preserve validation independently.
3. Build and migrate `pub.tool.General` and `pub.lib.General` before proceeding to other repos; fix the corresponding XSD types without falling back to `xs:anyType` for required structured data.
4. Verify resource-only artifact packaging and staged public URLs for both meta-schema dialects and Markdown vocabulary. Publish only after Builder 1.1's local generation, staging and integration tests pass.
5. Switch individual `settings.gradle.kts` to the tested Builder 1.1; switch GitHub Actions workflows **last**, once Builder 1.1 is used everywhere required.

The existing v15 bootstrap does not deploy to Scaleway and does not yet recognize `jsonmetadefs` as a canonical definition kind. The stable `$id` values in this checkpoint are **proposed** public identifiers, not claims of deployment.
