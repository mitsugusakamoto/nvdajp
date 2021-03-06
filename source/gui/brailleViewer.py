# -*- coding: utf-8 -*-
#brailleViewer.py
#brailleDisplayDrivers/DirectBM.py
#A part of NonVisual Desktop Access (NVDA)
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.
#Copyright (C) 2012 Masataka.Shinke

import wx
import gui
import config

class brailleViewerFrame(wx.MiniFrame):

	def __init__(self):
		super(brailleViewerFrame, self).__init__(gui.mainFrame, wx.ID_ANY, _("NVDA Braille Viewer"), style=wx.CAPTION | wx.RESIZE_BORDER)
		self.Bind(wx.EVT_CLOSE, self.onClose)
		self.SetFont(wx.Font(20,wx.FONTFAMILY_DEFAULT,wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_NORMAL,False,"DejaVu Sans"))
		sizer = wx.BoxSizer(wx.VERTICAL)
		self.textCtrl = wx.TextCtrl(self, -1,size=(600,200),style=wx.TE_READONLY|wx.TE_MULTILINE)
		sizer.Add(self.textCtrl, proportion=1, flag=wx.EXPAND)
		sizer.Fit(self)
		self.SetSizer(sizer)
		self.Show(True)

	def onClose(self, evt):
		deactivate()
		gui.mainFrame.sysTrayIcon.menu_tools_toggleBrailleViewer.Check(False)

_guiFrame=None
isActive=False

def activate():
	global _guiFrame, isActive
	_guiFrame = brailleViewerFrame()
	isActive=True

def appendText(text):
	if not isActive:
		return
	if not isinstance(text,basestring):
		return
	#If the braille viewer text control has the focus, we want to disable updates
	#Otherwize it would be impossible to select text, or even just read it (as a blind person).
	if _guiFrame.FindFocus()==_guiFrame.textCtrl:
		return
	translate = __import__("synthDrivers.jtalk.translator2", globals(), locals(), ('getReadingAndBraille',))
	(sp, tr) = getattr(translate, 'getReadingAndBraille')(text, nabcc=config.conf["braille"]["expandAtCursor"])
	if tr:
		_guiFrame.textCtrl.AppendText(sp+"\n")
		_guiFrame.textCtrl.AppendText(tr+"\n")

def deactivate():
	global _guiFrame, isActive
	if not isActive:
		return
	isActive=False
	_guiFrame.Destroy()
	_guiFrame=None

