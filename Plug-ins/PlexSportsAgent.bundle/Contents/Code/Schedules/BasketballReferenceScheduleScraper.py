import re, os, sys
import json
from datetime import datetime, date, time, timedelta
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
from Data.NBA.BasketballReferenceDownloader import *



EXPORT_NBA_SCHEDULE_FILENAME = "basketball-reference.Schedule-%s.json"

br_league_year_selectors = {	# /leagues/
	"seasons": "table#stats",
	"season-cell": "th[data-stat='season']",
	"league-cell": "td[data-stat='lg_id']",
}

br_season_schedule_selectors = {	# /leagues/NBA_2020_games.html
	"content": "div#content",
	"filter": "div.filter",
	"subdivision-link": "div a",
	}

br_season_subdivision_schedule_selectors = {	# /leagues/NBA_2020_games-december.html
	"schedule": "div#div_schedule",
	"date-row": "tbody tr",
	"game-key": "th[data-stat='date_game']",
	"game-date": "a",
	"game-time": "td[data-stat='game_start_time']",
	"away-team": "td[data-stat='visitor_team_name'] a",
	"home-team": "td[data-stat='home_team_name'] a",
	"box-score": "td[data-stat='box_score_text'] a"
	}

br_playoffs_selectors = {	# /playoffs/NBA_2020.html
	"playoffs": "table#all_playoffs",
	"playoff-round-row": "tbody tr",
	"playoff-round-text": "td span.opener strong",
	"game-row": "td > div > table tr",
	}


br_season_leagues = dict()

br_cached_schedules = dict()
#	[season]
#		[dateStr]
#		[
#			{
#				date:%DATE%+%TIME%,
#				dateDisp:,
#				id:,
#				league:,
#				href:,
#				homeTeam:,
#				awayTeam:,
#			}	
#		]



def ScrapeScheduleForSeason(season):
	return __scrape_schedule(season)






def __scrape_schedule(season, download=False):
	schedule = dict()

	if download == False: # Nab from cache
		schedule = __scrape_schedule_from_cache(season)

	else: # Download and scrape from Website
		schedule = __process_season(season)

	return schedule






def __process_all_season_leagues():
	if br_season_leagues: return br_season_leagues

	selectors = br_league_year_selectors
	markup = DownloadSeasonsIndex()
	if not markup: return None
	soup = BeautifulSoup(markup, "html5lib")


	tbl = soup.select_one(selectors["seasons"])
	if not tbl: return br_season_leagues

	rows = tbl.select("tr")
	for row in rows:
		if row.has_attr("class") and "thead" in row["class"]:
			continue

		season = None
		disp = None
		href = None
		league = None

		sznCell = row.select_one(selectors["season-cell"])
		lgCell = row.select_one(selectors["league-cell"])

		sznLink = sznCell.select_one("a")
		disp = sznLink.text.strip()
		season = disp.split("-")[0]
		href = sznLink.attrs["href"]

		lgLink = lgCell.select_one("a")
		league = lgLink.text.strip()
		if not href: href = lgLink.attrs["href"]

		if not href:
			continue

		if not season or not league:
			fn = href.split("/")[-1]
			pieces = fn.split("_")
			if not league:
				league = pieces[0]
			if not season:
				season = str(int(pieces[1]) - 1)

		br_season_leagues.setdefault(season, {
			"href": href,
			"season": season,
			"league": league,
			"diaplayName": disp,
			})

	return br_season_leagues







def __process_season(season):
	sznLgs = __process_all_season_leagues()
	if season not in sznLgs.keys():
		return seasonDict

	sznLg = sznLgs[season]
	league = sznLg["league"]
	seasonDict = __process_league_season_schedule_page(league, season)

	playoffs = __process_playoffs_page(league, season)
	if playoffs:
		for dateKey in playoffs.keys():
			daysEvents = seasonDict.get(dateKey)
			if not daysEvents:
				daysEvents = []
				seasonDict.setdefault(dateKey, daysEvents)
			playoffDaysEvents = playoffs[dateKey]
			for playoffEvent in playoffDaysEvents:
				event = None
				for i in range(0, len(daysEvents)):
					if playoffEvent["id"] == daysEvents[i].get("id"):
						event = daysEvents[i]
						break
				if event:
					merge_dictionaries(playoffEvent, event)

	return seasonDict

