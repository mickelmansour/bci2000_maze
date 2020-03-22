import turtle
import time
import queue
from maze_template import *
import math
from datetime import datetime as dt_dt
import datetime as dt
import socket
import sys
from progress_bar import Bar
from connect_util import Pkg

class OutOfBounds(BaseException):
	def __init__(self, msg, x, y):
		self.msg = msg
		self.x = x
		self.y = y

class GameCtrl:
	players = []
	ready = []
	tcp = []
	start_pos = [20, 38]
	travel_t = 1
	server_up = 0
	f_mv = [0, -1]
	b_mv = [0, 1]
	l_mv = [-1, 0]
	r_mv = [1, 0]
	ONE_SEC = dt.timedelta(seconds=1)
	sec_till_start = 10
	game_started = 0
	MSG_START = "Go...Go...Go..."
	MSG_WILL_START = "Game will start in:"
	MSG_WAIT_JOIN = "Waiting for players to join..."
	ERR_EXISTS = "Player with same attributes already exists"
	TEST_COUNT = 9
	MAX_PLAYERS = 5
	ERR_FLAG = -9999
	
	def __init__(self, ui, sckt_tcp, file_status):
		self.sckt_tcp = sckt_tcp
		self.file_status = file_status
		self.ui = ui
	
	def start(self):
		try:
			self.discover_players()
			self.wait()
			self.count_down()
			self.update_ui()
		except KeyboardInterrupt:
			print('', flush=True)
		self.ui.close()
	
	def discover_players(self):
		bar = Bar(self.TEST_COUNT-1)
		for i in range(self.TEST_COUNT):
			self.status(self.sckt_tcp.status, self.file_status)
			time.sleep(3)
			if not self.sckt_tcp.rcv_buff.empty():
				pkg = self.sckt_tcp.rcv_buff.get(block=True)
				if pkg.val == '_x_join_x_':
					self.sckt_tcp.send_buff.put(pkg, block=True)
					if not self.get_player(pkg.ip, pkg.clr):
						if self.is_unique_clr(pkg.clr) and len(self.players) < self.MAX_PLAYERS:
							self.add2players(self.create_player(pkg.ip, pkg.clr))
						elif not self.is_unique_clr(pkg.clr) and \
							pkg.ip == socket.gethostbyname(socket.gethostname()):
							print('', flush=True)
							sys.stderr.write(self.ERR_EXISTS)
							sys.stderr.flush()
							raise KeyboardInterrupt
			bar.update()
	
	def wait(self):
		ips = []
		joined = 0
		print(self.MSG_WAIT_JOIN, flush=True)
		while joined < len(self.players):
			self.sckt_tcp.send_buff.put(Pkg('_x_ready_x_', socket.gethostbyname(socket.gethostname()), ''), block=True)
			pkg = self.sckt_tcp.rcv_buff.get(block=True)
			if pkg.val == '_x_ready_x_':
				try:
					index = ips.index(pkg.ip)
				except ValueError:
					index = -1
				if index == -1:
					ips.append(pkg.ip)
					joined += 1
		self.sckt_tcp.flush()
		
	def count_down(self):
		t_curr = dt_dt.now()
		t_last_count = dt_dt.now()
		print(self.MSG_WILL_START, flush=True)
		while self.sec_till_start >= 0 and \
			not self.status(self.sckt_tcp.status, self.file_status):
			while t_curr - t_last_count < self.ONE_SEC and \
				not self.status(self.sckt_tcp.status, self.file_status):
				t_curr = dt_dt.now()
			if self.sec_till_start == 0:
				print(self.MSG_START, flush=True)
			else:
				print(self.sec_till_start, flush=True)
			t_last_count = dt_dt.now()
			self.sec_till_start -= 1
	
	def update_ui(self):
		while not self.status(self.sckt_tcp.status, self.file_status):
			i = 0
			P = None
			if not self.sckt_tcp.rcv_buff.empty():
				c = self.sckt_tcp.rcv_buff.get(block=True)
				P = self.get_player(c.ip, c.clr)
				if P != None:
					try:
						if c.val == '_x_F_x_':
							P.crawl(self.f_mv[0], self.f_mv[1], self.travel_t)
						elif c.val == '_x_B_x_':
							P.crawl(self.b_mv[0], self.b_mv[1], self.travel_t)
						elif c.val == '_x_L_x_':
							P.crawl(self.l_mv[0], self.l_mv[1], self.travel_t)
						elif c.val == '_x_R_x_':
							P.crawl(self.r_mv[0], self.r_mv[1], self.travel_t)
					except OutOfBounds as e:
						print("%s (%d, %d)" % (e.msg, e.x, e.y), flush=True)

	def add2players(self, new_p):
		self.players.append(new_p)

	def is_unique_clr(self, clr):
		for p in self.players:
			if p.clr == clr:
				return False
		return True

	def get_player(self, ip, clr):
		for p in self.players:
			if p.ip == ip and p.clr == clr:
				return p
		return None

	def create_player(self, ip, clr):
		return Player(self.start_pos[0]+len(self.players)/3, self.start_pos[1], clr, ip)

	def status(self, *status_q):
		for q in status_q:
			if not q.empty() and q.get(block=True) == self.ERR_FLAG:
				raise KeyboardInterrupt

