import json
import threading

from Constants import *
from StringUtils import *
from UserAgent import *
from Data.GetResultFromNetwork import *

#THE_SPORTS_DB_API_KEY = "2" # TODO: Read from settings file?
THE_SPORTS_DB_API_KEY = "8123456712556"
THE_SPORTS_DB_BASE_URL = "https://www.thesportsdb.com/api/v1/json/%s/"

THE_SPORTS_DB_GET_ALL_LEAGUES = "all_leagues.php"
THE_SPORTS_DB_GET_ALL_TEAMS_FOR_LEAGUE = "search_all_teams.php?l=%s" # (TheSportsDbLeagueName)
THE_SPORTS_DB_GET_ALL_SEASONS = "search_all_seasons.php?id=%s" # (TheSportsDbLeagueId)
THE_SPORTS_DB_GET_SCHEDULE_FOR_SEASON = "eventsseason.php?id=%s&s=%s" # (TheSportsDbLeagueId, Season)

the_sports_db_headers = {
	"User-Agent": USER_AGENT
}

sportsdb_league_ids = {
	LEAGUE_MLB: "4424",
	LEAGUE_NBA: "4387",
	LEAGUE_NFL: "4391",
	LEAGUE_NHL: "4380"
	}

sportsdb_seasonIdentifiers = dict()


def DownloadAllTeamsForLeague(league):
	if (league in known_leagues.keys() == False):
		return None # TODO: Throw
	print("Getting %s teams data from The SportsDB ..." % league)
	urlTemplate = THE_SPORTS_DB_BASE_URL + THE_SPORTS_DB_GET_ALL_TEAMS_FOR_LEAGUE
	return GetResultFromNetwork(
		urlTemplate % (THE_SPORTS_DB_API_KEY, league),
		the_sports_db_headers, True, cacheExtension=EXTENSION_JSON)



def DownloadAllSeasons(league):
	if (league in known_leagues.keys() == False):
		return None # TODO: Throw
	print("Getting %s season data from The SportsDB ..." % league)
	urlTemplate = THE_SPORTS_DB_BASE_URL + THE_SPORTS_DB_GET_ALL_SEASONS
	return GetResultFromNetwork(
		urlTemplate % (THE_SPORTS_DB_API_KEY, sportsdb_league_ids[league]),
		the_sports_db_headers, True, cacheExtension=EXTENSION_JSON)

def __getSeasonIdentifiers(league, season):
	leagueId = sportsdb_league_ids[league]
	sznIdentifiers = []
	allSznIdentifiers = dict()
	if sportsdb_seasonIdentifiers.get(leagueId):
		allSznIdentifiers = sportsdb_seasonIdentifiers[leagueId]

	if not allSznIdentifiers:
		seasonJson = DownloadAllSeasons(league)
		apiResponse = json.loads(seasonJson)
		for apiSzn in apiResponse["seasons"]:
			identifier = apiSzn["strSeason"]
			indexOfDash = indexOf(identifier, "-")
			sznBeginYear = identifier[:indexOfDash] if indexOfDash >= 0 else identifier
			allSznIdentifiers.setdefault(deunicode(sznBeginYear), [])
			allSznIdentifiers[deunicode(sznBeginYear)].append(deunicode(identifier))
		sportsdb_seasonIdentifiers[leagueId] = allSznIdentifiers

	return allSznIdentifiers.get(season)


def DownloadScheduleForLeagueAndSeason(league, season):
	if (league in known_leagues.keys() == False):
		return None # TODO: Throw
	urlTemplate = THE_SPORTS_DB_BASE_URL + THE_SPORTS_DB_GET_SCHEDULE_FOR_SEASON


	def get_and_append_data(szn, results):
		print("Getting %s %s schedule data from The SportsDB ..." % (league, szn))
		downloadedJson = GetResultFromNetwork(
			urlTemplate % (THE_SPORTS_DB_API_KEY, sportsdb_league_ids[league], szn),
			the_sports_db_headers, True, cacheExtension=EXTENSION_JSON)
		results.append (downloadedJson)
		pass

	results = []
	threads = []
	sznIdentifiers = __getSeasonIdentifiers(league, str(season))
	if not sznIdentifiers: return None
	for szn in sznIdentifiers:
		t = threading.Thread(target=get_and_append_data, kwargs={"szn": szn, "results": results})
		threads.append(t)
		t.start()
		
	for t in threads:
		t.join()

	return results
