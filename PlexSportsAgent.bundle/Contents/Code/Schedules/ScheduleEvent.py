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

		self.__augmentationkey__ = None
		self.__key__ = None

		# TODO: May make this into its own separate shape, rather than continually extending ScheduleEvent
		self.TheSportsDBID = None
		self.SportsDataIOID = None
		self.MLBAPIID = None
		self.NHLAPIID = None
		if kwargs.get("TheSportsDBID"): self.TheSportsDBID = str(kwargs.get("TheSportsDBID")) 
		if kwargs.get("SportsDataIOID"): self.SportsDataIOID = str(kwargs.get("SportsDataIOID")) 
		if kwargs.get("MLBAPIID"): self.MLBAPIID = str(kwargs.get("MLBAPIID")) 
		if kwargs.get("NHLAPIID"): self.NHLAPIID = str(kwargs.get("NHLAPIID")) 

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
		if self.playoffround == None and kwargs.get("playoffround"): self.playoffround = kwargs.get("playoffround")
		if self.eventindicator == None and kwargs.get("eventindicator"): self.eventindicator = kwargs.get("eventindicator")
		if self.week == None and kwargs.get("week"): self.week = kwargs.get("week")
		if not self.game and kwargs.get("game"): self.game = kwargs.get("game")
		
		if not self.homeTeam: self.homeTeam = deunicode(kwargs.get("homeTeam"))
		if not self.awayTeam: self.awayTeam = deunicode(kwargs.get("awayTeam"))
		# TODO: fields for non team-based sports, like Boxing

		# Additional metadata items (if provided)
		if not self.title: self.title = deunicode(kwargs.get("title"))
		if not self.altTitle: self.altTitle = deunicode(kwargs.get("altTitle"))
		if not self.description: self.description = deunicode(kwargs.get("description"))
		if not self.network: self.network = deunicode(kwargs.get("network"))
		if not self.poster: self.poster = deunicode(kwargs.get("poster"))
		if not self.fanArt: self.fanArt = deunicode(kwargs.get("fanArt"))
		if not self.thumbnail: self.thumbnail = deunicode(kwargs.get("thumbnail"))
		if not self.banner: self.banner = deunicode(kwargs.get("banner"))
		if not self.preview: self.preview = deunicode(kwargs.get("preview"))
		
		if not self.TheSportsDBID and kwargs.get("TheSportsDBID"): self.TheSportsDBID = str(kwargs.get("TheSportsDBID"))
		if not self.SportsDataIOID and kwargs.get("SportsDataIOID"): self.SportsDataIOID = str(kwargs.get("SportsDataIOID"))
		if not self.MLBAPIID and kwargs.get("MLBAPIID"): self.MLBAPIID = str(kwargs.get("MLBAPIID"))
		if not self.NHLAPIID and kwargs.get("NHLAPIID"): self.NHLAPIID = str(kwargs.get("NHLAPIID"))
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
	subhash = sched_compute_time_hash(event.date)

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
		elif None in evdict.keys(): # Augment and replace time-naive
			repl = evdict[None]
			repl.augment(**event.__dict__)
			del(evdict[None])
			evdict[subhash] = repl
		else: # Must be a double-header. Append
			evdict.setdefault(subhash, event)

	pass