import bluetooth as BT
import subprocess
import socket
import threading
import queue
import pickle
import time

class TCPServer:
	BUFFER_SZ = 2400
	MSG_JOIN = "%s joined the network"
	MSG_WELCOME = "Server is Up and Running..."
	HOW2CLOSE = "Ctrl + C to close Server"
	MSG_FORWARD = "forwarding pkg to: %s"
	MSG_LEFT = "%s left the network"
	MSG_REJECT_JOIN = "Rejected %s request to join (already on network)"
	clients = []

	def __init__(self, IP, PORT):
		self.IP = IP
		self.PORT = PORT
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.run_host_t = threading.Thread(target=self.run_host, args=(self.sock,), daemon=True)
	
	def setup_host(self):
		self.sock.bind((self.IP, self.PORT))
		self.run_host_t.start()
	
	def run_host(self, server_sock):
		print(self.MSG_WELCOME, flush=True)
		print(self.HOW2CLOSE)
		server_sock.listen(1)
		while True:
			sock, (ip, ext) = server_sock.accept()
			client = ClientInfo(sock, ip, ext)
			if not self.on_network(client):
				self.clients.append(client)
				print(self.MSG_JOIN % ip, flush=True)
				client_t = threading.Thread(target=self.talk2client, args=(client,), daemon=True)
				client_t.start()
			else:
				print(self.MSG_REJECT_JOIN % client.ip)
	
	def talk2client(self, client):
		try:
			while True:
				pkg = client.sock.recv(self.BUFFER_SZ)
				if pkg:
					self.broadcast(client, pkg)
			client.sock.close()
		except ConnectionResetError:
			print(self.MSG_LEFT % client.ip)
			self.remove(client)
			
	def broadcast(self, sender, pkg):
		for c in self.clients:
			c.sock.send(pkg)
			print(self.MSG_FORWARD % c.ip , flush=True)
	
	def on_network(self, client):
		for c in self.clients:
			if c.ip == client.ip:
				return True
		return False
	
	def remove(self, client):
		for c in self.clients:
			if c.ip == client.ip:
				self.clients.remove(c)

class ClientInfo:
	def __init__(self, sock, ip, ext):
		self.sock = sock
		self.ip = ip
		self.ext = ext

class Pkg:
	def __init__(self, val, ip, clr):
		self.val = val
		self.ip = ip
		self.clr = clr

class TCPClient:
	BUFFER_SZ = 2400
	MSG_NOT_UP = "Server is not running"
	MSG_DISCONNECT = "Disconnected from server..."

	def __init__(self, IP, PORT):
		self.IP = IP
		self.PORT = PORT
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.send_buff = queue.Queue()
		self.rcv_buff = queue.Queue()
		self.send_t = threading.Thread(target=self.send, args=(self.sock,), daemon=True)
		self.rcv_t = threading.Thread(target=self.rcv, args=(self.sock,), daemon=True)
		self.status = queue.Queue()
		
	def join(self):
		try:
			self.sock.connect((self.IP, self.PORT))
			self.send_t.start()
			self.rcv_t.start()
			return True
		except socket.error:
			print(self.MSG_NOT_UP, flush=True)
			return False
	
	def send(self, sock):
		try:
			while True:
				if not self.send_buff.empty():
					sock.send(pickle.dumps(self.send_buff.get(block=True)))
					time.sleep(0.05)
		except ConnectionResetError as e:
			print(self.MSG_DISCONNECT, flush=True)
			self.status.put(-9999, block=True)
			
	def rcv(self, sock):
		try:
			while True:
				pkg = sock.recv(self.BUFFER_SZ)
				if not self.rcv_buff.full() and pkg:
					self.rcv_buff.put(pickle.loads(pkg), block=True)
		except ConnectionResetError as e:
			print(self.MSG_DISCONNECT, flush=True)
			self.status.put(-9999, block=True)
	
	def flush(self):
		with self.rcv_buff.mutex:
			self.rcv_buff.queue.clear()
		with self.send_buff.mutex:
			self.send_buff.queue.clear()
		

class BTConnect:
	TRIAL_COUNT     = 3
	SEARCH_FOR      = 5
	MSG_SEARCHING   = "Looking for nearby BT devices..."
	MSG_BTS         = "Nearby BT devices:"
	MSG_NO_BTS      = "No BT devices found"
	MSG_BT_NOTFOUND = "Could not locate target BT device"
	DIVIDER         = "+-----------------+---------------------+"
	format_lng      = "| %s | %s\t|"
	format_shrt     = "| %s\t  | %s\t|"
	COL_WIDTH       = 15
	MSG_BT_FOUND    = "Found target BT device"
	MSG_FIND_FAILED = "Make sure target BT device is in range and is turned on!"
	MSG_CONNECT     = "Connected to target BT device..."
	MSG_DISCONNECT  = "Disconnecting BT device..."
	
	def __init__(self, trgt_addr, trgt_port):
		self.port       = trgt_port
		self.trgt_addr  = trgt_addr
		self.sock       = BT.BluetoothSocket(BT.RFCOMM)
		
	def connect(self, addr):
		if addr != "":
			self.sock.connect((addr, self.port))
			print(self.MSG_CONNECT)
			
	def find(self):
		trial = 0
		addr = ""
		
		while addr == "" and trial < self.TRIAL_COUNT:
			trial+=1
			print(self.MSG_SEARCHING)
			bt_devices = BT.discover_devices(lookup_names = True, 
						 duration = self.SEARCH_FOR, flush_cache = True)
			if len(bt_devices)!=0:
				print(self.MSG_BTS, flush=True)
				print(self.DIVIDER, flush=True)
				print(self.format_shrt %("Device Name", "Device Address"))
				print(self.DIVIDER)
				for dev_addr, dev_id in bt_devices:
					if len(dev_id) < self.COL_WIDTH:
						str_form = self.format_shrt
					else:
						str_form = self.format_lng
					print(str_form%(dev_id[:self.COL_WIDTH], dev_addr),flush=True)
					if dev_addr == self.trgt_addr:
						addr = dev_addr
					print(self.DIVIDER, flush=True)
			else:
				print(self.MSG_NO_BTS, flush=True)
			if addr == "":
				print(self.MSG_BT_NOTFOUND, flush=True)
			else:
				print(self.MSG_BT_FOUND, flush=True)
		if addr == "":
			print(self.MSG_FIND_FAILED, flush=True)
		
		return addr
	
	def disconnect(self):
		print(self.MSG_DISCONNECT, flush=True)
		self.sock.close()
		
	def send(self, data):
		err = "Failed to send msg to"
		connected_dev = subprocess.getoutput("hcitool con")
		if self.trgt_addr in connected_dev:
			self.sock.send(data)
		else:
			raise RuntimeError(err+self.trgt_addr)