"""Lightweight smoke tests for fungame-sudoku."""

import copy

import numpy as np
import pytest

import fungame
from fungame.sudoku import (
    Sudoku,
    sudoku_check_solution,
    sudoku_generate,
    sudoku_solve_solution,
)

# A known-valid, fully solved 9x9 sudoku grid (ground truth).
SOLVED_GRID = [
    [5, 3, 4, 6, 7, 8, 9, 1, 2],
    [6, 7, 2, 1, 9, 5, 3, 4, 8],
    [1, 9, 8, 3, 4, 2, 5, 6, 7],
    [8, 5, 9, 7, 6, 1, 4, 2, 3],
    [4, 2, 6, 8, 5, 3, 7, 9, 1],
    [7, 1, 3, 9, 2, 4, 8, 5, 6],
    [9, 6, 1, 5, 3, 7, 2, 8, 4],
    [2, 8, 7, 4, 1, 9, 6, 3, 5],
    [3, 4, 5, 2, 8, 6, 1, 7, 9],
]


def _make_puzzle_from_solved(solved):
    """Zero out one cell per row of a solved grid to build a solvable puzzle."""
    puzzle = copy.deepcopy(solved)
    for r in range(9):
        c = r % 9  # zero a different column in each row
        puzzle[r][c] = 0
    return puzzle


def test_imports():
    """Package and submodule should import cleanly."""
    assert fungame is not None
    import fungame.sudoku as sudoku_module

    assert hasattr(sudoku_module, "Sudoku")
    assert hasattr(sudoku_module, "sudoku_check_solution")
    assert hasattr(sudoku_module, "sudoku_solve_solution")
    assert hasattr(sudoku_module, "sudoku_generate")


def test_sudoku_object_construction():
    """Sudoku() should build a 9x9 internal grid from a puzzle with blanks."""
    puzzle = _make_puzzle_from_solved(SOLVED_GRID)
    sudo = Sudoku(puzzle)
    assert sudo.value.shape == (9, 9)
    # get_num_count reports how many cells are already fixed integers.
    # 9 cells were zeroed out (one per row), so 81 - 9 = 72 should remain fixed.
    assert sudo.get_num_count() == 81 - 9


def test_check_solution_valid_grid():
    """A correctly solved grid should be reported as valid."""
    assert sudoku_check_solution(SOLVED_GRID) is True


def test_check_solution_invalid_grid_duplicate_in_row():
    """A grid with a duplicate digit in a row must be reported as invalid."""
    broken = copy.deepcopy(SOLVED_GRID)
    # Row 0 is [5, 3, 4, 6, 7, 8, 9, 1, 2]; overwrite the last cell (2) with a
    # duplicate of the first cell's value (5) to break the row constraint.
    broken[0][8] = broken[0][0]
    assert sudoku_check_solution(broken) is False


@pytest.mark.timeout(30)
def test_solve_solution_matches_expected():
    """sudoku_solve_solution() should recover the original solved grid."""
    puzzle = _make_puzzle_from_solved(SOLVED_GRID)
    solved = sudoku_solve_solution(puzzle)

    solved_list = [[int(v) for v in row] for row in np.array(solved).tolist()]
    assert solved_list == SOLVED_GRID

    # Cross-check with the other public API as well, for robustness.
    assert sudoku_check_solution(solved_list) is True


@pytest.mark.timeout(10)
def test_generate_normal_path():
    """sudoku_generate() should return a 9x9 grid with roughly mask_rate blanks."""
    grid = sudoku_generate(mask_rate=0.5)
    assert grid.shape == (9, 9)
    # The masked (blank) cells should be a plausible fraction of 81, not all-or-nothing.
    blanks = int((grid == 0).sum())
    assert 0 < blanks < 81


@pytest.mark.timeout(10)
def test_generate_mask_rate_zero_is_a_full_valid_solution():
    """mask_rate=0 should leave every cell filled, forming a valid solved grid."""
    grid = sudoku_generate(mask_rate=0)
    assert (grid != 0).all()
    assert sudoku_check_solution(grid.tolist()) is True


@pytest.mark.timeout(10)
def test_generate_mask_rate_one_is_fully_blank():
    """mask_rate=1 should blank out every cell."""
    grid = sudoku_generate(mask_rate=1)
    assert (grid == 0).all()
