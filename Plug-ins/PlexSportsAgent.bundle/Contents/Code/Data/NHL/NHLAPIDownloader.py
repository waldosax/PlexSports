import json
import datetime
from dateutil.parser import parse

from Constants import *
from ..UserAgent import *
from ..GetResultFromNetwork import *

NHLAPI_BASE_URL = "http://statsapi.web.nhl.com/api/v1/"

NHLAPI_GET_ALL_TEAMS = "teams"
NHLAPI_GET_TEAMS_FOR_SEASON = "teams?season=%s%s" # (seasonbegin, seasonend)
NHLAPI_GET_TEAMS_HISTORY = "teams/history?fields=%s" # ([field1,field2])
NHLAPI_GET_FRANCHISES = "franchises"
NHLAPI_GET_FRANCHISE = "franchises/%s" # (franchiseId)
NHLAPI_GET_ALL_SEASONS = "seasons"
NHLAPI_GET_SEASON = "seasons/%s%s" # (seasonbegin, seasonend)
NHLAPI_GET_SCHEDULE = "schedule/games/?startDate=%s&endDate=%s" # (season)
NHLAPI_GET_GAME_CONTENT = "game/%s/content" # (gameId)

nhl_api_headers = {
	"User-Agent": USER_AGENT
}


def DownloadAllFranchiseInfo():
	print("Getting franchise current state from NHL API ...")
	urlTemplate = NHLAPI_BASE_URL + NHLAPI_GET_FRANCHISES
	return GetResultFromNetwork(
		urlTemplate,
		nhl_api_headers, cacheExtension=EXTENSION_JSON)

def DownloadAllTeams():
	print("Getting teams current state from NHL API ...")
	urlTemplate = NHLAPI_BASE_URL + NHLAPI_GET_ALL_TEAMS
	return GetResultFromNetwork(
		urlTemplate,
		nhl_api_headers, cacheExtension=EXTENSION_JSON)

def DownloadTeamsForSeason(season):
	print("Getting teams state for %s season from NHL API ..." % (season))
	(seasonBegin, seasonEnd) = __nhlapi_expand_season(season)
	urlTemplate = NHLAPI_BASE_URL + NHLAPI_GET_TEAMS_FOR_SEASON
	return GetResultFromNetwork(
		urlTemplate % (seasonBegin, seasonEnd),
		nhl_api_headers, cacheExtension=EXTENSION_JSON)

def DownloadTeamHistories(fields=None):
	print("Getting team histories from NHL API ...")
	urlTemplate = NHLAPI_BASE_URL + NHLAPI_GET_TEAMS_HISTORY
	return GetResultFromNetwork(
		urlTemplate % (",".join(fields) if fields else ""),
		nhl_api_headers, cacheExtension=EXTENSION_JSON)

def DownloadAllSeasons():
	print("Getting all seasons from NHL API ...")
	url = NHLAPI_BASE_URL + NHLAPI_GET_ALL_SEASONS
	return GetResultFromNetwork(
		url,
		nhl_api_headers, cacheExtension=EXTENSION_JSON)

def DownloadSeasonInfo(season):
	print("Getting %s season info from NHL API ..." % (season))
	(seasonBegin, seasonEnd) = __nhlapi_expand_season(season)
	urlTemplate = NHLAPI_BASE_URL + NHLAPI_GET_SEASON
	return GetResultFromNetwork(
		urlTemplate % (seasonBegin, seasonEnd),
		nhl_api_headers, cacheExtension=EXTENSION_JSON)

def DownloadScheduleForSeason(season):
	print("Getting schedule info for %s season from NHL API ..." % (season))

	shouldCache = True
	seasonInfoJson = DownloadSeasonInfo(season)
	seasons = json.loads(seasonInfoJson)

	def get_property(dct, keys):
		for key in keys:
			if dct.get(key): return dct[key]

	if len(seasons["seasons"]) == 0: return None
	seasonInfo = seasons["seasons"][0]
	startDate = get_property(seasonInfo, ["preSeasonStartDate", "regularSeasonStartDate"])
	endDate = get_property(seasonInfo, ["postSeasonEndDate", "seasonEndDate", "regularSeasonEndDate"])

	now = datetime.datetime.now()
	if int(season) >= now.year:
		shouldCache = False
	elif parse(endDate) > now:
		shouldCache = False

	if int(season) >= 1949 and int(season) <= 1965:
		# Back up the startDate by a week to try and catch the All-Star game for that season
		# https://en.wikipedia.org/wiki/NHL_All-Star_Game#Official_games
		startDate = (parse(startDate) + datetime.timedelta(days=-7)).strftime("%Y-%m-%d")
		pass

	return __downloadScheduleForDateRange(startDate, endDate, shouldCache)

def __downloadScheduleForDateRange(startDate, endDate, shouldCache=True):
	urlTemplate = NHLAPI_BASE_URL + NHLAPI_GET_SCHEDULE
	return GetResultFromNetwork(
		urlTemplate % (startDate, endDate),
		nhl_api_headers, cache=shouldCache, cacheExtension=EXTENSION_JSON)

def DownloadGameContentData(gameId):
	print("Getting game content from NHL API ...")
	urlTemplate = NHLAPI_BASE_URL + NHLAPI_GET_GAME_CONTENT
	return GetResultFromNetwork(
		urlTemplate % (gameId),
		nhl_api_headers, cacheExtension=EXTENSION_JSON)


def __nhlapi_expand_season(season):
	seasonBegin = season
	seasonEnd = season
	try: seasonEnd = str(int(season) + 1)
	except ValueError: pass
	return (seasonBegin, seasonEnd)