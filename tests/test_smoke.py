"""fungame-sudoku 的轻量冒烟测试。"""

import copy

import numpy as np
import pytest

import fungame
from fungame.sudoku import (
    Sudoku,
    SudokuUnsolvableError,
    sudoku_check_solution,
    sudoku_generate,
    sudoku_solve_solution,
)

# 一个已知合法、填满的 9x9 数独解（作为真值基准）。
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
    """在一个已解出的网格基础上，每行挖掉一个格子，构造出可解的题目。"""
    puzzle = copy.deepcopy(solved)
    for r in range(9):
        c = r % 9  # 每行挖掉的列不同，避免挖出的格子凑巧共线
        puzzle[r][c] = 0
    return puzzle


def test_imports():
    """包及其子模块应能正常导入，公开 API 均可访问。"""
    assert fungame is not None
    import fungame.sudoku as sudoku_module

    assert hasattr(sudoku_module, "Sudoku")
    assert hasattr(sudoku_module, "sudoku_check_solution")
    assert hasattr(sudoku_module, "sudoku_solve_solution")
    assert hasattr(sudoku_module, "sudoku_generate")
    assert hasattr(sudoku_module, "SudokuUnsolvableError")


def test_sudoku_object_construction():
    """Sudoku() 应能从带空格的题目正确构造出 9x9 内部网格。"""
    puzzle = _make_puzzle_from_solved(SOLVED_GRID)
    sudo = Sudoku(puzzle)
    assert sudo.value.shape == (9, 9)
    # get_num_count 统计已经是确定整数的格子数量。
    # 每行挖掉一个格子，共挖掉 9 个，所以应剩下 81 - 9 个已确定格子。
    assert sudo.get_num_count() == 81 - 9


def test_sudoku_object_construction_invalid_shape_raises():
    """给 Sudoku() 传入无法整理成 9x9 的数据应直接报错，而不是静默产生错误结果。"""
    with pytest.raises(ValueError):
        Sudoku([1, 2, 3])

    with pytest.raises(ValueError):
        Sudoku([[1, 2], [3, 4]])


def test_check_solution_valid_grid():
    """正确填满的网格应被判定为合法解。"""
    assert sudoku_check_solution(SOLVED_GRID) is True


def test_check_solution_invalid_grid_duplicate_in_row():
    """同一行出现重复数字时必须被判定为非法解。"""
    broken = copy.deepcopy(SOLVED_GRID)
    # 第一行是 [5, 3, 4, 6, 7, 8, 9, 1, 2]，把最后一格的 2 改成与第一格相同的 5，
    # 从而破坏「同一行不重复」的约束。
    broken[0][8] = broken[0][0]
    assert sudoku_check_solution(broken) is False


def test_check_solution_accepts_csv_path(tmp_path):
    """sudoku_check_solution() 的公开入参还支持 CSV 文件路径，应能正确读取并校验。"""
    csv_path = tmp_path / "solved.csv"
    csv_path.write_text("\n".join(",".join(str(v) for v in row) for row in SOLVED_GRID))
    assert sudoku_check_solution(str(csv_path)) is True


@pytest.mark.timeout(30)
def test_solve_solution_matches_expected():
    """sudoku_solve_solution() 默认（method=1，Sudoku 类回溯）应能还原出原始解。"""
    puzzle = _make_puzzle_from_solved(SOLVED_GRID)
    solved = sudoku_solve_solution(puzzle)

    solved_list = [[int(v) for v in row] for row in np.array(solved).tolist()]
    assert solved_list == SOLVED_GRID

    # 同时用另一个公开 API 交叉验证，增加鲁棒性。
    assert sudoku_check_solution(solved_list) is True


@pytest.mark.timeout(30)
def test_solve_solution_method2_matches_expected():
    """method=2（最少候选数优先的随机填数策略）在给定题目下也应得到正确解。"""
    puzzle = _make_puzzle_from_solved(SOLVED_GRID)
    solved = sudoku_solve_solution(puzzle, method=2)

    solved_list = [[int(v) for v in row] for row in np.array(solved).tolist()]
    assert solved_list == SOLVED_GRID
    assert sudoku_check_solution(solved_list) is True


@pytest.mark.timeout(30)
def test_solve_solution_unsolvable_puzzle_raises():
    """无解的题目（给定数字本身就互相矛盾）求解时应抛出领域异常 SudokuUnsolvableError。"""
    # 第一行放两个相同的数字 5，直接构成矛盾，确定无解。
    unsolvable = [
        [5, 5, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
    with pytest.raises(SudokuUnsolvableError):
        sudoku_solve_solution(unsolvable, method=1)


@pytest.mark.timeout(10)
def test_generate_normal_path():
    """sudoku_generate() 应返回 9x9 的网格，挖空比例与 mask_rate 大致相符。"""
    grid = sudoku_generate(mask_rate=0.5)
    assert grid.shape == (9, 9)
    # 挖空的格子应该是 81 格中合理的一部分，不应该全空或全满。
    blanks = int((grid == 0).sum())
    assert 0 < blanks < 81


@pytest.mark.timeout(10)
def test_generate_mask_rate_zero_is_a_full_valid_solution():
    """mask_rate=0 应保留所有格子，构成一个合法的完整解。"""
    grid = sudoku_generate(mask_rate=0)
    assert (grid != 0).all()
    assert sudoku_check_solution(grid.tolist()) is True


@pytest.mark.timeout(10)
def test_generate_mask_rate_one_is_fully_blank():
    """mask_rate=1 应挖空所有格子。"""
    grid = sudoku_generate(mask_rate=1)
    assert (grid == 0).all()


@pytest.mark.timeout(10)
@pytest.mark.parametrize("bad_mask_rate", [-0.1, 1.5])
def test_generate_invalid_mask_rate_raises(bad_mask_rate):
    """mask_rate 超出 [0, 1] 范围属于非法入参，应报错而不是返回错误结果。"""
    with pytest.raises(ValueError):
        sudoku_generate(mask_rate=bad_mask_rate)
