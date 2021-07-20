import sys, os, json, re
import datetime
from pprint import pprint

from Constants import *
from TimeZoneUtils import *
from StringUtils import *
from Matching import __strip_to_alphanumeric
import Teams
from Data import TheSportsDB, SportsDataIO

WEIGHT_SPORT = 1
WEIGHT_LEAGUE = 5
WEIGHT_SEASON = 10
WEIGHT_SUBSEASON = 6
WEIGHT_WEEK = 4
WEIGHT_EVENT_DATE = 20
WEIGHT_GAME = 1
WEIGHT_TEAM = 25
WEIGHT_VS = 30

cached_schedules = dict() # cached_schedules[sport][league][eventHash][subHash]

class event_cache_dict(dict):
	def __init__(self, weight, *args, **kwargs):
		dict.__init__(self, *args, **kwargs)
		self.weight = weight
		self.sports = event_cache_dict(WEIGHT_SPORT, parent=self)
		self.leagues = event_cache_dict(WEIGHT_LEAGUE, parent=self)
		self.seasons = event_cache_dict(WEIGHT_SEASON, parent=self)
		self.subseasons = event_cache_dict(WEIGHT_SUBSEASON, parent=self)
		self.weeks = event_cache_dict(WEIGHT_WEEK, parent=self)
		self.dates = event_cache_dict(WEIGHT_EVENT_DATE, parent=self)
		self.games = event_cache_dict(WEIGHT_GAME, parent=self)
		self.teams = event_cache_dict(WEIGHT_TEAM, parent=self)
		self.vs = event_cache_dict(WEIGHT_VS, parent=self)
		self.parent = kwargs.get("parent")

class event:
	def __init__(self, **kwargs):
		self.sport = str(kwargs.get("sport"))
		self.league = str(kwargs.get("league"))
		self.season = str(kwargs.get("season"))
		self.date = kwargs.get("date")
		self.title = str(kwargs.get("title"))
		self.altTitle = str(kwargs.get("altTitle"))
		self.description = str(kwargs.get("description"))
		self.homeTeam = str(kwargs.get("homeTeam"))
		self.awayTeam = str(kwargs.get("awayTeam"))
		# TODO: fields for non team-based sports, like Boxing

		# Additional metadata items (if provided)
		self.network = str(kwargs.get("network"))
		self.poster = str(kwargs.get("poster"))
		self.fanArt = str(kwargs.get("fanArt"))
		self.thumbnail = str(kwargs.get("thumbnail"))
		self.banner = str(kwargs.get("banner"))
		self.preview = str(kwargs.get("preview"))

		self.TheSportsDBID = str(kwargs.get("TheSportsDBID"))
		self.SportsDataIOID = str(kwargs.get("SportsDataIOID"))

	def augment(self, **kwargs):
		if not self.sport: self.sport = str(kwargs.get("sport"))
		if not self.league: self.league = str(kwargs.get("league"))
		if not self.season: self.season = str(kwargs.get("season"))
		if not self.date: self.date = kwargs.get("date")

		if not kwargs.get("title"): self.title = str(kwargs.get("title"))
		if not kwargs.get("altTitle"): self.altTitle = str(kwargs.get("altTitle"))
		if not kwargs.get("description"): self.description = str(kwargs.get("description"))
		
		if not self.homeTeam: self.homeTeam = str(kwargs.get("homeTeam"))
		if not self.homeTeam: self.awayTeam = str(kwargs.get("awayTeam"))
		# TODO: fields for non team-based sports, like Boxing

		# Additional metadata items (if provided)
		if not self.network: self.network = str(kwargs.get("network"))
		if not self.poster: self.poster = str(kwargs.get("poster"))
		if not self.fanArt: self.fanArt = str(kwargs.get("fanArt"))
		if not self.thumbnail: self.thumbnail = str(kwargs.get("thumbnail"))
		if not self.banner: self.banner = str(kwargs.get("banner"))
		if not self.preview: self.preview = str(kwargs.get("preview"))
		
		if not self.TheSportsDBID: self.TheSportsDBID = str(kwargs.get("TheSportsDBID"))
		if not self.SportsDataIOID: self.SportsDataIOID = str(kwargs.get("SportsDataIOID"))

