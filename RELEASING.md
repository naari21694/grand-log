# Releasing

Grand Log tracks every shipped change as a GitHub Release. Each release carries its bundled downloads: the source archives (zip and tar.gz, attached by GitHub) and a multi-arch container image on GHCR. The [`Release` workflow](.github/workflows/release.yml) does the build and the publishing; you only push a tag.

## Cut a release
1. In [CHANGELOG.md](CHANGELOG.md), rename the `## [Unreleased]` heading to `## [x.y.z] - YYYY-MM-DD` and add a fresh empty `## [Unreleased]` above it.
2. Set the version in [VERSION](VERSION), and the version badge in the README, to `x.y.z`.
3. Land those on `main` (through a PR), then tag and push:
   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```
4. The `Release` workflow builds and pushes `ghcr.io/naari21694/grand-log:vX.Y.Z` and `:latest`, then creates the GitHub Release with auto-generated notes and the source archives.

## What lands in every release
- Source code, zip and tar.gz, attached automatically by GitHub.
- The container image: `docker pull ghcr.io/naari21694/grand-log:vX.Y.Z` (amd64 and arm64).
- Release notes generated from the merged pull requests since the previous tag, on top of the CHANGELOG entry.

## Versioning and cadence
Semantic versioning: a new feature bumps the minor (0.2 to 0.3), a fix bumps the patch (0.3.0 to 0.3.1), a breaking change bumps the major once the project reaches 1.0. Every feature gets a CHANGELOG entry under `[Unreleased]` as it lands; cut a release per feature when you want each one tracked separately, or group a few related features into one release to keep the list readable. Use a patch release for an isolated fix.

## Notes
- The GHCR package inherits the repository's visibility (private while the repo is private, public when it is). No manual setup is needed; the workflow authenticates with the built-in `GITHUB_TOKEN`.
- A release is the human gate. Pushing the tag is the deliberate, outward-facing step; the workflow only runs on a `v*` tag.
