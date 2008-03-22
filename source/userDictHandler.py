#userDictHandler.py
#A part of NonVisual Desktop Access (NVDA)
#Copyright (C) 2006-2007 NVDA Contributors <http://www.nvda-project.org/>
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import re
import globalVars
import os
import codecs
import synthDriverHandler

dictionaries = {}
dictTypes = ("temp", "voice", "default") # ordered by their priority E.G. voice specific user dictionary is processed before the default
userDictsPath="userdicts"

class UserDictEntry:

	def __init__(self, pattern, replacement,comment,caseSensitive=True,regexp=False):
		self.pattern = pattern
		flags=re.IGNORECASE if not caseSensitive else 0
		tempPattern=pattern if regexp else re.escape(pattern)
		self.compiled = re.compile(tempPattern,flags)
		self.replacement = replacement
		self.comment=comment
		self.caseSensitive=caseSensitive
		self.regexp=regexp

	def sub(self, text):
		replacement=self.replacement
		return self.compiled.sub(replacement, text)

class UserDict(list):

	def load(self, fileName):
		self.fileName=fileName
		comment=""
		del self[:]
		globalVars.log.debug("Loading user dictionary '%s'..." % fileName)
		if not os.path.isfile(fileName): 
			globalVars.log.debug("file '%s' not found." % fileName)
			return
		file = codecs.open(fileName,"r","utf_8_sig",errors="replace")
		for line in file:
			if line.isspace():
				comment=""
				continue
			line=line.rstrip('\r\n')
			if line.startswith('#'):
				if comment:
					comment+=" "
				comment+=line[1:]
			else:
				temp=line.split("\t")
				if len(temp) ==4:
					self.append(UserDictEntry(temp[0],temp[1],comment,bool(int(temp[2])),bool(int(temp[3]))))
					comment=""
				else:
					globalVars.log.warning("can't parse line '%s'" % line)
		globalVars.log.debug("%d loaded records." % len(self))
		file.close()
		return

	def save(self,fileName=None):
		if not fileName:
			fileName=getattr(self,'fileName',None)
		if fileName:
			file = codecs.open(fileName,"w","utf_8_sig",errors="replace")
			for entry in self:
				if entry.comment:
					file.write("#%s\r\n"%entry.comment)
				file.write("%s\t%s\t%s\t%s\r\n"%(entry.pattern,entry.replacement,int(entry.caseSensitive),int(entry.regexp)))
			file.close()

	def sub(self, text):
		for entry in self:
			text = entry.sub(text)
		return text

def processText(text):
	if not globalVars.userDictionaryProcessing:
		return text
	for entry in dictionaries.values():
		text=entry.sub(text)
	return text

def getFileName(type):
	if type is "default":
		return "%s/default.dic"%userDictsPath
	elif type is "voice":
		s=synthDriverHandler.getSynth()
		return "%s/%s-%s.dic"%(userDictsPath,s.name,s.getVoiceName(s.voice))
	return None

def initialize():
	for type in dictTypes:
		dictionaries[type]=UserDict()
	dictionaries["default"].load(getFileName("default"))

