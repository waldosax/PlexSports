# Python framework
import sys, os, json, re
import datetime
from pprint import pprint

from Constants import *
from Matching import __strip_to_alphanumeric
from PathUtils import *
from PluginSupport import *
from Serialization import *
from StringUtils import *
import Teams
from TimeZoneUtils import *
from Data import TheSportsDB, SportsDataIO
from Data.CacheContainer import *

CACHE_DURATION = 7
CACHE_VERSION = "2"

WEIGHT_SPORT = 1
WEIGHT_LEAGUE = 5
WEIGHT_SEASON = 12
WEIGHT_SUBSEASON = 6
WEIGHT_PLAYOFF_ROUND = 10
WEIGHT_WEEK = 4
WEIGHT_EVENT_DATE = 20
WEIGHT_GAME = 1
WEIGHT_TEAM = 25
WEIGHT_VS = 8

FLAGS_SPORT = 1
FLAGS_LEAGUE = 2
FLAGS_SEASON = 4
FLAGS_SUBSEASON = 8
FLAGS_PLAYOFF_ROUND = 16
FLAGS_WEEK = 32
FLAGS_EVENT_DATE = 64
FLAGS_GAME = 128
FLAGS_TEAM1 = 256
FLAGS_TEAM2 = 512


cached_schedules = dict() # cached_schedules[sport][league][eventHash][subHash]

event_scan = dict()

class ScheduleEvent:
	def __init__(self, **kwargs):
		self.sport = deunicode(kwargs.get("sport"))
		self.league = deunicode(kwargs.get("league"))
		self.season = deunicode(str(kwargs.get("season")))
		self.date = kwargs.get("date")
		self.subseason = kwargs.get("subseason")

		# Event metadata
		self.playoffround = kwargs.get("playoffround")
		self.week = kwargs.get("week")
		self.game = kwargs.get("game")
		self.title = deunicode(kwargs.get("title"))
		self.altTitle = deunicode(kwargs.get("altTitle"))
		self.description = kwargs.get("description")

		self.homeTeam = deunicode(kwargs.get("homeTeam"))
		self.awayTeam = deunicode(kwargs.get("awayTeam"))
		# TODO: fields for non team-based sports, like Boxing

		# Additional metadata items (if provided)
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
		if self.week == None and kwargs.get("week"): self.week = kwargs.get("week")
		if self.playoffround == None and kwargs.get("playoffround"): self.week = kwargs.get("playoffround")
		if not self.game and kwargs.get("game"): self.week = kwargs.get("game")

		if not kwargs.get("title"): self.title = deunicode(kwargs.get("title"))
		if not kwargs.get("altTitle"): self.altTitle = deunicode(kwargs.get("altTitle"))
		if not kwargs.get("description"): self.description = deunicode(kwargs.get("description"))
		
		if not self.homeTeam: self.homeTeam = deunicode(kwargs.get("homeTeam"))
		if not self.awayTeam: self.awayTeam = deunicode(kwargs.get("awayTeam"))
		# TODO: fields for non team-based sports, like Boxing

		# Additional metadata items (if provided)
		if not self.network: self.network = deunicode(kwargs.get("network"))
		if not self.poster: self.poster = deunicode(kwargs.get("poster"))
		if not self.fanArt: self.fanArt = deunicode(kwargs.get("fanArt"))
		if not self.thumbnail: self.thumbnail = deunicode(kwargs.get("thumbnail"))
		if not self.banner: self.banner = deunicode(kwargs.get("banner"))
		if not self.preview: self.preview = deunicode(kwargs.get("preview"))
		
		if not self.TheSportsDBID and kwargs.get("TheSportsDBID"): self.TheSportsDBID = str(kwargs.get("TheSportsDBID"))
		if not self.SportsDataIOID and kwargs.get("SportsDataIOID"): self.SportsDataIOID = str(kwargs.get("SportsDataIOID"))
		self.__key__ = None

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



