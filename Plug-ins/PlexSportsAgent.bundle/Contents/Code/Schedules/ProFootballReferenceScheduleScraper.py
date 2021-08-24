import re, os, sys
import json
from datetime import datetime, date, time
from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup
import bs4
from pprint import pprint
import threading, Queue

from Constants import *
from TimeZoneUtils import *
from PathUtils import *
from PluginSupport import *
import RomanNumerals
from Serialization import *
from Data.NFL.ProFootballReferenceDownloader import *



EXPORT_NFL_SCHEDULE_FILENAME = "pro-football-reference.Schedule-%s.json"
NFL_SUPERBOWL_1_YEAR = 1966

pfr_year_schedule_selectors = {	# /years/2020/games.htm
	"game-table": "table#games",
	"game-row": "tbody tr",
	"week-number": "th[data-stat='week_num']",
	"dow": "td[data-stat='game_day_of_week']",
	"game-date": "td[data-stat='game_date']",
	"game-time": "td[data-stat='gametime']",
	"winner": "td[data-stat='winner'] a",
	"@": "td[data-stat='game_location']",
	"loser": "td[data-stat='loser'] a",
	"away-team": "td[data-stat='visitor_team'] a",
	"home-team": "td[data-stat='home_team'] a",
	"box-score": "td[data-stat='boxscore_word']",
	"game-link": "a"
	}

pfr_teams_footer_selectors = {
	"footer-menu": "div#footer_general div#site_menu",
	"footer-menu-items": "ul li"
}


pfr_cached_schedules = dict() # [league][year][href:|subseasons: ... [subseason, ...]][week][alias:|href:] ... [{date:datetime.date|homeTeam:|awayTeam:|time:time|alias:}, event, ...]




def ScrapeScheduleForSeason(season):
	return __scrape_schedule(season)


def __parse_conference_and_division(s):
	conference = None
	division = None

	if s:
		s = s.strip()
		if s[:3].upper() in ["AFC", "NFC"]: # TODO: Pull in NFL constants in a way that isnt confusing. Might need to invert some modules
			conference = s[:3]
			s = s[3:].lstrip()
		if s[-8:].upper() == "DIVISION":
			division = s[:-8].strip()
		else:
			division = s.strip()

	return (conference, division)


def __correct_superbowl(s):
	"""Superbowl is one word, dammit."""
	if not s: return s
	return s.replace("Super Bowl", "Superbowl").replace("SuperBowl", "Superbowl").rstrip(": ")


def __get_subseason_name(subseason):
	if subseason == -1: return "Preseason"
	if subseason == 1: return "Playoffs"
	return "Regular Season"


def __extract_team_abbrev_from_team_url(teamLink):
	parts = teamLink.split("/")
	return parts[-2].upper()



def __scrape_schedule(year, download=False):
	schedule = dict()

	if download == False: # Nab from cache
		schedule = __scrape_schedule_from_cache(year)

	else: # Download and scrape from Website
		schedule = __process_nfl_season(year)

	return schedule


def __process_nfl_season(year):
	yearDict = __process_nfl_schedule_page(year)
	#for subseason in yearDist.get("subseasons"):
	#	for week in yearDist["subseasons"][subseason].keys():
	#		for event in yearDist["subseasons"][subseason][week]["events"].values():
	#			if not event.get("time") and int(year or 0) > 1969:
	#				__process_nfl_game_page(event)

	return yearDict