def foo():
	league = LEAGUE_MLB
	season = 2021
	(leagueName, sport) = known_leagues[league]

	sched = GetSchedule(sport, league, season)
	pass

def GetSchedule(sport, league, season, download=False):
	if not sport in supported_sports:
		return None
	if not league in known_leagues.keys():
		return None

	sched = dict()
	
	if download == False: # Nab from cache
		sched = __get_schedule_from_cache(sport, league, season)
   
	else: # Download from APIs
		sched = __download_all_schedule_data(sport, league, season)

	return sched

def __download_all_schedule_data(sport, league, season):
	sched = dict()
	teams = Teams.GetTeams(league)

	# Retrieve data from TheSportsDB.com
	downloadedJson = TheSportsDB.__the_sports_db_download_schedule_for_league_and_season(league, season)
	sportsDbSchedule = json.loads(downloadedJson)
	for schedEvent in sportsDbSchedule["events"]:
		homeTeamStripped = __strip_to_alphanumeric(normalize_string(schedEvent["strHomeTeam"]))
		awayTeamStripped = __strip_to_alphanumeric(normalize_string(schedEvent["strAwayTeam"]))
		homeTeamAbbrev = Teams.cached_team_keys[league][homeTeamStripped]
		awayTeamAbbrev = Teams.cached_team_keys[league][awayTeamStripped]
		
		# TODO: Relate all date/times to UTC (currently presented as E[S|D]T (local))
		date = None
		if schedEvent.get("dateEventLocal") and schedEvent.get("strTimeLocal"):
			# Relative to East Coast
			# TODO: Account for Daylight Savings Time/Summer Time? What about Arizona?
			date = datetime.datetime.strptime("%sT%s" % (schedEvent["dateEventLocal"], schedEvent["strTimeLocal"]), "%Y-%m-%dT%H:%M:%S")
			date = date.replace(tzinfo=EasternTime).astimezone(tz=UTC)
		elif schedEvent.get("dateEvent") and schedEvent.get("strTime"):
			# Zulu Time
			date = datetime.datetime.strptime("%sT%s" % (schedEvent["dateEvent"], schedEvent["strTime"]), "%Y-%m-%dT%H:%M:%S")
			date = date.replace(tzinfo=UTC)
		elif schedEvent.get("strTimestamp"):
			# Zulu Time
			date = datetime.datetime.strptime(schedEvent["strTimestamp"], "%Y-%m-%dT%H:%M:%S")
			date = date.replace(tzinfo=UTC)

		kwargs = {
			"sport": sport,
			"league": league,
			"season": season,
			"date": date,
			"TheSportsDBID": normalize_string(schedEvent["idEvent"]),
			"title": normalize_string(schedEvent["strEvent"]),
			"altTitle": normalize_string(schedEvent["strEventAlternate"]),
			#"description": normalize_string(schedEvent["strDescriptionEN"]),
			"homeTeam": homeTeamAbbrev,
			"awayTeam": awayTeamAbbrev,
			"network": normalize_string(schedEvent["strTVStation"]),
			"poster": normalize_string(schedEvent["strPoster"]),
			"fanArt": normalize_string(schedEvent["strFanart"]),
			"thumbnail": normalize_string(schedEvent["strThumb"]),
			"banner": normalize_string(schedEvent["strBanner"]),
			"preview": normalize_string(schedEvent["strVideo"])}
		ev = event(**kwargs)

		hash = __sched_compute_hash(ev)
		subhash = __sched_compute_time_hash(ev.date)
		print("%s|%s" % (hash, subhash))
		if not hash in sched.keys():
			sched.setdefault(hash, {subhash:ev})
		else:
			evdict = sched[hash]
			if (not subhash in evdict.keys()):
				sched[hash].setdefault(subhash, ev)
			else:
				sched[hash][subhash].augment(**ev.__dict__)


	# Augment/replace with data from SportsData.io
	downloadedJsons = SportsDataIO.__sports_data_io_download_schedule_for_league_and_season(league, season)
	for downloadedJson in downloadedJsons:
		sportsDataIOSchedule = json.loads(downloadedJson)
		for schedEvent in sportsDataIOSchedule:
			homeTeamAbbrev = normalize_string(schedEvent["HomeTeam"])
			awayTeamAbbrev = normalize_string(schedEvent["AwayTeam"])
			if awayTeamAbbrev == "BYE":
				continue
			homeTeam = Teams.cached_teams[league][homeTeamAbbrev]
			awayTeam = Teams.cached_teams[league][awayTeamAbbrev]

			# TODO: Relate all date/times to UTC (currently presented as E[S|D]T (local))
			# TODO: Account for Daylight Savings Time/Summer Time? What about Arizona?
			date = None
			if schedEvent.get("Date"):
				date = datetime.datetime.strptime(schedEvent["Date"], "%Y-%m-%dT%H:%M:%S")
				date = date.replace(tzinfo=EasternTime).astimezone(tz=UTC)
			elif schedEvent.get("DateTime"):
				date = datetime.datetime.strptime(schedEvent["DateTime"], "%Y-%m-%dT%H:%M:%S")
				date = date.replace(tzinfo=EasternTime).astimezone(tz=UTC)
	
			gameID = None
			if schedEvent.get("GameKey"):
				gameID = normalize_string(str(schedEvent["GameKey"]))
			if schedEvent.get("GameID"):
				gameID = normalize_string(str(schedEvent["GameID"]))

			kwargs = {
				"sport": sport,
				"league": league,
				"season": season,
				"date": date,
				"SportsDataIOID": gameID,
				"title": "%s vs %s" % (homeTeam.FullName, awayTeam.FullName),
				"altTitle": "%s @ %s" % (awayTeam.FullName, homeTeam.FullName),
				"homeTeam": homeTeamAbbrev,
				"awayTeam": awayTeamAbbrev,
				"network": normalize_string(schedEvent["Channel"])}
			ev = event(**kwargs)

			hash = __sched_compute_hash(ev)
			subhash = __sched_compute_time_hash(ev.date)
			#print("%s|%s" % (hash, subhash))
			if not hash in sched.keys():
				sched.setdefault(hash, {subhash:ev})
			else:
				evdict = sched[hash]
				if (not subhash in evdict.keys()):
					evdict.setdefault(subhash, ev)
				else:
					evdict[subhash].augment(**ev.__dict__)
	
	return sched







