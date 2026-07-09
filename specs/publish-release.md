# Publish & Release Process

Canonical workflow for shipping Willbe Trends to production. Cursor agents follow `.cursor/rules/publish-release.mdc`.

## Steps

| Step | Action |
|------|--------|
| 1 | `pytest` and `cd web && npm run build` |
| 2 | Bump `version` in `pyproject.toml` |
| 3 | Write `releases/vX.Y.Z.md` (see template in rule) |
| 4 | Update `specs/` if behavior changed |
| 5 | `git add` → commit → `git tag -a vX.Y.Z` |
| 6 | `git push origin main && git push origin vX.Y.Z` |
| 7 | `cd infra && pulumi up` with `AWS_PROFILE=willbe-trends-deploy` |

## Versioning

- **Patch** — bug fixes, copy, config
- **Minor** — new API routes, UI flows, research features
- **Major** — breaking API or data migrations

Tags use the `v` prefix (`v0.2.0`) and match `pyproject.toml`.

## Deploy target

- Stack: `dev` (see `infra/README.md`)
- URL: configured `domainName` (e.g. `trending-research.wilbi.fi`)
- Image: Docker build from repo root on `pulumi up`
