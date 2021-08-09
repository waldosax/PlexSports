import json
import datetime
from dateutil.parser import parse

from Constants import *
from ..UserAgent import *
from ..GetResultFromNetwork import *

MLBAPI_BASE_URL = "http://statsapi.mlb.com/api/v1/"

MLBAPI_GET_ALL_TEAMS = "teams?sportId=1"
MLBAPI_GET_TEAMS_FOR_SEASON = "teams?sportId=1&season=%s" # (season)
MLBAPI_GET_TEAMS_HISTORY = "teams/history?teamIds=%s" # ([TeamID, TeamID])
MLBAPI_GET_LEAGUES = "league?sportId=1&seasons=%s" # ([season,season, season])
MLBAPI_GET_ALL_SEASONS = "seasons/all?sportId=1"
MLBAPI_GET_SEASON = "seasons/%s?sportId=1" # (season)
MLBAPI_GET_SCHEDULE = "schedule/games/?sportId=1&startDate=%s&endDate=%s" # (season)

mlb_api_headers = {
	"User-Agent": USER_AGENT
}


def DownloadAllTeams():
	print("Getting teams current state from MLB API ...")
	urlTemplate = MLBAPI_BASE_URL + MLBAPI_GET_ALL_TEAMS
	return GetResultFromNetwork(
		urlTemplate,
		mlb_api_headers)

def DownloadTeamsForSeason(season):
	print("Getting teams state for %s season from MLB API ..." % (season))
	urlTemplate = MLBAPI_BASE_URL + MLBAPI_GET_TEAMS_FOR_SEASON
	return GetResultFromNetwork(
		urlTemplate % (season),
		mlb_api_headers)

def DownloadTeamHistories(teamIds):
	print("Getting team histories from MLB API ...")
	urlTemplate = MLBAPI_BASE_URL + MLBAPI_GET_TEAMS_FOR_SEASON
	return GetResultFromNetwork(
		urlTemplate % (",".join(teamIds)),
		mlb_api_headers)

def DownloadSeasonInfo(season):
	print("Getting %s season info from MLB API ..." % (season))
	urlTemplate = MLBAPI_BASE_URL + MLBAPI_GET_SEASON
	return GetResultFromNetwork(
		urlTemplate % (season),
		mlb_api_headers)

def DownloadScheduleForSeason(season):
	print("Getting schedule info for %s season from MLB API ..." % (season))

	shouldCache = True
	seasonInfoJson = DownloadSeasonInfo(season)
	seasonInfo = json.loads(seasonInfoJson)

	startDate = seasonInfo["seasons"][0]["preSeasonStartDate"] if seasonInfo["seasons"][0].get("preSeasonStartDate") else seasonInfo["seasons"][0].get("regularSeasonStartDate")
	endDate = seasonInfo["seasons"][0]["postSeasonEndDate"] if seasonInfo["seasons"][0].get("postSeasonEndDate") else seasonInfo["seasons"][0].get("regularSeasonEndDate")

	now = datetime.datetime.now()
	if int(season) >= now.year:
		shouldCache = False
	elif parse(endDate) > now:
		shouldCache = False


	urlTemplate = MLBAPI_BASE_URL + MLBAPI_GET_SCHEDULE
	return GetResultFromNetwork(
		urlTemplate % (startDate, endDate),
		mlb_api_headers, cache=shouldCache)

