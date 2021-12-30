from Constants import *
from .UserAgent import *
from .GetResultFromNetwork import *


SCORES_AND_STATS_BASE_URL = "https://www.scoresandstats.com/"

SCORES_AND_STATS_RECAPS_MLB = "recaps/baseball/mlb/"
SCORES_AND_STATS_RECAPS_NBA = "recaps/basketball/nba/"
SCORES_AND_STATS_RECAPS_NFL = "recaps/football/nfl/"
SCORES_AND_STATS_RECAPS_NHL = "recaps/hockey/nhl/"


scores_and_stats_headers = {
	"User-Agent": USER_AGENT,
	"Referer": SCORES_AND_STATS_BASE_URL
}




def DownloadLeagueRecapsForCurrentCalendarYear(sport, league, season):

	fragment = None
	if league == LEAGUE_MLB:
		fragment = SCORES_AND_STATS_RECAPS_MLB
	if league == LEAGUE_NBA:
		fragment = SCORES_AND_STATS_RECAPS_NBA
	if league == LEAGUE_NFL:
		fragment = SCORES_AND_STATS_RECAPS_NFL
	if league == LEAGUE_NHL:
		fragment = SCORES_AND_STATS_RECAPS_NHL

	url = SCORES_AND_STATS_BASE_URL + fragment
	return DownloadPage(sport, league, season, url)


def DownloadPage(sport, league, season, url):
	return GetResultFromNetwork(
		url,
		scores_and_stats_headers, cacheExtension=EXTENSION_HTML)

