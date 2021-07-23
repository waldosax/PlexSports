from Constants import *
from UserAgent import *
from Data.GetResultFromNetwork import *

SPORTS_DATA_IO_MLB_API_KEY = "be605ffcf1b64c5696ef305e1bf74e2b" # TODO: Read from settings file?
SPORTS_DATA_IO_NBA_API_KEY = "435d4c60b0ba4a7fa79cd0bbbcf9e76d" # TODO: Read from settings file?
SPORTS_DATA_IO_NFL_API_KEY = "f6c469f009e04fcfb9f71d2d3b993f86" # TODO: Read from settings file?
SPORTS_DATA_IO_NHL_API_KEY = "e6b62fe4b3b041dcba7c51c41f6affe7" # TODO: Read from settings file?

SPORTS_DATA_IO_BASE_URL = "https://fly.sportsdata.io/v3/%s/" # (League)

SPORTS_DATA_IO_GET_ALL_TEAMS_FOR_LEAGUE = SPORTS_DATA_IO_BASE_URL + "scores/json/AllTeams?key=%s" # (League, ApiKey)

SPORTS_DATA_IO_SUBSCRIPTION_KEY_NAME = "Ocp-Apim-Subscription-Key"

sports_data_io_headers = {
    "User-Agent": USER_AGENT,
    SPORTS_DATA_IO_SUBSCRIPTION_KEY_NAME: "",
}

sports_data_io_api_keys = {
    LEAGUE_MLB: SPORTS_DATA_IO_MLB_API_KEY,
    LEAGUE_NBA: SPORTS_DATA_IO_NBA_API_KEY,
    LEAGUE_NFL: SPORTS_DATA_IO_NFL_API_KEY,
    LEAGUE_NHL: SPORTS_DATA_IO_NHL_API_KEY
}

def __sports_data_io_download_all_teams_for_league(league):
    if (league in known_leagues.keys() == False):
        return None # TODO: Throw
    key = sports_data_io_api_keys[league]
    headers = sports_data_io_headers.copy()
    headers[SPORTS_DATA_IO_SUBSCRIPTION_KEY_NAME] = key
    print("Getting %s teams data from SportsData.io ..." % league)
    return GetResultFromNetwork(SPORTS_DATA_IO_GET_ALL_TEAMS_FOR_LEAGUE % (league, sports_data_io_api_keys[league]), headers, True)