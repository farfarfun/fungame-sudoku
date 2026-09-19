# fungame-sudoku

数独（Sudoku）生成与求解工具库：随机生成数独题目、校验一个数独解是否合法、以及求解给定的数独题目。

## 安装

```bash
pip install fungame-sudoku
```

注意：发布包名是 `fungame-sudoku`，但导入路径是 `fungame.sudoku`（源码在 `src/fungame/sudoku/`），不是 `import fungame_sudoku`。`fungame` 是 farfarfun 组织下多个游戏相关子包共用的 [PEP 420 隐式命名空间包](https://peps.python.org/pep-0420/)，`src/fungame/` 目录本身不含 `__init__.py`，以便与同组织其他 `fungame-*` 发行包合并到同一个 `fungame` 顶层命名空间下。

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

# 随机生成一道新题目（mask_rate 为挖空比例）
puzzle2 = sudoku_generate(mask_rate=0.5)
```

`Sudoku` 类实现了完整的排除法 + 回溯求解算法，`sudoku_solve_solution(array, method=1|2)` 提供两种求解策略（`method=1` 用 `Sudoku` 类回溯求解，`method=2` 用一种基于最少候选数优先的随机填数策略），`sudoku_solve_solution()` 和 `sudoku_check_solution()` 均已验证可正常工作。

## 数独生成

`sudoku_generate(mask_rate=0.5)` 使用随机顺序回溯算法生成一个完整合法解，再按 `mask_rate` 随机挖空部分格子，`mask_rate` 取值范围 `[0, 1]`。回溯在候选耗尽时只回退到上一个格子重试，能在有限步内稳定收敛。

---

## 关于 farfarfun

[farfarfun](https://github.com/farfarfun) 是一个专注于实用工具库的开源组织，
涵盖云存储、数据处理、AI、多媒体与开发工具链等方向。

- 🏠 组织主页：<https://github.com/farfarfun>
- 📦 PyPI：<https://pypi.org/user/niuliangtao/>
- 📧 联系：farfarfun@qq.com

本项目基于 [MIT](LICENSE) 协议开源。
