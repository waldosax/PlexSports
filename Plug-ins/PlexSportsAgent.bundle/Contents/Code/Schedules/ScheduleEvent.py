import datetime

from Constants.Assets import *
from Hashes import *
from StringUtils import *
from TimeZoneUtils import *


class ScheduleEvent:
	def __init__(self, **kwargs):
		self.sport = deunicode(kwargs.get("sport"))
		self.league = deunicode(kwargs.get("league"))
		self.season = deunicode(str(kwargs.get("season")))
		date = kwargs.get("date")
		if isinstance(kwargs["date"], basestring) and IsISO8601Date(kwargs["date"]):
			date = ParseISO8601Date(kwargs["date"]).replace(tzinfo=UTC)
		self.date = date

		# Event metadata
		self.subseason = kwargs.get("subseason")
		self.subseasonTitle = deunicode(kwargs.get("subseasonTitle"))
		self.playoffround = kwargs.get("playoffround")
		self.eventindicator = kwargs.get("eventindicator")
		self.eventTitle = deunicode(kwargs.get("eventTitle"))
		self.week = kwargs.get("week")
		self.game = kwargs.get("game")

		self.homeTeam = deunicode(kwargs.get("homeTeam"))
		self.awayTeam = deunicode(kwargs.get("awayTeam"))
		# TODO: fields for non team-based sports, like Boxing

		# Additional metadata items (if provided)
		self.vs = deunicode(kwargs.get("vs"))
		self.title = deunicode(kwargs.get("title"))
		self.altTitle = deunicode(kwargs.get("altTitle"))
		self.description = kwargs.get("description")
		self.networks = []
		if kwargs.get("networks"):
			self.networks = list(set(self.networks + kwargs["networks"]))
		if kwargs.get("network"):
			self.networks = list(set(self.networks + splitAndTrim(deunicode(kwargs["network"]))))
		
		self.assets = EventAssets()
		if kwargs.get("assets"):
			assets = kwargs["assets"]
			if isinstance(assets, (EventAssets)): self.assets.Augment(**assets.__dict__)
			elif isinstance(assets, (dict)): self.assets.Augment(**assets)

		self.__augmentationkey__ = None
		self.__key__ = None

		self.identity = ScheduleEventIdentity(**kwargs)
		self.identity.Augment(**kwargs)
		if kwargs.get("identity"):
			identity = kwargs["identity"]
			if isinstance(identity, (ScheduleEventIdentity)): self.identity.Augment(**identity.__dict__)
			elif isinstance(identity, (dict)): self.identity.Augment(**identity)

		pass


	def augment(self, **kwargs):
		if not self.sport and kwargs.get("sport"): self.sport = deunicode(kwargs.get("sport"))
		if not self.league and kwargs.get("league"): self.league = deunicode(kwargs.get("league"))
		if not self.season and kwargs.get("season"): self.season = deunicode(str(kwargs.get("season")))

		date = kwargs.get("date")
		if isinstance(kwargs["date"], basestring) and IsISO8601Date(kwargs["date"]):
			date = ParseISO8601Date(kwargs["date"]).replace(tzinfo=UTC)

		# Augment date if missing or missing time
		if not self.date and date:
			self.date = date
		elif self.date and not self.date.time() and date and date.time():
			self.date = date
		
		if self.subseason == None and kwargs.get("subseason"): self.subseason = kwargs.get("subseason")
		if not self.subseasonTitle: self.subseasonTitle = deunicode(kwargs.get("subseasonTitle"))
		if self.playoffround == None and kwargs.get("playoffround"): self.playoffround = kwargs.get("playoffround")
		if self.eventindicator == None and kwargs.get("eventindicator"): self.eventindicator = kwargs.get("eventindicator")
		if not self.eventTitle: self.eventTitle = deunicode(kwargs.get("eventTitle"))
		if self.week == None and kwargs.get("week"): self.week = kwargs.get("week")
		if not self.game and kwargs.get("game"): self.game = kwargs.get("game")
		
		if not self.homeTeam: self.homeTeam = deunicode(kwargs.get("homeTeam"))
		if not self.awayTeam: self.awayTeam = deunicode(kwargs.get("awayTeam"))
		# TODO: fields for non team-based sports, like Boxing

		# Additional metadata items (if provided)
		if not self.vs: self.vs = deunicode(kwargs.get("vs"))
		if not self.title: self.title = deunicode(kwargs.get("title"))
		if not self.altTitle: self.altTitle = deunicode(kwargs.get("altTitle"))
		if not self.description: self.description = deunicode(kwargs.get("description"))
		if kwargs.get("networks"): self.networks = list(set(self.networks + kwargs["networks"]))
		if kwargs.get("network"): self.networks = list(set(self.networks + splitAndTrim(deunicode(kwargs["network"]))))
		
		if kwargs.get("assets"):
			assets = kwargs["assets"]
			if isinstance(assets, (EventAssets)): self.assets.Augment(**assets.__dict__)
			elif isinstance(assets, (dict)): self.assets.Augment(**assets)
		
		self.identity.Augment(**kwargs)
		if kwargs.get("identity"):
			identity = kwargs["identity"]
			if isinstance(identity, (ScheduleEventIdentity)): self.identity.Augment(**identity.__dict__)
			elif isinstance(identity, (dict)): self.identity.Augment(**identity)

		self.__augmentationkey__ = None
		self.__key__ = None

	@property
	def augmentationkey(self):
		if not self.__augmentationkey__:
			self.__augmentationkey__ = sched_compute_augmentation_hash(self)
		return self.__augmentationkey__

	@property
	def key(self):
		if not self.__key__:
			self.__key__ = sched_compute_hash(self)
		return self.__key__

	def __repr__(self):
		output = ""
		
		if self.league:
			output += self.league
		elif self.sport:
			output += self.sport

		if self.title:
			if output: output += " "
			if self.season: output += self.season + " "
			output += self.title
		elif self.altTitle:
			if output: output += " "
			if self.season: output += self.season + " "
			output += self.altTitle

		if self.date:
			if output: output += " "
			output += "%s/%s/%s" % (self.date.month, self.date.day, self.date.year)

		if not self.title and self.homeTeam and self.awayTeam:
			if output: output += " "
			output += "%s vs. %s" % (self.homeTeam, self.awayTeam)


		return output

