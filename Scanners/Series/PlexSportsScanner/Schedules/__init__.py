# Python framework
import sys, os, json, re
import datetime
from pprint import pprint

from Constants import *
from Hashes import *
from PathUtils import *
from PluginSupport import *
from Serialization import *
from StringUtils import *
from TimeZoneUtils import *
from ..Data.CacheContainer import *
import Teams
import TheSportsDB, SportsDataIO
from ScheduleEvent import *

CACHE_DURATION = 7
CACHE_VERSION = "2"

WEIGHT_SPORT = 1
WEIGHT_LEAGUE = 5
WEIGHT_SEASON = 12
WEIGHT_SUBSEASON = 6
WEIGHT_PLAYOFF_ROUND = 10
WEIGHT_WEEK = 4
WEIGHT_EVENT_DATE = 20
WEIGHT_EVENT_INDICATOR = 30
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
FLAGS_EVENT_INDICATOR = 128
FLAGS_GAME = 256
FLAGS_TEAM1 = 512
FLAGS_TEAM2 = 1024


cached_schedules = dict() # cached_schedules[sport][league][eventHash][subHash]

event_scan = dict()




def Find(meta):
	results = []

	sport = meta.get(METADATA_SPORT_KEY)
	league = meta.get(METADATA_LEAGUE_KEY)
	season = str(meta[METADATA_SEASON_BEGIN_YEAR_KEY]) if meta.get(METADATA_SEASON_BEGIN_YEAR_KEY) else meta.get(METADATA_SEASON_KEY)
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
	GetSchedule(sport, league, season)
	
	# Construct an expression
	def construct_expression_fragment(key, molecule, value):
		return r"(?P<%s>%s\:%s)(?:\||$)?" % (key, molecule, re.escape(str(value)))

	def compute_weight(m):
		if not m: return 0

		hasAnyMatchingGroups = False
		for g in m.groups():
			if not g: continue
			hasAnyMatchingGroups = True
			break
		if not hasAnyMatchingGroups: return 0


		weight = WEIGHT_SPORT + WEIGHT_LEAGUE
		flags = FLAGS_SPORT + FLAGS_LEAGUE
		gd = m.groupdict() 
		for key in gd:
			if key == "season" and m.group(key):
				weight += WEIGHT_SEASON
				flags += FLAGS_SEASON
			elif key == "subseason" and m.group(key):
				weight += WEIGHT_SUBSEASON
				flags += FLAGS_SUBSEASON
			elif key == "playoffround" and m.group(key):
				weight += WEIGHT_PLAYOFF_ROUND
				flags += FLAGS_PLAYOFF_ROUND
			elif key == "eventindicator" and m.group(key):
				weight += WEIGHT_EVENT_INDICATOR
				flags += FLAGS_EVENT_INDICATOR
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

		if flags & (FLAGS_EVENT_DATE | FLAGS_TEAM1 | FLAGS_TEAM2 | FLAGS_GAME) == (FLAGS_EVENT_DATE | FLAGS_TEAM1 | FLAGS_TEAM2 | FLAGS_GAME):
			return weight
		if flags & (FLAGS_EVENT_DATE | FLAGS_TEAM1 | FLAGS_TEAM2) == (FLAGS_EVENT_DATE | FLAGS_TEAM1 | FLAGS_TEAM2):
			return weight
		if flags & (FLAGS_EVENT_DATE | FLAGS_TEAM1) == (FLAGS_EVENT_DATE | FLAGS_TEAM1):
			return weight
		if flags & (FLAGS_SUBSEASON | FLAGS_WEEK | FLAGS_TEAM1 | FLAGS_TEAM2 | FLAGS_GAME) == (FLAGS_SUBSEASON | FLAGS_WEEK | FLAGS_TEAM1 | FLAGS_TEAM2 | FLAGS_GAME):
			return weight
		if flags & (FLAGS_SUBSEASON | FLAGS_WEEK | FLAGS_TEAM1 | FLAGS_TEAM2) == (FLAGS_SUBSEASON | FLAGS_WEEK | FLAGS_TEAM1 | FLAGS_TEAM2):
			return weight
		if flags & (FLAGS_SUBSEASON | FLAGS_WEEK | FLAGS_TEAM1) == (FLAGS_SUBSEASON | FLAGS_WEEK | FLAGS_TEAM1):
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
	#molecules.append(construct_expression_fragment("sport", "sp", meta[METADATA_SPORT_KEY]))
	#molecules.append(construct_expression_fragment("league", "lg", meta[METADATA_LEAGUE_KEY]))
	if meta.get(METADATA_SEASON_BEGIN_YEAR_KEY):
		atom = meta[METADATA_SEASON_BEGIN_YEAR_KEY]
		atoms.append("s:%s" % atom)
		molecules.append(construct_expression_fragment("season", "s", atom))
	if meta.get(METADATA_SUBSEASON_INDICATOR_KEY) != None:
		atom = meta[METADATA_SUBSEASON_INDICATOR_KEY]
		atoms.append("ss:%s" % atom)
		molecules.append(construct_expression_fragment("subseason", "ss", atom))
	if meta.get(METADATA_PLAYOFF_ROUND_KEY):
		atom = meta[METADATA_PLAYOFF_ROUND_KEY]
		atoms.append("pr:%s" % atom)
		molecules.append(construct_expression_fragment("playoffround", "pr", atom))
	if meta.get(METADATA_EVENT_INDICATOR_KEY) != None:
		atom = meta[METADATA_EVENT_INDICATOR_KEY]
		atoms.append("ei:%s" % atom)
		molecules.append(construct_expression_fragment("eventindicator", "ei", atom))
	if meta.get(METADATA_WEEK_KEY) != None:
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
		atoms.append("gm:%s" % atom)
		molecules.append(construct_expression_fragment("game", "gm", atom))

	repr = "|".join(atoms)
	print(repr)
	expr = "".join(molecules)

	scan_hashes = event_scan[sport][league][season]
	for augmentationKey in sorted(scan_hashes.keys()):
		for event in scan_hashes[augmentationKey]:
			scanKey = event.key
			m = re.search(expr, event.key, re.IGNORECASE)
			if m:
				weight = compute_weight(m)
				if weight <= 0: continue
				else:
					if weight > WEIGHT_SPORT + WEIGHT_LEAGUE + WEIGHT_SEASON:
						results.append((weight, scan_hashes[augmentationKey], scanKey))

	if results:
		return filter(results)
	else: return []











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

	if league == LEAGUE_MLB:
		pass # TODO: MLBAPI

	TheSportsDB.GetSchedule(sched, Teams.cached_team_keys[league], sport, league, season)
	SportsDataIO.GetSchedule(sched, teams, sport, league, season)
		
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



