# MoBoReceiver runs inside Motionbuilder. It is responsible for parsing the remote input strings,
# and running Motionbuilder commands.

import re
import math
import telnetlib
from pyfbsdk import *
from PySide.QtCore import QTimer, QObject

class MoBoReceiver(QObject):
	FStopMap = [0.6, 0.7, 0.8, 1.0, 1.4, 1.7, 2.0, 2.4, 2.8, 3.3, 4.0, 5.6, 6.7, 8.0, 9.5, 11, 13, 16, 22]
	ISOMap = [0.01, 0.02, 0.03, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 1, 1.6, 3, 6, 12, 25, 50, 100, 200, 400, 800, 1600, 3200, 6400]
	
	def __init__(self, remoteIP=None, remotePort=23):
		super(MoBoReceiver, self).__init__()
		self.remoteIP = remoteIP
		self.remotePort = remotePort
	
	@staticmethod
	def mapVal(x, out_min, out_max, in_min=0, in_max=1023):
		return (x - in_min) * (out_max - out_min) / float(in_max - in_min) + out_min
	
	def processInput(self, data):
		print "ProcessInput", [data]
		down = re.findall(r'dn(\d\d)', data)
		if down:
			down = down[0]
			if down == '00':
				self.playToggle()
			elif down == '01':
				self.recordToggle()
			elif down == '02':
				self.prevCamera()
			elif down == '03':
				self.nextCamera()
			elif down == '04':
				self.setCameraFov( self.currentCamera().FieldOfView + 1 )
			elif down == '05':
				self.setCameraSpecificDistance( self.currentCamera().FocusSpecificDistance + 1 )
			elif down == '06':
				self.setCameraFocusAngle( self.FStopMap[self.closestFStopIndex(1)] )
			elif down == '07':
				self.setISO(self.ISOMap[self.closestISOIndex(1)])
			elif down == '08':
				self.setCameraFov( self.currentCamera().FieldOfView - 1 )
			elif down == '09':
				self.setCameraSpecificDistance( self.currentCamera().FocusSpecificDistance - 1 )
			elif down == '10':
				self.setCameraFocusAngle( self.FStopMap[self.closestFStopIndex(-1)] )
			elif down == '11':
				self.setISO(self.ISOMap[self.closestISOIndex(-1)])
			elif down == '12':
				self.startFrame()
			elif down == '13':
				self.loopToggle()
#			elif down == '14':
#				pass
			elif down == '15':
				print "press Esc"
			return
		# Use this to process button releases
#		up = re.findall(r'up(\d\d)', data)
#		if up:
#			if up == '00':
#				pass
		potVal = re.findall(r'p([A-C])(\d{,4})', data)
		if potVal:
			pot, value = potVal[0]
			if pot == 'A':
				fov = self.mapVal(int(value), 8, 150)
				self.setCameraFov(fov)
			if pot == 'B':
				dist = self.mapVal(int(value), 1, 500)
				self.setCameraSpecificDistance(dist)
#			if pot == 'C':
#				# -999999.99 - 100
#				angle = self.mapVal(int(value), 0.8, 11)
#				self.setCameraFocusAngle(angle)
			if pot == 'C':
				# Map ISO arithmetric range: 25-6400
#				isoLog = self.mapVal(int(value), 14.98, 39.09)
				isoLog = self.mapVal(int(value), 0.005, 39.09)
				self.setLogISO(isoLog)

	def closestFStopIndex(self, inc=0):
		current = self.currentCamera().FocusAngle
		index = self.FStopMap.index(min(self.FStopMap, key=lambda x:abs(x - current)))
		index += inc
		if index < 0:
			index = 0
		elif index >= len(self.FStopMap):
			index = len(self.FStopMap) - 1
		return index
	
	def closestISOIndex(self, inc=0):
		current = self.currentISO()
		index = self.ISOMap.index(min(self.ISOMap, key=lambda x: abs(x - current)))
		index += inc
		if index < 0:
			index = 0
		elif index >= len(self.ISOMap):
			index = len(self.ISOMap) - 1
		return index
	
	def currentCamera(self):
		cameraSwitcher = FBCameraSwitcher()
		return cameraSwitcher.CurrentCamera
	
	def currentISO(self):
		# TODO: Implement ISO
		return 400
	
	def findCameras(self):
		ret = []
		for child in FBSystem().Scene.RootModel.Children:
			if isinstance(child, FBCamera):
				ret.append(child)
		return ret
	
	def nextCamera(self):
		cameras = self.findCameras()
		FBSystem().Scene.Renderer.UseCameraSwitcher = True
		# Set our view to the newly created camera.
		cameraSwitcher = FBCameraSwitcher()
		current = cameraSwitcher.CurrentCamera
		for i, cam in enumerate(cameras):
			if cam == current:
				i += 1
				if i == len(cameras):
					i = 0
				cameraSwitcher.CurrentCamera = cameras[i]
				print 'Switched to camera:', cameras[i].Name
				return
		else:
			print 'Unable to find the camera'
	
	def prevCamera(self):
		print 'previous camera'
		cameras = self.findCameras()
		FBSystem().Scene.Renderer.UseCameraSwitcher = True
		# Set our view to the newly created camera.
		cameraSwitcher = FBCameraSwitcher()
		current = cameraSwitcher.CurrentCamera
		for i, cam in enumerate(cameras):
			if cam == current:
				i -= 1
				if i < 0:
					i = len(cameras) - 1
				cameraSwitcher.CurrentCamera = cameras[i]
				print 'Switched to camera:', cameras[i].Name
				return
		else:
			print 'Unable to find the camera'
	
	def setCameraFov(self, fov):
		self.currentCamera().FieldOfView = fov
	
	def setCameraFocusAngle(self, angle):
		print 'F-Stop', angle
		self.currentCamera().FocusAngle = angle
	
	def setLogISO(self, speed):
		""" Maps the ISO logarithmic scale values to map the arithmetric iso value.
		The ISO standard rounds to the nerest value in a table just to make it complicated
		"""
		arithmeticSpeed = math.pow(10.0, (speed-1.0)/10.0)
		print 'arithmeticSpeed', speed, arithmeticSpeed
		self.setISO(speed)
	
	def setISO(self, speed):
		print 'setISO', speed
		# TODO: Implement ISO
	
	def setCameraSpecificDistance(self, dist):
		self.currentCamera().FocusSpecificDistance = dist
	
	def playToggle(self):
		print 'Play toggle'
		playback = FBPlayerControl()
		if playback.IsPlaying:
			playback.Stop()
		else:
			playback.Play()
	
	def recordToggle(self):
		print 'Record Toggle'
		# this doesn't seem to work reliably.
		playback = FBPlayerControl()
		if playback.IsRecording:
			playback.Stop()
			host = telnetlib.Telnet(self.remoteIP, self.remotePort, 2).write('s\r\n')
		else:
			playback.Record()
			host = telnetlib.Telnet(self.remoteIP, self.remotePort, 2).write('r\r\n')
	
	def loopToggle(self):
		playback = FBPlayerControl()
		playback.LoopActive = not playback.LoopActive
	
	def startFrame(self):
		print 'Start Frame'
		FBPlayerControl().GotoStart()