def __process_nfl_schedule_page(year):
	selectors = pfr_year_schedule_selectors
	markup = DownloadSchedulePage(year)
	if not markup: return None
	soup = BeautifulSoup(markup, "html5lib")

	yearDict = dict()
	yearDict.setdefault("subseasons", dict())
	allTeams = dict()
	teamsLookup = dict()
	augmentedWithConferenceAndDivision = False

	gameTables = soup.select(selectors["game-table"])
	if gameTables:
		gameTable = gameTables[0]
		gameRows = gameTable.select(selectors["game-row"])
		for gameRow in gameRows:
			if gameRow.attrs.get("class") and "thead" in gameRow.attrs["class"]: continue
			subseason = 0
			weekNumber = None
			eventindicator = None
			dow = None
			gameDate = None
			gameTime = None
			winner = None
			loser = None
			teams = dict()
			vs = None
			gameHref = None
			id = None

			boxScoreNode = gameRow.select(selectors["box-score"])[0]
			boxScoreLinks = boxScoreNode.select("a")
			if boxScoreLinks:
				boxScoreLink = boxScoreLinks[0]
				gameHref = boxScoreLink.attrs["href"]
				id = gameHref.split("/")[-1].split(".")[0]

			gameDateNodes = gameRow.select(selectors["game-date"])
			if gameDateNodes:
				gameDateNode = gameDateNodes[0]
				if gameDateNode.text == "Playoffs": continue
				gameDate = datetime.datetime.strptime(gameDateNode.text, "%Y-%m-%d")
			else:
				gameDateNode = boxScoreNode
				offsetYear = year
				temp = datetime.datetime.strptime("%s, %s" % (gameDateNode.text, offsetYear), "%B %d, %Y")
				if temp.month < 8: temp += relativedelta(years=1)
				gameDate = temp

			weekNumberNode = gameRow.select(selectors["week-number"])[0]
			weekNumberText = weekNumberNode.text
			if weekNumberText[:3].upper() == "PRE":
				subseason = -1
				if weekNumberText[3:] == "0":
					eventindicator = NFL_EVENT_FLAG_HALL_OF_FAME
				else:
					week = int(weekNumberText[3:])
			elif weekNumberText == "WildCard":
				subseason = 1
				week = 1
			elif weekNumberText == "Division":
				subseason = 1
				week = 2
			elif weekNumberText in  ["ConfChamp", "Champ"]:
				subseason = 1
				week = 3
			elif weekNumberText == "SuperBowl":
				subseason = 1
				week = 4
			else:
				week = int(weekNumberText)

			dow = gameRow.select(selectors["dow"])[0].text
			
			gameTimeText = gameRow.select(selectors["game-time"])[0].text
			if gameTimeText:
				try: gameTime = datetime.datetime.strptime(gameTimeText, "%I:%M%p").time()
				except ValueError:
					try: gameTime = datetime.datetime.strptime(gameTimeText, "%I:%M %p").time()
					except ValueError: pass

			winnerNode = gameRow.select(selectors["winner"])
			loserNode = gameRow.select(selectors["loser"])
			if winnerNode and loserNode:
				vs = gameRow.select(selectors["@"])[0].text
				if vs == "@":
					awayTeam = winnerNode[0]
					homeTeam = loserNode[0]
				else:
					homeTeam = winnerNode[0]
					awayTeam = loserNode[0]
			else:
				awayTeam = gameRow.select(selectors["away-team"])[0]
				homeTeam = gameRow.select(selectors["home-team"])[0]

			# Full names of teams, abbreviation
			teams["homeTeam"] = [homeTeam.text, __extract_team_abbrev_from_team_url(homeTeam.attrs["href"]).upper()]
			teams["awayTeam"] = [awayTeam.text, __extract_team_abbrev_from_team_url(awayTeam.attrs["href"]).upper()]
			homeTeamName = teams["homeTeam"][0]
			homeTeamAbbrev = teams["homeTeam"][1]
			awayTeamName = teams["awayTeam"][0]
			awayTeamAbbrev = teams["awayTeam"][1]

			allTeams.setdefault(homeTeamName, {"fullName": homeTeamName, "name": homeTeamName, "abbreviation": homeTeamAbbrev})
			allTeams.setdefault(awayTeamName, {"fullName": awayTeamName, "name": awayTeamName, "abbreviation": awayTeamAbbrev})
			teamsLookup.setdefault(homeTeamAbbrev, homeTeamName)
			teamsLookup.setdefault(awayTeamAbbrev, awayTeamName)

			yearDict["subseasons"].setdefault(subseason, dict())
			yearDict["subseasons"][subseason].setdefault(week, dict())
			yearDict["subseasons"][subseason][week].setdefault("events", dict())

			key = "nfl%s-%s%svs%s" % (year, gameDate.strftime("%Y%m%d"), homeTeamAbbrev, awayTeamAbbrev)
			if not id: id = "%s0%s" % (gameDate.strftime("%Y%m%d"), homeTeamAbbrev.lower())
			event = {
				"key": key,
				"id": id,
				"league": LEAGUE_NFL,
				"year": year,
				"subseason": subseason,
				"week": week,
				"day": dow,
				"date": gameDate,
				"time": gameTime,
				"vs": "%s vs. %s" % (homeTeamName, awayTeamName),
				"homeTeam": homeTeamAbbrev,
				"awayTeam": awayTeamAbbrev,
				"eventindicator": eventindicator,
				"href": gameHref
				}

			if subseason == 1:
				if not augmentedWithConferenceAndDivision:
					__process_teams_footer(soup, allTeams, teamsLookup)
					augmentedWithConferenceAndDivision = True

				conference = allTeams[teamsLookup[homeTeamAbbrev]].get("conference")
				if week == 1:
					if conference: event["subseasonTitle"] = "%s Wildcard Round" % conference
				if week == 2:
					if conference: event["subseasonTitle"] = "%s Divisional Round" % conference
				if week == 3:
					if conference: event["subseasonTitle"] = "%s Conference Championship" % conference
				elif week == 4:
					event["eventindicator"] = NFL_EVENT_FLAG_SUPERBOWL
					if yearDict["subseasons"][subseason][week].get("alias"):
						event["alias"] = event["subseasonTitle"] = yearDict["subseasons"][subseason][week]["alias"]
					elif int(year) >= NFL_SUPERBOWL_1_YEAR:
						event["alias"] = event["subseasonTitle"] = "Superbowl %s" % RomanNumerals.Format(int(year) - NFL_SUPERBOWL_1_YEAR + 1)

			yearDict["subseasons"][subseason][week]["events"].setdefault(key, event)
	

	return yearDict


