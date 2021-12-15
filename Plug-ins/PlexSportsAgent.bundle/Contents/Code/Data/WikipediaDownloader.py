from Constants import *
from .UserAgent import *
from .GetResultFromNetwork import *


WIKIPEDIA_BASE_URL = "https://en.wikipedia.org/wiki/"

WIKIPEDIA_MLB_ALL_STAR_GAME_PATH = "%s_Major_League_Baseball_All-Star_Game" # (calendarYear)
WIKIPEDIA_MLB_HOME_RUN_DERBY_PATH = "%s_Major_League_Baseball_Home_Run_Derby" # (calendarYear)
WIKIPEDIA_NBA_ALL_STAR_GAME_PATH = "%s_NBA_All-Star_Game" # (calendarYear)
WIKIPEDIA_NFL_PRO_BOWL_PATH = "%s_Pro_Bowl" # (calendarYear)
WIKIPEDIA_NHL_ALL_STAR_GAME_PATH = "%s_National_Hockey_League_All-Star_Game" # (nth)
WIKIPEDIA_NHL_WINTER_CLASSIC_PATH = "%s_NHL_Winter_Classic" # (calendarYear)


wikipedia_headers = {
	"User-Agent": USER_AGENT
}


wikipedia_nhl_allstar_season_map = {
	1947: 1,
	1948: 2,
	1949: 3,
	1950: 4,
	1951: 5,
	1952: 6,
	1953: 7,
	1954: 8,
	1955: 9,
	1956: 10,
	1957: 11,
	1958: 12,
	1959: 13,
	1960: 14,
	1961: 15,
	1962: 16,
	1963: 17,
	1964: 18,
	1965: 19,
	1966: 20,
	1967: 21,
	1968: 22,
	1969: 23,
	1970: 24,
	1971: 25,
	1972: 26,
	1973: 27,
	1974: 28,
	1975: 29,
	1976: 30,
	1977: 31,
	1979: 32,
	1980: 33,
	1981: 34,
	1982: 35,
	1983: 36,
	1984: 37,
	1985: 38,
	1987: 39,
	1988: 40,
	1989: 41,
	1990: 42,
	1991: 43,
	1992: 44,
	1993: 45,
	1995: 46,
	1996: 47,
	1997: 48,
	1998: 49,
	1999: 50,
	2000: 51,
	2001: 52,
	2002: 53,
	2003: 54,
	2006: 55,
	2007: 56,
	2008: 57,
	2010: 58,
	2011: 59,
	2014: 60,
	2015: 61,
	2016: 62,
	2017: 63,
	2018: 64,
	2019: 65,
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

	nth = season
	key = int(season)
	if key < 1947:
		return None
	if key in wikipedia_nhl_allstar_season_map.keys():
		inst = wikipedia_nhl_allstar_season_map[key]
		suffix = "th"
		if inst % 10 == 1 and inst // 10 != 1: suffix = "st"
		if inst % 10 == 2 and inst // 10 != 1: suffix = "nd"
		if inst % 10 == 3 and inst // 10 != 1: suffix = "rd"
		nth = "%s%s" % (inst, suffix)
	else:
		nth = key + 1


	urlTemplate = WIKIPEDIA_BASE_URL + WIKIPEDIA_NHL_ALL_STAR_GAME_PATH
	return GetResultFromNetwork(
		urlTemplate % (nth),
		wikipedia_headers, cacheExtension=EXTENSION_HTML)
	pass

def DownloadNHLWinterClassicSupplement(sport, league, season):
	calendarYear = int(season) + 1

	urlTemplate = WIKIPEDIA_BASE_URL + WIKIPEDIA_NHL_WINTER_CLASSIC_PATH
	return GetResultFromNetwork(
		urlTemplate % (calendarYear),
		wikipedia_headers, cacheExtension=EXTENSION_HTML)
	pass
