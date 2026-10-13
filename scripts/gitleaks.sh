#!/usr/bin/env bash
# Runs gitleaks from its pinned Docker image against this repository.
#   scripts/gitleaks.sh git           scan the full git history (run before every push)
#   scripts/gitleaks.sh git --staged  scan staged changes (used by the pre-commit hook)
set -euo pipefail

GITLEAKS_IMAGE="zricethezav/gitleaks:v8.28.0"
repo_root="$(git rev-parse --show-toplevel)"

docker run --rm \
  -v "${repo_root}:/repo" \
  -w /repo \
  --entrypoint sh \
  "$GITLEAKS_IMAGE" \
  -c 'git config --global --add safe.directory /repo && gitleaks "$@" --redact --no-banner --verbose /repo' \
  gitleaks "$@"