def AddOrAugmentEvent(sched, event):
	hash = sched_compute_augmentation_hash(event)
	subhash = sched_compute_time_hash(event)

	#print("%s|%s" % (hash, subhash))
	
	evdict = None
	if hash in sched.keys():
		evdict = sched[hash]
	else:
		evdict = dict()
		sched[hash] = evdict

	if not subhash: # Time-naive
		if evdict.keys() and not None in evdict.keys(): # If any time-aware, augment the 1st
			for subhash in evdict.keys():
				repl = evdict[subhash]
				repl.augment(**event.__dict__)
				break;
		else: # Otherwise, add the time-naive
			evdict[None] = event
	else: # Time-aware
		if subhash in evdict.keys(): # Times agree
			evdict[subhash].augment(**event.__dict__)
		else: #Times are close enough?
			foundSubhash = False

			projectedSubhashes = [] # Project subhash by two hours in each direction
			subhashHour = int(subhash)
			for i in range(subhashHour-2,subhashHour+3):
				hr = i
				if hr < 0: hr = 24 + i
				elif hr >= 24: hr = i - 24
				ssh = ("00%s" % hr)[-2:]
				if ssh in evdict.keys():
					foundSubhash = True
					subhash = ssh
					break

			if foundSubhash:
				evdict[subhash].augment(**event.__dict__)
			else: # Must be a double-header. Append
				if None in evdict.keys(): # Augment and replace time-naive
					repl = evdict[None]
					repl.augment(**event.__dict__)
					del(evdict[None])
					evdict[subhash] = repl
				else:
					evdict.setdefault(subhash, event)

	pass

class ScheduleEventIdentity:
	def __init__(self, **kwargs):
		self.TheSportsDBID = kwargs.get("TheSportsDBID")
		self.SportsDataIOID = kwargs.get("SportsDataIOID")
		self.MLBAPIID = kwargs.get("MLBAPIID")
		self.NBAAPIID = kwargs.get("NBAAPIID")
		self.NHLAPIID = kwargs.get("NHLAPIID")
		self.ESPNAPIID = kwargs.get("ESPNAPIID")
		self.ProFootballReferenceID = kwargs.get("ProFootballReferenceID")
		pass

	def Augment(self, **kwargs):
		if kwargs.get("TheSportsDBID"): self.TheSportsDBID = kwargs["TheSportsDBID"]
		if kwargs.get("SportsDataIOID"): self.SportsDataIOID = kwargs["SportsDataIOID"]
		if kwargs.get("MLBAPIID"): self.MLBAPIID = kwargs["MLBAPIID"]
		if kwargs.get("NBAAPIID"): self.NBAAPIID = kwargs["NBAAPIID"]
		if kwargs.get("NHLAPIID"): self.NHLAPIID = kwargs["NHLAPIID"]
		if kwargs.get("ESPNAPIID"): self.ESPNAPIID = kwargs["ESPNAPIID"]
		if kwargs.get("ProFootballReferenceID"): self.ProFootballReferenceID = kwargs["ProFootballReferenceID"]
		pass

