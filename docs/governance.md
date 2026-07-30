# Control and exception governance

Mappings identify which technical safeguard a rule can support; they do not
prove the full ISO 27001 control or SOC 2 criterion. A compliance owner must
review mappings at least annually and whenever standards, cloud services, or
rule semantics change.

An exception is a time-bounded risk decision, not a false-positive toggle.
The owner must document the business reason, compensating control, approver,
and remediation ticket outside this public sample. Keep repository exceptions
free of sensitive system names. CI rejects expired, wildcard, malformed, or
unknown-rule entries. Renewal requires a new review and a changed expiry.

Material gate severity changes require security owner approval and evidence
from both compliant and noncompliant fixtures. Downgrading a rule should be
treated like widening an exception.
