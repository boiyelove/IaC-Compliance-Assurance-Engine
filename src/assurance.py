#!/usr/bin/env python3
"""Deterministic Terraform/Bicep material-defect assurance engine."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

SEVERITY = {"note": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
MAX_FILE_BYTES = 2 * 1024 * 1024
SUPPORTED = {".bicep": "bicep", ".tf": "terraform"}


class AssuranceError(ValueError):
    """Invalid input or policy configuration."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, separators=(",", ": ")) + "\n"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def safe_path(raw: str, root: Path) -> Path:
    candidate = PurePosixPath(raw)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise AssuranceError(f"unsafe path: {raw}")
    lexical = root / Path(*candidate.parts)
    current = lexical
    while current != root:
        if current.is_symlink():
            raise AssuranceError(f"symlink input refused: {raw}")
        current = current.parent
    resolved = lexical.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise AssuranceError(f"path leaves repository: {raw}")
    if resolved.suffix not in SUPPORTED:
        raise AssuranceError(f"unsupported IaC file: {raw}")
    if not resolved.is_file():
        raise AssuranceError(f"missing IaC file: {raw}")
    if resolved.stat().st_size > MAX_FILE_BYTES:
        raise AssuranceError(f"file exceeds 2 MiB: {raw}")
    return resolved


def normalize_changed(lines: Iterable[str], root: Path) -> list[str]:
    accepted: set[str] = set()
    for line in lines:
        raw = line.strip().replace(os.sep, "/")
        if not raw or PurePosixPath(raw).suffix not in SUPPORTED:
            continue
        try:
            path = safe_path(raw, root)
        except AssuranceError:
            continue
        accepted.add(path.relative_to(root.resolve()).as_posix())
    return sorted(accepted)


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AssuranceError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise AssuranceError(f"{path} must contain a JSON object")
    return value


def validate_catalog(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(catalog.get("catalog_version"), str):
        raise AssuranceError("catalog_version is required")
    rules = catalog.get("rules")
    if not isinstance(rules, list) or not rules:
        raise AssuranceError("catalog rules must be a non-empty list")
    ids: set[str] = set()
    for rule in rules:
        required = {"id", "title", "severity", "controls", "remediation", "patterns"}
        if not isinstance(rule, dict) or required - rule.keys():
            raise AssuranceError("each rule must have complete metadata")
        if rule["id"] in ids:
            raise AssuranceError(f"duplicate rule: {rule['id']}")
        ids.add(rule["id"])
        if rule["severity"] not in SEVERITY:
            raise AssuranceError(f"invalid severity for {rule['id']}")
        if not rule["controls"] or not all(isinstance(x, str) for x in rule["controls"]):
            raise AssuranceError(f"control mapping required for {rule['id']}")
        for language, patterns in rule["patterns"].items():
            if language not in SUPPORTED.values() or not isinstance(patterns, list):
                raise AssuranceError(f"invalid patterns for {rule['id']}")
            for pattern in patterns:
                re.compile(pattern, re.IGNORECASE)
    return rules


def validate_exceptions(
    document: dict[str, Any], rule_ids: set[str], now: dt.datetime
) -> list[dict[str, Any]]:
    values = document.get("exceptions")
    if not isinstance(values, list):
        raise AssuranceError("exceptions must be a list")
    result = []
    seen: set[str] = set()
    for item in values:
        required = {"id", "rule_id", "path", "owner", "justification", "expires_at"}
        if not isinstance(item, dict) or required - item.keys():
            raise AssuranceError("each exception must have complete metadata")
        if item["id"] in seen:
            raise AssuranceError(f"duplicate exception: {item['id']}")
        seen.add(item["id"])
        if item["rule_id"] not in rule_ids:
            raise AssuranceError(f"unknown exception rule: {item['rule_id']}")
        path = str(item["path"])
        if "*" in path or PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts:
            raise AssuranceError(f"exception path must be exact: {path}")
        if not str(item["owner"]).strip() or len(str(item["justification"]).strip()) < 12:
            raise AssuranceError(f"exception {item['id']} needs owner and justification")
        try:
            expiry = dt.datetime.fromisoformat(str(item["expires_at"]).replace("Z", "+00:00"))
        except ValueError as exc:
            raise AssuranceError(f"invalid expiry for {item['id']}") from exc
        if expiry.tzinfo is None:
            raise AssuranceError(f"expiry must include timezone for {item['id']}")
        if expiry <= now:
            raise AssuranceError(f"exception expired: {item['id']}")
        result.append(item)
    return result


def scan_file(path: Path, relative: str, rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise AssuranceError(f"cannot read {relative}: {exc}") from exc
    language = SUPPORTED[path.suffix]
    findings = []
    for rule in rules:
        for pattern in rule["patterns"].get(language, []):
            for match in re.finditer(pattern, text, re.IGNORECASE):
                line = text.count("\n", 0, match.start()) + 1
                fingerprint = sha256_bytes(
                    f"{rule['id']}:{relative}:{line}:{match.group(0).strip()}".encode()
                )[:20]
                findings.append(
                    {
                        "rule_id": rule["id"],
                        "title": rule["title"],
                        "severity": rule["severity"],
                        "controls": rule["controls"],
                        "path": relative,
                        "line": line,
                        "message": f"{rule['title']}: {match.group(0).strip()}",
                        "remediation": rule["remediation"],
                        "fingerprint": fingerprint,
                        "suppressed": False,
                        "exception_id": None,
                    }
                )
    return findings


def apply_exceptions(
    findings: list[dict[str, Any]], exceptions: list[dict[str, Any]]
) -> None:
    by_scope = {(x["rule_id"], x["path"]): x for x in exceptions}
    for finding in findings:
        exception = by_scope.get((finding["rule_id"], finding["path"]))
        if exception:
            finding["suppressed"] = True
            finding["exception_id"] = exception["id"]


def to_sarif(findings: list[dict[str, Any]], rules: list[dict[str, Any]]) -> dict:
    levels = {"critical": "error", "high": "error", "medium": "warning", "low": "note", "note": "note"}
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "iac-assurance",
                        "version": "0.1.0",
                        "informationUri": "https://github.com/example/IaC-Compliance-Assurance-Engine",
                        "rules": [
                            {
                                "id": rule["id"],
                                "name": rule["title"],
                                "shortDescription": {"text": rule["title"]},
                                "help": {"text": rule["remediation"]},
                                "properties": {
                                    "security-severity": str(SEVERITY[rule["severity"]] * 2.5),
                                    "tags": rule["controls"],
                                },
                            }
                            for rule in rules
                        ],
                    }
                },
                "results": [
                    {
                        "ruleId": finding["rule_id"],
                        "level": levels[finding["severity"]],
                        "message": {
                            "text": f"{finding['message']} Remediation: {finding['remediation']}"
                        },
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {"uri": finding["path"]},
                                    "region": {"startLine": finding["line"]},
                                }
                            }
                        ],
                        "partialFingerprints": {
                            "primaryLocationLineHash": finding["fingerprint"]
                        },
                        "suppressions": (
                            [{"kind": "external", "justification": finding["exception_id"]}]
                            if finding["suppressed"]
                            else []
                        ),
                    }
                    for finding in findings
                ],
            }
        ],
    }


