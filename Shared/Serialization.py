import json
from TimeZoneUtils import *


def SerializationDefaults(o):
	if (isinstance(o, datetime.date)):
		return o.strftime("%Y-%m-%d")
	if (isinstance(o, datetime.time)):
		return o.strftime("%H:%M:%S")
	if (isinstance(o, datetime.datetime)):
		return FormatISO8601(o)

def DeserializationDefaults(dct):
	for key in dct.keys():
		value = dct[key]
		if isinstance(value, basestring):
			if IsISO8601Date(value): dct[key] = ParseISO8601Date(value)
			elif IsISO8601Time(value): dct[key] = ParseISO8601Time(value)
	return dct

