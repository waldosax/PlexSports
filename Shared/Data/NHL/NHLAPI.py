import json
import datetime
from dateutil.parser import parse

from Constants import *
from ..UserAgent import *
from ..GetResultFromNetwork import *

NHLAPI_BASE_URL = "http://statsapi.web.nhl.com/api/v1/"

NHLAPI_GET_ALL_TEAMS = "teams?sportId=1"
NHLAPI_GET_TEAMS_FOR_SEASON = "teams?sportId=1&season=%s%s" # (seasonbegin, seasonend)
NHLAPI_GET_TEAMS_HISTORY = "teams/history"
NHLAPI_GET_FRANCHISES = "teams/franchises"
NHLAPI_GET_FRANCHISE = "teams/franchises/%s" # (franchiseId)
NHLAPI_GET_ALL_SEASONS = "seasons?sportId=1"
NHLAPI_GET_SEASON = "seasons/%s%s?sportId=1" # (seasonbegin, seasonend)
NHLAPI_GET_SCHEDULE = "schedule/games/?sportId=1&startDate=%s&endDate=%s" # (season)
NHLAPI_GET_GAME_CONTENT = "game/%s/content" # (gameId)

nhl_api_headers = {
	"User-Agent": USER_AGENT
}


def DownloadAllTeams():
	print("Getting teams current state from NHL API ...")
	urlTemplate = NHLAPI_BASE_URL + NHLAPI_GET_ALL_TEAMS
	return GetResultFromNetwork(
		urlTemplate,
		nhl_api_headers)

def DownloadTeamsForSeason(season):
	print("Getting teams state for %s season from NHL API ..." % (season))
	(seasonBegin, seasonEnd) = __nhlapi_expand_season(season)
	urlTemplate = NHLAPI_BASE_URL + NHLAPI_GET_TEAMS_FOR_SEASON
	return GetResultFromNetwork(
		urlTemplate % (seasonBegin, seasonEnd),
		nhl_api_headers)

def DownloadTeamHistories(teamIds):
	print("Getting team histories from NHL API ...")
	urlTemplate = NHLAPI_BASE_URL + NHLAPI_GET_TEAMS_FOR_SEASON
	return GetResultFromNetwork(
		urlTemplate % (",".join(teamIds)),
		nhl_api_headers)

def DownloadSeasonInfo(season):
	print("Getting %s season info from NHL API ..." % (season))
	(seasonBegin, seasonEnd) = __nhlapi_expand_season(season)
	urlTemplate = NHLAPI_BASE_URL + NHLAPI_GET_SEASON
	return GetResultFromNetwork(
		urlTemplate % (seasonBegin, seasonEnd),
		nhl_api_headers)

def DownloadScheduleForSeason(season):
	print("Getting schedule info for %s season from NHL API ..." % (season))

	shouldCache = True
	seasonInfoJson = DownloadSeasonInfo(season)
	seasons = json.loads(seasonInfoJson)

	def get_property(dct, keys):
		for key in keys:
			if dct.get(key): return dct[key]

	seasonInfo = seasons["seasons"][0]
	startDate = get_property(seasonInfo, ["preSeasonStartDate", "regularSeasonStartDate"])
	endDate = get_property(seasonInfo, ["postSeasonEndDate", "seasonEndDate", "regularSeasonEndDate"])

	now = datetime.datetime.now()
	if int(season) >= now.year:
		shouldCache = False
	elif parse(endDate) > now:
		shouldCache = False


	urlTemplate = NHLAPI_BASE_URL + NHLAPI_GET_SCHEDULE
	return GetResultFromNetwork(
		urlTemplate % (startDate, endDate),
		nhl_api_headers, cache=shouldCache)

def DownloadGameContentData(gameId):
	print("Getting game content from NHL API ...")
	urlTemplate = NHLAPI_BASE_URL + NHLAPI_GET_GAME_CONTENT
	return GetResultFromNetwork(
		urlTemplate % (gameId),
		nhl_api_headers)


def __nhlapi_expand_season(season):
	seasonBegin = season
	seasonEnd = season
	try: seasonEnd = str(int(season) + 1)
	except ValueError: pass
	return (seasonBegin, seasonEnd)