from Constants import *
from ..UserAgent import *
from ..GetResultFromNetwork import *

# The "NBA API" is actually an amalgam of public-facing APIs, querying the same data from the NBA

NBA_SPAAPI_BASE_URL = "https://neulionms-a.akamaihd.net/nbad/player/v1/"
NBA_STATSAPI_BASE_URL = "https://stats.nba.com/stats/"
NBA_DATAAPI_BASE_URL = "https://data.nba.com/data/"


NBA_SPA_CONFIG_ENDPOINT = "nba/site_spa/config.json"

NBA_FRANCHISE_HISTORY_ENDPOINT = "franchisehistory?LeagueID=00"
NBA_TEAMINFO_COMMON_ENDPOINT = "teaminfocommon?LeagueID=00&TeamID=%s" # TeamID
NBA_TEAM_DETAILS_ENDPOINT = "teamdetails?TeamID=%s" # TeamID
NBA_COMMON_PLAYOFF_SERIES_ENDPOINT = "commonplayoffseries?LeagueID=00&Season=%s" # Season

NBA_TEAM_SCHEDULE_ENDPOINT = "v2015/json/mobile_teams/nba/%s/teams/%s_schedule.json" # (Season, slug)
NBA_SCHEDULE_ENDPOINT = "v2015/json/mobile_teams/nba/%s/league/00_full_schedule.json" # Season
NBA_SCHEDULE_SUPPLEMENT_ENDPOINT = "10s/prod/v1/%s/schedule.json" # Season

nba_api_headers = {
	"User-Agent": USER_AGENT,
	"Referer": "https://www.nba.com/"
}


def DownloadSPAConfig():
	print("Getting SPA configuration from NBA API ...")
	url = NBA_SPAAPI_BASE_URL + NBA_SPA_CONFIG_ENDPOINT
	return GetResultFromNetwork(
		url,
		nba_api_headers, cacheExtension=EXTENSION_JSON)

def DownloadAllFranchiseInfo():
	print("Getting franchise history from NBA API ...")
	url = NBA_STATSAPI_BASE_URL + NBA_FRANCHISE_HISTORY_ENDPOINT
	return GetResultFromNetwork(
		url,
		nba_api_headers, cacheExtension=EXTENSION_JSON)

def DownloadScheduleForSeason(season):
	print("Getting %s schedule from NBA API ..." % season)
	url = (NBA_DATAAPI_BASE_URL + NBA_SCHEDULE_ENDPOINT) % season
	return GetResultFromNetwork(
		url,
		nba_api_headers, cacheExtension=EXTENSION_JSON)

def DownloadScheduleSupplementForSeason(season):
	print("Getting %s schedule supplement from NBA API ..." % season)
	url = (NBA_DATAAPI_BASE_URL + NBA_SCHEDULE_SUPPLEMENT_ENDPOINT) % season
	return GetResultFromNetwork(
		url,
		nba_api_headers, cacheExtension=EXTENSION_JSON)




#def DownloadPlayoffSeriesInfoForSeason(season):
#	print("Getting %s playoff series info from NBA API ..." % season)
#	url = (NBA_STATSAPI_BASE_URL + NBA_COMMON_PLAYOFF_SERIES_ENDPOINT) % season
#	return GetResultFromNetwork(
#		url,
#		nba_api_headers, cacheExtension=EXTENSION_JSON)
