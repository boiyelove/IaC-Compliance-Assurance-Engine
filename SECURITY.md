# Security Policy

Report bypasses, parser denial of service, path traversal, unsafe exception
matching, evidence tampering, and CI privilege escalation through GitHub
private vulnerability reporting.

The latest version on `main` is supported. Run CI with untrusted pull-request
code under read-only permissions. The attestation job receives `id-token:
write` only after scanning and must never execute repository scripts with
elevated permissions. Branch protection, CODEOWNERS approval, immutable action
pinning policy, and Defender for DevOps are repository-owner responsibilities.

The engine reads source files but never invokes them. It rejects symlinks,
absolute/traversing paths, and oversized inputs. Treat SARIF and imported
scanner results as untrusted data.