def __process_teams_footer(soup, teams, teamsLookup):
	selectors = pfr_teams_footer_selectors

	footerMenu = soup.select(selectors["footer-menu"])
	if footerMenu:
		footerMenuItems = footerMenu[0].select(selectors["footer-menu-items"])
		if footerMenuItems:
			foundMenuItem = False
			for footerMenuItem in footerMenuItems:
				links = footerMenuItem.select("a")
				if links and links[0].text == "Teams":
					foundMenuItem = True
					break;
			if foundMenuItem and footerMenuItem:
				divisionNodes = footerMenuItem.select("div")
				if divisionNodes:
					for divisionNode in divisionNodes:
						if divisionNode.children:
							divisionText = divisionNode.contents[0]
							(conference, division) = __parse_conference_and_division(divisionText.rstrip(": "))
							for teamLink in divisionNode.select("a"):
								teamShortName = teamLink.text
								teamLinkHref = teamLink.attrs["href"]
								abbrev = __extract_team_abbrev_from_team_url(teamLinkHref)
								city = None

								team = teams[teamsLookup[abbrev]]
								if team["name"][:-len(teamShortName)].strip() == teamShortName:
									city = team["name"][:-len(teamShortName)].strip()

								if team:
									if city:
										team["name"] = teamShortName
										team["city"] = city
									team["conference"] = conference
									team["division"] = division
	return teams.values()






def __scrape_schedule_from_cache(year):
	if (__schedule_cache_has_events(year) == False):
		if __schedule_cache_file_exists(year) == False:
			__refresh_schedule_cache(year)
		else:
			cachedJson = __read_schedule_cache_file(year) #TODO: Try/Catch
			jsonschedules = json.loads(cachedJson, object_hook=DeserializationDefaults)

			if not jsonschedules:
				jsonschedules = __refresh_schedule_cache(year)

			if pfr_cached_schedules.get(year):
				pfr_cached_schedules[year].clear()
			else:
				pfr_cached_schedules.setdefault(year, dict())

			for key in jsonschedules.keys():
				pfr_cached_schedules[year][key] = jsonschedules[key]
	return pfr_cached_schedules[year]

def __refresh_schedule_cache(year):
	print("Refreshing NFL schedules cache from pro-footbal-reference.com ...")
	schedule = __scrape_schedule(year, download=True)

	if pfr_cached_schedules.get(year):
		pfr_cached_schedules[year].clear()
	else:
		pfr_cached_schedules.setdefault(year, dict())

	for key in schedule.keys():
		pfr_cached_schedules[year][key] = schedule[key]
	jsonschedule = json.dumps(schedule, default=SerializationDefaults, sort_keys=True, indent=4)
	__write_schedule_cache_file(year, jsonschedule)

	return jsonschedule

def __schedule_cache_has_events(year):
	if not pfr_cached_schedules.get(year): return False
	if len(pfr_cached_schedules[year]) == 0: return False
	yearDict = pfr_cached_schedules[year]
	hasAnyEvents = False
	if yearDict.get("subseasons"):
		for subseason in yearDict["subseasons"].keys():
			weeks = yearDict["subseasons"][subseason]
			for week in weeks.keys():
				if weeks[week].get("events"):
					if len(weeks[week]["events"]) > 0:
						return True

	return hasAnyEvents

def __schedule_cache_file_exists(year):
	path = __get_schedule_cache_file_path(year)
	return os.path.exists(path)

def __read_schedule_cache_file(year):
	path = __get_schedule_cache_file_path(year)
	return open(path, "r").read() # TODO: Invalidate cache

def __write_schedule_cache_file(year, json):
	print("Writing NFL schedule cache from pro-footbal-reference.com to disk ...")
	path = __get_schedule_cache_file_path(year)
	dir = os.path.dirname(path)
	EnsureDirectory(dir)
	f = open(path, "w")
	f.write(json)
	f.close()

def __get_schedule_cache_file_path(year):
	path = os.path.join(GetDataPathForLeague(LEAGUE_NFL), (EXPORT_NFL_SCHEDULE_FILENAME % year))
	return path

