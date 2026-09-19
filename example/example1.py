"""生成一道数独题目，并用两种求解策略分别求解、校验。"""

from farlog import getLogger

from fungame.sudoku import sudoku_check_solution, sudoku_generate, sudoku_solve_solution

logger = getLogger("fungame-sudoku-example")

if __name__ == "__main__":
    puzzle = sudoku_generate(mask_rate=0.7)

    solved1 = sudoku_solve_solution(puzzle, method=1)
    logger.info("method 1 solved")
    solved2 = sudoku_solve_solution(puzzle, method=2)
    logger.info("method 2 solved")

    sudoku_check_solution(solved1)
    sudoku_check_solution(solved2)
