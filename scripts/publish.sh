#!/usr/bin/env bash
# Publish helper: verify, commit, tag, push. Run deploy separately (pulumi up).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="${1:-}"

if [[ -z "$VERSION" ]]; then
  echo "Usage: $0 <version>   e.g. $0 0.2.0" >&2
  exit 1
fi

TAG="v${VERSION#v}"
NOTES="$ROOT/releases/${TAG}.md"

cd "$ROOT"

echo "==> Running tests"
pytest -q

echo "==> Building web"
(cd web && npm run build)

if [[ ! -f "$NOTES" ]]; then
  echo "Missing release notes: $NOTES" >&2
  echo "Create them before publishing (see specs/publish-release.md)." >&2
  exit 1
fi

if ! grep -q "^version = \"${VERSION#v}\"" pyproject.toml; then
  echo "pyproject.toml version must be ${VERSION#v}" >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "==> Committing release"
  git add -A
  git commit -m "Release ${TAG}: $(head -1 "$NOTES" | sed 's/^# [^—]*— //')"
fi

if ! git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "==> Tagging ${TAG}"
  git tag -a "$TAG" -m "$TAG"
fi

echo "==> Pushing main and ${TAG}"
git push origin main
git push origin "$TAG"

echo "Done. Deploy with: cd infra && AWS_PROFILE=willbe-trends-deploy AWS_REGION=ap-southeast-1 pulumi up"
