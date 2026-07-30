# Test matrix

| Scenario | Expected |
|---|---|
| Compliant Bicep and Terraform | Gate pass, empty findings |
| Public access/TLS/local auth/purge protection fixtures | Correct material rules and lines |
| Threshold reached | Exit `2`, evidence still written |
| Scanner/config/path failure | Exit `1`, fail closed |
| Exact active exception | Finding retained and marked suppressed |
| Expired/unknown/wildcard exception | Configuration rejected |
| Duplicate/traversing/unsupported changed files | Sorted safe allowlist only |
| Repeat same scan | Byte-identical report, SARIF, manifest |
| Catalog mutation | Manifest catalog digest changes |
| Bicep compile/Terraform format | Tool validation passes |
| GitHub push | Evidence uploaded and OIDC-attested |
| External scanner unavailable | Built-in gate still operates; CI external step fails visibly |

Live Defender for DevOps ingestion, branch protection, required checks, and
attestation verification require a real GitHub organization/repository and are
documented acceptance gates rather than simulated evidence.
