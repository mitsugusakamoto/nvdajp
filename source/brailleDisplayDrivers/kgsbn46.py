# coding: UTF-8
#brailleDisplayDrivers/kgs.py
#A part of NonVisual Desktop Access (NVDA)
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.
#Copyright (C) 2011-2012 Takuya Nishimoto, Masataka Shinke
#Copyright (C) 2013 Masamitsu Misono

import braille
import brailleInput
import inputCore
import hwPortUtils
import time
import tones
import os
from collections import OrderedDict
import ctypes
from ctypes import *
from ctypes.wintypes import *
import config
from logHandler import log
import sys

kgs_dir = unicode(os.path.dirname(__file__), 'mbcs')
if (not 'addons' in kgs_dir.split("\\")) and hasattr(sys,'frozen'):
	d = os.path.join(os.getcwdu(), 'brailleDisplayDrivers')
	if os.path.isdir(d):
		kgs_dir = d

fConnection = False
numCells = 0
lastReleaseTime = None

#BM_DISPMODE_FOREGROUND = 0x01
#BM_DISPMODE_BACKGROUND = 0x02
#BM_DISPMODE_KEYHANDLER = 0x04
#BM_DISPMODE_SUSPENDED  = 0x08
KGS_DISPMODE = 0x02|0x04

# void (CALLBACK *pStatusChanged)(int nStatus, int nDispSize)
@WINFUNCTYPE(c_void_p, c_int, c_int)
def nvdaKgsStatusChangedProc(nStatus, nDispSize):
	global fConnection, numCells
	if 0==nStatus: #BMDRVS_DISCONNECTED
		fConnection = False
		tones.beep(1000, 300)
		log.info("disconnect")
	elif 1==nStatus: #BMDRVS_CONNECTED
		numCells = nDispSize
		fConnection = True
		tones.beep(1000, 30)
		log.info("display size:%d" % nDispSize)
	elif 2==nStatus: #BMDRVS_DRIVER_CANNOT_OPEN
		fConnection = False
		log.info("driver cannot open")
	elif 3==nStatus: #BMDRVS_INVALID_DRIVER
		fConnection = False
		log.info("invalid driver")
	elif 4==nStatus: #BMDRVS_OPEN_PORT_FAILED
		#fConnection = False
		log.info("open port failed")
	elif 5==nStatus: #BMDRVS_CREATE_THREAD_FAILED
		fConnection = False
		log.info("create thread failed")
	elif 6==nStatus: #BMDRVS_CHECKING_EQUIPMENT
		log.info("checking equipment")
	elif 7==nStatus: #BMDRVS_UNKNOWN_EQUIPMENT
		log.info("unknown equipment")
	elif 8==nStatus: #BMDRVS_PORT_RELEASED
		log.info("port released")
	elif 9==nStatus: #BMDRVS_MAX
		log.info("max")
	else:
		log.info("status changed to %d" % nStatus)

# BOOL (CALLBACK *pHandleKeyInfo)(BYTE info[4])
@WINFUNCTYPE(c_int, POINTER(c_ubyte))
def nvdaKgsHandleKeyInfoProc(lpKeys):
	keys = (lpKeys[0], lpKeys[1], lpKeys[2])
	log.io("keyInfo %d %d %d" % keys)
	log.io("keyInfo hex %x %x %x" % keys)
	names = set()
	routingIndex = None
	if keys[0] == 0:
		if keys[1] &   1: names.add('lf')
		if keys[1] &   2: names.add('bk')
		if keys[1] &   4: names.add('sr')
		if keys[1] &   8: names.add('sl')
		if keys[1] &  16: names.add('func1')
		if keys[1] &  32: names.add('func2')
		if keys[1] &  64: names.add('func3')
		if keys[1] & 128: names.add('func4')
	else:
		tCode = 240
		if keys[0] &   1+tCode: names.add('func1')
		if keys[0] &   2+tCode: names.add('func2')
		if keys[0] &   4+tCode: names.add('func3')
		if keys[0] &   8+tCode: names.add('func4')
		names.add('route')
		routingIndex = keys[1] - 1
	if routingIndex is not None:
		log.io("names %s %d" % ('+'.join(names), routingIndex))
	else:
		log.io("names %s" % '+'.join(names))
	if len(names):
		inputCore.manager.executeGesture(InputGesture(names, routingIndex))
		return True
	return False

