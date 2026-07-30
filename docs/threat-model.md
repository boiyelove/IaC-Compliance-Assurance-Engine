# Threat model

| Threat | Control | Residual risk |
|---|---|---|
| Contributor bypasses scan with path traversal | Repository-relative resolution, extension allowlist | CI file list must cover all deployable roots |
| Symlink reads sensitive file | Symlink rejection and repository boundary | TOCTOU on hostile self-hosted runner |
| Huge/binary input exhausts scanner | 2 MiB limit and UTF-8 decoding | Many small files can still consume time |
| Regex/catalog disables detection | CODEOWNERS, rule metadata tests, review | Malicious privileged maintainer |
| Broad/permanent suppression | Exact path, known rule, owner, justification, expiry | Reviewer accepts weak justification |
| Expired suppression remains active | Validation fails closed | Incorrect runner clock |
| Evidence modified after scan | SHA-256 manifest and OIDC artifact attestation | Local manifest alone is not signed |
| PR code steals OIDC token | Attestation isolated after validation on push | Compromised third-party action |
| Scanner crashes and pipeline passes | Error exit `1`; shell uses `set -e` | Workflow configured with continue-on-error |

The catalog and CI workflow are privileged policy. Require security approval
and protected branches. Imported external SARIF is untrusted and must never be
rendered as unsanitized HTML.
