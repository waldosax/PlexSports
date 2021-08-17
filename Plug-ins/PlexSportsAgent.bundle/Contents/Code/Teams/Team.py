
from StringUtils import *

class Team():
	def __init__(self, fullName=None, **kwargs):
		self.key = deunicode(kwargs.get("key") or kwargs.get("Key") or "")
		self.abbreviation = deunicode(kwargs.get("abbreviation") or kwargs.get("Abbreviation") or "")

		self.fullName = fullName or deunicode(kwargs.get("fullName") or kwargs.get("FullName") or "")
		self.city = deunicode(kwargs.get("city") or kwargs.get("City"))
		self.name = deunicode(kwargs.get("name") or kwargs.get("Name"))
		
		self.active = (kwargs.get("active") or kwargs.get("Active")) == True
		self.description = deunicode(kwargs.get("description") or kwargs.get("Description") or "") or None

		self.conference = deunicode(kwargs.get("conference") or kwargs.get("Conference"))
		self.division = deunicode(kwargs.get("division") or kwargs.get("Division"))
	
		self.years = []
		if kwargs.get("years"):
			for span in kwargs["years"]:
				if isinstance(span, (YearSpan)):
					self.years.append(span)
				else:
					fromYear = span.get("fromYear") or span.get("from")
					toYear = span.get("toYear") or span.get("to")
					self.years.append(YearSpan(fromYear, toYear))

		self.aliases = []
		if kwargs.get("aliases"):
			for alias in kwargs["aliases"]:
				self.aliases.append(alias)
			self.aliases = list(set(self.aliases))

		self.identity = TeamIdentity(**kwargs)
		self.identity.Augment(**kwargs)
		if kwargs.get("identity"):
			identity = kwargs["identity"]
			if isinstance(identity, (TeamIdentity)): self.identity.Augment(**identity.__dict__)
			elif isinstance(identity, (dict)): self.identity.Augment(**identity)

		self.assets = TeamAssets()
		if kwargs.get("assets"):
			assets = kwargs["assets"]
			if isinstance(assets, (TeamAssets)): self.assets.Augment(**assets.__dict__)
			elif isinstance(assets, (dict)): self.assets.Augment(**assets)

		pass


	def Augment(self, **kwargs):
		if not self.key: self.key = deunicode(kwargs.get("key") or kwargs.get("Key") or "")
		if not self.abbreviation: self.abbreviation = deunicode(kwargs.get("abbreviation") or kwargs.get("Abbreviation") or "")

		if not self.fullName: self.fullName = deunicode(kwargs.get("fullName") or kwargs.get("FullName"))
		if not self.city: self.city = deunicode(kwargs.get("city") or kwargs.get("City"))
		if not self.name: self.name = deunicode(kwargs.get("name") or kwargs.get("Name"))
		
		if not self.active: self.active = (kwargs.get("active") or kwargs.get("Active")) == True
		if not self.description: self.description = deunicode(kwargs.get("description") or kwargs.get("Description") or "") or None

		if not self.conference: self.conference = deunicode(kwargs.get("conference") or kwargs.get("Conference"))
		if not self.division: self.division = deunicode(kwargs.get("division") or kwargs.get("Division"))

		if kwargs.get("years"):
			for span in kwargs["years"]:
				if isinstance(span, (YearSpan)):
					fromYear = span.fromYear
					toYear = span.toYear
					#self.years.append(span)
				else:
					fromYear = int(span.get("fromYear") or span.get("from") or "0") or None
					toYear = int(span.get("toYear") or span.get("to") or "0") or None

				if not self.years: shouldAppend = True
				else:
					shouldAppend = False
					foundSpan = False
					for existing in self.years:
						if fromYear >= existing.fromYear:
							if toYear <= existing.toYear:
								foundSpan = True
								break
					if not foundSpan: shouldAppend = True
					# TODO: This should get me by for now

				if shouldAppend:
					self.years.append(YearSpan(fromYear, toYear))

		if kwargs.get("aliases"):
			for alias in kwargs["aliases"]:
				if not alias in self.aliases:
					self.aliases.append(alias)
			self.aliases = list(set(self.aliases))

		self.identity.Augment(**kwargs)
		if kwargs.get("identity"):
			identity = kwargs["identity"]
			if isinstance(identity, (TeamIdentity)): self.identity.Augment(**identity.__dict__)
			elif isinstance(identity, (dict)): self.identity.Augment(**identity)
	
		if kwargs.get("assets"):
			assets = kwargs["assets"]
			if isinstance(assets, (TeamAssets)): self.assets.Augment(**assets.__dict__)
			elif isinstance(assets, (dict)): self.assets.Augment(**assets)

		pass

	def __repr__(self):
		return self.fullName


class YearSpan():
	def __init__(self, fromYear=None, toYear=None):
		# TODO: validation
		self.fromYear = int(fromYear or 0) or None
		self.toYear = int(toYear or 0) or None

	def __repr__(self):
		s = ""
		if self.fromYear:
			s += ("from %s" % (self.fromYear))
		elif not self.toYear:
			s = "[empty]"
			return s
		else:
			s += "?"

		if self.toYear:
			s += (" to %s" % (self.toYear))
		else:
			s += " to [now]"

		return s


ASSET_SOURCE_THESPORTSDB = "thesportsdb"
ASSET_SOURCE_SPORTSDATAIO = "sportsdataio"
ASSET_SOURCE_PROBASEBALLRFERENCE = "probaseballreference"
ASSET_SOURCE_PROBASKETBALLRFERENCE = "probasketballreference"
ASSET_SOURCE_PROFOOTBALLRFERENCE = "profootballreference"
ASSET_SOURCE_PROHOCKEYRFERENCE = "prohockeyreference"
ASSET_SOURCE_NFLDOTCOM = "nfldotcom"
ASSET_SOURCE_WIKIPEDIA = "wikipedia"