def getKbdcName(hBrl):
	#DEVNAME_JA = u"BMシリーズ機器".encode('shift-jis')
	#DEVNAME_EN = u"BM series"
	DEVNAME_JA = u"ブレイルノート46C/46D".encode('shift-jis')
	DEVNAME_EN = u"BrailleNote46C/46D"
	REGKEY_KBDC110_PATH_JA = r"SOFTWARE\KGS\KBDC110"
	REGKEY_KBDC110_PATH_EN = r"SOFTWARE\KGS\KBDC110-E"
	ret = hBrl.IsKbdcInstalled(REGKEY_KBDC110_PATH_JA)
	if ret:
		devName = DEVNAME_JA
	else:
		ret = hBrl.IsKbdcInstalled(REGKEY_KBDC110_PATH_EN)
		if ret:
			devName = DEVNAME_EN
	return devName

def _fixConnection(hBrl, devName, port):
	global fConnection, lastReleaseTime
	log.info("scanning port %s" % port)
	if port[:3] == 'COM':
		_port = int(port[3:])-1
	else:
		return False, None
	SPEED = 3 # 9600bps
	fConnection = False
	if lastReleaseTime is not None and time.time() - lastReleaseTime < 5.0:
		for loop in xrange(10):
			time.sleep(0.5)
			tones.beep(400-(loop*20), 20)
			msg=ctypes.wintypes.MSG()
			if ctypes.windll.user32.PeekMessageW(ctypes.byref(msg),None,0,0,1):
				ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
				ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))
	ret = hBrl.bmStart(devName, _port, SPEED, nvdaKgsStatusChangedProc)
	for loop in xrange(40):
		try:
			if fConnection:
				ret = hBrl.bmStartDisplayMode2(KGS_DISPMODE, nvdaKgsHandleKeyInfoProc)
				break
			time.sleep(0.5)
			tones.beep(400+(loop*20), 20)
			msg=ctypes.wintypes.MSG()
			if ctypes.windll.user32.PeekMessageW(ctypes.byref(msg),None,0,0,1):
				ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
				ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))
		except:
			raise
	if not fConnection:
		bmDisConnect(hBrl, _port)
		port = None
		tones.beep(200, 100)
	log.info("connection:%d port:%d" % (fConnection, _port))
	return fConnection, port

def _autoConnection(hBrl, devName, port):
	Port = _port = None
	ret = False
	for portInfo in hwPortUtils.listComPorts(onlyAvailable=True):
		_port = portInfo["port"]
		hwID = portInfo["hardwareID"]
		frName = portInfo.get("friendlyName")
		btName = portInfo.get("bluetoothName")
		log.info(u"set port:{_port} hw:{hwID} fr:{frName} bt:{btName}".format(_port=_port, hwID=hwID, btName=btName, frName=frName))
		#if hwID[:3] != 'USB':
		#	continue
		ret, Port = _fixConnection(hBrl, devName, _port)
		if ret:
			break
	return ret, Port

def bmConnect(hBrl, port, execEndConnection=False):
	if execEndConnection:
		bmDisConnect(hBrl, port)
	devName = getKbdcName(hBrl)
	if not devName:
		return False
	if port is None or port=="auto":
		ret, pName = _autoConnection(hBrl, devName, port)
	else:
		ret, pName = _fixConnection(hBrl, devName, port)
	return ret, pName

def bmDisConnect(hBrl, port):
	global fConnection, numCells, lastReleaseTime
	ret = hBrl.bmEndDisplayMode()
	log.info("BmEndDisplayMode %s %d" % (port, ret))
	ret = hBrl.bmEnd()
	log.info("BmEnd %s %d" % (port, ret))
	numCells=0
	fConnection = False
	lastReleaseTime = time.time()
	return ret

