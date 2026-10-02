# Changelog

## [未发布]

### 修复

- `dev` 依赖组里 `pytest-timeout` 补上版本下限 `>=2.4.0`，不再是裸依赖名。
- `src/fungame/sudoku/__init__.py` 补充导出 `SudokuUnsolvableError`，此前只能从
  `fungame.sudoku.core` 内部模块访问，调用方无法在包顶层 `import` 它来做异常捕获。

### 新增

- `tests/test_smoke.py` 新增 `sudoku_solve_solution(method=2)`、`sudoku_check_solution()`
  的 CSV 文件输入、非法棋盘形状、无解题目抛出 `SudokuUnsolvableError`、
  `sudoku_generate()` 非法 `mask_rate` 等公开 API 的正常路径与边界/失败路径测试；
  测试模块说明、docstring、注释统一改为中文。

## [1.0.3] - 2026-09-19

### 修复

- 修复 `sudoku_generate()` 贪心填数遇冲突即整盘重来、实践中经常长时间不收敛的问题，改为随机顺序回溯算法，保证有限步内稳定收敛。
- `recall()` 无解时不再抛出裸 `Exception`，改为领域异常 `SudokuUnsolvableError`。
- 日志改用组织统一日志包 `farlog`，不再裸用标准库 `logging`；`example/example1.py` 不再依赖已废弃的 `funtool.log`。

### 新增

- `tests/test_smoke.py` 补充 `sudoku_generate()` 的正常路径与边界（`mask_rate=0`、`mask_rate=1`）测试。
- 公开类 `Sudoku` 及公开函数补充 3.10 风格类型标注与中文 docstring。

### 变更

- `pyproject.toml` 补充 `license = "MIT"`、`numpy`/`farlog` 依赖版本下限。
- `.gitignore` 补充 `*.db`、`*.rar`、`.run/`、`logs/`、`.idea/`、`.vscode/`。
