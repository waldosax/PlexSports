import json
import datetime
import threading
import Queue 

from Constants import *
from UserAgent import *
from GetResultFromNetwork import *

ESPNAPI_BASE_URL = "https://site.api.espn.com/apis/site/v2/"
ESPNAPI_LEAGUE_FILTER = "sports/%s/%s/" # (sport.lower(), league.lower())
ESPNAPI_GET_ACTIVE_TEAMS = "teams"
ESPNAPI_GET_SCHEDULE = "scoreboard?dates=%s" # (season)

espn_api_headers = {
	"User-Agent": USER_AGENT
}


def DownloadAllTeamsForLeague(league):
	if not league in known_leagues.keys(): return None # TODO: Throw
	print("Getting %s teams current state from ESPN API ..." % league)
	(leagueName, sport) = known_leagues[league]
	urlTemplate = ESPNAPI_BASE_URL + ESPNAPI_LEAGUE_FILTER + ESPNAPI_GET_ACTIVE_TEAMS
	return GetResultFromNetwork(
		urlTemplate % (sport.lower(), league.lower()),
		espn_api_headers, cacheExtension=EXTENSION_JSON)

# Maybe thread this, but it's only 2 small requests
def DownloadCalendarForLeagueAndSeason(league, season, isWhitelist = False):
	if not league in known_leagues.keys(): return None # TODO: Throw
	print("Getting %s calendar for %s season from ESPN API ..." % (league, season))
	(leagueName, sport) = known_leagues[league]
	urlTemplate = ESPNAPI_BASE_URL + ESPNAPI_LEAGUE_FILTER + ESPNAPI_GET_SCHEDULE + "%s"
	return GetResultFromNetwork(
		urlTemplate % (sport.lower(), league.lower(), ("%s0000" % season), ("&calendarType=whitelist" if isWhitelist == True else "")),
		espn_api_headers, cacheExtension=EXTENSION_JSON)


def DownloadScheduleForLeagueAndDate(league, date):
	if isinstance(date, datetime.datetime): date = date.date()
	if not league in known_leagues.keys(): return None # TODO: Throw
	print("Getting %s schedule info for %s from ESPN API ..." % (league, date.strftime("%m/%d/%Y")))
	(leagueName, sport) = known_leagues[league]
	urlTemplate = ESPNAPI_BASE_URL + ESPNAPI_LEAGUE_FILTER + ESPNAPI_GET_SCHEDULE

	shouldUseCache = True
	if date >= datetime.datetime.utcnow().date(): shouldUseCache = False

	return GetResultFromNetwork(
		urlTemplate % (sport.lower(), league.lower(), date.strftime("%Y%m%d")),
		espn_api_headers, shouldUseCache, cacheExtension=EXTENSION_JSON)