class GUI:
	WIN_MAX_X       = 650
	WIN_MAX_Y       = 650
	PX_LOW_LIMIT    = -300
	PX_HIGH_LIMIT   = 300
	SPRITE_SZ       = 15
	STEP_SZ         = 1
	MSG_EXIT        = "Closing UI..."
	ERR_MAP         = "Attempting to add element outside window"
	ERR_WALL        = "About to hit a wall"
	admin           = 0
	
	def __init__(self):
		self.win = turtle.Screen()
		self.cur = turtle
		
	def set_win(self): 
		self.win.bgcolor("white")
		self.win.setup(self.WIN_MAX_X, self.WIN_MAX_Y)
		self.win.tracer(0,0)

	def print_at(self, x, y):
		x, y = self.map_loc(x, y)
		if x < self.PX_LOW_LIMIT or y < self.PX_LOW_LIMIT \
			or x > self.PX_HIGH_LIMIT or y > self.PX_HIGH_LIMIT:
			raise OutOfBounds(self.ERR_MAP, x, y)
		self.cur.setpos(x, y)
		self.stmp_id = self.cur.stamp()
		self.win.update()
		return self.stmp_id	
	
	def rm_cur(self):
		self.cur.clearstamp(self.stmp_id)
		self.win.update()
	
	def close(self):
		print(self.MSG_EXIT, flush=True)
		self.win.bye()

	def map_loc(self, x, y):
		return (math.floor(self.SPRITE_SZ * x + self.PX_LOW_LIMIT), 
			math.floor(-1*self.SPRITE_SZ * y + self.PX_HIGH_LIMIT))

	def set_cursor(self, shp, clr, sz):
		self.cur.shape(shp)
		self.cur.color(clr)
		self.cur.shapesize(sz, sz, None)
		self.cur.penup()
		self.cur.speed(0)
		return self.cur
	
class Maze(GUI):
	
	def __init__(self):
		super(Maze, self).__init__()
		self.set_cursor("square", "black", 1)
		self.admin = 1

	def draw_maze(self):
		for pos_x in range(len(maze_template)):
			for pos_y in range(len(maze_template[pos_x])):
				if maze_template[pos_y][pos_x]:
					self.print_at(pos_x, pos_y)
		self.win.update()

class Player(GUI):
	DOT_SZ  = 0.7
	
	def __init__(self, start_x, start_y, clr, ip):
		super(Player, self).__init__()
		self.clr = clr
		self.ip  = ip
		self.r   = start_y
		self.c   = start_x
		self.set_cursor("circle", self.clr, self.DOT_SZ)
		self.print_at(start_x, start_y)

	def mv_cur(self, lr, ud):
		try:
			if not self.admin and self.near_wall(lr, ud):
				raise OutOfBounds(self.ERR_WALL, self.r+ud, self.c+lr)
			self.rm_cur()
			self.r+=ud
			self.c+=lr
			self.print_at(self.c, self.r)
		except IndexError:
			raise OutOfBounds(self.ERR_MAP, self.r+ud, self.c+lr)
		
	def near_wall(self, lr, ud):
		lr = lr/abs(lr) if lr else 0
		ud = ud/abs(ud) if ud else 0
		r_new = math.floor(round(self.r+ud))
		c_new = math.floor(round(self.c+lr))
		return True if maze_template[r_new][c_new] else False
		
	def crawl(self, lr, ud, t):
		baby_step = self.STEP_SZ/2
		self.set_cursor("circle", self.clr, self.DOT_SZ)
		t_inc = t/(abs(lr)+abs(ud))
		try:
			while lr != 0:
				if lr < 0:
					self.mv_cur(-1*baby_step, 0)
					lr += baby_step
				elif lr > 0:
					self.mv_cur(baby_step, 0)
					lr += -1*baby_step
				time.sleep(t_inc)
			while ud != 0:
				if ud < 0:
					self.mv_cur(0, -1*baby_step)
					ud += baby_step
				elif ud > 0:
					self.mv_cur(0, baby_step)
					ud += -1*baby_step
				time.sleep(t_inc)
		except OutOfBounds as e:
			raise e