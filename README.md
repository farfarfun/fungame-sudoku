# fungame-sudoku

数独（Sudoku）生成与求解工具库：随机生成数独题目、校验一个数独解是否合法、以及求解给定的数独题目。

## 安装

```bash
pip install fungame-sudoku
```

注意：发布包名是 `fungame-sudoku`，但导入用的是顶层包名 `fungame`（`src/fungame/sudoku/`），不是 `import fungame_sudoku`。

## 用法示例

```python
from fungame.sudoku import Sudoku, sudoku_check_solution, sudoku_generate, sudoku_solve_solution

# 求解一个数独题目（0 表示空格，长度为 81 的一维数组或 9x9 二维数组均可）
puzzle = [
    8, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 3, 6, 0, 0, 0, 0, 0,
    0, 7, 0, 0, 9, 0, 2, 0, 0,
    0, 5, 0, 0, 0, 7, 0, 0, 0,
    0, 0, 0, 0, 4, 5, 7, 0, 0,
    0, 0, 0, 1, 0, 0, 0, 3, 0,
    0, 0, 1, 0, 0, 0, 0, 6, 8,
    0, 0, 8, 5, 0, 0, 0, 1, 0,
    0, 9, 0, 0, 0, 0, 4, 0, 0,
]
solved = sudoku_solve_solution(puzzle)      # 排除法 + 回溯，返回求解后的 9x9 数组
sudoku_check_solution(solved)               # 校验每行/每列/每个九宫格是否 1-9 不重复
```

`Sudoku` 类实现了完整的排除法 + 回溯求解算法，`sudoku_solve_solution(array, method=1|2)` 提供两种求解策略（`method=1` 用 `Sudoku` 类回溯求解，`method=2` 用一种基于最少候选数优先的随机填数策略），`sudoku_solve_solution()` 和 `sudoku_check_solution()` 均已验证可正常工作。

## 已知问题

`sudoku_generate(mask_rate=0.5)` 用于随机生成一个新的数独题目，但其实现按行按列贪心填数、遇到某个格子无候选数字时只会整体重来（外层 `while True` 从头再生成一整个 9x9 网格），而不是对已填的格子做真正的回溯。这个算法在统计上大概率会反复冲突、重新整表生成，实践中经常长时间不收敛，**不建议在生产环境使用**；如需生成题目建议自行实现或寻找其他方案。