class BrailleDisplayDriver(braille.BrailleDisplayDriver):
	name = "kgsbn46"
	description = _(u"KGS BrailleNote 46C/46D")
	_portName = None
	_directBM = None

	def __init__(self, port="auto"):
		super(BrailleDisplayDriver,self).__init__()
		global fConnection, numCells
		if port != self._portName and self._portName:
			execEndConnection = True
			log.info("changing connection %s to %s" % (self._portName, port))
		elif fConnection:
			log.info("already connection %s" % port)
			execEndConnection = False
			self.numCells = numCells
			return
		else:
			log.info("first connection %s" % port)
			execEndConnection = False
			self.numCells = 0
		kgs_dll = os.path.join(kgs_dir, 'DirectBM.dll')
		self._directBM = windll.LoadLibrary(kgs_dll.encode('mbcs'))
		if not self._directBM:
			raise RuntimeError("No KGS instance found")
		ret,self._portName = bmConnect(self._directBM, port, execEndConnection)
		if ret:
			config.conf["braille"][self.name] = {"port" : self._portName}
			self.numCells = numCells
			log.info("connected %s" % port)
		else:
			config.conf["braille"][self.name] = {"port" : "auto"}
			self.numCells = 0
			log.info("failed %s" % port)
			raise RuntimeError("No KGS display found")

	def terminate(self):
		super(BrailleDisplayDriver, self).terminate()
		if self._directBM and self._directBM._handle:
			bmDisConnect(self._directBM, self._portName)
			ret = windll.kernel32.FreeLibrary(self._directBM._handle)
			# ret is not zero if success
			log.info("KGS driver terminated %d" % ret)
		self._directBM = None
		self._portName = None

	@classmethod
	def check(cls):
		return True		

	@classmethod
	def getPossiblePorts(cls):
		ar = [cls.AUTOMATIC_PORT]
		ar.extend([ (p["port"], p["friendlyName"]) for p in hwPortUtils.listComPorts() ])
		return OrderedDict(ar)

	def display(self, data):
		if not data or len(data) == 0: return
		s = ''
		for c in data:
			d = 0
			if c & 0x01: d += 0x80
			if c & 0x02: d += 0x40
			if c & 0x04: d += 0x20
			if c & 0x08: d += 0x08
			if c & 0x10: d += 0x04
			if c & 0x20: d += 0x02
			if c & 0x40: d += 0x10
			if c & 0x80: d += 0x01
			s += chr(d)
		dataBuf   = create_string_buffer(s, 256)
		cursorBuf = create_string_buffer('', 256)
		try:
			ret = self._directBM.bmDisplayData(dataBuf, cursorBuf, self.numCells)
			log.debug("bmDisplayData %d" % ret)
		except:
			log.debug("error bmDisplayData")


	gestureMap = inputCore.GlobalGestureMap({
		"globalCommands.GlobalCommands": {
			"showGui": ("br(kgsbn46):func1",),
			"braille_routeTo": ("br(kgsbn46):route",),
			"braille_scrollBack": ("br(kgsbn46):sl",),
			"braille_scrollForward": ("br(kgsbn46):sr",),
#			"braille_previousLine": ("br(kgsbn46):bk",),
#			"braille_nextLine": ("br(kgsbn46):lf",),
			"review_previousLine": ("br(kgsbn46):func2+bk",),
			"review_nextLine": ("br(kgsbn46):func2+lf",),
			"review_previousWord": ("br(kgsbn46):func2+sl",),
			"review_nextWord": ("br(kgsbn46):func2+sr",),
			"kb:upArrow": ("br(kgsbn46):bk",),
			"kb:downArrow": ("br(kgsbn46):lf",),
			"kb:leftArrow": ("br(kgsbn46):func3",),
			"kb:rightArrow": ("br(kgsbn46):func4",),
#			"kb:leftArrow": ("br(kgsbn46):sl",),
#			"kb:rightArrow": ("br(kgsbn46):sr",),
#			"kb:shift": ("br(kgsbn46):func2",),
#			"kb:control": ("br(kgsbn46):ctrl",),nc2+bk",),
#			"kb:shift+downArrow": ("br(kgsbn46):func2+lf",),
#			"kb:shift+leftArrow": ("br(kgsbn46):func2+sl",),
#			"kb:shift+rightArrow": ("br(kgsbn46):func2+sr",),
#			"kb:shift+upArrow": ("br(kgsbn46):fu
		}
	})


class InputGesture(braille.BrailleDisplayGesture):

	source = BrailleDisplayDriver.name

	def __init__(self, names, routingIndex):
		super(InputGesture, self).__init__()
		self.id = "+".join(names)
		self.routingIndex = routingIndex