def Find(meta):
	results = []

	sport = meta.get(METADATA_SPORT_KEY)
	league = meta.get(METADATA_LEAGUE_KEY)
	season = meta.get(METADATA_SEASON_BEGIN_YEAR_KEY)
	airdate = meta.get(METADATA_AIRDATE_KEY)

	# ensure minimally-viable
	if not league in known_leagues.keys():
		print("Not enough information for a minimally-viable match; Invalid League, '%s'." % league)
		return results
	(ln, sp) = known_leagues[league]
	if sport and not sport == sp:
		print("Not enough information for a minimally-viable match; Invalid Sport, '%s'." % sport)
		return results
	if not season and not airdate:
		print("Not enough information for a minimally-viable match; Invalid Season/Date.")
		return results
	elif not season and airdate:
		# TODO: For now, let's assume that season is the same year as airdate.
		#	We know for a fact it's not when season bleeds over a year boundary.
		#	Ex: Superbowl is in February
		season = airdate.year


	# Warm up cache if not already
	GetSchedule(sport, league, str(season))
	
	# Construct an expression
	def construct_expression_fragment(key, molecule, value):
		return r"(?:(?P<%s>%s\:%s)(?:\||$))?" % (key, molecule, re.escape(str(value)))

	def compute_weight(m):
		if not m: return None

		weight = WEIGHT_SPORT
		flags = FLAGS_SPORT
		gd = m.groupdict() 
		for key in gd:
			if key == "league" and m.group(key):
				weight += WEIGHT_LEAGUE
				flags += FLAGS_LEAGUE
			elif key == "season" and m.group(key):
				weight += WEIGHT_SEASON
				flags += FLAGS_SEASON
			elif key == "subseason" and m.group(key):
				weight += WEIGHT_SUBSEASON
				flags += FLAGS_SUBSEASON
			elif key == "playoffround" and m.group(key):
				weight += WEIGHT_PLAYOFF_ROUND
				flags += FLAGS_PLAYOFF_ROUND
			elif key == "week" and m.group(key):
				weight += WEIGHT_WEEK
				flags += FLAGS_WEEK
			elif key == "date" and m.group(key):
				weight += WEIGHT_EVENT_DATE
				flags += FLAGS_EVENT_DATE
			elif key == "game" and m.group(key):
				weight += WEIGHT_GAME
				flags += FLAGS_GAME
			elif key == "team1" and m.group(key):
				weight += WEIGHT_TEAM
				flags += FLAGS_TEAM1
			elif key == "team2" and m.group(key):
				weight += WEIGHT_TEAM
				flags += FLAGS_TEAM2

		if "team1" in gd.keys() and m.group("team1") and "team2" in gd.keys() and m.group("team2"):
			weight += WEIGHT_VS

		if flags & (FLAGS_LEAGUE | FLAGS_SEASON | FLAGS_EVENT_DATE | FLAGS_TEAM1 | FLAGS_TEAM2) == (FLAGS_LEAGUE | FLAGS_SEASON | FLAGS_EVENT_DATE | FLAGS_TEAM1 | FLAGS_TEAM2):
			return weight
		if flags & (FLAGS_LEAGUE | FLAGS_EVENT_DATE | FLAGS_TEAM1 | FLAGS_TEAM2) == (FLAGS_LEAGUE | FLAGS_EVENT_DATE | FLAGS_TEAM1 | FLAGS_TEAM2):
			return weight
		if flags & (FLAGS_LEAGUE | FLAGS_SEASON | FLAGS_EVENT_DATE | FLAGS_TEAM1) == (FLAGS_LEAGUE | FLAGS_SEASON | FLAGS_EVENT_DATE | FLAGS_TEAM1):
			return weight
		if flags & (FLAGS_LEAGUE | FLAGS_EVENT_DATE | FLAGS_TEAM1) == (FLAGS_LEAGUE | FLAGS_EVENT_DATE | FLAGS_TEAM1):
			return weight
		if flags & (FLAGS_LEAGUE | FLAGS_SEASON | FLAGS_SUBSEASON | FLAGS_WEEK | FLAGS_TEAM1 | FLAGS_TEAM2 | FLAGS_GAME) == (FLAGS_LEAGUE | FLAGS_SEASON | FLAGS_SUBSEASON | FLAGS_WEEK | FLAGS_TEAM1 | FLAGS_TEAM2 | FLAGS_GAME):
			return weight
		if flags & (FLAGS_LEAGUE | FLAGS_SEASON | FLAGS_SUBSEASON | FLAGS_WEEK | FLAGS_TEAM1 | FLAGS_TEAM2) == (FLAGS_LEAGUE | FLAGS_SEASON | FLAGS_SUBSEASON | FLAGS_WEEK | FLAGS_TEAM1 | FLAGS_TEAM2):
			return weight
		if flags & (FLAGS_LEAGUE | FLAGS_SEASON | FLAGS_SUBSEASON | FLAGS_WEEK | FLAGS_TEAM1) == (FLAGS_LEAGUE | FLAGS_SEASON | FLAGS_SUBSEASON | FLAGS_WEEK | FLAGS_TEAM1):
			return weight


		return -1

	def results_sort_key(result):
		return result[0]

	def filter(results):
		filtered = []
		maxes = dict()	# dict<eventKey, (maxweight, howItMatched)>
		events = dict()	# dict<eventKey, event>

		for (weight, result, howItMatched) in results:
			for event in result:
				key = event.key
				if not key in events.keys():
					events.setdefault(key, event)
				if not key in maxes.keys():
					maxes.setdefault(key, (weight, howItMatched))
				else:
					maxweight = maxes[key][0]
					if weight > maxweight:
						maxes[key] = (weight, howItMatched)

		for key in maxes.keys():
			maxweight = maxes[key][0]
			event = events[key]
			filtered.append((maxweight, event, maxes[key][1]))

		filtered.sort(reverse=True, key=results_sort_key)
		return filtered

	molecules = []
	atoms = []
	molecules.append(construct_expression_fragment("sport", "sp", meta[METADATA_SPORT_KEY]))
	molecules.append(construct_expression_fragment("league", "lg", meta[METADATA_LEAGUE_KEY]))
	if meta.get(METADATA_SEASON_BEGIN_YEAR_KEY):
		atom = meta[METADATA_SEASON_BEGIN_YEAR_KEY]
		atoms.append("s:%s" % atom)
		molecules.append(construct_expression_fragment("season", "s", atom))
	if meta.get(METADATA_SUBSEASON_INDICATOR_KEY):
		atom = meta[METADATA_SUBSEASON_INDICATOR_KEY]
		atoms.append("ss:%s" % atom)
		molecules.append(construct_expression_fragment("subseason", "ss", atom))
	if meta.get(METADATA_PLAYOFF_ROUND_KEY):
		atom = meta[METADATA_PLAYOFF_ROUND_KEY]
		atoms.append("pr:%s" % atom)
		molecules.append(construct_expression_fragment("playoffround", "pr", atom))
	if meta.get(METADATA_WEEK_KEY):
		atom = meta[METADATA_WEEK_KEY]
		atoms.append("wk:%s" % atom)
		molecules.append(construct_expression_fragment("week", "wk", atom))
	if meta.get(METADATA_AIRDATE_KEY):
		atom = sched_compute_date_hash(meta[METADATA_AIRDATE_KEY])
		atoms.append("dt:%s" % atom)
		molecules.append(construct_expression_fragment("date", "dt", atom))
	if meta.get(METADATA_HOME_TEAM_KEY):
		atom = meta[METADATA_HOME_TEAM_KEY]
		atoms.append("tm:%s" % atom)
		molecules.append(construct_expression_fragment("team1", "tm", atom))
	if meta.get(METADATA_AWAY_TEAM_KEY):
		atom = meta[METADATA_AWAY_TEAM_KEY]
		atoms.append("tm:%s" % atom)
		molecules.append(construct_expression_fragment("team2", "tm", atom))
	if meta.get(METADATA_GAME_NUMBER_KEY):
		atom = meta[METADATA_GAME_NUMBER_KEY] # TODO: Convert to integer?
		atoms.append("g:%s" % atom)
		molecules.append(construct_expression_fragment("game", "g", atom))

	print("|".join(atoms))
	expr = "".join(molecules)

	for scanKey in event_scan.keys():
		m = re.search(expr, scanKey, re.IGNORECASE)
		if m:
			weight = compute_weight(m)
			if weight > WEIGHT_SPORT + WEIGHT_LEAGUE + WEIGHT_SEASON:
				results.append((weight, event_scan[scanKey], scanKey))

	return filter(results)











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
	downloadedJson = TheSportsDB.DownloadScheduleForLeagueAndSeason(league, season)
	
	if downloadedJson:
		try: sportsDbSchedule = json.loads(downloadedJson)
		except ValueError: pass

	if sportsDbSchedule and sportsDbSchedule["events"]:
		for schedEvent in sportsDbSchedule["events"]:
			homeTeamStripped = __strip_to_alphanumeric(deunicode(schedEvent["strHomeTeam"]))
			awayTeamStripped = __strip_to_alphanumeric(deunicode(schedEvent["strAwayTeam"]))
			homeTeamKey = Teams.cached_team_keys[league][homeTeamStripped]
			awayTeamKey = Teams.cached_team_keys[league][awayTeamStripped]
		
			date = None
			if schedEvent.get("dateEventLocal") and schedEvent.get("strTimeLocal"):
				date = ParseISO8601Date("%sT%s" % (schedEvent["dateEventLocal"], schedEvent["strTimeLocal"]))
				# Relative to East Coast
				date = date.replace(tzinfo=EasternTime).astimezone(tz=UTC)
			elif schedEvent.get("dateEvent") and schedEvent.get("strTime"):
				date = ParseISO8601Date("%sT%s" % (schedEvent["dateEvent"], schedEvent["strTime"]))
				## Zulu Time
				#date = date.replace(tzinfo=UTC)
				# Relative to East Coast
				date = date.replace(tzinfo=EasternTime).astimezone(tz=UTC)
			elif schedEvent.get("dateEvent") and not schedEvent.get("strTime"):
				date = ParseISO8601Date(schedEvent["dateEvent"])
			elif schedEvent.get("strTimestamp"):
				date = ParseISO8601Date(schedEvent["strTimestamp"])
				# Zulu Time
				date = date.replace(tzinfo=UTC)

			kwargs = {
				"sport": sport,
				"league": league,
				"season": season,
				"date": date,
				"TheSportsDBID": schedEvent["idEvent"],
				"title": schedEvent["strEvent"],
				"altTitle": schedEvent["strEventAlternate"],
				"description": normalize(schedEvent["strDescriptionEN"]),
				"homeTeam": homeTeamKey,
				"awayTeam": awayTeamKey,
				"network": deunicode(schedEvent["strTVStation"]),
				"poster": deunicode(schedEvent["strPoster"]),
				"fanArt": deunicode(schedEvent["strFanart"]),
				"thumbnail": deunicode(schedEvent["strThumb"]),
				"banner": deunicode(schedEvent["strBanner"]),
				"preview": deunicode(schedEvent["strVideo"])}



			event = ScheduleEvent(**kwargs)

			hash = sched_compute_hash(event)
			subhash = sched_compute_time_hash(event.date)
			#print("%s|%s" % (hash, subhash))
			if not hash in sched.keys():
				sched.setdefault(hash, {subhash:event})
			else:
				evdict = sched[hash]
				if (not subhash in evdict.keys()):
					sched[hash].setdefault(subhash, event)
				else:
					sched[hash][subhash].augment(**event.__dict__)


	# Augment/replace with data from SportsData.io
	downloadedJsons = SportsDataIO.__sports_data_io_download_schedule_for_league_and_season(league, season)
	for downloadedJson in downloadedJsons:
		if not downloadedJson: continue
		try: sportsDataIOSchedule = json.loads(downloadedJson)
		except ValueError: continue

		# If sportsdata.io returns an unauthorized message, log and bail
		if not isinstance(sportsDataIOSchedule, list) and "Code" in sportsDataIOSchedule.keys():
			print("%s: %s" % (sportsDataIOSchedule["Code"], sportsDataIOSchedule["Description"]))
		elif isinstance(sportsDataIOSchedule, list):
			for schedEvent in sportsDataIOSchedule:
				homeTeamKey = deunicode(schedEvent["HomeTeam"])
				awayTeamKey = deunicode(schedEvent["AwayTeam"])
				if awayTeamKey == "BYE":
					continue
				homeTeam = Teams.cached_teams[league][homeTeamKey]
				awayTeam = Teams.cached_teams[league][awayTeamKey]

				date = None
				if schedEvent.get("Date"):
					date = datetime.datetime.strptime(schedEvent["Date"], "%Y-%m-%dT%H:%M:%S")
					date = date.replace(tzinfo=EasternTime).astimezone(tz=UTC)
				elif schedEvent.get("DateTime"):
					date = datetime.datetime.strptime(schedEvent["DateTime"], "%Y-%m-%dT%H:%M:%S")
					date = date.replace(tzinfo=EasternTime).astimezone(tz=UTC)
				elif schedEvent.get("Day"):
					date = datetime.datetime.strptime(schedEvent["Day"], "%Y-%m-%dT%H:%M:%S")
					date = date.replace(tzinfo=UTC)
	
				gameID = None
				if schedEvent.get("GameKey"):
					gameID = deunicode(schedEvent["GameKey"])
				if schedEvent.get("GameID"):
					gameID = deunicode(schedEvent["GameID"])

				kwargs = {
					"sport": sport,
					"league": league,
					"season": season,
					"date": date,
					"week": schedEvent.get("Week"),
					"SportsDataIOID": gameID,
					"title": "%s vs %s" % (homeTeam.FullName, awayTeam.FullName),
					"altTitle": "%s @ %s" % (awayTeam.FullName, homeTeam.FullName),
					"homeTeam": homeTeamKey,
					"awayTeam": awayTeamKey,
					"network": deunicode(schedEvent.get("Channel"))}
				event = ScheduleEvent(**kwargs)

				hash = sched_compute_hash(event)
				subhash = sched_compute_time_hash(event.date)
				#print("%s|%s" % (hash, subhash))
				if not hash in sched.keys():
					sched.setdefault(hash, {subhash:event})
				else:
					evdict = sched[hash]
					if (not subhash in evdict.keys()):
						evdict.setdefault(subhash, event)
					else:
						evdict[subhash].augment(**event.__dict__)
	
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
			cacheContainer = CacheContainer.Deserialize(cachedJson, itemTransform=event_deserialization_item_transform)

			if not cacheContainer or cacheContainer.IsInvalid(CACHE_VERSION):
				events = __refresh_schedule_cache(sport, league, season)
			else:
				events = cacheContainer.Items

			if not jsonEvents:
				events = __refresh_schedule_cache(sport, league, season)
			else:
				cached_schedules.setdefault(sport, dict())
				cached_schedules[sport].setdefault(league, dict())
				cached_schedules[sport][league].setdefault(season, dict())
				schedule = dict()
				for event in events:
					hash = sched_compute_hash(event)
					subhash = sched_compute_time_hash(event.date)

					schedule.setdefault(hash, dict())
					schedule[hash].setdefault(subhash, event)
				cached_schedules[sport][league][season] = schedule
				__refresh_scan_dict(sport, league, season, schedule)
	return cached_schedules[sport][league][season]

