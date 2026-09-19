"""数独（Sudoku）生成、求解与校验的核心实现。"""

from __future__ import annotations

import copy
import random
from queue import LifoQueue, Queue

import numpy as np
from farlog import getLogger

logger = getLogger("fungame-sudoku")


class SudokuUnsolvableError(Exception):
    """数独无解时抛出：回溯队列已耗尽，仍未找到满足约束的填数方案。"""


class Recorder:
    """回溯记录：保存一次猜测发生时的坐标、候选索引与整盘快照。"""

    point = None  # 进行猜测的点
    point_index = 0  # 猜测候选列表使用的值的索引
    value = None  # 回溯记录的值


class Sudoku:
    """数独求解器：排除法 + 回溯猜测，直到得到唯一确定解。"""

    def __init__(self, data: list | np.ndarray) -> None:
        """初始化数独盘面。

        Args:
            data: 长度为 81 的一维数组，或 9x9 的二维数组，`0` 表示空格。
        """
        # 数据初始化(二维的object数组)
        self.value = np.array(
            [[0] * 9] * 9, dtype=object
        )  # 数独的值，包括未解决和已解决的
        self.new_points = Queue()  # 先进先出，新解（已解决值）的坐标
        self.recorder = LifoQueue()  # 先进后出，回溯器
        self.guess_times = 0  # 猜测次数

        # 九宫格的基准列表
        self.base_points = [
            [0, 0],
            [0, 3],
            [0, 6],
            [3, 0],
            [3, 3],
            [3, 6],
            [6, 0],
            [6, 3],
            [6, 6],
        ]

        # 整理数据
        _data = np.array(data).reshape(9, -1)
        for r in range(9):
            for c in range(9):
                if _data[r, c]:  # if not Zero
                    # numpy default is int32, convert to int
                    self.value[r, c] = int(_data[r, c])
                    # 新的确认的值添加到列表中，以便遍历
                    self.new_points.put((r, c))
                    # logger.debug(f'init: answer={self.value[r, c]} at {(r, c)}')
                else:  # if Zero, guess no. is 1-9
                    self.value[r, c] = [1, 2, 3, 4, 5, 6, 7, 8, 9]

    # 剔除数字
    def _cut_num(self, point: tuple[int, int]) -> None:
        r, c = point
        val = self.value[r, c]

        # 行
        for i, item in enumerate(self.value[r]):
            if isinstance(item, list):
                if item.count(val):
                    item.remove(val)

                    # 判断移除后，是否剩下一个元素
                    if len(item) == 1:
                        self.new_points.put((r, i))  # 添加坐标到“已解决”列表
                        logger.debug(
                            f"only one in row: answer={self.value[r, i]} at {(r, i)}"
                        )
                        self.value[r, i] = item[0]

        # 列
        for i, item in enumerate(self.value[:, c]):
            if isinstance(item, list):
                if item.count(val):
                    item.remove(val)

                    # 判断移除后，是否剩下一个元素
                    if len(item) == 1:
                        self.new_points.put((i, c))
                        logger.debug(
                            f"only one in col: answer={self.value[i, c]} at {(i, c)}"
                        )
                        self.value[i, c] = item[0]

        # 所在九宫格(3x3的数组)
        b_r, b_c = map(lambda x: x // 3 * 3, point)  # 九宫格基准点
        for m_r, row in enumerate(self.value[b_r : b_r + 3, b_c : b_c + 3]):
            for m_c, item in enumerate(row):
                if isinstance(item, list):
                    if item.count(val):
                        item.remove(val)

                        # 判断移除后，是否剩下一个元素
                        if len(item) == 1:
                            r = b_r + m_r
                            c = b_c + m_c
                            self.new_points.put((r, c))
                            # logger.debug(f'only one in block: answer={self.value[r, c]} at {(r, c)}')
                            self.value[r, c] = item[0]

    # 同一行、列或九宫格中, List里，可能性只有一个的情况
    def _check_one_possible(self) -> bool | None:
        # 同一行只有一个数字的情况
        for r in range(9):
            # 只取出是这一行是List的格子
            values = list(filter(lambda x: isinstance(x, list), self.value[r]))

            for c, item in enumerate(self.value[r]):
                if isinstance(item, list):
                    for value in item:
                        if sum(map(lambda x: x.count(value), values)) == 1:
                            self.value[r, c] = value
                            self.new_points.put((r, c))
                            logger.debug(
                                f"list val is only one in row: answer={self.value[r, c]} at {(r, c)}"
                            )
                            return True

        # 同一列只有一个数字的情况
        for c in range(9):
            values = list(filter(lambda x: isinstance(x, list), self.value[:, c]))

            for r, item in enumerate(self.value[:, c]):
                if isinstance(item, list):
                    for value in item:
                        if sum(map(lambda x: x.count(value), values)) == 1:
                            self.value[r, c] = value
                            self.new_points.put((r, c))
                            logger.debug(
                                f"list val is only one in col: answer={self.value[r, c]} at {(r, c)}"
                            )
                            return True

        # 九宫格内的单元格只有一个数字的情况
        for r, c in self.base_points:
            # reshape: 3x3 改为1维数组
            values = list(
                filter(
                    lambda x: isinstance(x, list),
                    self.value[r : r + 3, c : c + 3].reshape(1, -1)[0],
                )
            )

            for m_r, row in enumerate(self.value[r : r + 3, c : c + 3]):
                for m_c, item in enumerate(row):
                    if isinstance(item, list):
                        for value in item:
                            if sum(map(lambda x: x.count(value), values)) == 1:
                                self.value[r + m_r, c + m_c] = value
                                self.new_points.put((r + m_r, c + m_c))
                                logger.debug(
                                    f"list val is only one in block: answer={self.value[r + m_r, c + m_c]} at {(r + m_r, c + m_c)}"
                                )
                                return True

    # 同一个九宫格内数字在同一行或同一列处理(同行列隐性排除)
    def _check_same_num(self) -> bool | None:
        for b_r, b_c in self.base_points:
            block = self.value[b_r : b_r + 3, b_c : b_c + 3]

            # 判断数字1~9在该九宫格的分布情况
            _data = block.reshape(1, -1)[0]
            for i in range(1, 10):
                result = map(
                    lambda x: (
                        0
                        if not isinstance(x[1], list)
                        else x[0] + 1
                        if x[1].count(i)
                        else 0
                    ),
                    enumerate(_data),
                )
                result = list(filter(lambda x: x > 0, result))
                r_count = len(result)

                if r_count in [2, 3]:
                    # 2或3个元素才有可能同一行或同一列
                    rows = list(map(lambda x: (x - 1) // 3, result))
                    cols = list(map(lambda x: (x - 1) % 3, result))

                    if len(set(rows)) == 1:
                        # 同一行，去掉其他行的数字
                        result = list(map(lambda x: b_c + (x - 1) % 3, result))
                        row = b_r + rows[0]

                        for col in range(9):
                            if col not in result:
                                item = self.value[row, col]
                                if isinstance(item, list):
                                    if item.count(i):
                                        item.remove(i)

                                        # 判断移除后，是否剩下一个元素
                                        if len(item) == 1:
                                            self.new_points.put((row, col))
                                            logger.debug(
                                                f"block compare row: answer={self.value[row, col]} at {(row, col)}"
                                            )
                                            self.value[row, col] = item[0]
                                            return True

                    elif len(set(cols)) == 1:
                        # 同一列
                        result = list(map(lambda x: b_r + (x - 1) // 3, result))
                        col = b_c + cols[0]

                        for row in range(9):
                            if row not in result:
                                item = self.value[row, col]
                                if isinstance(item, list):
                                    if item.count(i):
                                        item.remove(i)

                                        # 判断移除后，是否剩下一个元素
                                        if len(item) == 1:
                                            self.new_points.put((row, col))
                                            logger.debug(
                                                f"block compare col: answer={self.value[row, col]} at {(row, col)}"
                                            )
                                            self.value[row, col] = item[0]
                                            return True

    # 排除法解题
    def sudo_exclude(self) -> None:
        """反复应用排除法（唯余法 + 区块摒除法），推进盘面直到无法再确定新格。"""
        is_run_same = True
        is_run_one = True

        while is_run_same:
            while is_run_one:
                # 剔除数字
                while not self.new_points.empty():
                    point = self.new_points.get()  # 先进先出
                    self._cut_num(point)

                # 检查List里值为单个数字的情况，如有新answer则加入new_points Queue，立即_cut_num
                is_run_one = self._check_one_possible()

            # 检查同行或列的情况
            is_run_same = self._check_same_num()
            is_run_one = True

    # 得到有多少个确定的数字
    def get_num_count(self) -> int:
        """返回当前盘面中已确定（非候选列表）的格子数量。"""
        return sum(
            map(lambda x: 1 if isinstance(x, int) else 0, self.value.reshape(1, -1)[0])
        )

    # 评分，找到最佳的猜测坐标
    def get_best_point(self) -> tuple[int, int]:
        """挑选候选数最少、且所在行列已确定数字最多的格子，作为下一次猜测点。"""
        best_score = 0
        best_point = (0, 0)

        for r, row in enumerate(self.value):
            for c, item in enumerate(row):
                point_score = self._get_point_score((r, c))
                if best_score < point_score:
                    best_score = point_score
                    best_point = (r, c)
        return best_point

    # 计算某坐标的评分
    def _get_point_score(self, point: tuple[int, int]) -> int:
        # 评分标准 (10-候选个数) + 同行确定数字个数 + 同列确定数字个数
        r, c = point
        item = self.value[r, c]

        if isinstance(item, list):
            score = 10 - len(item)
            score += sum(map(lambda x: 1 if isinstance(x, int) else 0, self.value[r]))
            score += sum(
                map(lambda x: 1 if isinstance(x, int) else 0, self.value[:, c])
            )
            return score
        else:
            return 0

    # 验证有没错误
    def check_value(self) -> bool:
        """校验当前盘面是否仍然自洽：每行/列/九宫格已填数字不重复，且候选列表非空。"""
        # 行
        r = 0
        for row in self.value:
            nums = []
            lists = []
            for item in row:
                (lists if isinstance(item, list) else nums).append(item)
            if len(set(nums)) != len(nums):
                # logger.error(f'verify failed. dup in row {r}')
                logger.debug(f"verify failed. dup in row {r}")
                return False  # 数字要不重复
            if len(list(filter(lambda x: len(x) == 0, lists))):
                return False  # 候选列表不能为空集
            r += 1

        # 列
        for c in range(9):
            nums = []
            lists = []
            col = self.value[:, c]

            for item in col:
                (lists if isinstance(item, list) else nums).append(item)
            if len(set(nums)) != len(nums):
                logger.debug(f"verify failed. dup in col {c}")
                return False  # 数字要不重复
            if len(list(filter(lambda x: len(x) == 0, lists))):
                return False  # 候选列表不能为空集

        # 九宫格
        for b_r, b_c in self.base_points:
            nums = []
            lists = []
            block = self.value[b_r : b_r + 3, b_c : b_c + 3].reshape(1, -1)[0]

            for item in block:
                (lists if isinstance(item, list) else nums).append(item)
            if len(set(nums)) != len(nums):
                logger.debug(f"verify failed. dup in block {(b_r, b_c)}")
                return False  # 数字要不重复
            if len(list(filter(lambda x: len(x) == 0, lists))):
                return False  # 候选列表不能为空集
        return True

    # 猜测记录
    def record_guess(self, point: tuple[int, int], index: int = 0) -> None:
        """记录一次猜测（用于失败后回溯），并沿该猜测继续排除法求解。

        Args:
            point: 猜测格子的坐标 (行, 列)。
            index: 使用该格子候选列表中第几个值（默认第 0 个）。
        """
        # 记录
        recorder = Recorder()
        recorder.point = point
        recorder.point_index = index
        # recorder.value = self.value.copy() #numpy的copy不行
        recorder.value = copy.deepcopy(self.value)
        self.recorder.put(recorder)
        logger.debug(f"added to LIFO queue: {[x.point for x in self.recorder.queue]}")
        self.guess_times += 1  # 记录猜测次数

        # 新一轮的排除处理
        item = self.value[point]
        # assume only 1 in this point
        self.value[point] = item[index]
        self.new_points.put(point)
        logger.debug(f"guessing: answer={self.value[point]}/{item} @{point}")
        self.sudo_exclude()

    # 回溯，需要先进后出
    def recall(self) -> None:
        """回溯到上一次猜测，尝试该格候选列表中的下一个值。

        Raises:
            SudokuUnsolvableError: 回溯队列已空，说明题目本身无解。
        """
        while True:
            if self.recorder.empty():
                raise SudokuUnsolvableError(
                    "数独无解：回溯队列已空，未找到满足约束的填数方案"
                )
            else:
                recorder = self.recorder.get()
                point = recorder.point
                index = recorder.point_index + 1
                item = recorder.value[point]

                # 判断索引是否超出范围
                # if not exceed，则再回溯一次
                if index < len(item):
                    break
                # if exceed, pop next recorder
                logger.debug("Recall! Try previous point.")

        logger.debug(f"Recall! Try next possible in same point, {item[index]} @{point}")
        self.value = recorder.value
        self.record_guess(point, index)

    # Main function 解题
    def sudo_solve(self) -> None:
        """求解入口：先用排除法推进，遇到冲突再猜测+回溯，直到全部 81 格确定。

        Raises:
            SudokuUnsolvableError: 题目无解。
        """
        # 第一次解题，排除法
        logger.debug("excluding knowning answers")
        self.sudo_exclude()
        logger.debug(f"excluded, current result:\n{self.value}")

        # 检查有没错误的，有错误的则回溯；没错误却未解开题目，则再猜测
        while True:
            if self.check_value():
                fixed_answer = self.get_num_count()
                logger.debug(f"current no. of fixed answers: {fixed_answer}")
                if fixed_answer == 81:
                    break
                else:
                    # 获取最佳猜测点
                    point = self.get_best_point()
                    logger.debug(f"Adding new guessing in LIFO, {point}")

                    # 记录并处理
                    self.record_guess(point)
                    logger.debug(f"guessed, current result:\n{self.value}")
            else:
                # 出错，则回溯，尝试下一个猜测
                self.recall()


def _generate_full_grid() -> list[list[int]]:
    """用随机顺序回溯填数，生成一个完整合法的 9x9 数独解。

    与逐格贪心、失败即整盘重来的朴素算法不同，这里在候选耗尽时只回退到
    上一个格子重新尝试，因此保证能在有限步内收敛，不会长时间不收敛。
    """
    grid = [[0] * 9 for _ in range(9)]

    def is_valid(r: int, c: int, v: int) -> bool:
        for i in range(9):
            if grid[r][i] == v or grid[i][c] == v:
                return False
        br, bc = (r // 3) * 3, (c // 3) * 3
        for i in range(br, br + 3):
            for j in range(bc, bc + 3):
                if grid[i][j] == v:
                    return False
        return True

    def backtrack(pos: int) -> bool:
        if pos == 81:
            return True
        r, c = divmod(pos, 9)
        candidates = list(range(1, 10))
        random.shuffle(candidates)
        for v in candidates:
            if is_valid(r, c, v):
                grid[r][c] = v
                if backtrack(pos + 1):
                    return True
                grid[r][c] = 0
        return False

    if not backtrack(0):  # pragma: no cover - 数学上不可能发生，仅作防御
        raise SudokuUnsolvableError("生成完整数独解时发生意外冲突")
    return grid


def sudoku_generate(mask_rate: float = 0.5) -> np.ndarray:
    """随机生成一道数独题目。

    先用随机顺序回溯填出一个完整合法解，再按 `mask_rate` 随机挖空部分格子。

    Args:
        mask_rate: 挖空比例，取值范围 [0, 1]，默认 0.5。

    Returns:
        9x9 的 `numpy.ndarray`，`0` 表示挖空的格子。
    """
    grid = np.array(_generate_full_grid(), dtype=int)
    mask = np.random.choice(
        [True, False], size=grid.shape, p=[mask_rate, 1 - mask_rate]
    )
    grid[mask] = 0
    return grid


def sudoku_check_solution(m: list | str | np.ndarray) -> bool:
    """校验一个数独解是否合法：每行、每列、每个九宫格都恰好包含 1-9。

    Args:
        m: 9x9 数据，可以是二维列表、`numpy.ndarray`，或以逗号分隔的 CSV 文件路径。

    Returns:
        合法为 `True`，否则为 `False`。
    """
    if isinstance(m, list):
        m = np.array(m)
    elif isinstance(m, str):
        m = np.loadtxt(m, dtype=int, delimiter=",")
    set_rg = set(np.arange(1, m.shape[0] + 1))
    no_good = False
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            r1 = (
                set(
                    m[
                        3 * (i // 3) : 3 * (i // 3 + 1), 3 * (j // 3) : 3 * (j // 3 + 1)
                    ].ravel()
                )
                == set_rg
            )
            r2 = set(m[i, :]) == set_rg
            r3 = set(m[:, j]) == set_rg
            if not (r1 and r2 and r3):
                no_good = True
                break
        if no_good:
            break
    if no_good:
        logger.info("Checked: not good")
    else:
        logger.info("Checked: OK")

    return not no_good


def sudoku_solve_solution1(array: list | str | np.ndarray) -> np.ndarray:
    """用 `Sudoku` 类的排除法 + 回溯求解数独题目。

    Args:
        array: 长度为 81 的一维数组，或 9x9 的二维数组，`0` 表示空格。

    Returns:
        求解后的 9x9 `numpy.ndarray`。

    Raises:
        SudokuUnsolvableError: 题目无解。
    """
    sudo = Sudoku(array)
    sudo.sudo_solve()
    return sudo.value


def sudoku_solve_solution2(array: list | str | np.ndarray) -> np.ndarray:
    """基于最少候选数优先的随机填数策略求解数独题目（不保证唯一解路径）。

    Args:
        array: 9x9 二维数组或长度为 81 的一维数组，也可以是 CSV 文件路径。

    Returns:
        求解后的 9x9 `numpy.ndarray`。
    """
    if isinstance(array, list):
        array = np.array(array)
    elif isinstance(array, str):
        array = np.loadtxt(array, dtype=int, delimiter=",")
    rg = np.arange(array.shape[0] + 1)
    while True:
        mt = array.copy()
        while True:
            d = []
            d_len = []
            for i in range(array.shape[0]):
                for j in range(array.shape[1]):
                    if mt[i, j] == 0:
                        possibles = np.setdiff1d(
                            rg,
                            np.union1d(
                                np.union1d(mt[i, :], mt[:, j]),
                                mt[
                                    3 * (i // 3) : 3 * (i // 3 + 1),
                                    3 * (j // 3) : 3 * (j // 3 + 1),
                                ],
                            ),
                        )
                        d.append([i, j, possibles])
                        d_len.append(len(possibles))
            if len(d) == 0:
                break
            idx = np.argmin(d_len)
            i, j, p = d[idx]
            if len(p) > 0:
                num = np.random.choice(p)
            else:
                break
            mt[i, j] = num
            if len(d) == 0:
                break
        if np.all(mt != 0):
            break

    return mt


def sudoku_solve_solution(
    array: list | str | np.ndarray, method: int = 1
) -> np.ndarray:
    """求解数独题目的统一入口。

    Args:
        array: 长度为 81 的一维数组，或 9x9 的二维数组/CSV 文件路径，`0` 表示空格。
        method: `1` 使用 `Sudoku` 类回溯求解；`2` 使用最少候选数优先的随机填数策略。

    Returns:
        求解后的 9x9 `numpy.ndarray`。
    """
    if method == 1:
        return sudoku_solve_solution1(array)
    else:
        return sudoku_solve_solution2(array)
