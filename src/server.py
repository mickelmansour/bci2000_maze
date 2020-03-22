from connect_util import TCPServer
import sys

MSG_USAGE = 'Usage: python3 server.py <IPv4_HOST> <PORT>'
MSG_USAGE_IE = '\ni.e. python3 server.py 127.0.0.1 9001'

def main():
	try:
		if len(sys.argv) == 3:
			server = TCPServer(sys.argv[1], int(sys.argv[2]))
			server.setup_host()
			while True:
				pass
		else:
			print(MSG_USAGE+MSG_USAGE_IE, flush=True)
	except KeyboardInterrupt:
		print("Closing Server...", flush=True)

if __name__ == "__main__":
	main()