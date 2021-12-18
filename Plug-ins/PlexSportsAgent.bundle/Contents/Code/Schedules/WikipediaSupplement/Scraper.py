
import re, os, sys
import json
from datetime import datetime, date, time
from dateutil.relativedelta import relativedelta
from Constants import *
from PathUtils import *
from PluginSupport import *
from Serialization import *
from ...Data.CacheContainer import *

import MLB
import NBA
import NFL
import NHL


CACHE_VERSION = "0"
CACHE_DURATION = 365

WIKIPEDIA_SUPPLEMENT_FILENAME = "%s-wikipedia.%s.supplement.json" # type
WIKIPEDIA_SUPPLEMENT_TYPE_ALL_STAR_GAME = "all-star-game"
WIKIPEDIA_SUPPLEMENT_TYPE_PRO_BOWL = "pro-bowl"



def ScrapeAllStarGame(sport, league, season, download=False):
	if not download:
		return __get_supplement_from_cache(sport, league, season)
		
	return __download_all_supplement_data(sport, league, season)





def __download_all_supplement_data(sport, league, season):
	if league == LEAGUE_MLB:
		return MLB.Scraper.ScrapeAllStarGame(season)
	if league == LEAGUE_NBA:
		return NBA.Scraper.ScrapeAllStarGame(season)
	if league == LEAGUE_NFL:
		return NFL.Scraper.ScrapeProBowl(season)
	if league == LEAGUE_NHL:
		return NHL.Scraper.ScrapeAllStarGame(season)
	pass




def __get_supplement_from_cache(sport, league, season):
	if not sport in supported_sports:
		return None
	if not league in known_leagues.keys():
		return None

	supplement = dict()

	if not __supplement_cache_file_exists(sport, league, season):
		__refresh_supplement_cache(sport, league, season)
		pass
	else:

		items = []
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

		if items: supplement = items[0]

		if supplement:
			for s in supplement.values():
				if "date" in s.keys() and isinstance(s["date"], basestring):
					s["date"] = ParseISO8601Date(s["date"])

	return supplement




def __supplement_deserialization_item_transform(jsonItems):
	if not jsonItems: return jsonItems

	items = []
	for jsonItem in jsonItems:
		deserialized = dict()
		for key in jsonItem.keys():
			if key.isnumeric():
				ind = int(key)
				deserialized.setdefault(ind, jsonItem[key])
			else:
				deserialized[key] = jsonItem[key]
		items.append(deserialized)
	return items

def __refresh_supplement_cache(sport, league, season):
	print("Refreshing %s %s all-star game supplement cache ..." % (league, season))
	
	supplement = __download_all_supplement_data(sport, league, season)

	# Persist
	jsonEvents = [supplement]
	if len(supplement) > 0:
		cacheContainer = CacheContainer(jsonEvents, CacheType="WIKIPEDIA%s%sALLSTARSUPPLEMENT" % (league, season), Version=CACHE_VERSION, Duration=CACHE_DURATION)
		__write_supplement_cache_file(sport, league, season, cacheContainer.Serialize())
	
	print("Done refreshing %s %s all-star game supplement cache." % (league, season))
	return jsonEvents


def __supplement_cache_file_exists(sport, league, season):
	path = __get_supplement_cache_file_path(sport, league, season)
	return os.path.exists(path)

def __read_supplement_cache_file(sport, league, season):
	path = __get_supplement_cache_file_path(sport, league, season)
	print("Reading %s %s all-star game supplement from disk cache ..." % (league, season))
	return open(path, "r").read() # TODO: Invalidate cache

def __write_supplement_cache_file(sport, league, season, json):
	print("Writing %s %s all-star game supplement cache to disk ..." % (league, season))
	path = __get_supplement_cache_file_path(sport, league, season)
	dir = os.path.dirname(path)
	EnsureDirectory(dir)
	f = open(path, "w")
	f.write(json)
	f.close()


def __get_supplement_cache_file_path(sport, league, season):
	supplementType = WIKIPEDIA_SUPPLEMENT_TYPE_ALL_STAR_GAME
	if league == LEAGUE_NFL: supplementType = WIKIPEDIA_SUPPLEMENT_TYPE_PRO_BOWL
	fileName = WIKIPEDIA_SUPPLEMENT_FILENAME % (season, supplementType)
	path = os.path.join(GetDataPathForLeague(league), fileName)
	return path