def __process_league_season_schedule_page(league, season):
	if br_cached_schedules.get(season):
		return br_cached_schedules[season]

	scheduledict = dict()

	br_cached_schedules.setdefault(season, scheduledict)

	selectors = br_season_schedule_selectors
	markup = DownloadSchedulePage(league, season)
	if not markup: return None
	soup = BeautifulSoup(markup, "html5lib")

	content = soup.select_one(selectors["content"])
	if not content:
		return scheduledict

	filter = content.select_one(selectors["filter"])
	if not filter:
		return scheduledict

	links = filter.select(selectors["subdivision-link"])
	for link in links:

		href = link.attrs["href"]

		displayName = link.text.strip()
		fn = href.split("/")[-1]
		pieces = fn.split("_")
		lg = pieces[0]
		szn = pieces[1]
		subdivision = pieces[2].split("-")[-1].split(".")[0]

		eventsByDate = __process_league_season_subdivision_schedule_page(lg, season, subdivision)
		if not eventsByDate: continue

		for dateStr in eventsByDate.keys():
			if not scheduledict.get(dateStr):
				scheduledict[dateStr] = eventsByDate[dateStr]
			else:
				scheduledict.setdefault(dateStr, [])
				for evt in eventsByDate[dateStr]:
					scheduledict[dateStr].append(evt)


	return scheduledict

def __process_league_season_subdivision_schedule_page(league, season, subdivision):
	selectors = br_season_subdivision_schedule_selectors
	markup = DownloadSchedulePage(league, season, subdivision)
	if not markup: return None
	soup = BeautifulSoup(markup, "html5lib")

	eventsByDate = dict()

	schedule = soup.select_one(selectors["schedule"])
	if not schedule:
		return eventsByDate

	dateRows = schedule.select(selectors["date-row"])
	for daterow in dateRows:
		if daterow.has_attr("class") and "thead" in daterow["class"]:
			continue

		gameKey = None
		dateKey = None
		id = None
		dateDisp = None
		timeDisp = None
		homeTeam = None
		awayTeam = None
		href = None

		airDate = None
		airDateDisp = None

		idCell = daterow.select_one(selectors["game-key"])
		if idCell:
			gameKey = idCell.attrs["csk"]
			dateLink = idCell.select_one(selectors["game-date"])
			if dateLink:
				dateDisp = dateLink.text
				# boxscoresHref = dateLink.attrs["href"]

		timeLink = daterow.select_one(selectors["game-time"])
		if timeLink:
			timeDisp = timeLink.text

		homeTeamLink = daterow.select_one(selectors["home-team"])
		if homeTeamLink:
			homeTeam = homeTeamLink.text

		awayTeamLink = daterow.select_one(selectors["away-team"])
		if awayTeamLink:
			awayTeam = awayTeamLink.text

		boxscoreLink = daterow.select_one(selectors["box-score"])
		if boxscoreLink:
			href = boxscoreLink.attrs["href"]

		if not dateDisp: continue

		date = extract_date(dateDisp)
		airDateDisp = dateDisp

		if not date:
			continue

		dateKey = date.strftime("%Y-%m-%d")
		airDate = date
		if timeDisp:
			time = extract_time(timeDisp)
			airDateDisp = "%s %s" % (dateDisp, timeDisp)
			airDate = datetime.datetime.combine(date, time)

		event = {
			"sport": SPORT_BASKETBALL,
			"league": league,
			"season": season,
			"id": gameKey,
			"date": airDate,
			"dateDisp": airDateDisp,
			"league": league,
			"href": href,
			"homeTeam": homeTeam,
			"awayTeam": awayTeam,
			"vs": "%s vs. %s" % (homeTeam, awayTeam),
			}


		if eventsByDate.get(dateKey):
			eventsByDate[dateKey].append(event)
		else:
			eventsByDate.setdefault(dateKey, [event])


	return eventsByDate


