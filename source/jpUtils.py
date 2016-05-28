# coding: UTF-8
# jpUtils.py
# NVDA Japanese Team
# A part of NonVisual Desktop Access (NVDA)
# for unittest, see ../jptools/jpDicTest.py

import characterProcessing
import languageHandler
import config
import re
import collections
from logHandler import log

RE_HIRAGANA = re.compile(u'^[\u3041-\u309e]+$')

def getLongDesc(s):
	try:
		lang = languageHandler.getLanguage()[:2]
		if len(s) == 1 and ord(s) < 128 and lang != 'ja':
			d = characterProcessing.getCharacterDescription(lang, s)
			log.info(repr([s, d, 0]))
			if d:
				r = '  '.join(d)
				return r
		d = characterProcessing.getCharacterDescription('ja', s)
		log.info(repr([s, d, 1]))
		if d:
			r = '  '.join(d)
			return r
	except Exception as e:
		log.info(repr(e))
	log.info(repr([s, 2]))
	return s

def getShortDesc(s):
	lang = languageHandler.getLanguage()[:2]
	if len(s) == 1 and ord(s) < 128 and lang != 'ja':
		return characterProcessing.processSpeechSymbol(lang, s)
	s2 = characterProcessing.processSpeechSymbol('ja', s)
	if s != s2:
		return s2
	return characterProcessing.getCharacterReading('ja', s.lower())

# characters which use dictionary for spelling reading
SMALL_ZEN_KATAKANA = u'ァィゥェォッャュョヮヵヶ'
SMALL_KANA_CHARACTERS = SMALL_ZEN_KATAKANA + u'ぁぃぅぇぉっゃゅょゎｧｨｩｪｫｬｭｮｯ'
SPECIAL_KANA_CHARACTERS = SMALL_KANA_CHARACTERS + u'をヲｦはへー'
FIX_NEW_TEXT_CHARS = SMALL_ZEN_KATAKANA + u'ー'

def isJa(locale=None):
	if locale is None:
		return languageHandler.getLanguage()[:2] == 'ja'
	return locale[:2] == 'ja'

def isZenkakuHiragana(c):
	return re.search(ur'[ぁ-ゞ]', c) is not None

def isZenkakuKatakana(c):
	if c == u'ー':
		return False
	return re.search(ur'[ァ-ヾ]', c) is not None

def isHankakuKatakana(c):
	return re.search(ur'[ｦ-ﾝ｢｣､｡ｰ]', c) is not None

def isHalfShape(c):
	return len(c) == 1 and (32 < ord(c)) and (ord(c) < 128)

def isFullShapeAlphabet(c):
	return re.search(ur'[ａ-ｚＡ-Ｚ]', c) is not None

def isHalfShapeAlphabet(c):
	return re.search(ur'[a-zA-Z]', c) is not None

def isFullShapeNumber(c):
	return re.search(ur'[０-９]', c) is not None

def isHalfShapeNumber(c):
	return re.search(ur'[0-9]', c) is not None

def isKanaCharacter(c):
	return isZenkakuHiragana(c) or isZenkakuKatakana(c) or isHankakuKatakana(c)

def isLatinCharacter(c):
	return isFullShapeAlphabet(c) or isHalfShapeAlphabet(c)

def isFullShapeSymbol(c):
	return c in u'　、。，．・：；？！´｀¨＾￣＿ー―／＼～∥｜‘’“”（）〔〕［］「」｛｝〈〉＋－＝＜＞￥＄％＃＆＊＠＇＂゙゚゛゜'

def isUpper(c):
	return (len(c) == 1) and (re.search(ur'[A-ZＡ-Ｚ]', c) is not None)

def replaceSpecialKanaCharacter(c):
	if c in SPECIAL_KANA_CHARACTERS:
		c = getShortDesc(c)
	return c

CharAttr = collections.namedtuple('CharAttr', 'upper hira kata half full latin')

def getAttrDesc(a):
	d = []
	if a.hira:
		d.append(_('hiragana'))
	if a.kata:
		d.append(_('katakana'))
	if a.half:
		d.append(_('half shape'))
	if a.full:
		d.append(_('full shape'))
	if a.latin:
		d.append(_('latin'))
	if a.upper:
		d.append(_('cap'))
	return ' '.join(d)

def code2kana(code):
	"""
	input 0x123a
　	output 'イチニーサンエー'
	"""
	s = ''
	src = hex(code)[2:]
	src = ("0000" + src)[-5:]
	if src[0] == '0':
		src = src[1:]
	for c in src:
		if c == '2':
			s += u'ニー'
		elif c == '5':
			s += u'ゴー'
		else:
			s += getShortDesc(c)
	return s

def code2hex(code):
	"""
	input 0x123a
　	output 'u+0123a'
	"""
	s = ''
	src = hex(code)[2:]
	src = ("0000" + src)[-5:]
	if src[0] == '0':
		src = src[1:]
	return 'u+' + src