def event_deserialization_item_transform(jsonEvents):
	events = []
	for jsonEvent in jsonEvents: events.append(ScheduleEvent(**jsonEvent))
	return events

def __refresh_schedule_cache(sport, league, season):
	print("Refreshing %s %s schedule cache ..." % (league, season))
	cached_schedules.setdefault(sport, dict())
	cached_schedules[sport].setdefault(league, dict())
	cached_schedules[sport][league].setdefault(season, dict())
	schedule = __download_all_schedule_data(sport, league, season)
	cached_schedules[sport][league][season] = schedule

	# Persist Cache
	jsonEvents = []
	for daysEvents in schedule.values():
		for event in daysEvents.values():
			jsonEvents.append(event)
	cacheContainer = CacheContainer(jsonEvents, CacheType="%s%sSCHEDULE" % (league, season), Version=CACHE_VERSION, Duration=CACHE_DURATION)
	__write_schedule_cache_file(sport, league, season, cacheContainer.Serialize())
	
	# Insert into the scan dict
	__refresh_scan_dict(sport, league, season, schedule)
	
	print("Done refreshing %s %s schedule cache." % (league, season))
	return jsonEvents


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
	print("Reading %s %s schedule from disk cache ..." % (league, season))
	return open(path, "r").read() # TODO: Invalidate cache

