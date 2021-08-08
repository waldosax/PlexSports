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

THESPORTSDB_ROUND_QUARTERFINAL = 125
THESPORTSDB_ROUND_SEMIFINAL = 150
THESPORTSDB_ROUND_PLAYOFF = 160
THESPORTSDB_ROUND_PLAYOFF_SEMIFINAL = 170
THESPORTSDB_ROUND_PLAYOFF_FINAL = 180
THESPORTSDB_ROUND_FINAL = 200
THESPORTSDB_ROUND_PRESEASON = 500



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







def SupplementScheduleEvent(league, schedEvent, kwargs):
	# I wish thesportsdb were more comprehensive when it comes to playoff round/preseason
	if league == LEAGUE_MLB:
		if schedEvent.get("intRound") == THESPORTSDB_ROUND_FINAL:
			kwargs.setdefault("subseason", MLB_SUBSEASON_POSTSEASON)
			kwargs.setdefault("playoffround", MLB_PLAYOFF_ROUND_WORLD_SERIES)
	elif league == LEAGUE_NFL:
		if schedEvent.get("intRound") == THESPORTSDB_ROUND_FINAL:
			kwargs.setdefault("subseason", NFL_SUBSEASON_POSTSEASON)
			kwargs.setdefault("playoffround", NFL_PLAYOFF_ROUND_SUPERBOWL)
			kwargs.setdefault("eventindicator", NFL_EVENT_FLAG_SUPERBOWL)
