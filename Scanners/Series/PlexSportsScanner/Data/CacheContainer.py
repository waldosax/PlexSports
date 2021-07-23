import re, json
from datetime import *

from ..TimeZoneUtils import *


CACHE_DURATION_DEFAULT = 7	# Duration in days



class CacheContainer:
	def __init__(self, items, **kwargs):
		nowUtc = datetime.datetime.utcnow()
				
		self.CachedOn = kwargs.get("CachedOn") or nowUtc
		self.CacheType = kwargs.get("CacheType") or "Unknown"
		self.CacheVersion = kwargs.get("Version")
		self.__duration = kwargs.get("Duration") or CACHE_DURATION_DEFAULT
		self.__expiresOn = kwargs.get("ExpiresOn")
		self.Items = []
		if items:
			for i in items:
				self.Items.append(i)

	def IsInvalid(self, version):
		if not self.__expiresOn == None:
			return self.__expiresOn <= datetime.datetime.utcnow()
		if not self.__duration > 0:
			return self.__expiresOn <= datetime.datetime.utcnow()
		return False

	@staticmethod
	def DefaultSerializationTransform(item):
		"""Returns a JSON-serializable value/dictionary from a given item."""
		if item == None: return None

		if isinstance(item, (basestring, float, int, bool)):
			return item

		if isinstance(item, datetime.datetime):
			return FormatISO8601(item)

		if isinstance(item, list):
			l = []
			for li in val:
				l.append(CacheContainer.DefaultSerializationTransform(li))
			return l

		serializable = dict()
		if isinstance(item, dict): itemDict = item
		else: itemDict = item.__dict__

		for key in itemDict.keys()[0:]:
			if not key[:2] == "__":
				val = itemDict[key]
				if not val == None:
					serializable[key] = CacheContainer.DefaultSerializationTransform(val)
		return serializable

	@staticmethod
	def DefaultDeserializationTransform(item):
		"""Converts JSON deserialized objects into usable types."""
		if item == None: return None

		if isinstance(item, basestring):
			if IsISO8601Date(item):
				return ParseISO8601Date(item)

		if isinstance(item, list):
			l = []
			for i in item:
				l.append(CacheContainer.DefaultDeserializationTransform(i))
			return l

		if isinstance(item, dict):
			d = dict()
			for key in item.keys():
				i = item[key]
				d[key] = CacheContainer.DefaultDeserializationTransform(i)
			return d

		return item

	def Serialize(self, itemTransform=None):
		if not itemTransform: itemTransform = CacheContainer.DefaultSerializationTransform
		nowUtc = datetime.datetime.utcnow()

		items = []
		if self.Items:
			for i in self.Items:
				items.append(itemTransform(i))
		duration = self.__duration
		if duration == None: duration = CACHE_DURATION_DEFAULT
		jsonSerializable = {
			"CacheContainer": {
				"CacheType": self.CacheType,
				"Version": self.CacheVersion,
				"CachedOn": nowUtc.strftime("%Y-%m-%dT%H:%M:%S%z"),
				"ExpiresOn": (nowUtc + datetime.timedelta(days=duration)).strftime("%Y-%m-%dT%H:%M:%S%z")
				},
			"Items": items
			}

		return json.dumps(jsonSerializable, sort_keys=True, indent=4)

	@staticmethod
	def Deserialize(jsonText, itemTransform=None):
		if not jsonText: return None
		if not itemTransform: itemTransform = CacheContainer.DefaultDeserializationTransform
		
		jsonContainer = json.loads(jsonText)
		if not jsonContainer: return None

		cachedOn = jsonContainer["CacheContainer"]["CachedOn"]
		cacheType = jsonContainer["CacheContainer"]["CacheType"]
		cacheVersion = jsonContainer["CacheContainer"]["Version"]
		expiresOn = ParseISO8601Date(jsonContainer["CacheContainer"]["ExpiresOn"])
		
		items = itemTransform(jsonContainer["Items"])

		return CacheContainer(items, CachedOn=cachedOn, CacheType=cacheType, Version=cacheVersion, ExpiresOn=expiresOn)
