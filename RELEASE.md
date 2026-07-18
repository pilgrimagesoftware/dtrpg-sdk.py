# Release Process

Versioning and the changelog are both derived from [Conventional Commits](https://www.conventionalcommits.org/)
history via [git-cliff](https://git-cliff.org), configured in [cliff.toml](cliff.toml).

## Cutting a release

```sh
git checkout develop
git pull
```

Trigger the **Prepare Release** workflow (`workflow_dispatch` in the Actions tab). It:

1. Runs `git-cliff --bump` against `develop` to determine the next version from commits since the last tag.
2. Updates `pyproject.toml` to that version via `uv version`.
3. Prepends the generated changelog section to `CHANGELOG.md`.
4. Opens a pull request from an auto-created `release/<version>` branch into `master`.

Review the PR, merge into `master`, then merge the same changes back into `develop`. Tag the release:

```sh
git checkout master
git pull
git tag -a v<version> -m "Release <version>"
git push origin v<version>
```

The tag push triggers the **Release** workflow, which tests, builds, publishes to PyPI, and creates the GitHub
Release with the changelog for that tag attached.

## Hotfixes

For an urgent fix to what's currently in production:

```sh
git checkout master
git pull
git checkout -b hotfix/<description>
# fix, bump patch version, commit
```

PR into `master`, merge, tag, which triggers the release workflow. Then PR the same branch into `develop` so the
fix isn't lost on the next regular release.

## Secrets

- `PYPI_API_TOKEN` — a repo secret with publish access to the `dtrpg-sdk` project on PyPI, used by the Release
  workflow's `uv publish` step.
