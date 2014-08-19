import os
import sys
import telnetlib
import socket
import time
# I don't have PySide set up outside of MotionBuilder so I'm using PyQt4
#from PySide.QtCore import QObject, Signal
from PyQt4.QtCore import QObject, pyqtSignal

class TelnetClient(QObject):
#	commandReceived = Signal(str)
#	connectedToDevice = Signal()
#	connectingToDevice = Signal()
#	disconnectedFromDevice = Signal()
	
	commandReceived = pyqtSignal(str)
	connectedToDevice = pyqtSignal()
	connectingToDevice = pyqtSignal()
	disconnectedFromDevice = pyqtSignal()
	
	def __init__(self, ip, port=23, timeout=1.5, parent=None):
		super(TelnetClient, self).__init__(parent)
		self.ip = ip
		self.port = port
		self.timeout = timeout
		self.host = None
		self.mbHost = None

	# Thanks, http://chrisevans3d.com/tutorials/mbui.htm
	def mbPipe(self, command, printTag=None):
		if not self.mbHost:
			raise Exception("No Motion Builder Host connected")
		self.mbHost.read_until('>>>', .01)
		#write the command
		self.mbHost.write(command + '\n')
		#read all data returned
		raw = str(self.mbHost.read_until('>>>', .1))
		#removing garbage i don't want
		raw = raw.replace('\n\r>>>','')
		raw = raw.replace('\r','')
		if 'Record Toggle' in raw:
			self.host.write('r\r\n')
		if printTag:
			print '    ', printTag, '*'*50
			print raw
		#make an array, 1 element per line returned
		rawArr = raw.split('\n')
		return rawArr 

	def sendCommand(self, command):
		printTag = "OUTPUT:"
		self.mbPipe('import Remote')
		self.mbPipe('Remote.receiver.processInput("{command}")'.format(command=command), printTag=printTag)

	def connectToHost(self):
		if not self.host:
			print 'connecting to host', self.ip, self.port
			try:
				self.connectingToDevice.emit()
				self.host = telnetlib.Telnet(self.ip, self.port, self.timeout * 2)
				self.connectedToDevice.emit()
				print 'Connected to host'
			except socket.timeout:
				print 'Connection timeout'
				self.disconnectedFromDevice.emit()
			except socket.error as e:
				print 'Socket Error:', e
				self.disconnectedFromDevice.emit()
		return self.host

	def listen(self):
		# connect to motion builder
		try:
			self.mbHost = telnetlib.Telnet("localhost", 4242)
		except socket.error:
			raise
		while True:
			self.host = self.connectToHost()
			if not self.host:
				time.sleep(self.timeout)
				continue
			out = self.host.expect(['Beat', r'dn\d\d', r'up\d\d', r'p[abc]\d{,4}'], self.timeout)
			if out:
				if out[0] != -1:
					# remove the Beats
					text = out[-1].replace('Beat', '').replace('\r\n', '\n').replace('\r', '\n')
					for item in text.split('\n'):
						if item:
							self.sendCommand(item)
				# The heartbeat was not received, we must have lost the connection,
				# reset it so we can re-connect next loop.
				else:
					print 'Missed a beat'
					self.closeTerminal()
		self.closeTerminal()

	def closeTerminal(self):
		#Close the terminal
		if self.host:
			self.host.close()
			self.host = None
			self.disconnectedFromDevice.emit()

if __name__ == '__main__':
	print sys.argv
	if len(sys.argv) > 1:
		# connect to the arduino
		con = TelnetClient(*sys.argv[1:])
		# start listening
		con.listen()
	else:
		print 'Please provide a ip address and optionally a port number'
