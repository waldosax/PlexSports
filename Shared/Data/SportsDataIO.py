import threading
from Constants import *
from UserAgent import *
from Data.GetResultFromNetwork import *

SPORTS_DATA_IO_MLB_API_KEY = "be605ffcf1b64c5696ef305e1bf74e2b" # TODO: Read from settings file?
SPORTS_DATA_IO_NBA_API_KEY = "435d4c60b0ba4a7fa79cd0bbbcf9e76d" # TODO: Read from settings file?
SPORTS_DATA_IO_NFL_API_KEY = "f6c469f009e04fcfb9f71d2d3b993f86" # TODO: Read from settings file?
SPORTS_DATA_IO_NHL_API_KEY = "e6b62fe4b3b041dcba7c51c41f6affe7" # TODO: Read from settings file?

SPORTS_DATA_IO_BASE_URL = "https://fly.sportsdata.io/v3/%s/" # (League)

SPORTS_DATA_IO_GET_ALL_TEAMS_FOR_LEAGUE = SPORTS_DATA_IO_BASE_URL + "scores/json/AllTeams?key=%s" # (League, ApiKey)
SPORTS_DATA_IO_GET_MLB_GAMES_FOR_SEASON = SPORTS_DATA_IO_BASE_URL + "scores/json/Games/%s?key=%s" # (Season, ApiKey)
SPORTS_DATA_IO_GET_NBA_GAMES_FOR_SEASON = SPORTS_DATA_IO_BASE_URL + "scores/json/Games/%s?key=%s" # (Season, ApiKey)
SPORTS_DATA_IO_GET_NFL_SCHEDULE_FOR_SEASON = SPORTS_DATA_IO_BASE_URL + "scores/json/Schedules/%s?key=%s" # (Season, ApiKey)
SPORTS_DATA_IO_GET_NHL_GAMES_FOR_SEASON = SPORTS_DATA_IO_BASE_URL + "scores/json/Games/%s?key=%s" # (Season, ApiKey)

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

sports_data_io_schedule_url_fragments = {
	LEAGUE_MLB: SPORTS_DATA_IO_GET_MLB_GAMES_FOR_SEASON,
	LEAGUE_NBA: SPORTS_DATA_IO_GET_NBA_GAMES_FOR_SEASON,
	LEAGUE_NFL: SPORTS_DATA_IO_GET_NFL_SCHEDULE_FOR_SEASON,
	LEAGUE_NHL: SPORTS_DATA_IO_GET_NHL_GAMES_FOR_SEASON
}

SPORTS_DATA_IO_SUBSEASON_PRESEASON = "PRE"
SPORTS_DATA_IO_SUBSEASON_REGULARSEASON = ""
SPORTS_DATA_IO_SUBSEASON_POSTSEASON = "POST"
SPORTS_DATA_IO_SUBSEASON_ALLSTAR = "STAR"

def __sports_data_io_download_all_teams_for_league(league):
	if (league in known_leagues.keys() == False):
		return None # TODO: Throw
	key = sports_data_io_api_keys[league]
	headers = sports_data_io_headers.copy()
	headers[SPORTS_DATA_IO_SUBSCRIPTION_KEY_NAME] = key
	print("Getting %s teams data from SportsData.io ..." % league)
	return GetResultFromNetwork(SPORTS_DATA_IO_GET_ALL_TEAMS_FOR_LEAGUE % (league, sports_data_io_api_keys[league]), headers, True)