def __write_schedule_cache_file(sport, league, season, json):
	print("Writing %s %s schedules cache to disk ..." % (league, season))
	path = __get_schedule_cache_file_path(sport, league, season)
	dir = os.path.dirname(path)
	EnsureDirectory(dir)
	f = open(path, "w")
	f.write(json)
	f.close()

SCHEDULE_FILE_NAME = "%s-Schedule.json"
def __get_schedule_cache_file_path(sport, league, season):
	# TODO: Modify filename when non-seasonal sport, like Boxing
	path = os.path.join(GetDataPathForLeague(league), SCHEDULE_FILE_NAME) % season
	return path




def __refresh_scan_dict(sport, league, season, schedule):
	print("Computing %s %s scan hashes ..." % (league, season))
	event_scan.setdefault(sport, dict())
	event_scan[sport].setdefault(league, dict())
	event_scan[sport][league].setdefault(season, dict())
	event_scan[sport][league][season].clear()	# Or whatever

	for key in schedule.keys():	# dict<HASH, dict<HOUR, event>>.keys()
		events = schedule[key]
		keyPieces = key.split("|")
		# sport, league, season
		# date, home, away
		leagueKey = "lg:%s" % keyPieces[1]
		seasonKey = "s:%s" % keyPieces[2]
		dateKey = "dt:%s" % keyPieces[3]
		homeKey = "tm:%s" % keyPieces[4]
		awayKey = "tm:%s" % keyPieces[5]

		numberOfGames = len(events)
		gameNumber = 1
		for event in events.values():	# dict<HOUR, event>().values()
			possible_keys = []
			gameKey = "g:%s" % gameNumber
			weekKey = None
			if event.week:
				weekKey = "wk:%s" % event.week
			#elif sport in week_scheduled_sports
			#	weekKey = __get_week_from_season_and_date(sport, league, season, date)


			possible_keys.append("|".join([leagueKey, seasonKey, dateKey, homeKey, awayKey]))
			possible_keys.append("|".join([leagueKey, seasonKey, dateKey, awayKey, homeKey]))
			if weekKey:
				possible_keys.append("|".join([leagueKey, seasonKey, weekKey, dateKey, homeKey, awayKey]))
				possible_keys.append("|".join([leagueKey, seasonKey, weekKey, dateKey, awayKey, homeKey]))
				possible_keys.append("|".join([leagueKey, seasonKey, weekKey, homeKey, awayKey]))
				possible_keys.append("|".join([leagueKey, seasonKey, weekKey, awayKey, homeKey]))
			
			if numberOfGames > 1:	# Double-headers
				possible_keys.append("|".join([leagueKey, seasonKey, dateKey, homeKey, awayKey, gameKey]))
				possible_keys.append("|".join([leagueKey, seasonKey, dateKey, awayKey, homeKey, gameKey]))
				if weekKey:
					possible_keys.append("|".join([leagueKey, seasonKey, weekKey, dateKey, homeKey, awayKey, gameKey]))
					possible_keys.append("|".join([leagueKey, seasonKey, weekKey, dateKey, awayKey, homeKey, gameKey]))
					possible_keys.append("|".join([leagueKey, seasonKey, weekKey, homeKey, awayKey, gameKey]))
					possible_keys.append("|".join([leagueKey, seasonKey, weekKey, awayKey, homeKey, gameKey]))



			possible_keys.append("|".join([leagueKey, dateKey, homeKey, awayKey]))
			possible_keys.append("|".join([leagueKey, dateKey, awayKey, homeKey]))
			
			if numberOfGames > 1:	# Double-headers
				possible_keys.append("|".join([leagueKey, dateKey, homeKey, awayKey, gameKey]))
				possible_keys.append("|".join([leagueKey, dateKey, awayKey, homeKey, gameKey]))
	

			# Vagaries
			possible_keys.append("|".join([leagueKey, dateKey, homeKey]))
			possible_keys.append("|".join([leagueKey, dateKey, awayKey]))
			if weekKey:
				possible_keys.append("|".join([leagueKey, seasonKey, weekKey, homeKey]))
				possible_keys.append("|".join([leagueKey, seasonKey, weekKey, awayKey]))
			if numberOfGames > 1:	# Double-headers
				if weekKey:
					possible_keys.append("|".join([leagueKey, seasonKey, weekKey, homeKey]))
					possible_keys.append("|".join([leagueKey, seasonKey, weekKey, awayKey]))
				possible_keys.append("|".join([leagueKey, dateKey, homeKey, gameKey]))
				possible_keys.append("|".join([leagueKey, dateKey, awayKey, gameKey]))


			possible_keys = list(set(possible_keys))
			for scanKey in possible_keys:
				event_scan.setdefault(scanKey, [])
				event_scan[scanKey].append(event)

			gameNumber += 1


	print("Done computing %s %s scan hashes." % (league, season))

























