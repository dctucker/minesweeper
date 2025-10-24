#!/usr/bin/env python3
# pylint: disable=import-error,wrong-import-position
"""minesweeper"""

import random
import curses
import argparse
import numpy as np

class Board:
	"""model the game board"""
	SWEEPED = 1
	FLAGGED = 2
	MINE = 4

	# Setup
	def __init__(self, size: int):
		self.height = size[0]
		self.width = size[1]
		self.grid = np.zeros(size, dtype=np.int8)

	def add_random_mines(self, count: int) -> None:
		"""adds mines to the board at random positions"""
		for _ in range(count):
			i = random.randint(0, self.height - 1)
			j = random.randint(0, self.width - 1)
			while self.grid[i,j] == self.MINE:
				i = random.randint(0, self.height - 1)
				j = random.randint(0, self.width - 1)

			self.grid[i,j] = self.MINE

	# Getters
	def mine_count(self) -> int:
		"""return the number of unidentified mines on the board"""
		ret = 0
		for (i,j), _ in np.ndenumerate(self.grid):
			ret += self.cell_mines((i,j))
		return ret

	def flag_count(self) -> int:
		"""return the number of flags placed on the board"""
		ret = 0
		for _, cell in np.ndenumerate(self.grid):
			if int(cell) & self.FLAGGED:
				ret += 1
		return ret

	def correct_flag_count(self) -> int:
		"""return the number of correctly-flagged mines on the board"""
		ret = 0
		for (i,j), cell in np.ndenumerate(self.grid):
			if int(cell) & self.FLAGGED:
				ret += self.cell_mines((i,j))
		return ret

	def fully_sweeped(self) -> bool:
		"""return True if the board no longer has any unflagged mines"""
		for (i,j), cell in np.ndenumerate(self.grid):
			cell = int(cell)
			if not cell & self.SWEEPED:
				if cell & self.FLAGGED and self.cell_mines((i,j)) > 0:
					continue
				return False
		return True

	def mine_triggered(self) -> bool:
		"""return True if sweeping an area has triggered a mine"""
		for _, cell in np.ndenumerate(self.grid):
			cell = int(cell)
			if cell & self.SWEEPED and cell & self.MINE:
				return True
		return False

	def cell_mines(self, coord: tuple[int,int]) -> int:
		"""return 1 if a mine is present in a given cell with bounds checking"""
		if coord[0] < 0 or coord[0] >= self.height or coord[1] < 0 or coord[1] >= self.width:
			return 0
		if int(self.grid[coord]) & self.MINE:
			return 1
		return 0

	def get_adjacents(self, coord: tuple[int,int]) -> tuple[tuple[int,int],...]:
		"""return a list containing the coordinates of all adjacent cells for the given coordinate"""
		return (
			( coord[0] - 1 , coord[1] - 1 ),
			( coord[0]     , coord[1] - 1 ),
			( coord[0] + 1 , coord[1] - 1 ),
			( coord[0] - 1 , coord[1]     ),
			( coord[0] + 1 , coord[1]     ),
			( coord[0] - 1 , coord[1] + 1 ),
			( coord[0]     , coord[1] + 1 ),
			( coord[0] + 1 , coord[1] + 1 ),
		)

	def count_adjacent(self, coord: tuple[int,int]) -> int:
		"""reutrn the total number of mines in all adjacent cells"""
		ret = 0
		for adjacent in self.get_adjacents(coord):
			ret += self.cell_mines(adjacent)
		return ret

	# Actions
	def sweep_cell(self, coord: tuple[int,int]) -> int:
		"""step on a cell, sweep adjacent cells if empty, or return how many mines were found"""
		if coord[0] < 0 or coord[0] >= self.height or coord[1] < 0 or coord[1] >= self.width:
			return 0
		cell = int(self.grid[coord])
		if cell & self.SWEEPED or cell & self.FLAGGED:
			return 0
		self.grid[coord] = cell | self.SWEEPED
		mines = self.cell_mines(coord)
		adjacent = self.count_adjacent(coord)

		if mines == 0 and adjacent == 0:
			self.sweep_adjacent_cells(coord)
		return mines

	def sweep_adjacent_cells(self, coord: tuple[int,int]) -> int:
		"""sweep all adjacent cells and return the number of mines found"""
		ret = 0
		for adjacent in self.get_adjacents(coord):
			ret += self.sweep_cell(adjacent)
		return ret

	def flag_cell(self, coord: tuple[int,int]) -> None:
		"""plant a flag on the specified cell"""
		cell = int(self.grid[coord])
		self.grid[coord] = cell ^ self.FLAGGED

	def reveal_all_mines(self) -> None:
		"""sweeps all the cells in the grid to reveal all mines and adjacencies"""
		for (i,j), cell in np.ndenumerate(self.grid):
			if int(cell) & self.MINE:
				self.grid[i,j] = int(cell) | self.SWEEPED