def __get_schedule_from_cache(sport, league, season):
	if not sport in supported_sports:
		return None
	if not league in known_leagues.keys():
		return None
	if not __schedule_cache_has_schedule(sport, league, season):
		if not __schedule_cache_file_exists(sport, league, season):
			__refresh_schedule_cache(sport, league, season)
		else:
			jsonEvents = []
			cachedJson = __read_schedule_cache_file(sport, league, season) #TODO: Try/Catch
			jsonEvents = json.loads(cachedJson)
			if (len(jsonEvents) == 0):
				__refresh_schedule_cache(sport, league, season)
			else:
				cached_schedules.setdefault(sport, dict())
				cached_schedules[sport].setdefault(league, dict())
				cached_schedules[sport][league].setdefault(season, dict())
				schedules = dict()
				for jsonTeam in jsonEvents:
					eventDict = dict(jsonTeam)
					dateStr = eventDict["date"]
					date = ParseIso8861Date(dateStr)
					eventDict["date"] = date
					schedule = event(**eventDict)
					hash = __sched_compute_hash(schedule)
					subhash = __sched_compute_time_hash(schedule.date)

					schedules.setdefault(hash, dict())
					schedules[hash].setdefault(subhash, event)
				cached_schedules[sport][league][season] = schedules
	return cached_schedules[sport][league][season]