def __sports_data_io_download_schedule_for_league_and_season(league, season, subseason=None):
	if (league in known_leagues.keys() == False):
		return None # TODO: Throw
	key = sports_data_io_api_keys[league]
	headers = sports_data_io_headers.copy()
	headers[SPORTS_DATA_IO_SUBSCRIPTION_KEY_NAME] = key
	allSubseasons = [SPORTS_DATA_IO_SUBSEASON_PRESEASON, SPORTS_DATA_IO_SUBSEASON_REGULARSEASON, SPORTS_DATA_IO_SUBSEASON_POSTSEASON, SPORTS_DATA_IO_SUBSEASON_ALLSTAR]
	subseasons = []
	if not subseason:
		subseasons = allSubseasons[0:]
	elif isinstance(list, subseason):
		for suffix in subseason:
			if suffix in allSubseasons:
				subseasons.append(suffix)
	elif isinstance(subseason, basestring):
		if subseason in allSubseasons:
			subseasons.append(subseason)

	if len(subseasons) == 0:
		subseasons.append(SPORTS_DATA_IO_SUBSEASON_REGULARSEASON)


	def get_and_append_data(suffix, results):
		print("Getting %s, %s%s schedule data from The SportsDB ..." % (league, season, suffix))
		json = GetResultFromNetwork(sports_data_io_schedule_url_fragments[league] % (league, str(season) + suffix, sports_data_io_api_keys[league]), headers, True)
		results.append (json)
		pass

	results = []
	threads = []
	for suffix in subseasons:
		t = threading.Thread(target=get_and_append_data, kwargs={"suffix": suffix, "results": results})
		threads.append(t)
		t.start()
		
	for t in threads:
		t.join()

	return results

SPORTS_DATA_IO_SEASON_TYPE_REGULAR_SEASON = 1
SPORTS_DATA_IO_SEASON_TYPE_PRESEASON = 2
SPORTS_DATA_IO_SEASON_TYPE_POSTSEASON = 3
SPORTS_DATA_IO_SEASON_TYPE_OFFSEASON = 4
SPORTS_DATA_IO_SEASON_TYPE_ALLSTAR = 5

def SupplementScheduleEvent(league, schedEvent, kwargs):
	if schedEvent.get("SeasonType"):
		if league == LEAGUE_MLB:
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_PRESEASON: kwargs["subseason"] = MLB_SUBSEASON_FLAG_PRESEASON
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_REGULAR_SEASON: kwargs["subseason"] = MLB_SUBSEASON_FLAG_REGULAR_SEASON
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_POSTSEASON:
				kwargs["subseason"] = MLB_SUBSEASON_FLAG_POSTSEASON
				# TODO: Identify Playoff Round/World Series
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_ALLSTAR: kwargs["eventindicator"] = MLB_EVENT_FLAG_ALL_STAR_GAME
		if league == LEAGUE_NBA:
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_PRESEASON: kwargs["subseason"] = NBA_SUBSEASON_FLAG_PRESEASON
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_REGULAR_SEASON: kwargs["subseason"] = NBA_SUBSEASON_FLAG_REGULAR_SEASON
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_POSTSEASON:
				kwargs["subseason"] = NBA_SUBSEASON_FLAG_POSTSEASON
				# TODO: Identify Playoff Round
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_ALLSTAR: kwargs["eventindicator"] = NBA_EVENT_FLAG_ALL_STAR_GAME
		if league == LEAGUE_NFL:
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_PRESEASON: kwargs["subseason"] = NFL_SUBSEASON_FLAG_PRESEASON
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_REGULAR_SEASON: kwargs["subseason"] = NFL_SUBSEASON_FLAG_REGULAR_SEASON
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_POSTSEASON:
				kwargs["subseason"] = NFL_SUBSEASON_FLAG_POSTSEASON
				# TODO: Identify Playoff Round/Superbowl
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_ALLSTAR: kwargs["eventindicator"] = NFL_EVENT_FLAG_PRO_BOWL
		if league == LEAGUE_NHL:
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_PRESEASON: kwargs["subseason"] = NHL_SUBSEASON_FLAG_PRESEASON
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_REGULAR_SEASON: kwargs["subseason"] = NHL_SUBSEASON_FLAG_REGULAR_SEASON
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_POSTSEASON:
				kwargs["subseason"] = NHL_SUBSEASON_FLAG_POSTSEASON
				# TODO: Identify Playoff Round/Stanley Cup
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_ALLSTAR: kwargs["eventindicator"] = NHL_EVENT_FLAG_ALL_STAR_GAME
