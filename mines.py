#!/usr/bin/env python3

import random
import numpy as np
import curses
import argparse

class Board:
	SWEEPED = 1
	FLAGGED = 2
	MINE = 4

	# Setup
	def __init__(self, size):
		self.height = size[0]
		self.width = size[1]
		self.grid = np.zeros(size, dtype=int)

	def add_random_mines(self, count):
		for m in range(count):
			i = random.randint(0, self.height - 1)
			j = random.randint(0, self.width - 1)
			self.grid[i,j] = self.MINE

	# Getters
	def mine_count(self):
		ret = 0
		for (i,j), cell in np.ndenumerate(self.grid):
			ret += self.cell_mines((i,j))
		return ret

	def flag_count(self):
		ret = 0
		for (i,j), cell in np.ndenumerate(self.grid):
			if int(cell) & self.FLAGGED:
				ret += 1
		return ret

	def correct_flag_count(self):
		ret = 0
		for (i,j), cell in np.ndenumerate(self.grid):
			if int(cell) & self.FLAGGED:
				ret += self.cell_mines((i,j))
		return ret

	def fully_sweeped(self):
		for (i,j), cell in np.ndenumerate(self.grid):
			cell = int(cell)
			if not cell & self.SWEEPED:
				if cell & self.FLAGGED and self.cell_mines((i,j)) > 0:
					continue
				return False
		return True

	def mine_triggered(self):
		for (i,j), cell in np.ndenumerate(self.grid):
			cell = int(cell)
			if cell & self.SWEEPED and cell & self.MINE:
				return True
		return False

	def cell_mines(self, coord):
		if coord[0] < 0 or coord[0] >= self.height or coord[1] < 0 or coord[1] >= self.width:
			return 0
		if int(self.grid[coord]) & self.MINE:
			return 1
		return 0

	def get_adjacents(self, coord):
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

	def count_adjacent(self, coord):
		ret = 0
		for adjacent in self.get_adjacents(coord):
			ret += self.cell_mines(adjacent)
		return ret

	# Actions
	def sweep_cell(self, coord):
		if coord[0] < 0 or coord[0] >= self.height or coord[1] < 0 or coord[1] >= self.width:
			return 0
		cell = int(self.grid[coord])
		if cell & self.SWEEPED or cell & self.FLAGGED:
			return 0
		self.grid[coord] = cell | 1
		mines = self.cell_mines(coord)
		adjacent = self.count_adjacent(coord)
		if mines == 0 and adjacent == 0:
			self.sweep_adjacent_cells(coord)
		return mines

	def sweep_adjacent_cells(self, coord):
		ret = 0
		for adjacent in self.get_adjacents(coord):
			ret += self.sweep_cell(adjacent)
		return ret

	def flag_cell(self, coord):
		cell = int(self.grid[coord])
		self.grid[coord] = cell ^ 2

	def reveal_all_mines(self):
		for (i,j), cell in np.ndenumerate(self.grid):
			if int(cell) & self.MINE:
				self.grid[i,j] = int(cell) | 1


class Controller:
	def __init__(self, board):
		self.cursor = [board.height // 2, board.width // 2]
		self.board = board
		self.alive = True

	def move_cursor(self, direction):
		new_i = self.cursor[0] + direction[0]
		if 0 <= new_i and new_i < self.board.height:
			self.cursor[0] = new_i
		new_j = self.cursor[1] + direction[1]
		if 0 <= new_j and new_j < self.board.width:
			self.cursor[1] = new_j

	def key_press(self, c):
		mines = 0
		if not self.alive:
			return
		if c in (ord('h'), curses.KEY_LEFT):
			self.move_cursor((0, -1))
		elif c in (ord('l'), curses.KEY_RIGHT):
			self.move_cursor((0, 1))
		elif c in (ord('k'), curses.KEY_UP):
			self.move_cursor((-1, 0))
		elif c in (ord('j'), curses.KEY_DOWN):
			self.move_cursor((1, 0))
		elif c in ( ord('/'), ord('x') ):
			self.board.flag_cell((self.cursor[0], self.cursor[1]))
		elif c == ord(' '):
			mines += self.board.sweep_cell((self.cursor[0], self.cursor[1]))
		elif c == ord("\n"):
			mines += self.board.sweep_cell((self.cursor[0], self.cursor[1]))
			mines += self.board.sweep_adjacent_cells((self.cursor[0], self.cursor[1]))
		if mines > 0:
			self.board.reveal_all_mines()
			self.alive = False


class View:
	def __init__(self, screen):
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

	def draw_board(self, board):
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

	def cell_char(self, board, coord):
		cell = int(board.grid[coord])
		if cell & board.SWEEPED:
			if cell & board.MINE:
				return "*"
			else:
				adjacent = board.count_adjacent(coord)
				if adjacent == 0:
					return " "
				return str(adjacent)
		elif cell & board.FLAGGED:
			return "X"
		else:
			return "."


def main(stdscr):
	ap = argparse.ArgumentParser()
	ap.add_argument("-s", "--size", required=False,  default="12x12", help="Size of the board (e.g. 12x12)")
	ap.add_argument("-m", "--mines", required=False, type=int, default=8, help="number of mines to add to the board")
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
		if key == ord('q'):
			break
		ctrl.key_press(key)

if __name__ == '__main__':
	curses.wrapper(main)