def run_scan(args: argparse.Namespace) -> int:
    root = Path.cwd().resolve()
    catalog_path = Path(args.catalog).resolve()
    catalog = load_json(catalog_path)
    rules = validate_catalog(catalog)
    now = dt.datetime.now(dt.timezone.utc)
    exceptions = validate_exceptions(
        load_json(Path(args.exceptions).resolve()), {r["id"] for r in rules}, now
    )
    raw_files = list(args.files)
    if args.files_from:
        raw_files.extend(
            line.strip()
            for line in Path(args.files_from).read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    if not raw_files:
        raise AssuranceError("at least one IaC file is required")
    files: list[tuple[Path, str]] = []
    for raw in sorted(set(raw_files)):
        path = safe_path(raw, root)
        files.append((path, path.relative_to(root).as_posix()))

    findings: list[dict[str, Any]] = []
    for path, relative in files:
        findings.extend(scan_file(path, relative, rules))
    findings.sort(key=lambda x: (x["path"], x["line"], x["rule_id"]))
    apply_exceptions(findings, exceptions)

    threshold = SEVERITY[args.fail_on]
    active = [f for f in findings if not f["suppressed"]]
    failed = [f for f in active if SEVERITY[f["severity"]] >= threshold]
    report = {
        "schema_version": "1.0",
        "catalog_version": catalog["catalog_version"],
        "files": [relative for _, relative in files],
        "summary": {
            "total": len(findings),
            "active": len(active),
            "suppressed": len(findings) - len(active),
            "gate_threshold": args.fail_on,
            "gate": "fail" if failed else "pass",
        },
        "findings": findings,
    }
    sarif = to_sarif(findings, rules)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    report_bytes = canonical_json(report).encode()
    sarif_bytes = canonical_json(sarif).encode()
    (output / "report.json").write_bytes(report_bytes)
    (output / "results.sarif").write_bytes(sarif_bytes)
    catalog_bytes = catalog_path.read_bytes()
    manifest = {
        "schema_version": "1.0",
        "catalog_version": catalog["catalog_version"],
        "artifacts": {
            "report.json": {"sha256": sha256_bytes(report_bytes)},
            "results.sarif": {"sha256": sha256_bytes(sarif_bytes)},
            "control-catalog.json": {"sha256": sha256_bytes(catalog_bytes)},
        },
        "signature": {
            "type": "external",
            "instruction": "Verify the GitHub artifact attestation for manifest.json.",
        },
    }
    (output / "manifest.json").write_text(canonical_json(manifest), encoding="utf-8")
    print(
        f"gate={report['summary']['gate']} active={len(active)} "
        f"suppressed={report['summary']['suppressed']} output={output}"
    )
    return 2 if failed else 0


def run_changed(args: argparse.Namespace) -> int:
    lines = sys.stdin if args.stdin else Path(args.input).read_text(encoding="utf-8").splitlines()
    values = normalize_changed(lines, Path.cwd())
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text("".join(f"{value}\n" for value in values), encoding="utf-8")
    print(f"selected={len(values)} output={args.output}")
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    scan = commands.add_parser("scan", help="scan IaC and create evidence")
    scan.add_argument("files", nargs="*")
    scan.add_argument("--files-from")
    scan.add_argument("--catalog", required=True)
    scan.add_argument("--exceptions", required=True)
    scan.add_argument("--output", required=True)
    scan.add_argument("--fail-on", choices=SEVERITY, default="high")
    scan.set_defaults(handler=run_scan)
    changed = commands.add_parser("changed", help="normalize changed IaC paths")
    changed_source = changed.add_mutually_exclusive_group(required=True)
    changed_source.add_argument("--stdin", action="store_true")
    changed_source.add_argument("--input")
    changed.add_argument("--output", required=True)
    changed.set_defaults(handler=run_changed)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        return args.handler(args)
    except (AssuranceError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
