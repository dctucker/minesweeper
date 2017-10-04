import random
import numpy as np
import curses


class Board:
	SWEEPED = 1
	FLAGGED = 2
	MINE = 4

	def __init__(self, size):
		self.height = size[0]
		self.width = size[1]
		self.grid = np.zeros(size)

	def add_random_mines(self, count):
		for m in range(count):
			i = random.randint(0, self.height - 1)
			j = random.randint(0, self.width - 1)
			self.grid[i,j] = self.MINE

	def mine_count(self):
		ret = 0
		for i in range(self.height):
			for j in range(self.width):
				ret += self.cell_mines((i,j))
		return ret

	def flag_count(self):
		ret = 0
		for i in range(self.height):
			for j in range(self.width):
				if int(self.grid[i,j]) & self.FLAGGED:
					ret += 1
		return ret

	def correct_flag_count(self):
		ret = 0
		for i in range(self.height):
			for j in range(self.width):
				if int(self.grid[i,j]) & self.FLAGGED:
					ret += self.cell_mines((i,j))
		return ret

	def fully_sweeped(self):
		for i in range(self.height):
			for j in range(self.width):
				cell = int(self.grid[i,j])
				if not cell & self.SWEEPED:
					if cell & self.FLAGGED and self.cell_mines((i,j)) > 0:
						continue
					return False
		return True

	def mine_triggered(self):
		for i in range(self.height):
			for j in range(self.width):
				cell = int(self.grid[i,j])
				if cell & self.SWEEPED and cell & self.MINE:
					return True
		return False

	
	def draw_cell(self, coord):
		cell = int(self.grid[coord])
		if cell & self.SWEEPED:
			if cell & self.MINE:
				return "*"
			else:
				adjacent = self.count_adjacent(coord)
				if adjacent == 0:
					return " "
				return str(adjacent)
		elif cell & self.FLAGGED:
			return "X"
		else:
			return "."

	def sweep_cell(self, coord):
		if coord[0] < 0 or coord[0] >= self.height or coord[1] < 0 or coord[1] >= self.width:
			return 0
		cell = int(self.grid[coord])
		if cell & self.SWEEPED:
			return
		self.grid[coord] = cell | 1
		mines = self.cell_mines(coord)
		adjacent = self.count_adjacent(coord)
		if mines == 0 and adjacent == 0:
			self.sweep_adjacent_cells(coord)
		return mines

	def sweep_adjacent_cells(self, coord):
		for adjacent in self.get_adjacents(coord):
			self.sweep_cell(adjacent)

	def flag_cell(self, coord):
		cell = int(self.grid[coord])
		self.grid[coord] = cell ^ 2

	def reveal_all_mines(self):
		for i in range(self.height):
			for j in range(self.width):
				if int(self.grid[i,j]) & self.MINE:
					self.grid[i,j] = int(self.grid[i,j]) | 1

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

class Controller:
	def __init__(self, board):
		self.cursor = [board.height / 2, board.width / 2]
		self.board = board
		self.alive = True

	def move_cursor(self, direction):
		new_x = self.cursor[0] + direction[0]
		if 0 <= new_x and new_x < self.board.width:
			self.cursor[0] = new_x
		new_y = self.cursor[1] + direction[1]
		if 0 <= new_y and new_y < self.board.height:
			self.cursor[1] = new_y

	def key_press(self, c):
		if not self.alive:
			return
		if c == curses.KEY_LEFT:
			self.move_cursor((0, -1))
		elif c == curses.KEY_RIGHT:
			self.move_cursor((0, 1))
		elif c == curses.KEY_UP:
			self.move_cursor((-1, 0))
		elif c == curses.KEY_DOWN:
			self.move_cursor((1, 0))
		elif c == ord('/'):
			self.board.flag_cell((self.cursor[0], self.cursor[1]))
		elif c == ord(' '):
			mines = self.board.sweep_cell((self.cursor[0], self.cursor[1]))
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

	def draw_board(self, board):
		self.screen.clear()
		self.screen.addstr( board.height+1, 0, str(board.mine_count() - board.flag_count()) + " mines" )
		if board.fully_sweeped():
			self.screen.addstr( board.height+2, 0, "All mines found, good work" )
		elif board.mine_triggered():
			self.screen.addstr( board.height+2, 0, "You stepped on a mine. Nice knowin' ya!" )


		for i in range(board.height):
			for j in range(board.width):
				char = board.draw_cell((i,j))
				if char in ('1','2','3','4','5','6','7','8'):
					color = int(char)
				elif char == '*':
					color = 9
				elif char == 'X':
					color = 10
				else:
					color = 0
				self.screen.addstr(i,j*2, char, curses.color_pair(color) )

		self.screen.refresh()


def main(stdscr):
	board = Board((12,12))
	board.add_random_mines(8)
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
