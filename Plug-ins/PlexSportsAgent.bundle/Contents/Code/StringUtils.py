import re, unicodedata

RE_UNICODE_CONTROL =  u'([\u0000-\u0008\u000b-\u000c\u000e-\u001f\ufffe-\uffff])' + \
					  u'|' + \
					  u'([%s-%s][^%s-%s])|([^%s-%s][%s-%s])|([%s-%s]$)|(^[%s-%s])' % \
					  (
						unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff),
						unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff),
						unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff)
					  )

ALPHANUMERIC_CHARACTERS = "abcdefghijklmnopqrstuvwxyz0123456789"
ALPHANUMERIC_CHARACTERS_AND_AT = ALPHANUMERIC_CHARACTERS + "@"

def indexOf(s, sub, start=0, end=None):
	try: return s.index(sub, start, end)
	except ValueError: return -1

def expandYear(year):
	if not year:
		return None

	intYear = 0
	if type(year) is str:
		intYear = int(year)
	elif type(year) is int:
		intYear = year

	if intYear < 100:
		if intYear < 40:
			intYear = 2000 + intYear
		else:
			intYear = 1900 + intYear

	return str(intYear)



def deunicode(s):
	"""Returns a UTF-8 compatible string, ignoring any characters that will not convert."""
	if not s:
		return s
	return str(s.decode('utf-8', 'ignore').encode('utf-8'))

def normalize(s):
	"""Decomposes a Unicode string into its sets of combined characters."""
	if not s:
		return s

	# Decompose unicode string.
	try: s = unicodedata.normalize('NFKD', s.decode('utf-8'))
	except:
		try: s = unicodedata.normalize('NFKD', s.decode(sys.getdefaultencoding()))
		except:
			try: s = unicodedata.normalize('NFKD', s.decode(sys.getfilesystemencoding()))
			except:
				try: s = unicodedata.normalize('NFKD', s.decode('ISO-8859-1'))
				except:
					try: s = unicodedata.normalize('NFKD', s)
					except Exception, e:
						pass

	# Strip control characters.
	if s:
		s = re.sub(RE_UNICODE_CONTROL, '', s)

	return s

def strip_diacritics(s):
	"""Decomposes and removes any diacritic characters from a string."""
	if not s: return s
	s = normalize(s)
	return ''.join([c for c in s if not unicodedata.combining(c)])

def strip_to_alphanumeric_and_at(s):
	if not s: return s
	s = normalize(s).lower()
	return ''.join([c for c in s if "L" in unicodedata.category(c) or "Nd" in unicodedata.category(c) or c == '@'])

def strip_to_alphanumeric(s):
	if not s: return s
	s = normalize(s).lower()
	return ''.join([c for c in s if "L" in unicodedata.category(c) or "Nd" in unicodedata.category(c)])