def getCandidateCharDesc(c, a, forBraille=False):
	d = ''
	if forBraille and (isLatinCharacter(c) or isZenkakuHiragana(c) or isZenkakuKatakana(c) or isFullShapeNumber(c) or isHalfShapeNumber(c) or c == u'．'):
		d = c
	elif a.half or isFullShapeAlphabet(c) or isFullShapeNumber(c) or isFullShapeSymbol(c):
		d = getShortDesc(c)
		log.debug(u"shortdesc (%s) %s" % (c, d))
	elif a.hira or a.kata:
		d = replaceSpecialKanaCharacter(c)
		log.debug(u"kana (%s) %s" % (c, d))
	else:
		d = getLongDesc(c)
		if d != c:
			log.info(u"longdesc (%s) %s" % (c, d))
		else:
			d2 = characterProcessing.processSpeechSymbol('ja', c)
			if d != d2:
				log.debug(u"sym (%s) %s" % (c, d2))
				d = d2
			elif (0xd800 <= ord(c[0]) <= 0xdbff) and len(c) == 2:
				uc = (ord(c[0]) - 0xd800) * 0x800 + (ord(c[1]) - 0xdc00)
				d = code2hex(uc)
				log.info(u"sp (%s) %s" % (c, d))
			else:
				d = code2hex(ord(c[0]))
				log.info(u"code (%s) %s" % (c, d))
	if len(d) > 1:
		return ' ' + d + ' '
	return d

def useAttrDesc(a):
	if a[0] == u'ー':
		return False
	if a[1].half or a[1].upper or a[1].hira or a[1].kata or a[1].full:
		return True
	return False

def getOrd(s):
	# handle surrogate pairs
	if len(s) == 1:
		return ord(s)
	if len(s) != 2:
		raise Exception
	o0 = ord(s[0])
	o1 = ord(s[1])
	uc = (o0 - 0xd800) * 0x800 + (o1 - 0xdc00)
	return uc

def splitChars(name):
	# handle surrogate pairs
	nameChars = []
	n = len(name)
	p = 0
	while p < n:
		o0 = ord(name[p])
		if (0xd800 <= o0 <= 0xdbff) and (p + 1 < n):
			#o1 = ord(name[p+1])
			# assert 0xdc00 <= o1 <= 0xdfff:
			#uc = (o0 - 0xd800) * 0x800 + (o1 - 0xdc00)
			c = name[p] + name[p+1]
			nameChars.append(c)
			#log.info(u"%d %d %d (%s)" % (n, p, p+1, c))
			p += 2
		else:
			c = name[p]
			nameChars.append(c)
			#log.info(u"%d %d (%s)" % (n, p, c))
			p += 1
	#log.info(repr(nameChars))
	return nameChars

#TODO: merge _get_description() and getDiscriminantReading().
#nvdajp must modify locale/ja/characterDescriptions.dic and jpUtils.py.
def getDiscriminantReading(name, attrOnly=False, capAnnounced=False, forBraille=False):
	if not name: return ''
	nameChars = splitChars(name)
	attrs = []
	for uc in nameChars:
		c = uc[0]
		ca = CharAttr(
			isUpper(c) if (not capAnnounced and not forBraille) else False,
			isZenkakuHiragana(c),
			isZenkakuKatakana(c),
			isHalfShape(c) or isHankakuKatakana(c),
			isFullShapeAlphabet(c) or isFullShapeNumber(c) or isFullShapeSymbol(c),
			isLatinCharacter(c) and not forBraille)
		if not attrOnly:
			log.info(u"(%s) %d %s" % (uc, len(c), getAttrDesc(ca)))
		attrs.append((uc, ca))
	if attrOnly:
		s = ''
		for a in attrs:
			s += getAttrDesc(a[1]) + ' '
		return s
	s = ''
	prevAttr = None
	prevChar = None
	for a in attrs:
		# attribute unchanged
		if prevAttr == a[1]:
			s += getCandidateCharDesc(a[0], a[1], forBraille=forBraille)
			prevAttr = a[1]
		else:
			if s:
				s += u' '
			if useAttrDesc(a):
				s += getAttrDesc(a[1]) + ' '
			s += getCandidateCharDesc(a[0], a[1], forBraille=forBraille)
			prevAttr = a[1]
		prevChar = a[0]
	s = s.replace('  ', ' ')
	r = s.strip(' ')
	log.info(repr(r))
	return r

def processHexCode(locale, msg):
	if isJa(locale):
		try:
			msg = re.sub(r"u\+([0-9a-f]{4})", lambda x: "u+" + code2kana(int("0x"+x.group(1),16)), unicode(msg))
		except Exception as e:
			log.debug(e)
			pass
	return msg

def fixNewText(newText, isCandidate=False):
	log.debug(newText)
	if RE_HIRAGANA.match(newText):
		newText = ''.join([unichr(ord(c) + 0x60) for c in newText])
		log.debug('convert hiragana to katakana: ' + newText)
	if not isCandidate:
		for c in FIX_NEW_TEXT_CHARS:
			newText = newText.replace(c, ' ' + getShortDesc(c) + ' ')
	return newText
