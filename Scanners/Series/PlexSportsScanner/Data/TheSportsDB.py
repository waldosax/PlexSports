from Constants import *
from UserAgent import *
from Data.GetResultFromNetwork import *

#THE_SPORTS_DB_API_KEY = "1" # TODO: Read from settings file?
THE_SPORTS_DB_API_KEY = "8123456712556"
THE_SPORTS_DB_BASE_URL = "https://www.thesportsdb.com/api/v1/json/%s/"

THE_SPORTS_DB_GET_ALL_LEAGUES = "all_leagues.php"
THE_SPORTS_DB_GET_ALL_TEAMS_FOR_LEAGUE = "search_all_teams.php?l=%s" # (TheSportsDbLeagueName)
THE_SPORTS_DB_GET_SCHEDULE_FOR_SEASON = "eventsseason.php?id=%s&s=%s" # (TheSportsDbTeamId, Season)

the_sports_db_headers = {
	"User-Agent": USER_AGENT
}

sportsdb_team_ids = {
	LEAGUE_MLB: "4424",
	LEAGUE_NBA: "4387",
	LEAGUE_NFL: "4391",
	LEAGUE_NHL: "4388"
	}


def DownloadAllTeamsForLeague(league):
	if (league in known_leagues.keys() == False):
		return None # TODO: Throw
	print("Getting %s teams data from The SportsDB ..." % league)
	urlTemplate = THE_SPORTS_DB_BASE_URL + THE_SPORTS_DB_GET_ALL_TEAMS_FOR_LEAGUE
	return GetResultFromNetwork(
		urlTemplate % (THE_SPORTS_DB_API_KEY, league),
		the_sports_db_headers, True)

def DownloadScheduleForLeagueAndSeason(league, season):
	if (league in known_leagues.keys() == False):
		return None # TODO: Throw
	print("Getting %s, %s schedule data from The SportsDB ..." % (league, season))
	urlTemplate = THE_SPORTS_DB_BASE_URL + THE_SPORTS_DB_GET_SCHEDULE_FOR_SEASON
	return GetResultFromNetwork(
		urlTemplate % (THE_SPORTS_DB_API_KEY, sportsdb_team_ids[league], season),
		the_sports_db_headers, True)

