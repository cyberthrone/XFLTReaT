import sys

if "packetselector.py" in sys.argv[0]:
	print "[-] Instead of poking around just try: python xfltreat.py --help"
	sys.exit(-1)


'''
This is the engine of the whole communication. Every packet that arrives to the tunnel will be carefully selected.
In case a destination IP match is found, it will be redirected (written) to the properly selected pipe that belongs to that client.
'''


import threading
import os
import select
import struct
import socket

from client import Client

class PacketSelector(threading.Thread):
#	temp_pipe_r, temp_pipe_w = os.pipe()
	clients = None

	def __init__(self, tunnel): #??
		threading.Thread.__init__(self)
		self.timeout = 1.0 # still not sure this is the best value and idea
		self.clients = []
		self.tunnel = tunnel
		self._stop = False

	def get_clients(self):

		return self.clients

	def add_client(self, client):
		self.clients.append(client)

		return

	def replace_client(self, old_client, new_client):
		if old_client in self.clients:
			self.clients.remove(old_client)
			self.clients.append(new_client)
			try:
				old_client.get_pipe_w_fd().close()
			except:
				pass
			try:
				old_client.get_pipe_r_fd().close()
			except:
				pass
			try:
				socket.close(old_client.get_socket())
			except:
				pass

	def delete_client(self, client):
		if client in self.clients:
			self.clients.remove(client)

		return


	def run(self):
		rlist = [self.tunnel]
		wlist = []
		xlist = []

		while not self._stop:
			try:
				readable, writable, exceptional = select.select(rlist, wlist, xlist, self.timeout)
			except select.error, e:
				print e
				break

			for s in readable:
				if s is self.tunnel:
					message = os.read(self.tunnel, 4096)
					while True:
						if (len(message) < 4) and (message[0:1] != "\x45"): #Only care about IPv4
							break
						packetlen = struct.unpack(">H", message[2:4])[0]
						if packetlen == 0:
							break
						if packetlen > len(message):
							message += os.read(self.tunnel_r, 4096)
						readytogo = message[0:packetlen]
						message = message[packetlen:]
						for c in self.clients:
							if c.get_private_ip_addr() == readytogo[16:20]:
								os.write(c.get_pipe_w(), readytogo) # !!!!
								c.get_pipe_w_fd().flush()

		return

	def stop(self):
		self._stop = True

		return