import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import re, unicodedata
from pprint import pprint

RE_UNICODE_CONTROL =  u'([\u0000-\u0008\u000b-\u000c\u000e-\u001f\ufffe-\uffff])' + \
					  u'|' + \
					  u'([%s-%s][^%s-%s])|([^%s-%s][%s-%s])|([%s-%s]$)|(^[%s-%s])' % \
					  (
						unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff),
						unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff),
						unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff)
					  )


def deunicode(s):
	if not s:
		return s
	return str(s).decode('utf-8', 'ignore').encode('utf-8')

# Safely return vanilla text.
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

	return s

def stripdiacritics(s):
	s = normalize(s)
	return ''.join([c for c in s if not unicodedata.combining(c)])

def strip_to_alphanumeric_and_at(s):
	s = normalize(s).lower()
	return ''.join([c for c in s if "L" in unicodedata.category(c) or "Nd" in unicodedata.category(c) or c == '@'])

def strip_to_alphanumeric(s):
	s = normalize(s).lower()
	return ''.join([c for c in s if "L" in unicodedata.category(c) or "Nd" in unicodedata.category(c)])


s = "@Montréal Canadiens"
pprint(s)
pprint(normalize(s))
pprint(stripdiacritics(s))
pprint(deunicode(stripdiacritics(s)))
pprint(strip_to_alphanumeric_and_at(s))
pprint(strip_to_alphanumeric(s))
pprint(deunicode(strip_to_alphanumeric_and_at(s)))

pprint(unicodedata.category(u'a'))
pprint(unicodedata.category(u'A'))
pprint(unicodedata.category(u'8'))
pprint(unicodedata.category(u'@'))
pprint("L" in "Lu")