def __process_playoffs_page(league, season):
	scheduledict = dict()

	year = int(season) + 1

	selectors = br_playoffs_selectors
	markup = DownloadPlayoffsPage(league, season)
	if not markup: return scheduledict
	soup = BeautifulSoup(markup, "html5lib")

	container = soup.select_one(selectors["playoffs"])
	if not container:
		return scheduledict

	# Go through this once to collect and analyze playoff rounds
	playoffRounds = {
		"Finals": NBA_PLAYOFF_ROUND_FINALS
		}

	playoffRoundRows = container.select(selectors["playoff-round-row"])
	l = len(playoffRoundRows)
	i = 0
	for i in range(0, l):
		row = playoffRoundRows[i]

		playoffRoundTextEl = row.select_one(selectors["playoff-round-text"])
		if not playoffRoundTextEl:
			continue

		playoffRoundText = playoffRoundTextEl.text.strip()
		if playoffRoundText == "Semifinals" or \
			playoffRoundText.find("Conference Finals") >= 0 or \
			(playoffRoundText.find("Division Finals") >= 0 and NBA_PLAYOFF_ROUND_QUARTERFINALS not in playoffRounds.values()):
			playoffRounds.setdefault(playoffRoundText, NBA_PLAYOFF_ROUND_SEMIFINALS)

		elif playoffRoundText == "Quarterfinals" or \
			playoffRoundText.find("Conference Semifinals") >= 0 or \
			(playoffRoundText.find("Division Semifinals") >= 0 and NBA_PLAYOFF_1ST_ROUND not in playoffRounds.values()):
			playoffRounds.setdefault(playoffRoundText, NBA_PLAYOFF_ROUND_QUARTERFINALS)

		elif playoffRoundText.find("Tiebreaker") >= 0 or\
			playoffRoundText.find("First Round") >= 0:
			playoffRounds.setdefault(playoffRoundText, NBA_PLAYOFF_1ST_ROUND)
		
		pass




	l = len(playoffRoundRows)
	i = 0
	while i < l:
		row = playoffRoundRows[i]

		playoffRoundTextEl = row.select_one(selectors["playoff-round-text"])
		if not playoffRoundTextEl:
			i = i + 1
			continue

		playoffRound = None
		playoffRoundText = playoffRoundTextEl.text.strip()

		playoffRound = playoffRounds.get(playoffRoundText)
		if not playoffRound:
			i = i + 1
			continue

		i = i + 1
		while i < l:
			row = playoffRoundRows[i]
			if not row.has_attr("class") or not "toggleable" in row["class"]:
				i = i + 1
				continue
			else:
				break


		gamesRow = row
		gameRows = gamesRow.select(selectors["game-row"])
		for gameRow in gameRows:
			
			href = None
			gameNumber = None
			date = None
			homeTeam = None
			awayTeam = None
			id = None


			tds = gameRow.select("td")
			a = tds[0].select_one("a")
			href = a.attrs["href"]
			id = href.split("/")[-1].split(".")[0]
			linkText = a.text.strip()
			for expr in game_number_expressions:
				m = re.search(expr, linkText, re.IGNORECASE)
				if m:
					gameNumber = int(m.group("game_number"))
					break
			
			datePart = tds[1].text.strip()
			date = extract_date("%s, %s" % (datePart, year))

			awayTeam = tds[2].text.strip()
			homeTeam = tds[4].text.strip("@ ")

			dateKey = date.strftime("%Y-%m-%d")
			scheduledict.setdefault(dateKey, [])
			scheduledict[dateKey].append({
				"sport": SPORT_BASKETBALL,
				"league": league,
				"season": season,
				"date": date,
				"href": href,
				"id": id,
				"homeTeam": homeTeam,
				"awayTeam": awayTeam,
				"playoffround": playoffRound,
				"subseason": NBA_SUBSEASON_FLAG_POSTSEASON,
				"game": gameNumber,
				"subseasonTitle": playoffRoundText,
				"vs": "%s vs. %s" % (homeTeam, awayTeam),
				})

			pass


		i = i + 1
		while i < l:
			if row.has_attr("class") and "thead" in row["class"]:
				i = i + 1
			else:
				break
		
			
		pass


	return scheduledict




def merge_dictionaries(dct, into):
	if into == None or not dct: return into

	for key in dct.keys():
		value = dct[key]
		if not key in into.keys(): into.setdefault(key, value)
		elif into[key] == None: into[key] = value
		if isinstance(into[key], (dict)): merge_dictionaries(value, into[key])

	return into


def extract_date(value):
	weekday_expression = r"(?P<dow>(Sun(day)?)|(Mon(day)?)|(Tue(sday)?)|(Wed(nesday)?)|(Thu(rsday)?)|(Fri(day)?)|(Sat(urday)?))"
	month_expression = r"(?P<MMM>(Jan(uary)?)|(Feb(ruary)?)|(Mar(ch)?)|(Apr(il)?)|(May)|(Jun(e)?)|(Jul(y)?)|(Aug(ust)?)|(Sep(tember)?)|(Oct(ober)?)|(Nov(ember)?)|(Dec(ember)?))"

	eventDate = None
	expr = r"((?:%s,\s)?%s\s(?P<dd>\d{1,2}),\s(?P<yyyy>\d{2,4}))" % (weekday_expression, month_expression)
	m = re.search(expr, value, re.IGNORECASE)
	if m:
		formatted = "%s%s %02d, %04d" % ( \
			(m.group("dow") + ", ") if m.group("dow") else "", \
			m.group("MMM"), \
			int(m.group("dd")), \
			int(m.group("yyyy")) \
			)
		eventDate = __parse_date(formatted)

	return eventDate

