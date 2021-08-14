import re, json
from datetime import *

from Serialization import *
from TimeZoneUtils import *

foo = SerializationDefaults

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


	

	def Serialize(self, itemTransform=None):
		if not itemTransform: itemTransform = SerializationDefaults
		nowUtc = datetime.datetime.utcnow()

		items = []
		if self.Items:
			for i in self.Items:
				tr = i
				if i != None and itemTransform:
					tr = itemTransform(i)
					if tr == None: tr = i
				items.append(tr)
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
	def Deserialize(jsonText, objectHook=DeserializationDefaults, itemTransform=None):
		if not jsonText: return None
		if not itemTransform: itemTransform = objectHook or DeserializationDefaults
		
		jsonContainer = json.loads(jsonText, object_hook=objectHook)
		if not jsonContainer: return None

		cachedOn = jsonContainer["CacheContainer"]["CachedOn"]
		cacheType = jsonContainer["CacheContainer"]["CacheType"]
		cacheVersion = jsonContainer["CacheContainer"]["Version"]
		expiresOn = jsonContainer["CacheContainer"]["ExpiresOn"]
		
		if itemTransform: items = itemTransform(jsonContainer["Items"])
		else: items = jsonContainer["Items"]

		return CacheContainer(items, CachedOn=cachedOn, CacheType=cacheType, Version=cacheVersion, ExpiresOn=expiresOn)
