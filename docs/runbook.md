# Operations runbook

## Triage a failed gate

1. Confirm exit code `2`; exit `1` is a tool/configuration failure.
2. Open `report.json` or the SARIF annotation and locate the exact line.
3. Apply the catalog remediation, rerun locally, and review the IaC plan.
4. If remediation cannot occur before deployment, stop and obtain formal risk
   approval before adding a narrowly scoped, short-lived exception.

## Scanner/tool failure

Do not convert tool errors to warnings. Confirm UTF-8 input, path bounds,
catalog validity, runner clock, disk space, and pinned tool availability.
Retry external download/service failures with the CI platform's bounded retry;
the built-in engine itself is deterministic and should not need retries.

## Evidence verification

Recalculate SHA-256 for `report.json` and `results.sarif`, compare them with
`manifest.json`, then verify the GitHub artifact attestation against the
expected repository, workflow, ref, and commit. Preserve evidence according to
the organization's retention schedule.

## Rollback

Revert the policy or exception commit through review and rerun the full
pipeline. Never alter an existing evidence artifact. Publish a new artifact
that references the corrective commit.
