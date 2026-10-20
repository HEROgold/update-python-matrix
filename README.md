# update-python-matrix

Keeps a workflow's Python version matrix in step with [endoflife.date](https://endoflife.date/python), and opens a PR when it changes.

The lowest version in the matrix is the project's floor. The action replaces the list with every Python release at or above that floor that is not past end of life, so it:

- adds new releases as they come out,
- drops versions that reached end of life,
- never goes below the floor.

Later runs push to the same branch, so there is at most one open PR.

## Inputs

| Input | Default | Description |
|---|---|---|
| `github_token` | *required* | Pushes the branch and opens the PR. Needs `contents: write` and `pull-requests: write`. |
| `workflow` | `.github/workflows/test.yml` | The workflow file holding the matrix. |
| `key` | `python-version` | The matrix key whose block list holds the versions. |
| `branch` | `chore/update-python-matrix` | The branch the update is pushed to. |

## Outputs

| Output | Description |
|---|---|
| `changed` | `true` when the matrix was updated. |
| `versions` | The new versions, as a JSON array. |

The matrix must be a block list, in any indentation or quoting:

```yaml
python-version:
  - "3.14"
  - "3.15"
```

## Example usage

```yaml
# .github/workflows/update-python-matrix.yml
name: Update Python version matrix

on:
  schedule:
    - cron: "0 6 * * 1" # Monday 06:00 UTC
  workflow_dispatch:

permissions:
  contents: write
  pull-requests: write

jobs:
  update-matrix:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: HEROgold/update-python-matrix@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

PRs opened with `GITHUB_TOKEN` don't trigger other workflows. To run CI on the PR, pass a fine-grained token or a GitHub App token instead.

## Development

```sh
uv run pytest
uv run ruff check . && uv run ruff format --check .
```
