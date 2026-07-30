# Support

Community support covers reproducible behavior of the built-in scanner,
catalog, SARIF, gate, and evidence manifest. External scanner availability,
Defender licensing, Azure Policy evaluation, and organization-specific control
interpretation are outside the support boundary.

Supported runtime: Python 3.11+. Input dialects are ordinary UTF-8 `.bicep` and
`.tf` files up to 2 MiB. Parsing is intentionally conservative and cannot
resolve modules, variables, or generated expressions.
