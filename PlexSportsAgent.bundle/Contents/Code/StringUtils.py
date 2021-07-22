import re, unicodedata

RE_UNICODE_CONTROL =  u'([\u0000-\u0008\u000b-\u000c\u000e-\u001f\ufffe-\uffff])' + \
					  u'|' + \
					  u'([%s-%s][^%s-%s])|([^%s-%s][%s-%s])|([%s-%s]$)|(^[%s-%s])' % \
					  (
						unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff),
						unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff),
						unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff)
					  )

def __expand_year(year):
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
	if not s:
		return s
	return str(s).decode('utf-8', 'ignore')

# Safely return Unicode.
def normalize(s):
	if not s:
		return s

	# Precompose.
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

	return deunicode(s)
