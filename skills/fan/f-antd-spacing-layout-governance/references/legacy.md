# Legacy and third-party compatibility

Use this priority:

1. Safely remove layout margin from an owned component.
2. Wrap an immutable component in an existing or scoped LegacyModuleAdapter.
3. Use a local negative-margin escape only when the adapter cannot otherwise neutralize the behavior.

Negative margin must be isolated inside the legacy adapter, narrowly scoped, commented, and prohibited from new business code. Do not break third-party internals to satisfy a zero-margin rule. Search for existing adapter patterns before using `templates/LegacyModuleAdapter.*`; avoid global internal Ant selectors.
