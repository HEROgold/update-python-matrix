from datetime import date

import pytest

from update_matrix import MatrixNotFoundError, update_matrix

TODAY = date(2026, 10, 20)

CYCLES = [
    {"cycle": "3.15", "eol": "2031-10-31"},
    {"cycle": "3.14", "eol": "2030-10-31"},
    {"cycle": "3.13", "eol": "2029-10-31"},
    {"cycle": "3.12", "eol": "2028-10-31"},
    {"cycle": "3.11", "eol": "2027-10-31"},
    {"cycle": "3.10", "eol": "2026-10-31"},
    {"cycle": "3.9", "eol": "2025-10-31"},
]

WORKFLOW = """\
jobs:
  test:
    strategy:
      matrix:
        os:
          - ubuntu-latest
        python-version:
          - "3.12"
          - "3.13"
    steps:
      - run: echo hi
"""


def test_adds_released_versions_above_the_floor() -> None:
    text, versions = update_matrix(WORKFLOW, CYCLES, TODAY)

    assert versions == ["3.12", "3.13", "3.14", "3.15"]
    assert text == WORKFLOW.replace(
        '          - "3.13"\n',
        '          - "3.13"\n          - "3.14"\n          - "3.15"\n',
    )


def test_drops_versions_past_end_of_life() -> None:
    workflow = WORKFLOW.replace('"3.12"', '"3.9"').replace('"3.13"', '"3.10"')

    _, versions = update_matrix(workflow, CYCLES, TODAY)

    assert versions == ["3.10", "3.11", "3.12", "3.13", "3.14", "3.15"]


def test_never_goes_below_the_floor() -> None:
    workflow = WORKFLOW.replace('          - "3.12"\n', "").replace('"3.13"', '"3.15"')

    text, versions = update_matrix(workflow, CYCLES, TODAY)

    assert versions == ["3.15"]
    assert text == workflow


def test_leaves_a_current_matrix_alone() -> None:
    current = WORKFLOW.replace(
        '          - "3.13"\n',
        '          - "3.13"\n          - "3.14"\n          - "3.15"\n',
    )

    text, _ = update_matrix(current, CYCLES, TODAY)

    assert text == current


def test_keeps_the_indentation_and_quoting_of_the_list() -> None:
    workflow = "matrix:\n  python-version:\n  - '3.14'\n"

    text, _ = update_matrix(workflow, CYCLES, TODAY)

    assert text == "matrix:\n  python-version:\n  - '3.14'\n  - '3.15'\n"


def test_a_cycle_without_an_end_of_life_date_is_supported() -> None:
    cycles = [{"cycle": "3.16", "eol": False}, *CYCLES]

    _, versions = update_matrix(WORKFLOW, cycles, TODAY)

    assert versions[-1] == "3.16"


def test_reports_a_missing_matrix_key() -> None:
    with pytest.raises(MatrixNotFoundError, match="python-version"):
        update_matrix("jobs: {}\n", CYCLES, TODAY)


def test_reads_another_matrix_key_when_asked() -> None:
    workflow = WORKFLOW.replace("python-version:", "python:")

    _, versions = update_matrix(workflow, CYCLES, TODAY, key="python")

    assert versions == ["3.12", "3.13", "3.14", "3.15"]