def extract_time(value):
	time_expression = r"(?P<hh>\d{1,2})\:(?P<mm>\d{2})(?P<ss>:\d{2})?\s?(?P<ampm>(a|p)m?)"

	eventTime = None
	m = re.search(time_expression, value, re.IGNORECASE)
	if m:
		ampm = m.group("ampm")
		if len(ampm) == 1: ampm = ampm.upper() + "M"
		
		formatted = "%02d:%02d %s" % ( \
			int(m.group("hh")), \
			int(m.group("mm")), \
			ampm.upper() \
			)
		eventTime = __parse_time(formatted)

	return eventTime

def __parse_date(value):
	eventDate = None
	try: eventDate = datetime.datetime.strptime(value, "%B %d, %Y").date()
	except ValueError:
		try: eventDate = datetime.datetime.strptime(value, "%a, %b %d, %Y").date()
		except ValueError:
			try: eventDate = datetime.datetime.strptime(value, "%a, %B %d, %Y").date()
			except ValueError:
				try: eventDate = datetime.datetime.strptime(value, "%A, %B %d, %Y").date()
				except ValueError: pass
	return eventDate

def __parse_time(value):
	eventTime = None
	try: eventTime = datetime.datetime.strptime("2021-01-01T" + value, "%Y-%m-%dT%I:%M %p").time()
	except ValueError: pass
	return eventTime


def __scrape_schedule_from_cache(season):
	if (__schedule_cache_has_events(season) == False):
		if __schedule_cache_file_exists(season) == False:
			__refresh_schedule_cache(season)
		else:
			cachedJson = __read_schedule_cache_file(season) #TODO: Try/Catch
			allEvents = json.loads(cachedJson, object_hook=DeserializationDefaults)

			jsonschedules = dict()
			for event in allEvents:
				origdate = event["date"]
				date = ParseISO8601Date(origdate) if isinstance(origdate, (basestring)) else origdate
				event["date"] = date.date() if not date.time() else date
				dateKey = date.strftime("%Y-%m-%d") 
				jsonschedules.setdefault(dateKey, [])
				jsonschedules[dateKey].append(event)
			for dateKey in jsonschedules.keys():
				jsonschedules[dateKey].sort(key=get_sort_key)

			if not jsonschedules:
				jsonschedules = __refresh_schedule_cache(season)

			if br_cached_schedules.get(season):
				br_cached_schedules[season].clear()
			else:
				br_cached_schedules.setdefault(season, dict())

			br_cached_schedules[season] = jsonschedules
	return br_cached_schedules[season]

def get_sort_key(event):
	sortKey = ""
	origdate = event["date"]
	date = ParseISO8601Date(origdate) if isinstance(origdate, (basestring)) \
		else origdate if type(origdate) is datetime.datetime \
		else datetime.datetime.combine(origdate, datetime.time(0, 0))
	sortKey = FormatISO8601Date(date) + "|" + str(event["homeTeam"] or "").lower()
	return sortKey

def __refresh_schedule_cache(season):
	print("Refreshing NBA schedules cache from basketball-reference.com ...")
	schedule = __scrape_schedule(season, download=True)


	allEvents = []
	for dateKey in schedule.keys():
		allEvents = allEvents + schedule[dateKey]
	allEvents.sort(key=get_sort_key)

	if br_cached_schedules.get(season):
		br_cached_schedules[season].clear()
	else:
		br_cached_schedules.setdefault(season, dict())

	jsonschedule = json.dumps(allEvents, default=SerializationDefaults, sort_keys=True, indent=4)
	__write_schedule_cache_file(season, jsonschedule)

	return jsonschedule

def __schedule_cache_has_events(season):
	if not br_cached_schedules: return False
	if not br_cached_schedules.get(season): return False
	return True

def __schedule_cache_file_exists(season):
	path = __get_schedule_cache_file_path(season)
	return os.path.exists(path)

def __read_schedule_cache_file(season):
	path = __get_schedule_cache_file_path(season)
	return open(path, "r").read() # TODO: Invalidate cache

def __write_schedule_cache_file(season, json):
	print("Writing NBA schedule cache from basketball-reference.com to disk ...")
	path = __get_schedule_cache_file_path(season)
	dir = os.path.dirname(path)
	EnsureDirectory(dir)
	f = open(path, "w")
	f.write(json)
	f.close()

def __get_schedule_cache_file_path(season):
	path = os.path.join(GetDataPathForLeague(LEAGUE_NBA), (EXPORT_NBA_SCHEDULE_FILENAME % season))
	return path

