from StringUtils import *

def create_scannable_key(s, include_at=True):
	if not s: return s
	s = strip_diacritics(s)
	if include_at: s = strip_to_alphanumeric_and_at(s)
	else: s = strip_to_alphanumeric(s)
	return deunicode(s)
