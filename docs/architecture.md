# Architecture and interfaces

## Design

The engine has four pure boundaries: safe file selection, versioned rule
evaluation, exception governance, and result serialization. It never executes
IaC. Stable sorting and canonical JSON make identical source and policy inputs
produce identical evidence bytes.

Built-in regular-expression rules intentionally detect only explicit unsafe
settings. They do not claim full language interpretation. External scanners
should publish SARIF into the same CI evidence artifact; a future normalizer
can merge them without weakening the built-in fail-closed gate.

## Interface contract

Input:

- UTF-8, repository-relative `.bicep` or `.tf` files, maximum 2 MiB.
- A catalog with unique rule IDs, valid severities, control mappings,
  remediation, and language patterns.
- An exception document with exact rule/path scope, owner, justification, and
  future UTC expiry.

Output:

- Exit `0`: no active finding at/above threshold.
- Exit `1`: invalid configuration, unsafe input, or tool failure.
- Exit `2`: valid scan with a material finding at/above threshold.
- `report.json`: complete findings and gate decision.
- `results.sarif`: annotations including suppressed findings.
- `manifest.json`: hashes and attestation verification instruction.

## Reliability and limits

The local scan target is under 10 seconds for 1,000 small files and uses no
network. Files are processed once; no retry is required. CI tool downloads and
Defender ingestion require platform-managed retries. The scanner does not
resolve modules, dynamic expressions, Terraform plans/state, Azure Policy
effects, or defaults. A passing result means only that these explicit defects
were not found in the supplied files.