def sched_compute_hash(event):
	molecules = []
	
	sport = sched_compute_sport_hash(event.sport) or ""
	molecules.append(sport)

	# TODO: Omit when taking on non-league sports, like Boxing
	league = sched_compute_league_hash(event.league) or ""
	molecules.append(league)

	# TODO: Omit when taking on non-seasonal sports, like Boxing
	season = sched_compute_league_hash(event.season) or ""
	molecules.append(season)

	subseason = sched_compute_subseason_hash(event.subseason) or ""
	molecules.append(subseason)

	playoffRound = sched_compute_playoff_round_hash(event.playoffround) or ""
	molecules.append(playoffRound)

	week = sched_compute_week_hash(event.week) or ""
	molecules.append(week)

	game = sched_compute_game_hash(event.game) or ""
	molecules.append(game)

	date = sched_compute_date_hash(event.date) or ""
	molecules.append(date)
	
	# TODO: Modify when taking on non-team sports, like Boxing
	home = sched_compute_team_hash(event.homeTeam) or ""
	away = sched_compute_team_hash(event.awayTeam) or ""
	molecules.append(home)
	molecules.append(away)

	if event.week: 	molecules.append(away)

	return "|".join(molecules)

def sched_compute_sport_hash(sport):
	if not sport:
		return None
	return sport.lower()

