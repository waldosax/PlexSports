import datetime
from dateutil.parser import parse

from Constants import *
from ..UserAgent import *
from ..GetResultFromNetwork import *

PFR_BASE_URL = "http://www.pro-football-reference.com"
PFR_CDN_DEFAULT_BASE_URL = "https://d2p3bygnnzw9w3.cloudfront.net"
PFR_CDN_DEFAULT_URL = PFR_CDN_DEFAULT_BASE_URL = "/req/202108041"
PFR_SEASONS_INDEX = "/years/"
PFR_SEASON_PAGE = "/years/%s/"
PFR_SCHEDULE_PAGE = "/years/%s/games.htm"
PFR_TEAMS_INDEX = "/teams/"
PFR_TEAM_INDEX = "/teams/%s/"
PFR_SEASON_TEAM_PAGE = "/teams/%s/%s.htm"

PFR_LOGO_BASE_PATH = "/tlogo/pfr/"
PFR_LOGO_PATH = "%s%s.png" # (teamId, ("-" + season) if season else "")

pfr_api_headers = {
	"User-Agent": USER_AGENT
}

def GetTeamUrl(teamName, teamId, season):
	urlTemplate = "%s%s" % (PFR_BASE_URL, PFR_SEASON_TEAM_PAGE if season else PFR_TEAM_INDEX)
	if season: return urlTemplate % (teamId, season)
	return urlTemplate % (teamId)

def GetTeamLogoUrl(teamName, teamId, season, cdnUrl=PFR_CDN_DEFAULT_URL):
	if not cdnUrl: cdnUrl = PFR_CDN_DEFAULT_URL
	urlTemplate = "%s%s%s" % (cdnUrl, PFR_LOGO_BASE_PATH, PFR_LOGO_PATH)
	return urlTemplate % (teamId, ("-" + season if season else ""))

def DownloadSeasonsIndexPage():
	print("Getting all seasons/leagues from pro-football-reference.com ...")
	url = PFR_BASE_URL + PFR_SEASONS_INDEX
	return GetResultFromNetwork(
		url,
		pfr_api_headers, cacheExtension=EXTENSION_HTML)

def DownloadSeasonPage(season):
	print("Getting all season information for %s season from pro-football-reference.com ..." % season)
	urlTemplate = PFR_BASE_URL + PFR_SEASON_PAGE
	return GetResultFromNetwork(
		urlTemplate % (season),
		pfr_api_headers, cacheExtension=EXTENSION_HTML)

def DownloadSchedulePage(season):
	print("Getting schedule for %s season from pro-football-reference.com ..." % season)
	urlTemplate = PFR_BASE_URL + PFR_SCHEDULE_PAGE
	return GetResultFromNetwork(
		urlTemplate % (season),
		pfr_api_headers, cacheExtension=EXTENSION_HTML)

def DownloadTeamsIndexPage():
	print("Getting all franchises/teams from pro-football-reference.com ...")
	url = PFR_BASE_URL + PFR_TEAMS_INDEX
	return GetResultFromNetwork(
		url,
		pfr_api_headers, cacheExtension=EXTENSION_HTML)

def DownloadTeamPage(teamName, teamId):
	print("Getting team info for the %s from pro-football-reference.com ..." % (teamName))
	urlTemplate = PFR_BASE_URL + PFR_TEAM_INDEX
	return GetResultFromNetwork(
		urlTemplate % (teamId),
		pfr_api_headers, cacheExtension=EXTENSION_HTML)

def DownloadSeasonTeamPage(season, teamName, teamId):
	print("Getting team info for the %s %s from pro-football-reference.com ..." % (season, teamName))
	urlTemplate = PFR_BASE_URL + PFR_SEASON_TEAM_PAGE
	return GetResultFromNetwork(
		urlTemplate % (season, teamId),
		pfr_api_headers, cacheExtension=EXTENSION_HTML)