SCHEDULE_HASH_INDEX_SPORT = 0
SCHEDULE_HASH_INDEX_LEAGUE = 1
SCHEDULE_HASH_INDEX_SEASON = 2
SCHEDULE_HASH_INDEX_SUBSEASON = 3
SCHEDULE_HASH_INDEX_PLAYOFFROUND = 4
SCHEDULE_HASH_INDEX_WEEK = 5
SCHEDULE_HASH_INDEX_GAME = 6
SCHEDULE_HASH_INDEX_EVENT_INDICATOR = 7
SCHEDULE_HASH_INDEX_DATE = 8
SCHEDULE_HASH_INDEX_HOMETEAM = 9
SCHEDULE_HASH_INDEX_AWAYTEAM = 10


def __refresh_scan_dict(sport, league, season, schedule):
	print("Computing %s %s scan hashes ..." % (league, season))

	scan_hashes = None

	event_scan.setdefault(sport, dict())
	scan_hashes = event_scan[sport]

	if sport in supported_league_sports:
		event_scan[sport].setdefault(league, dict())
		scan_hashes = event_scan[sport][league]

		if league in supported_seasonal_leagues:
			event_scan[sport][league].setdefault(season, dict())
			scan_hashes = event_scan[sport][league][season]

			scan_hashes = event_scan[sport][league][season]
	
	scan_hashes.clear()	# Or whatever

	for augmentationKey in schedule.keys():	# dict<HASH, dict<HOUR, event>>.keys()
		events = schedule[augmentationKey]

		molecules = []

		for event in events.values():	# dict<HOUR, event>().values()
			keyPieces = event.key.split("|")
			atoms = []
			
			atom = "lg:%s" % keyPieces[SCHEDULE_HASH_INDEX_LEAGUE]
			atoms.append(atom)
			
			atom = "s:%s" % keyPieces[SCHEDULE_HASH_INDEX_SEASON]
			atoms.append(atom)
			
			if keyPieces[SCHEDULE_HASH_INDEX_SUBSEASON]:
				atom = "ss:%s" % keyPieces[SCHEDULE_HASH_INDEX_SEASON]
				atoms.append(atom)
			
			if keyPieces[SCHEDULE_HASH_INDEX_PLAYOFFROUND]:
				atom = "pr:%s" % keyPieces[SCHEDULE_HASH_INDEX_PLAYOFFROUND]
				atoms.append(atom)

			if keyPieces[SCHEDULE_HASH_INDEX_WEEK]:
				atom = "wk:%s" % keyPieces[SCHEDULE_HASH_INDEX_WEEK]
				atoms.append(atom)
			
			atom = "dt:%s" % keyPieces[SCHEDULE_HASH_INDEX_DATE]
			atoms.append(atom)
			
			atom = "tm:%s" % keyPieces[SCHEDULE_HASH_INDEX_HOMETEAM]
			atoms.append(atom)
			
			atom = "tm:%s" % keyPieces[SCHEDULE_HASH_INDEX_AWAYTEAM]
			atoms.append(atom)

			if keyPieces[SCHEDULE_HASH_INDEX_EVENT_INDICATOR]:
				atom = "ei:%s" % keyPieces[SCHEDULE_HASH_INDEX_EVENT_INDICATOR]
				atoms.append(atom)

			if keyPieces[SCHEDULE_HASH_INDEX_GAME]:
				atom = "gm:%s" % keyPieces[SCHEDULE_HASH_INDEX_GAME]
				atoms.append(atom)
			elif len(events) > 1:
				atom = "gm:%s" % (len(molecules)+1)
				atoms.append(atom)

			molecule = "|".join(atoms)
			molecules.append(molecule)

			possible_keys = list(set(molecules))
			for scanKey in possible_keys:
				scan_hashes.setdefault(scanKey, [])
				scan_hashes[scanKey].append(event)


		#events = schedule[key]
		#keyPieces = key.split("|")
		## sport, league, season
		## date, home, away
		#leagueKey = "lg:%s" % keyPieces[SCHEDULE_HASH_INDEX_LEAGUE]
		#seasonKey = "s:%s" % keyPieces[SCHEDULE_HASH_INDEX_SEASON]
		#dateKey = "dt:%s" % keyPieces[SCHEDULE_HASH_INDEX_DATE]
		#homeKey = "tm:%s" % keyPieces[SCHEDULE_HASH_INDEX_HOMETEAM]
		#awayKey = "tm:%s" % keyPieces[SCHEDULE_HASH_INDEX_AWAYTEAM]

		#numberOfGames = len(events)
		#gameNumber = keyPieces[SCHEDULE_HASH_INDEX_LEAGUE] of "1"
		#for event in events.values():	# dict<HOUR, event>().values()
		#	possible_keys = []
		#	gameKey = "gm:%s" % gameNumber
		#	weekKey = None
		#	if event.week:
		#		weekKey = "wk:%s" % event.week
		#	#elif sport in week_scheduled_sports
		#	#	weekKey = __get_week_from_season_and_date(sport, league, season, date)


		#	possible_keys.append("|".join([leagueKey, seasonKey, dateKey, homeKey, awayKey]))
		#	possible_keys.append("|".join([leagueKey, seasonKey, dateKey, awayKey, homeKey]))
		#	if weekKey:
		#		possible_keys.append("|".join([leagueKey, seasonKey, weekKey, dateKey, homeKey, awayKey]))
		#		possible_keys.append("|".join([leagueKey, seasonKey, weekKey, dateKey, awayKey, homeKey]))
		#		possible_keys.append("|".join([leagueKey, seasonKey, weekKey, homeKey, awayKey]))
		#		possible_keys.append("|".join([leagueKey, seasonKey, weekKey, awayKey, homeKey]))
			
		#	if numberOfGames > 1:	# Double-headers
		#		possible_keys.append("|".join([leagueKey, seasonKey, dateKey, homeKey, awayKey, gameKey]))
		#		possible_keys.append("|".join([leagueKey, seasonKey, dateKey, awayKey, homeKey, gameKey]))
		#		if weekKey:
		#			possible_keys.append("|".join([leagueKey, seasonKey, weekKey, dateKey, homeKey, awayKey, gameKey]))
		#			possible_keys.append("|".join([leagueKey, seasonKey, weekKey, dateKey, awayKey, homeKey, gameKey]))
		#			possible_keys.append("|".join([leagueKey, seasonKey, weekKey, homeKey, awayKey, gameKey]))
		#			possible_keys.append("|".join([leagueKey, seasonKey, weekKey, awayKey, homeKey, gameKey]))



		#	possible_keys.append("|".join([leagueKey, dateKey, homeKey, awayKey]))
		#	possible_keys.append("|".join([leagueKey, dateKey, awayKey, homeKey]))
			
		#	if numberOfGames > 1:	# Double-headers
		#		possible_keys.append("|".join([leagueKey, dateKey, homeKey, awayKey, gameKey]))
		#		possible_keys.append("|".join([leagueKey, dateKey, awayKey, homeKey, gameKey]))
	

		#	# Vagaries
		#	possible_keys.append("|".join([leagueKey, dateKey, homeKey]))
		#	possible_keys.append("|".join([leagueKey, dateKey, awayKey]))
		#	if weekKey:
		#		possible_keys.append("|".join([leagueKey, seasonKey, weekKey, homeKey]))
		#		possible_keys.append("|".join([leagueKey, seasonKey, weekKey, awayKey]))
		#	if numberOfGames > 1:	# Double-headers
		#		if weekKey:
		#			possible_keys.append("|".join([leagueKey, seasonKey, weekKey, homeKey]))
		#			possible_keys.append("|".join([leagueKey, seasonKey, weekKey, awayKey]))
		#		possible_keys.append("|".join([leagueKey, dateKey, homeKey, gameKey]))
		#		possible_keys.append("|".join([leagueKey, dateKey, awayKey, gameKey]))


		#	possible_keys = list(set(possible_keys))
		#	for scanKey in possible_keys:
		#		scan_hashes.setdefault(scanKey, [])
		#		scan_hashes[scanKey].append(event)

		#	gameNumber += 1


	print("Done computing %s %s scan hashes." % (league, season))

