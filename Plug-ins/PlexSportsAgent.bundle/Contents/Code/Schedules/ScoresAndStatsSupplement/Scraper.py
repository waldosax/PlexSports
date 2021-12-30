import re, os, sys
import json
from datetime import datetime, date, time
from dateutil.relativedelta import relativedelta
from Constants import *
from PathUtils import *
from PluginSupport import *
from Serialization import *
from ...Data.CacheContainer import *

import RecapProcessor

CACHE_VERSION = "0"
CACHE_DURATION = 35

SCORES_AND_STATS_SUPPLEMENT_FILENAME = "%s-scores-and-stats.recaps.supplement.json"



def ScrapeRecaps(sport, league, season, download=False):
	if not download:
		return __get_supplement_from_cache(sport, league, season)
		
	return __download_all_supplement_data(sport, league, season)





def __download_all_supplement_data(sport, league, season):
	return RecapProcessor.ProcessRecaps(sport, league, season)




def __get_supplement_from_cache(sport, league, season):
	if not sport in supported_sports:
		return None
	if not league in known_leagues.keys():
		return None

	items = []
	if not __supplement_cache_file_exists(sport, league, season):
		items = __refresh_supplement_cache(sport, league, season)
	else:

		cachedJson = __read_supplement_cache_file(sport, league, season) #TODO: Try/Catch
		cacheContainer = CacheContainer.Deserialize(cachedJson, itemTransform=__supplement_deserialization_item_transform)

		if not cacheContainer or cacheContainer.IsInvalid(CACHE_VERSION):
			items = __refresh_supplement_cache(sport, league, season)
			pass
		else:
			items = cacheContainer.Items

		if not items:
			items = __refresh_supplement_cache(sport, league, season)
			pass

	return items




def __supplement_deserialization_item_transform(jsonItems):
	events = []
	for jsonEvent in jsonEvents:
		deserialized = dict()
		for key in jsonEvent.keys():
			if key == "date": deserialized[key] = ParseISO8601Date(jsonEvent[key])
			else: deserialized[key] = jsonEvent[key]
		events.append(deserialized)
	return events

def __refresh_supplement_cache(sport, league, season):
	print("Refreshing %s recap supplement cache ..." % (league))
	
	supplement = __download_all_supplement_data(sport, league, season)

	# Persist
	jsonEvents = supplement
	if jsonEvents and len(jsonEvents) > 0:
		cacheContainer = CacheContainer(jsonEvents, CacheType="SCORESANDSTATS%sRECAPSUPPLEMENT" % (league), Version=CACHE_VERSION, Duration=CACHE_DURATION)
		__write_supplement_cache_file(sport, league, season, cacheContainer.Serialize())
	
	print("Done refreshing %s recap supplement cache." % (league))
	return jsonEvents


def __supplement_cache_file_exists(sport, league, season):
	path = __get_supplement_cache_file_path(sport, league, season)
	return os.path.exists(path)

def __read_supplement_cache_file(sport, league, season):
	path = __get_supplement_cache_file_path(sport, league, season)
	print("Reading %s recap supplement from disk cache ..." % (league))
	return open(path, "r").read() # TODO: Invalidate cache

def __write_supplement_cache_file(sport, league, season, json):
	print("Writing %s recap supplement cache to disk ..." % (league))
	path = __get_supplement_cache_file_path(sport, league, season)
	dir = os.path.dirname(path)
	EnsureDirectory(dir)
	f = open(path, "w")
	f.write(json)
	f.close()


def __get_supplement_cache_file_path(sport, league, season):
	fileName = SCORES_AND_STATS_SUPPLEMENT_FILENAME % (season)
	path = os.path.join(GetDataPathForLeague(league), fileName)
	return path
