import datetime

from Hashes import *
from StringUtils import *
from TimeZoneUtils import *


class ScheduleEvent:
	def __init__(self, **kwargs):
		self.sport = deunicode(kwargs.get("sport"))
		self.league = deunicode(kwargs.get("league"))
		self.season = deunicode(str(kwargs.get("season")))
		self.date = kwargs.get("date")

		# Event metadata
		self.subseason = kwargs.get("subseason")
		self.playoffround = kwargs.get("playoffround")
		self.eventindicator = kwargs.get("eventindicator")
		self.week = kwargs.get("week")
		self.game = kwargs.get("game")

		self.homeTeam = deunicode(kwargs.get("homeTeam"))
		self.awayTeam = deunicode(kwargs.get("awayTeam"))
		# TODO: fields for non team-based sports, like Boxing

		# Additional metadata items (if provided)
		self.title = deunicode(kwargs.get("title"))
		self.altTitle = deunicode(kwargs.get("altTitle"))
		self.description = kwargs.get("description")
		self.network = deunicode(kwargs.get("network"))
		self.poster = deunicode(kwargs.get("poster"))
		self.fanArt = deunicode(kwargs.get("fanArt"))
		self.thumbnail = deunicode(kwargs.get("thumbnail"))
		self.banner = deunicode(kwargs.get("banner"))
		self.preview = deunicode(kwargs.get("preview"))

		self.__key__ = None
		self.TheSportsDBID = None
		self.SportsDataIOID = None
		if kwargs.get("TheSportsDBID"): self.TheSportsDBID = str(kwargs.get("TheSportsDBID")) 
		if kwargs.get("SportsDataIOID"): self.SportsDataIOID = str(kwargs.get("SportsDataIOID")) 

	def augment(self, **kwargs):
		if not self.sport and kwargs.get("sport"): self.sport = deunicode(kwargs.get("sport"))
		if not self.league and kwargs.get("league"): self.league = deunicode(kwargs.get("league"))
		if not self.season and kwargs.get("season"): self.season = deunicode(str(kwargs.get("season")))
		if not self.date and kwargs.get("date"):
			if isinstance(kwargs["date"], (datetime.datetime, datetime.date)): self.date = kwargs["date"]
			elif isinstance(kwargs["date"], basestring) and IsISO8601Date(kwargs["date"]): self.date = ParseISO8601Date(kwargs["date"]).replace(tzinfo=UTC)
		
		if self.subseason == None and kwargs.get("subseason"): self.subseason = kwargs.get("subseason")
		if self.playoffround == None and kwargs.get("playoffround"): self.playoffround = kwargs.get("playoffround")
		if self.eventindicator == None and kwargs.get("eventindicator"): self.eventindicator = kwargs.get("eventindicator")
		if self.week == None and kwargs.get("week"): self.week = kwargs.get("week")
		if not self.game and kwargs.get("game"): self.game = kwargs.get("game")
		
		if not self.homeTeam: self.homeTeam = deunicode(kwargs.get("homeTeam"))
		if not self.awayTeam: self.awayTeam = deunicode(kwargs.get("awayTeam"))
		# TODO: fields for non team-based sports, like Boxing

		# Additional metadata items (if provided)
		if not kwargs.get("title"): self.title = deunicode(kwargs.get("title"))
		if not kwargs.get("altTitle"): self.altTitle = deunicode(kwargs.get("altTitle"))
		if not kwargs.get("description"): self.description = deunicode(kwargs.get("description"))
		if not self.network: self.network = deunicode(kwargs.get("network"))
		if not self.poster: self.poster = deunicode(kwargs.get("poster"))
		if not self.fanArt: self.fanArt = deunicode(kwargs.get("fanArt"))
		if not self.thumbnail: self.thumbnail = deunicode(kwargs.get("thumbnail"))
		if not self.banner: self.banner = deunicode(kwargs.get("banner"))
		if not self.preview: self.preview = deunicode(kwargs.get("preview"))
		
		if not self.TheSportsDBID and kwargs.get("TheSportsDBID"): self.TheSportsDBID = str(kwargs.get("TheSportsDBID"))
		if not self.SportsDataIOID and kwargs.get("SportsDataIOID"): self.SportsDataIOID = str(kwargs.get("SportsDataIOID"))
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

