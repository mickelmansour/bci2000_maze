import sys
import threading as th
import queue

class Bar:
	def __init__(self, maxval):
		self.bar = ''
		self.bar_sz = 30
		self.iter = 1
		self.max_iter = maxval+1
		self.update_q = queue.Queue()
		self.destroy = False
		self.progress_symbol = '#'
		th.Thread(target=self.draw_bar, args=(), daemon=True).start()

	def update(self):
		self.update_q.put(1, block=True)
		self.iter += 1
		if self.iter > self.max_iter:
			self.destroy = True
			print('', flush=True)
	
	def draw_bar(self):
		iter_count = self.max_iter
		progress = 0
		percent = 0
		for i in range(self.bar_sz):
			self.bar+=' '
		sys.stdout.write("[%s] %d%%" % (self.bar, percent))
		sys.stdout.flush()
		while True:
			if iter_count > 1:
				if not self.update_q.empty() and self.update_q.get(block=True):
					self.bar = ''
					iter_count -= 1
					progress += round((self.bar_sz-progress)/iter_count)
					percent += round((100-percent)/iter_count)
					for i in range(progress):
						self.bar += self.progress_symbol
					for j in range(progress, self.bar_sz):
						self.bar += ' '
					sys.stdout.write("\b"* (self.bar_sz+6))
					sys.stdout.write("[%s] %d%%" % (self.bar, percent))
					sys.stdout.flush()
			if self.destroy:
				break