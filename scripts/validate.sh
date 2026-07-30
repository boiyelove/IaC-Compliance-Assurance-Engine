#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
evidence="$(mktemp -d)"
trap 'rm -rf "$evidence"' EXIT
cd "$repo_root"

python3 -m unittest discover -s tests -v
python3 -m json.tool config/control-catalog.json >/dev/null
python3 -m json.tool config/exceptions.json >/dev/null

python3 src/assurance.py scan \
  examples/compliant/main.bicep \
  examples/compliant/main.tf \
  --catalog config/control-catalog.json \
  --exceptions config/exceptions.json \
  --output "$evidence/first" \
  --fail-on high
python3 src/assurance.py scan \
  examples/compliant/main.bicep \
  examples/compliant/main.tf \
  --catalog config/control-catalog.json \
  --exceptions config/exceptions.json \
  --output "$evidence/second" \
  --fail-on high
cmp "$evidence/first/report.json" "$evidence/second/report.json"
cmp "$evidence/first/results.sarif" "$evidence/second/results.sarif"
cmp "$evidence/first/manifest.json" "$evidence/second/manifest.json"

if command -v bicep >/dev/null 2>&1; then
  bicep build examples/compliant/main.bicep \
    --outfile "$evidence/compliant.json"
elif command -v az >/dev/null 2>&1; then
  AZURE_CONFIG_DIR="$evidence/az" az bicep build \
    --file examples/compliant/main.bicep \
    --outfile "$evidence/compliant.json"
fi

if command -v terraform >/dev/null 2>&1; then
  terraform fmt -check examples/compliant/main.tf
fi
if command -v shellcheck >/dev/null 2>&1; then
  shellcheck scripts/validate.sh
fi