ASSET_TYPE_BANNERS = "banner"
ASSET_TYPE_BADGES = "badge"
ASSET_TYPE_FANART = "fanArt"
ASSET_TYPE_JERSEYS = "jersey"
ASSET_TYPE_LOGOS = "logo"
ASSET_TYPE_WORDMARKS = "wordmark"

class TeamAssets():
	def __init__(self, **kwargs):
		self.banner = []
		self.badge = []
		self.fanArt = []
		self.jersey = []
		self.logo = []
		self.wordmark = []
		self.Augment(**kwargs)

	def __add_asset(self, assetType, asset):
		found = self.Find(assetType, asset.source, asset.season)
		if not found: self.__dict__[assetType].append(asset)

	def Augment(self, **kwargs):
		if kwargs.get(ASSET_TYPE_BANNERS):
			for asset in kwargs[ASSET_TYPE_BANNERS]:
				if isinstance(asset, (TeamAsset)): self.__add_asset(ASSET_TYPE_BANNERS, asset)
				else: self.__add_asset(ASSET_TYPE_BANNERS, TeamAsset(**asset))
		
		if kwargs.get(ASSET_TYPE_BADGES):
			for asset in kwargs[ASSET_TYPE_BADGES]:
				if isinstance(asset, (TeamAsset)): self.__add_asset(ASSET_TYPE_BADGES, asset)
				else: self.__add_asset(ASSET_TYPE_BADGES, TeamAsset(**asset))
		
		if kwargs.get(ASSET_TYPE_FANART):
			for asset in kwargs[ASSET_TYPE_FANART]:
				if isinstance(asset, (TeamAsset)): self.__add_asset(ASSET_TYPE_FANART, asset)
				else: self.__add_asset(ASSET_TYPE_FANART, TeamAsset(**asset))
		
		if kwargs.get(ASSET_TYPE_JERSEYS):
			for asset in kwargs[ASSET_TYPE_JERSEYS]:
				if isinstance(asset, (TeamAsset)): self.__add_asset(ASSET_TYPE_JERSEYS, asset)
				else: self.__add_asset(ASSET_TYPE_JERSEYS, TeamAsset(**asset))
		
		if kwargs.get(ASSET_TYPE_LOGOS):
			for asset in kwargs[ASSET_TYPE_LOGOS]:
				if isinstance(asset, (TeamAsset)): self.__add_asset(ASSET_TYPE_LOGOS, asset)
				else: self.__add_asset(ASSET_TYPE_LOGOS, TeamAsset(**asset))
		
		if kwargs.get(ASSET_TYPE_WORDMARKS):
			for asset in kwargs[ASSET_TYPE_WORDMARKS]:
				if isinstance(asset, (TeamAsset)): self.__add_asset(ASSET_TYPE_WORDMARKS, asset)
				else: self.__add_asset(ASSET_TYPE_WORDMARKS, TeamAsset(**asset))

	def Find(self, assetType, source, season):
		assetCollection = self.__dict__.get(assetType)
		if not assetCollection: return None

		found = []
		for asset in assetCollection:
			if source:
				if asset.source == source:
					if season:
						if asset.season == season:
							found.append(asset)
					else:
						found.append(asset)
			else:
				if season:
					if asset.season == season:
						found.append(asset)
				else:
					found.append(asset)

		return found


	def __repr__(self):
		return repr(self.__dict__)

class TeamAsset():
	def __init__(self, **kwargs):
		self.source = deunicode(kwargs.get("source") or "")
		self.season = int(kwargs.get("season") or 0) or None
		self.url = deunicode(str(kwargs.get("url") or ""))
		pass

	def get_key(self):
		return ("%s%s" % (source, season if season else "")).lower()

	def __repr__(self):
		s = ""
		if self.source:
			s += "["
			s += self.source
			if self.season:
				s += ", %s" % self.season
			s += "]"
		if self.url:
			if s: s += " "
			s += self.url
		return s

class TeamIdentity:
	def __init__(self, **kwargs):
		self.ProBaseballReferenceID = kwargs.get("ProBaseballReferenceID")
		self.ProBasketballReferenceID = kwargs.get("ProBasketballReferenceID")
		self.ProFootballReferenceID = kwargs.get("ProFootballReferenceID")
		self.ProHockeyReferenceID = kwargs.get("ProHockeyReferenceID")
		self.SportsDBID = kwargs.get("SportsDBID")
		self.SportsDataIOID = kwargs.get("SportsDataIOID")
		pass

	def Augment(self, **kwargs):
		if kwargs.get("ProBaseballReferenceID"): self.ProBaseballReferenceID = kwargs["ProBaseballReferenceID"]
		if kwargs.get("ProBasketballReferenceID"): self.ProBasketballReferenceID = kwargs["ProBasketballReferenceID"]
		if kwargs.get("ProFootballReferenceID"): self.ProFootballReferenceID = kwargs["ProFootballReferenceID"]
		if kwargs.get("ProHockeyReferenceID"): self.ProHockeyReferenceID = kwargs["ProHockeyReferenceID"]
		if kwargs.get("SportsDBID"): self.SportsDBID = kwargs["SportsDBID"]
		if kwargs.get("SportsDataIOID"): self.SportsDataIOID = kwargs["SportsDataIOID"]
		pass