class EventAsset():
	def __init__(self, **kwargs):
		self.source = deunicode(kwargs.get("source"))
		self.url = deunicode(kwargs["url"]) if kwargs.get("url") else None
		pass

	@property
	def key(self):
		return ("%s" % (self.source)).lower()

	def __repr__(self):
		s = ""
		if self.source:
			s += "["
			s += self.source
			s += "]"
		if self.url:
			if s: s += " "
			s += self.url
		return s


class EventAssets():
	def __init__(self, **kwargs):
		self.poster = []
		self.fanArt = []
		self.thumbnail = []
		self.banner = []
		self.logo = []
		self.preview = []
		self.Augment(**kwargs)

	def __add_asset(self, assetType, asset, **kwargs):
		found = self.Find(assetType, asset.source, **kwargs)
		if not found: self.__dict__[assetType].append(asset)

	def Augment(self, **kwargs):
		if kwargs.get(ASSET_TYPE_POSTERS):
			for asset in kwargs[ASSET_TYPE_POSTERS]:
				if isinstance(asset, (EventAsset)): self.__add_asset(ASSET_TYPE_POSTERS, asset)
				else: self.__add_asset(ASSET_TYPE_POSTERS, EventAsset(**asset))
		
		if kwargs.get(ASSET_TYPE_FANART):
			for asset in kwargs[ASSET_TYPE_FANART]:
				if isinstance(asset, (EventAsset)): self.__add_asset(ASSET_TYPE_FANART, asset)
				else: self.__add_asset(ASSET_TYPE_FANART, EventAsset(**asset))
		
		if kwargs.get(ASSET_TYPE_THUMBNAIL):
			for asset in kwargs[ASSET_TYPE_THUMBNAIL]:
				if isinstance(asset, (EventAsset)): self.__add_asset(ASSET_TYPE_THUMBNAIL, asset)
				else: self.__add_asset(ASSET_TYPE_THUMBNAIL, EventAsset(**asset))
		
		if kwargs.get(ASSET_TYPE_BANNERS):
			for asset in kwargs[ASSET_TYPE_BANNERS]:
				if isinstance(asset, (EventAsset)): self.__add_asset(ASSET_TYPE_BANNERS, asset)
				else: self.__add_asset(ASSET_TYPE_BANNERS, EventAsset(**asset))
		
		if kwargs.get(ASSET_TYPE_LOGOS):
			for asset in kwargs[ASSET_TYPE_LOGOS]:
				if isinstance(asset, (EventAsset)): self.__add_asset(ASSET_TYPE_LOGOS, asset)
				else: self.__add_asset(ASSET_TYPE_LOGOS, EventAsset(**asset))
		
		if kwargs.get(ASSET_TYPE_PREVIEW):
			for asset in kwargs[ASSET_TYPE_PREVIEW]:
				if isinstance(asset, (EventAsset)): self.__add_asset(ASSET_TYPE_PREVIEW, asset)
				else: self.__add_asset(ASSET_TYPE_PREVIEW, EventAsset(**asset))
	
		
		pass



	def Find(self, assetType, source, **kwargs):
		assetCollection = self.__dict__.get(assetType)
		if not assetCollection: return None

		found = []
		for asset in assetCollection:
			if source and asset.source != source: continue

			shouldContinue = True
			for key in kwargs.keys():
				if not shouldContinue: break
				if key in asset.__dict__.keys():
					if key in ["source", "url"]: continue
					if kwargs[key] and asset.__dict__[key] != kwargs[key]:
						shouldContinue = False
						break

			if shouldContinue: found.append(asset)


		return found


	def __repr__(self):
		return repr(self.__dict__)
