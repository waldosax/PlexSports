import json
from TimeZoneUtils import *


def SerializationDefaults(item):
	if item == None: return None

	if isinstance(item, (basestring, float, int, bool)):
		return item

	if (isinstance(item, datetime.date)):
		return item.strftime("%Y-%m-%d")
	if (isinstance(item, datetime.time)):
		return FormatISO8601Time(item)
	if (isinstance(item, datetime.datetime)):
		return FormatISO8601Date(item)

	if isinstance(item, list):
		l = []
		for i in item: l.append(SerializationDefaults(i)) 
		return l
	
	serializableDict = None
	if isinstance(item, dict): serializableDict = item
	else: serializableDict = item.__dict__

	if serializableDict:
		d = dict()
		for key in serializableDict.keys():
			d[key] = SerializationDefaults(serializableDict[key])
		return d

	return item

def DeserializationDefaults(item):
	if item == None: return None

	if isinstance(item, (float, int, bool)):
		return item

	if isinstance(item, basestring):
		if IsISO8601Date(item): return ParseISO8601Date(item)
		elif IsISO8601Time(item): return ParseISO8601Time(item)

	if isinstance(item, list):
		return item

	if isinstance(item, dict):
		for key in item.keys():
			item[key] = DeserializationDefaults(item[key])

	return item