def sched_compute_league_hash(league):
	if not league:
		return None
	return league.lower()

def sched_compute_season_hash(season):
	if not season:
		return None

	s = ""
	if (isinstance(season, basestring)):
		s = season
		for expr in season_expressions:
			p = re.compile(expr, re.IGNORECASE)
			m = p.search(s)
			if m:
				return expandYear(m.group("season_begin_year")).lower()
	elif (isinstance(season, int)):
		s = str(season)
	
	return None

def sched_compute_week_hash(week):
	if week == None: return None
	if isinstance(week, int): week = str(week)
	return week.lower()

def sched_compute_subseason_hash(subseason):
	if subseason == None: return None
	if isinstance(subseason, int): subseason = str(subseason)
	return week.lower()

def sched_compute_playoff_round_hash(playoffRound):
	if playoffRound == None: return None
	if isinstance(playoffRound, int): playoffRound = str(playoffRound)
	return playoffRound.lower()

def sched_compute_game_hash(game):
	if not game: return None
	if isinstance(game, int): game = str(game)
	return game.lower()

def sched_compute_date_hash(eventDate):
	if not eventDate:
		return None

	if not isinstance(eventDate, (datetime.datetime, datetime.date)):
		return None

	if isinstance(eventDate, datetime.datetime):
		if eventDate.tzinfo != None:
			eventDate = eventDate.astimezone(tz=EasternTime)

	return eventDate.strftime("%Y%m%d")

def sched_compute_time_hash(eventDate):
	if not eventDate:
		return None

	if not isinstance(eventDate, (datetime.datetime, datetime.time)):
		return None

	if eventDate.tzinfo != None:
		eventDate = eventDate.astimezone(tz=EasternTime)

	return eventDate.strftime("%H")

def sched_compute_team_hash(abbrev):
	if not abbrev:
		return None
	return abbrev.lower()



