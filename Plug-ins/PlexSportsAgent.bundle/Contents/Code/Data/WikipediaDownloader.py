from Constants import *
from .UserAgent import *
from .GetResultFromNetwork import *


WIKIPEDIA_BASE_URL = "https://en.wikipedia.org/wiki/"

WIKIPEDIA_MLB_ALL_STAR_GAME_PATH = "%s_Major_League_Baseball_All-Star_Game" # (calendarYear)
WIKIPEDIA_MLB_HOME_RUN_DERBY_PATH = "%s_Major_League_Baseball_Home_Run_Derby" # (calendarYear)
WIKIPEDIA_NBA_ALL_STAR_GAME_PATH = "%s_NBA_All-Star_Game" # (calendarYear)
WIKIPEDIA_NFL_PRO_BOWL_PATH = "%s_Pro_Bowl" # (calendarYear)
WIKIPEDIA_NHL_ALL_STAR_GAME_PATH = "%s_National_Hockey_League_All-Star_Game" # (nth)


wikipedia_headers = {
	"User-Agent": USER_AGENT
}


wikipedia_nhl_allstar_season_map = {
	1948, 1 # TODO: Map this out fully
	}


def DownloadAllStarGameSupplement(sport, league, season):

	if league == LEAGUE_MLB:
		return __downloadMLBAllStarGameSupplement(sport, league, season)
	if league == LEAGUE_NBA:
		return __downloadNBAAllStarGameSupplement(sport, league, season)
	if league == LEAGUE_NFL:
		return __downloadNFLProBowlSupplement(sport, league, season)
	if league == LEAGUE_NHL:
		return __downloadNHLAllStarGameSupplement(sport, league, season)

	pass


def __downloadMLBAllStarGameSupplement(sport, league, season):
	calendarYear = int(season)

	urlTemplate = WIKIPEDIA_BASE_URL + WIKIPEDIA_MLB_ALL_STAR_GAME_PATH
	return GetResultFromNetwork(
		urlTemplate % (calendarYear),
		wikipedia_headers, cacheExtension=EXTENSION_HTML)
	pass

def DownloadMLBHomeRunDerbySupplement(sport, league, season):
	calendarYear = int(season)

	urlTemplate = WIKIPEDIA_BASE_URL + WIKIPEDIA_MLB_HOME_RUN_DERBY_PATH
	return GetResultFromNetwork(
		urlTemplate % (calendarYear),
		wikipedia_headers, cacheExtension=EXTENSION_HTML)
	pass

def __downloadNBAAllStarGameSupplement(sport, league, season):
	calendarYear = int(season) + 1

	urlTemplate = WIKIPEDIA_BASE_URL + WIKIPEDIA_NBA_ALL_STAR_GAME_PATH
	return GetResultFromNetwork(
		urlTemplate % (calendarYear),
		wikipedia_headers, cacheExtension=EXTENSION_HTML)
	pass

def __downloadNFLProBowlSupplement(sport, league, season):
	calendarYear = int(season) + 1

	urlTemplate = WIKIPEDIA_BASE_URL + WIKIPEDIA_NFL_PRO_BOWL_PATH
	return GetResultFromNetwork(
		urlTemplate % (calendarYear),
		wikipedia_headers, cacheExtension=EXTENSION_HTML)
	pass

def __downloadNHLAllStarGameSupplement(sport, league, season):
	if int(season) not in wikipedia_nhl_allstar_season_map.keys():
		return None # TODO: Leave message
		pass

	inst = wikipedia_nhl_allstar_season_map[int(season)]
	suffix = "th"
	if inst % 10 == 1 and inst // 10 != 1: suffix = "st"
	if inst % 10 == 2 and inst // 10 != 1: suffix = "nd"
	if inst % 10 == 3 and inst // 10 != 1: suffix = "rd"
	nth = "%s%s" % (inst, suffix)

	urlTemplate = WIKIPEDIA_BASE_URL + WIKIPEDIA_NHL_ALL_STAR_GAME_PATH
	return GetResultFromNetwork(
		urlTemplate % (nth),
		wikipedia_headers, cacheExtension=EXTENSION_HTML)
	pass
