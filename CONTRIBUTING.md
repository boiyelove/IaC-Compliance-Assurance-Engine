# Contributing

Run `./scripts/validate.sh`. Every rule change must include compliant and
noncompliant fixtures, remediation text, control mappings, and tests for the
gate and SARIF output. Exception changes require a named owner, bounded path,
justification, and near-term expiry. Use Conventional Commits.

Do not commit production IaC, credentials, scan evidence containing tenant or
subscription identifiers, or tool output that cannot be reproduced.