class Controller:
	"""provides the methods the allow user interaction with the game model"""
	def __init__(self, board):
		self.cursor = [board.height // 2, board.width // 2]
		self.board = board
		self.alive = True

	def get_cursor(self) -> tuple[int,int]:
		"""return a tuple representing the cursor coordinates"""
		return (self.cursor[0], self.cursor[1])

	def move_cursor(self, direction: tuple[int,int]) -> None:
		"""adjust the position of the cursor on the screen"""
		new_i = self.cursor[0] + direction[0]
		if 0 <= new_i < self.board.height:
			self.cursor[0] = new_i
		new_j = self.cursor[1] + direction[1]
		if 0 <= new_j < self.board.width:
			self.cursor[1] = new_j

	def explode_maybe(self, mines: int) -> None:
		"""explode if a non-zero number of mines were found"""
		if mines > 0:
			self.board.reveal_all_mines()
			self.alive = False

	def sweep_one(self) -> None:
		"""sweep the cell at the cursor"""
		mines = self.board.sweep_cell(self.get_cursor())
		self.explode_maybe(mines)

	def sweep_many(self) -> None:
		"""sweep the adjacent cells under the cursor"""
		mines = self.board.sweep_cell(self.get_cursor())
		mines += self.board.sweep_adjacent_cells(self.get_cursor())
		self.explode_maybe(mines)

	def flag(self) -> None:
		"""flag the cell at the cursor"""
		self.board.flag_cell(self.get_cursor())

	def key_press(self, c: int) -> bool:
		"""detect which key has been pressed and take the appropriate action"""
		if c in (ord('h'), curses.KEY_LEFT):
			self.move_cursor((0, -1))
		elif c in (ord('l'), curses.KEY_RIGHT):
			self.move_cursor((0, 1))
		elif c in (ord('k'), curses.KEY_UP):
			self.move_cursor((-1, 0))
		elif c in (ord('j'), curses.KEY_DOWN):
			self.move_cursor((1, 0))
		elif c in ( ord('/'), ord('x') ):
			self.flag()
		elif c == ord(' '):
			self.sweep_one()
		elif c == ord("\n"):
			self.sweep_many()
		elif c == ord('q'):
			return False
		return True


class View:
	"""provides the view of the game board"""
	def __init__(self, screen: curses.window):
		self.screen = screen
		curses.init_pair(1, curses.COLOR_CYAN,    curses.COLOR_BLACK)
		curses.init_pair(2, curses.COLOR_GREEN,   curses.COLOR_BLACK)
		curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
		curses.init_pair(4, curses.COLOR_BLUE,    curses.COLOR_BLACK)
		curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
		curses.init_pair(6, curses.COLOR_GREEN,   curses.COLOR_BLACK)
		curses.init_pair(7, curses.COLOR_WHITE,   curses.COLOR_BLACK)
		curses.init_pair(8, curses.COLOR_WHITE,   curses.COLOR_BLACK)
		curses.init_pair(9, curses.COLOR_BLACK,   curses.COLOR_RED)
		curses.init_pair(10, curses.COLOR_RED,    curses.COLOR_BLACK)
		curses.init_pair(11, curses.COLOR_BLUE,   curses.COLOR_BLUE)

	def draw_board(self, board: Board) -> None:
		"""render the game board on the screen, showing flags, mines, empty cells, and adjacencies"""
		self.screen.clear()

		self.screen.addstr(board.height, 0, ' ' * (board.width*2+1), curses.color_pair(11) )
		for i in range(board.height):
			self.screen.addstr(i, board.width*2, '|', curses.color_pair(11) )

			for j in range(board.width):
				char = self.cell_char(board, (i,j))
				if char in ('1','2','3','4','5','6','7','8'):
					color = int(char)
				elif char == '*':
					color = 9
				elif char == 'X':
					color = 10
				else:
					color = 0
				self.screen.addstr(i,j*2, char, curses.color_pair(color) )

		self.screen.addstr( board.height+1, 0, str(board.mine_count() - board.flag_count()) + " mines" )
		if board.fully_sweeped():
			self.screen.addstr( board.height+2, 0, "All mines found, good work" )
		elif board.mine_triggered():
			self.screen.addstr( board.height+2, 0, "You stepped on a mine. Nice knowin' ya!" )

		self.screen.refresh()

	def cell_char(self, board: Board, coord: tuple[int,int]) -> str:
		"""return a string representing a single cell of the game board"""
		cell = int(board.grid[coord])
		if cell & board.SWEEPED:
			if cell & board.MINE:
				return "*"

			adjacent = board.count_adjacent(coord)
			if adjacent == 0:
				return " "

			return str(adjacent)

		if cell & board.FLAGGED:
			return "X"

		return "."


def main(stdscr: curses.window):
	"""entrypoint"""
	ap = argparse.ArgumentParser()
	ap.add_argument("-s", "--size", required=False,  default="12x12",
		help="Size of the board (e.g. 12x12)")
	ap.add_argument("-m", "--mines", required=False, type=int, default=8,
		help="number of mines to add to the board")
	parsed_args = ap.parse_args()
	args = vars(parsed_args)

	width, height = args['size'].split('x')

	board = Board((int(height),int(width)))
	board.add_random_mines(args['mines'])
	ctrl = Controller(board)
	view = View(stdscr)

	while True:
		view.draw_board(board)
		stdscr.move( ctrl.cursor[0], ctrl.cursor[1] * 2 )
		key = stdscr.getch()
		if not ctrl.key_press(key):
			break

if __name__ == '__main__':
	curses.wrapper(main)
