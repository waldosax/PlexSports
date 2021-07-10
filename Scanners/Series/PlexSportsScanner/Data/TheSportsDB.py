from Constants import *
from Data.GetResultFromNetwork import *

THE_SPORTS_DB_API_KEY = "1" # TODO: Read from settings file?
THE_SPORTS_DB_BASE_URL = "https://www.thesportsdb.com/api/v1/json/%s/"

THE_SPORTS_DB_GET_ALL_LEAGUES = "all_leagues.php"
THE_SPORTS_DB_GET_ALL_TEAMS_FOR_LEAGUE = "search_all_teams.php?l=%s" # (TheSportsDbLeagueName)

the_sports_db_headers = {
    "User-Agent": USER_AGENT
}



def __the_sports_db_download_all_teams_for_league(league: str):
    if (league in known_leagues.keys() == False):
        return None # TODO: Throw
    print("Getting %s teams data from The SportsDB ..." % league)
    urlTemplate = THE_SPORTS_DB_BASE_URL + THE_SPORTS_DB_GET_ALL_TEAMS_FOR_LEAGUE
    return GetResultFromNetwork(
        urlTemplate % (THE_SPORTS_DB_API_KEY, league),
        the_sports_db_headers, True)