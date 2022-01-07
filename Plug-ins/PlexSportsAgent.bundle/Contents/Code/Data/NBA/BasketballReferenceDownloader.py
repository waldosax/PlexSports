import datetime
from dateutil.parser import parse

from Constants import *
from ..UserAgent import *
from ..GetResultFromNetwork import *

BR_BASE_URL = "http://www.basketball-reference.com"
BR_CDN_DEFAULT_BASE_URL = "https://d2p3bygnnzw9w3.cloudfront.net"
BR_CDN_DEFAULT_URL = BR_CDN_DEFAULT_BASE_URL = "/req/202108041"

BR_SEASONS_INDEX = "/leagues/"
BR_SEASON_PAGE = "/leagues/%s_%s.html" # (league, season+1)
BR_SCHEDULE_PAGE = "/leagues/%s_%s_games%s.html" # (league, season+1, (("-" + subdivision) if subdivision else ""))
BR_PLAYOFFS_PAGE = "/playoffs/%s_%s.html" # (league, season+1)


BR_TEAMS_INDEX = "/teams/"
BR_SEASON_TEAM_PAGE = "/teams/%s/%s.html" # (abbrev, season+1)

BR_LOGO_BASE_PATH = "/tlogo/pfr/"
BR_LOGO_PATH = "%s%s.png" # (teamId, ("-" + season) if season else "")

br_api_headers = {
	"User-Agent": USER_AGENT
}

def GetTeamUrl(teamName, teamId, season):
	urlTemplate = "%s%s" % (BR_BASE_URL, BR_SEASON_TEAM_PAGE)
	if season: return urlTemplate % (teamId, season)
	return urlTemplate % (teamId)

def GetTeamLogoUrl(teamName, teamId, season, cdnUrl=BR_CDN_DEFAULT_URL):
	if not cdnUrl: cdnUrl = BR_CDN_DEFAULT_URL
	urlTemplate = "%s%s%s" % (cdnUrl, BR_LOGO_BASE_PATH, BR_LOGO_PATH)
	return urlTemplate % (teamId, ("-" + season if season else ""))




def DownloadSeasonsIndex():
	print("Getting all league/season information from basketball-reference.com ...")
	urlTemplate = BR_BASE_URL + BR_SEASONS_INDEX
	return GetResultFromNetwork(
		urlTemplate,
		br_api_headers, cacheExtension=EXTENSION_HTML)

def DownloadSeasonPage(league, season):
	print("Getting all %s season information for %s season from basketball-reference.com ..." % (league, season))
	szn = int(season) + 1
	urlTemplate = BR_BASE_URL + BR_SEASON_PAGE
	return GetResultFromNetwork(
		urlTemplate % (league, szn),
		br_api_headers, cacheExtension=EXTENSION_HTML)

def DownloadSchedulePage(league, season, subdivision=None):
	print("Getting %s schedule for %s%s season from basketball-reference.com ..." % (league, subdivision[0].upper() + subdivision[1:] + " " if subdivision else "", season))
	szn = int(season) + 1
	urlTemplate = BR_BASE_URL + BR_SCHEDULE_PAGE
	return GetResultFromNetwork(
		urlTemplate % (league, szn, ("-" + subdivision if subdivision else "")),
		br_api_headers, cacheExtension=EXTENSION_HTML)

def DownloadPlayoffsPage(league, season):
	print("Getting %s playoff schedule for %s season from basketball-reference.com ..." % (league, season))
	szn = int(season) + 1
	urlTemplate = BR_BASE_URL + BR_PLAYOFFS_PAGE
	return GetResultFromNetwork(
		urlTemplate % (league, szn),
		br_api_headers, cacheExtension=EXTENSION_HTML)




#def DownloadTeamsIndexPage():
#	print("Getting all franchises/teams from basketball-reference.com ...")
#	url = BR_BASE_URL + BR_TEAMS_INDEX
#	return GetResultFromNetwork(
#		url,
#		br_api_headers, cacheExtension=EXTENSION_HTML)

#def DownloadSeasonTeamPage(season, teamName, teamId):
#	print("Getting team info for the %s %s from basketball-reference.com ..." % (season, teamName))
#	urlTemplate = BR_BASE_URL + BR_SEASON_TEAM_PAGE
#	return GetResultFromNetwork(
#		urlTemplate % (season, teamId),
#		br_api_headers, cacheExtension=EXTENSION_HTML)
