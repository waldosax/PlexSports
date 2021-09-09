from Constants.Assets import *
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
		if not self.name or self.name == self.fullName:
			if kwargs.get("name") or kwargs.get("Name"):
				self.name = deunicode(kwargs.get("name") or kwargs.get("Name"))
		
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




class TeamAssets():
	def __init__(self, **kwargs):
		self.banner = []
		self.badge = []
		self.fanArt = []
		self.jersey = []
		self.logo = []
		self.wordmark = []
		self.colors = []
		self.Augment(**kwargs)

	def __add_asset(self, assetType, asset, **kwargs):
		found = self.Find(assetType, asset.source, asset.season, **kwargs)
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
		
		if kwargs.get(ASSET_TYPE_COLORS):
			for asset in kwargs[ASSET_TYPE_COLORS]:
				if isinstance(asset, (TeamAsset)): self.__add_asset(ASSET_TYPE_COLORS, asset)
				else: self.__add_asset(ASSET_TYPE_COLORS, TeamAsset(**asset), colortype=asset.get("colortype"))
	
		
		pass



	def Find(self, assetType, source, season, **kwargs):
		assetCollection = self.__dict__.get(assetType)
		if not assetCollection: return None

		found = []
		for asset in assetCollection:
			if source and asset.source != source: continue
			if season and asset.season != season: continue

			shouldContinue = True
			for key in kwargs.keys():
				if not shouldContinue: break
				if key in asset.__dict__.keys():
					if key in ["source", "season", "url", "value"]: continue
					if kwargs[key] and asset.__dict__[key] != kwargs[key]:
						shouldContinue = False
						break

			if shouldContinue: found.append(asset)


		return found


	def __repr__(self):
		return repr(self.__dict__)

class TeamAsset():
	def __init__(self, **kwargs):
		self.source = deunicode(kwargs.get("source"))
		self.season = int(kwargs.get("season") or 0) or None
		self.url = deunicode(kwargs["url"]) if kwargs.get("url") else None
		self.colortype = deunicode(kwargs["colortype"]) if kwargs.get("colortype") else None
		self.value = deunicode(kwargs["value"]) if kwargs.get("value") else None
		pass

	@property
	def key(self):
		return ("%s%s%s" % (self.source,
					  self.season if self.season else "",
					  self.colortype if self.colortype else "")).lower()

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
		self.MLBAPIID = kwargs.get("MLBAPIID")
		self.NHLAPIID = kwargs.get("NHLAPIID")
		self.NBAdotcomID = kwargs.get("NBAdotcomID")
		self.ESPNAPIID = kwargs.get("ESPNAPIID")
		self.ProBaseballReferenceID = kwargs.get("ProBaseballReferenceID")
		self.ProBasketballReferenceID = kwargs.get("ProBasketballReferenceID")
		self.ProFootballReferenceID = kwargs.get("ProFootballReferenceID")
		self.ProHockeyReferenceID = kwargs.get("ProHockeyReferenceID")
		self.SportsDBID = kwargs.get("SportsDBID")
		self.SportsDataIOID = kwargs.get("SportsDataIOID")
		pass

	def Augment(self, **kwargs):
		if kwargs.get("MLBAPIID"): self.MLBAPIID = kwargs["MLBAPIID"]
		if kwargs.get("NHLAPIID"): self.NHLAPIID = kwargs["NHLAPIID"]
		if kwargs.get("ESPNAPIID"): self.ESPNAPIID = kwargs["ESPNAPIID"]
		if kwargs.get("NBAdotcomID"): self.NBAdotcomID = kwargs["NBAdotcomID"]
		if kwargs.get("ProBaseballReferenceID"): self.ProBaseballReferenceID = kwargs["ProBaseballReferenceID"]
		if kwargs.get("ProBasketballReferenceID"): self.ProBasketballReferenceID = kwargs["ProBasketballReferenceID"]
		if kwargs.get("ProFootballReferenceID"): self.ProFootballReferenceID = kwargs["ProFootballReferenceID"]
		if kwargs.get("ProHockeyReferenceID"): self.ProHockeyReferenceID = kwargs["ProHockeyReferenceID"]
		if kwargs.get("SportsDBID"): self.SportsDBID = kwargs["SportsDBID"]
		if kwargs.get("SportsDataIOID"): self.SportsDataIOID = kwargs["SportsDataIOID"]
		pass
