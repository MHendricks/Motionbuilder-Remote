# Adds Remote to the Window menu of Motionbuilder. This is used to launch the q_telnet_client subprocess that
# connects to the arduino remote and routes input back to Motionbuilder. It uses subprocess to prevent blocking
# the Motionbuilder interface.
# Also adds Reload Remote to the Window menu. This is allows us to update the MoBoReceiver code without 
# restarting Motionbuilder.

import os
import subprocess
import pyfbsdk
import Remote
import iphelper
import Remote.moboreceiver

receiver = None
ip = None

def eventMenu(control, event):
	name = event.Name
	if name == "Remote":
		global receiver, ip
		h = iphelper.IPHelper()
		if h.exec_():
			ip = h.ipAddress
			path = os.path.split(__file__)[0]
			subprocess.Popen(['cmd.exe', ['/k python.exe', ' "{}"'.format(os.path.join(path, 'q_telnet_client.py')), ' {}'.format(ip)]])
			if receiver == None:
				receiver = Remote.moboreceiver.MoBoReceiver(ip, 23)
	elif name == 'Reload Remote':
		reload(Remote.moboreceiver)
		receiver = Remote.moboreceiver.MoBoReceiver(ip, 23)

mgr = pyfbsdk.FBMenuManager()
pythonTools = mgr.GetMenu('Window')
pythonTools.OnMenuActivate.Add(eventMenu)
mgr.InsertLast('Window', '') #Separator
mgr.InsertLast('Window', 'Remote')
mgr.InsertLast('Window', 'Reload Remote')
