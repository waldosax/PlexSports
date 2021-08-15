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
import MLBAPI
import NHLAPI
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
	seasons = [season]

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
		season = str(airdate.year)
		seasons = [season]

	if league in year_boundary_leagues:
		seasons += [str(int(season)-1)]

	# Warm up cache(s) if not already
	for season in sorted(list(set(seasons))):
		if not season: continue
		GetSchedule(sport, league, season)
	

	def compute_weight(league, m):
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

		# Valid Vectors
		if are_flags_set(flags, FLAGS_EVENT_DATE | FLAGS_TEAM1 | FLAGS_TEAM2 | FLAGS_GAME):
			return weight
		if are_flags_set(flags, FLAGS_EVENT_DATE | FLAGS_TEAM1 | FLAGS_TEAM2):
			return weight
		if are_flags_set(flags, FLAGS_EVENT_DATE | FLAGS_TEAM1):
			return weight
		if are_flags_set(flags, FLAGS_SUBSEASON | FLAGS_WEEK | FLAGS_TEAM1 | FLAGS_TEAM2 | FLAGS_GAME):
			return weight
		if are_flags_set(flags, FLAGS_SUBSEASON | FLAGS_WEEK | FLAGS_TEAM1 | FLAGS_TEAM2):
			return weight
		if are_flags_set(flags, FLAGS_SUBSEASON | FLAGS_WEEK | FLAGS_TEAM1):
			return weight

		if are_flags_set(flags, FLAGS_SUBSEASON | FLAGS_PLAYOFF_ROUND | FLAGS_GAME):
			return weight
		if league == LEAGUE_NFL and are_flags_set(flags, FLAGS_SUBSEASON | FLAGS_PLAYOFF_ROUND):
			return weight

		if are_flags_set(flags, FLAGS_SUBSEASON | FLAGS_EVENT_INDICATOR):
			return weight
		if are_flags_set(flags, FLAGS_EVENT_INDICATOR):
			return weight


		return -1

	def are_flags_set(flags, query):
		return (flags & query) == query

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

	(repr, expr) = sched_compute_meta_scan_hash2(meta)
	print(repr)
	print(expr)

	scan_hashes = dict()
	for season in sorted(list(set(seasons)), reverse=True):
		if not season: continue
		if not event_scan: continue
		if not event_scan.get(sport): continue
		if not event_scan[sport].get(league): continue
		if not event_scan[sport][league].get(season): continue
		season_scan_hashes = event_scan[sport][league][season]
		for key in sorted(season_scan_hashes.keys()):
			scan_hashes.setdefault(key, season_scan_hashes[key])

	for scanKey in sorted(scan_hashes.keys(), reverse=True):
		#if indexOf(scanKey, "19931016") >= 0: print scanKey
		m = re.search(expr, scanKey, re.IGNORECASE)
		if m:


			weight = compute_weight(league, m)
			if weight <= 0: continue
			else:
				if weight > WEIGHT_SPORT + WEIGHT_LEAGUE + WEIGHT_SEASON:
					print(scanKey)
					results.append((weight, scan_hashes[scanKey], scanKey))

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
		MLBAPI.GetSchedule(sched, Teams.cached_team_keys[league], sport, league, season)
	elif league == LEAGUE_NHL:
		NHLAPI.GetSchedule(sched, Teams.cached_team_keys[league], sport, league, season)

	TheSportsDB.GetSchedule(sched, Teams.cached_team_keys[league], sport, league, season)
	SportsDataIO.GetSchedule(sched, teams, sport, league, season)
		
	return sched







def __get_schedule_from_cache(sport, league, season):
	if not sport in supported_sports:
		return None
	if not league in known_leagues.keys():
		return None

	if not __schedule_cache_has_schedule(sport, league, season):

		cached_schedules.setdefault(sport, dict())
		cached_schedules[sport].setdefault(league, dict())
		cached_schedules[sport][league].setdefault(season, dict())

		if not __schedule_cache_file_exists(sport, league, season):
			__refresh_schedule_cache(sport, league, season)
			pass
		else:

			events = []
			cachedJson = __read_schedule_cache_file(sport, league, season) #TODO: Try/Catch
			cacheContainer = CacheContainer.Deserialize(cachedJson, itemTransform=event_deserialization_item_transform)

			if not cacheContainer or cacheContainer.IsInvalid(CACHE_VERSION):
				events = __refresh_schedule_cache(sport, league, season)
				pass
			else:
				events = cacheContainer.Items

			if not events:
				events = __refresh_schedule_cache(sport, league, season)
				pass
			else:
				schedule = dict()
				for event in events:
					hash = sched_compute_augmentation_hash(event)
					subhash = sched_compute_time_hash(event.date)

					schedule.setdefault(hash, dict())
					schedule[hash].setdefault(subhash, event)
				cached_schedules[sport][league][season] = schedule
				__refresh_scan_dict(sport, league, season, schedule)
	return cached_schedules[sport][league][season]

def event_deserialization_item_transform(jsonEvents):
	events = []
	for jsonEvent in jsonEvents:
		deserialized = dict()
		for key in jsonEvent.keys():
			if key == "date": deserialized[key] = ParseISO8601Date(jsonEvent[key])
			else: deserialized[key] = jsonEvent[key]
		events.append(ScheduleEvent(**deserialized))
	return events

def __refresh_schedule_cache(sport, league, season):
	print("Refreshing %s %s schedule cache ..." % (league, season))
	cached_schedules.setdefault(sport, dict())
	cached_schedules[sport].setdefault(league, dict())
	cached_schedules[sport][league].setdefault(season, dict())
	schedule = __download_all_schedule_data(sport, league, season)
	cached_schedules[sport][league][season] = schedule

	def get_sortable_days_event_key(daysEvents):
		return get_sortable_event_key(sorted(daysEvents.values())[0])
	def get_sortable_event_key(event):
		return FormatISO8601Date(event.date)

	# Persist Cache
	jsonEvents = []
	for daysEvents in sorted(schedule.values(), key=get_sortable_days_event_key):
		for event in sorted(daysEvents.values(), key=get_sortable_event_key):
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

	for augmentationKey in schedule.keys():	# dict<AUGKEY, dict<HOUR, event>>.keys()
		events = schedule[augmentationKey]

		scanKeys = []

		for event in events.values():	# dict<HOUR, event>().values()
			for scanKey in sched_compute_scan_hashes(event):
				scanKeys.append(scanKey)

		possible_keys = list(set(scanKeys))
		for scanKey in possible_keys:
			scan_hashes.setdefault(scanKey, [])
			scan_hashes[scanKey].append(event)



	print("Done computing %s %s scan hashes." % (league, season))