def __refresh_schedule_cache(sport, league, season):
	print("Refreshing %s %s schedules cache ..." % (league, season))
	cached_schedules.setdefault(sport, dict())
	cached_schedules[sport].setdefault(league, dict())
	cached_schedules[sport][league].setdefault(season, dict())
	schedules = __download_all_schedule_data(sport, league, season)
	cached_schedules[sport][league][season] = schedules
	jsonEvents = []
	for daysEvents in schedules.values():
		for event in daysEvents.values():
			eventDict = dict(event.__dict__)
			date = eventDict["date"]
			dateStr = date.strftime("%Y-%m-%dT%H:%M:%S%z")
			eventDict["date"] = dateStr
			jsonEvents.append(eventDict)
	__write_schedule_cache_file(sport, league, season, json.dumps(jsonEvents, sort_keys=True, indent=4))



def __schedule_cache_has_schedule(sport, league, season):
	if len(cached_schedules) == 0:
		return False
	if not sport in cached_schedules.keys():
		return False
	if not league in cached_schedules[sport].keys():
		return False
	if not cached_schedules[sport][league].get(season):
		return False
	return len(cached_schedules[sport][league][season]) > 0

def __schedule_cache_file_exists(sport, league, season):
	path = __get_schedule_cache_file_path(sport, league, season)
	return os.path.exists(path)

def __read_schedule_cache_file(sport, league, season):
	path = __get_schedule_cache_file_path(sport, league, season)
	return open(path, "r").read() # TODO: Invalidate cache

def __write_schedule_cache_file(sport, league, season, json):
	print("Writing %s %s schedules cache to disk ..." % (league, season))
	path = __get_schedule_cache_file_path(sport, league, season)
	dir = os.path.dirname(path)
	if os.path.exists(dir) == False:
		nodes = Utils.SplitPath(dir)
		agg = None
		for node in nodes:
			agg = os.path.join(agg, node) if agg else node
			if os.path.exists(agg) == False:
				os.mkdir(agg)
	f = open(path, "w")
	f.write(json)
	f.close()

def __get_schedule_cache_file_path(sport, league, season):
	# TODO: Modify filename when non-seasonal sport, like Boxing
	path = os.path.abspath(r"%s/%s%s/%s-Schedule.json" % (os.path.dirname(__file__), DATA_PATH_LEAGUES, league, season))
	return path





























def __sched_compute_hash(ev):
	molecules = []
	
	sport = __sched_compute_sport_hash(ev.sport) or ""
	molecules.append(sport)

	# TODO: Omit when taking on non-league sports, like Boxing
	league = __sched_compute_league_hash(ev.league) or ""
	molecules.append(league)

	# TODO: Omit when taking on non-seasonal sports, like Boxing
	season = __sched_compute_league_hash(ev.season) or ""
	molecules.append(season)

	date = __sched_compute_date_hash(ev.date) or ""
	molecules.append(date)

	# TODO: Modify when taking on non-team sports, like Boxing
	home = __sched_compute_team_hash(ev.homeTeam) or ""
	away = __sched_compute_team_hash(ev.awayTeam) or ""
	molecules.append(home)
	molecules.append(away)

	return "|".join(molecules)

def __sched_compute_sport_hash(sport):
	if not sport:
		return None
	return sport.lower()

def __sched_compute_league_hash(league):
	if not league:
		return None
	return league.lower()

def __sched_compute_season_hash(season):
	if not season:
		return None

	s = ""
	if (isinstance(season, basestring)):
		s = season
	if (isinstance(season, int)):
		s = str(season)

	for expr in season_expressions:
		p = re.compile(expr, re.IGNORECASE)
		m = p.search(s)
		if m:
			return __expand_year(m.group("season_begin_year")).lower()
	
	return None

def __sched_compute_date_hash(eventDate):
	if not eventDate:
		return None

	if not isinstance(eventDate, datetime.datetime):
		return None

	return eventDate.strftime("%Y%m%d")

def __sched_compute_time_hash(eventDate):
	if not eventDate:
		return None

	if not isinstance(eventDate, datetime.datetime):
		return None

	return eventDate.strftime("%H")

def __sched_compute_team_hash(abbrev):
	if not abbrev:
		return None
	return abbrev.lower()



