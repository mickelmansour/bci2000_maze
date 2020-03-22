import threading
from ui import Maze, Player, GameCtrl
from connect_util import TCPClient, Pkg
from file_util import FParse
import socket
import sys
import time

MSG_CLOSE = "Closing app..."
MSG_USAGE = 'Usage: python3 join_game.py <IPv4_HOST> <PORT> <color> <BCI2000_app_log_path>'
MSG_USAGE_IE = '\ni.e. python3 join_game.py 127.0.0.1 9001 red C:\\Dir\\test001.applog'
MSG_READY = 'Are you Ready [y/n]: '
MSG_WAIT = "waiting...\n"

def main():
	try:
		if len(sys.argv) == 5:
			ui = Maze()
			ui.set_win()
			ui.draw_maze()
			
			p_ip = socket.gethostbyname(socket.gethostname())
			p_clr = sys.argv[3]
			
			tcp_c = TCPClient(sys.argv[1], int(sys.argv[2]))
			if tcp_c.join():
				file = FParse(sys.argv[4], p_ip, p_clr, tcp_c.send_buff)
				file_t = threading.Thread(target=file.parse_f, args=(), daemon=True)
				ready = 'n'
				request = 0
				while ready.lower() == 'n' and request < 5:
					ready = input(MSG_READY)
					request += 1
					if ready.lower() != 'y':
						sys.stdout.write(MSG_WAIT)
						sys.stdout.flush()
						time.sleep(5)
				if ready.lower() == 'y':
					file_t.start()
					tcp_c.send_buff.put(Pkg('_x_join_x_', p_ip, p_clr), block=True)
					gc = GameCtrl(ui, tcp_c, file.status)
					gc.start()	
		else:
			print(MSG_USAGE+MSG_USAGE_IE, flush=True)
	except KeyboardInterrupt:
		pass
	print(MSG_CLOSE, flush=True)

if __name__ == "__main__":
	main()
	