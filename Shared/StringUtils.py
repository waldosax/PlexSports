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
	"""Expands a 2-digit year into a 4-digit year.
	
	Takes a guess at the century, assuming that any year value < 40 was in the 1900's.
	"""
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

def converTextToInt(textnum, numwords={}):
    if not numwords:
      units = [
        "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
        "sixteen", "seventeen", "eighteen", "nineteen",
      ]

      tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

      scales = ["hundred", "thousand", "million", "billion", "trillion"]

      numwords["and"] = (1, 0)
      for idx, word in enumerate(units):    numwords[word] = (1, idx)
      for idx, word in enumerate(tens):     numwords[word] = (1, idx * 10)
      for idx, word in enumerate(scales):   numwords[word] = (10 ** (idx * 3 or 2), 0)

    current = result = 0
    for word in textnum.split():
        if word not in numwords:
          raise Exception("Illegal word: " + word)

        scale, increment = numwords[word]
        current = current * scale + increment
        if scale > 100:
            result += current
            current = 0

    return result + current



def splitAndTrim(s, separator=",", maxsplit=-1, removeEmptyEntries=True):
	"""Splits a string into a list, each value having been stripped of leading and trailing whitespace."""
	if s == None: return None
	values = []
	if not s: return values
	for x in s.split(separator, maxsplit):
		y = x.strip()
		if y or y == "" and not removeEmptyEntries:
			values.append(y)
	return values


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

UNICODE_CATEGORY_LETTER = "L"
UNICODE_CATEGORY_LETTER_UPPERCASE = "Lu"
UNICODE_CATEGORY_NUMBER = "Nd"

def strip_to_alphanumeric_and_at(s):
	if not s: return s
	s = normalize(s).lower()
	return ''.join([c for c in s if UNICODE_CATEGORY_LETTER in unicodedata.category(c) or UNICODE_CATEGORY_NUMBER in unicodedata.category(c) or c == '@'])

def strip_to_alphanumeric(s):
	if not s: return s
	s = normalize(s).lower()
	return ''.join([c for c in s if UNICODE_CATEGORY_LETTER in unicodedata.category(c) or UNICODE_CATEGORY_NUMBER in unicodedata.category(c)])

def strip_to_capitals(s):
	if not s: return s
	s = normalize(s)
	return ''.join([c for c in s if UNICODE_CATEGORY_LETTER_UPPERCASE in unicodedata.category(c)])
