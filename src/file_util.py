import re
import time
from datetime import datetime as dt_dt
import datetime as dt
import queue
from connect_util import Pkg

class FParse:
	REG         = ".*Selected command: ([A-Z_ ]).*"
	str_glbl    = ""
	TIME_OUT    = dt.timedelta(seconds=300)
	MSG_TIMEOUT = "Parser Timed out"
	ERR_NOT_FOUND = "File Not Found"
	MSG_CLOSE_F = "Closing BCI2000 app log: "
	ERR_FLAG = -9999
	
	def __init__(self, file_path, ip, clr, sckt_stream):
		self.path = file_path
		self.regex = re.compile(self.REG)
		self.ip = ip
		self.clr = clr
		self.sckt_stream = sckt_stream
		self.status = queue.Queue()

	def put_on_stream(self, e):
		self.sckt_stream.put(Pkg(e, self.ip, self.clr), block=True)

	def parse_f(self):
		t_curr = dt_dt.now()
		t_last_match = dt_dt.now()
		try:
			with open(self.path, "r+") as file:
				file.truncate(0)
				file.close()
			while t_curr - t_last_match < self.TIME_OUT:
				with open(self.path, "r") as file:
					matches = self.regex.findall(file.read())
					t_curr = dt_dt.now()
					if len(matches) > len(self.str_glbl):
						self.str_glbl = ""
						for m in matches:
							self.str_glbl += m
						if len(self.str_glbl) > 0:
							self.put_on_stream('_x_'+self.str_glbl[len(self.str_glbl)-1]+'_x_')
						t_last_match = dt_dt.now()
					file.close()
			print(self.MSG_TIMEOUT, flush=True)
			print(self.MSG_CLOSE_F + self.path, flush=True)
		except FileNotFoundError:
			print(self.ERR_NOT_FOUND)
		self.status.put(self.ERR_FLAG, block=True)
