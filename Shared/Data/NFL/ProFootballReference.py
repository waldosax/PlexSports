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
from Serialization import *
from ..GetResultFromNetwork import *



EXPORT_NFL_TEAMS_FILENAME = "pro-football-reference.Teams.json"
EXPORT_NFL_SCHEDULE_FILENAME = "pro-football-reference.Schedule-%s.json"


PFR_BASE_URL = "http://www.pro-football-reference.com"
PFR_CDN_BASE_URL = "https://d2p3bygnnzw9w3.cloudfront.net"
PFR_YEARS_INDEX = "/years/"
PFR_TEAMS_INDEX = "/teams/"
PFR_LOGO_BASE_PATH = "/req/202107261/tlogo/pfr/"


pfr_years_index_selectors = {	# /years/
	"year-table": "table#years",
	"year-row": "tbody tr",
	"league-defs": "thead tr th.poptip",
	"league-def_attr": "data-tip",
	"year-ind": "th[data-stat='year_id'] a",
	"year-league": "td[data-stat='league_id'] a",
	"year-superbowl": "td[data-stat='summary'] b"
	}

pfr_year_index_selectors = {	# /years/2020/
	"afc-standings": "div#all_AFC > div#div_AFC > table#AFC",
	"nfc-standings": "div#all_NFC > div#div_NFC > table#NFC",
	"standings-data-row": "tbody tr",
	"division": "td[data-stat='onecell']",
	"team-link": "th[data-stat='team'] a",
	"section-labels": "div#wrap div#inner_nav>ul>li>a",
	"week-summaries": "div>ul>li>a",
	"week-id-alt": "div#all_week_games div.placeholder",
	"week-template-summaries": "div#div_week_games div.filter div a"
	}

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

pfr_week_index_selectors = {	# /years/2020/week_3.htm
	"game-widgets": "div.game_summaries div.game_summary",
	"game-data": "table.teams tbody",
	"game-date": "tr.date td",
	"game-link": "tr td.gamelink a",
	"team-link": "tr td a"
	}

pfr_game_selectors = {	# /boxscores/202009240jax.htm
	"scorebox": "div.scorebox",
	"scorebox-meta": "div.scorebox_meta",
	"scorebox-meta-item": "div strong",
	"scorebox-team-box": "div[itemprop='performer'][itemtype='https://schema.org/Organization']",
	"scorebox-team-name": "a[itemprop='name']",
	"scorebox-team-logo": "div.logo img.teamlogo"
	}

pfr_team_selectors = {	# /teams/ram/2020.htm
	"team-logo": "div.logo img.teamlogo",
	"team-summary": "div#info div#meta div[data-template='Partials/Teams/Summary']",
	"team-summary-labels": "p strong",
	}

pfr_franchise_selectors = {	# /teams/
	"active-franchises": "table#teams_active",
	"inactive-franchises": "table#teams_inactive",
	"inactive-franchises-placeholder": "div#all_teams_inactive div.placeholder",
	"team": "tbody > tr",
	"team-name": "th[data-stat='team_name']",
	"team-link": "a",
	"from": "td[data-stat='year_min']",
	"to": "td[data-stat='year_max']",
	"franchise-logo": "div.logo img.teamlogo"
	}

__now = datetime.datetime.now()
prf_current_season = str(__now.year - 1 if __now.month < 8 else __now.year)
prf_last_season = str(__now.year - 2 if __now.month < 8 else __now.year - 1)

prf_league_defs = dict()
prf_year_hrefs = dict()
prf_year_superbowls = dict()
pfr_schedule_weeks = dict() # [league][year][href:|subseasons: ... [subseason, ...]][week][alias:|href:] ... [{date:datetime.date|homeTeam:|awayTeam:|time:time|alias:}, event, ...]
pfr_teams = dict() # [league][franchise]["teams"][team][year] ... [{logo:|href:}]

__worker_thread_queue = Queue.Queue()
__worker_thread_semaphore = threading.BoundedSemaphore(value = 4)


def __correct_superbowl(s):
	"""Superbowl is one word, dammit."""
	if not s: return s
	return s.replace("Super Bowl", "Superbowl").replace("SuperBowl", "Superbowl").rstrip(": ")

def __get_subseason_name(subseason):
	if subseason == -1: return "Preseason"
	if subseason == 1: return "Playoffs"
	return "Regular Season"

def __parse_conference_and_division(s):
	conference = None
	division = None

	if s:
		s = s.strip()
		if s[:3].upper() in ["AFC", "NFC"]:
			conference = s[:3]
			s = s[3:].lstrip()
		if s[-8:].upper() == "DIVISION":
			division = s[:-8].strip()
		else:
			division = s.strip()

	return (conference, division)

def monitor(queue, semaphore=None):
	while True:
		threads = []
		while queue.unfinished_tasks:
			(target, kwargs) = queue.get()
			if semaphore: semaphore.acquire()
			thrd = threading.Thread(target=target, kwargs=kwargs)
			threads.append(thrd)
			thrd.start()

		for t in threads:
			t.join()




def Scrape():
	league = LEAGUE_NFL

	thrd = threading.Thread(target=monitor, kwargs={"queue": __worker_thread_queue, "semaphore": __worker_thread_semaphore})
	thrd.daemon = True
	thrd.start()

	__process_franchise_index_page()
	__export_nfl_teams(raw=True)
	__export_nfl_teams()


	__process_years_index_page()

	years = prf_year_hrefs[league].keys()
	years.sort(reverse=True)
	prf_current_season = years[0]
	prf_last_season = years[1]

	## Filter years for testing
	#years = ["2021", "2020", "1970", "1969", "1922"]

	for year in years:
		__worker_thread_queue.put((__process_nfl_season, {"year":year}))


	__worker_thread_queue.join()

	# Export teams after potentially being modified/augmented by processing years
	__export_nfl_teams(raw=True)
	__export_nfl_teams()

	print("Done.")
	pass





def __find_nfl_franchise(teamName, year, create_if_not_found=True):
	franchise = None
	team = None

	pfr_teams.setdefault(LEAGUE_NFL, dict())

	def pfr_sort_franchise(x, y):
		activeX = x["active"] or False
		activeY = x["active"] or False
		if not activeX == activeY:
			return -1 if activeX else 1

		fromX = int(x["from"]) if x.get("from") else datetime.utcnow().year
		fromY = int(y["from"]) if y.get("from") else datetime.utcnow().year
		if fromX < fromY:
			return 1
		elif fromX > fromY:
			return -1
		toX = int(x["to"]) if x.get("to") else datetime.utcnow().year
		toY = int(y["to"]) if y.get("to") else datetime.utcnow().year
		if toX < toY:
			return 1
		elif toX > toY:
			return -1
		return 0


	franchises = []
	if pfr_teams[LEAGUE_NFL].get(teamName):
		franchise = pfr_teams[LEAGUE_NFL][teamName]
	else:
		for franchiseName in pfr_teams[LEAGUE_NFL].keys():
			if pfr_teams[LEAGUE_NFL][franchiseName].get("teams") and teamName in pfr_teams[LEAGUE_NFL][franchiseName]["teams"].keys():
				franchises.append(pfr_teams[LEAGUE_NFL][franchiseName])
		if franchises:
			franchises.sort(cmp=pfr_sort_franchise)
			for f in franchises:
				if teamName in f["teams"].keys():
					franchise = f
					break
			if not franchise:
				franchise = franchises[0]

	if franchise:
		if create_if_not_found: franchise.setdefault("teams", dict())
		if create_if_not_found: franchise["teams"].setdefault(teamName, {"name": teamName})
		if create_if_not_found: franchise["teams"][teamName].setdefault(year, {"name": teamName, "year": year})
		if franchise.get("teams") and franchise["teams"].get(teamName) and franchise["teams"][teamName].get(year):
		   team = franchise["teams"][teamName][year]
	elif create_if_not_found:
		team = {"name": teamName, "year": year}
		franchise = {"name": teamName, "teams": {teamName: {year: team}}}
		pfr_teams[LEAGUE_NFL][teamName] = franchise

	return (franchise, team)

def __process_years_index_page():
	print("Collecting all seasons/leagues ...")
	selectors = pfr_years_index_selectors
	url = PFR_BASE_URL + PFR_YEARS_INDEX
	soup = BeautifulSoup(GetResultFromNetwork(url, cacheExtension=".html"), "html5lib")

	lds = soup.select("%s %s" % (selectors["year-table"], selectors["league-defs"]))
	foundLeagueDefs = False
	for ld in lds:
		if foundLeagueDefs: break
		if not ld.attrs.get("data-stat") in ["year_id", "summary"]:
			ldRaw = ld.attrs[selectors["league-def_attr"]]
			foundLeagueDefs = True
			ldSoup = BeautifulSoup(ldRaw, "html5lib")
			for ldNode in ldSoup.select("b"):
				if not ldNode.next == "League" and ldNode.next and ldNode.next.next:
					key = ldNode.next
					value = ldNode.next.next
					while value[:1] in [" ", "-"]:
						value = value[1:]
					prf_league_defs[key] = value
	#pprint(prf_league_defs)

	yearRows = soup.select("%s %s" % (selectors["year-table"], selectors["year-row"]))
	for yearRow in yearRows:
		yearLink = None
		year = None

		yearIndicators = yearRow.select(selectors["year-ind"])
		if yearIndicators:
			yearIndicator = yearIndicators[0]
			yearHref = yearIndicator.attrs["href"]
			yearText = yearIndicator.text

		yearLeagues = yearRow.select(selectors["year-league"])
		for yearLeague in yearLeagues:
			yearLeagueHref = yearLeague.attrs["href"]
			yearLeagueText = yearLeague.text.upper()
			prf_year_hrefs.setdefault(yearLeagueText, dict())
			prf_year_hrefs[yearLeagueText][yearText] = yearLeagueHref

		yearSuperbowls = yearRow.select(selectors["year-superbowl"])
		if yearSuperbowls:
			yearSuperbowl = yearSuperbowls[0]
			yearSuperbowlText = __correct_superbowl(yearSuperbowl.text)
			prf_year_superbowls[yearText] = yearSuperbowlText.rstrip(": ")

	#pprint(prf_year_hrefs)
	#pprint(prf_year_superbowls)
	pass


def __process_nfl_season(year):
	league = LEAGUE_NFL
	__process_nfl_season_page(year)
	__process_nfl_schedule_page(year)
	for subseason in pfr_schedule_weeks[league][year].get("subseasons"):
		for week in pfr_schedule_weeks[league][year]["subseasons"][subseason].keys():
			#__process_nfl_week_page(year, subseason, week)
			for event in pfr_schedule_weeks[league][year]["subseasons"][subseason][week]["events"].values():
				if not event.get("time") and int(year or 0) > 1969:
					__process_nfl_game_page(event)
	__export_nfl_season(year, raw=True)
	__export_nfl_season(year)
	__worker_thread_semaphore.release()
	__worker_thread_queue.task_done()
	print("    Done processing %s season." % year)

def __process_nfl_season_page(year):
	print("    Collecting all season information for %s season ..." % year)
	selectors = pfr_year_index_selectors
	url = PFR_BASE_URL + prf_year_hrefs[LEAGUE_NFL][year]
	soup = BeautifulSoup(GetResultFromNetwork(url, cacheExtension=".html"), "html5lib")

	pfr_schedule_weeks.setdefault(LEAGUE_NFL, dict())
	pfr_schedule_weeks[LEAGUE_NFL].setdefault(year, dict())


	allTeams = soup.select(selectors["afc-standings"]) + soup.select(selectors["nfc-standings"])
	if allTeams:
		currentConference = None
		currentDivision = None
		for conferenceTable in allTeams:
			for dataRow in conferenceTable.select(selectors["standings-data-row"]):
				if dataRow.attrs.get("class") and "onecell" in dataRow.attrs["class"]:
					conferenceNode = dataRow.select(selectors["division"])[0]
					(conference, division) = __parse_conference_and_division(conferenceNode.text)
					currentConference = conference
					currentDivision = division
				else:	# Team Row
					teamLinkNodes = dataRow.select(selectors["team-link"])
					if teamLinkNodes:
						teamName = teamLinkNodes[0].text
						teamLinkHref = teamLinkNodes[0].attrs["href"]
						franchiseLinkHref = "%s/" % "/".join(teamLinkHref.split("/")[:-1])
						abbrev = teamLinkHref.split("/")[-2].upper()
						(franchise, team) = __find_nfl_franchise(teamName, year)
						franchise.setdefault("abbrev", abbrev)
						franchise.setdefault("href", franchiseLinkHref)
						franchise.setdefault("conference", currentConference)
						franchise.setdefault("division", currentDivision)
						teamMeta = franchise["teams"][teamName]
						teamMeta.setdefault("conference", currentConference)
						teamMeta.setdefault("division", currentDivision)
						teamMeta.setdefault("name", teamName)
						team.setdefault("href", teamLinkHref)
						if not team.get("conference") or currentConference != franchise["teams"][teamName]["conference"]: team.setdefault("conference", currentConference)
						if not team.get("division") or currentDivision != franchise["teams"][teamName]["division"]: team.setdefault("division", currentDivision)


	foundWeekIndicator = False
	foundScheduleIndicator = False
	scheduleHref = None
	weekSummaries = []
	sectionLabels = soup.select(selectors["section-labels"])
	for sectionLabel in sectionLabels:
		if foundWeekIndicator and foundScheduleIndicator: break
		sectionLabelText = sectionLabel.text
		if sectionLabelText == "Weeks":
			foundWeekIndicator = True
			weekSummaries = sectionLabel.parent.select(selectors["week-summaries"])
		elif sectionLabelText == "Schedule":
			foundScheduleIndicator = True
			scheduleHref = sectionLabel.attrs["href"]

	if not foundWeekIndicator:
		# Check alternate methond if season is not historical
		weekTemplatePlaceHolders = soup.select(selectors["week-id-alt"])
		if weekTemplatePlaceHolders:
			weekTemplateComment = weekTemplatePlaceHolders[0].next_sibling
			while weekTemplateComment:
				if isinstance(weekTemplateComment, bs4.Comment): break
				weekTemplateComment = weekTemplateComment.next_sibling
			if weekTemplateComment:
				weekTemplateSoup = BeautifulSoup(weekTemplateComment, "html5lib")
				weekSummaries = weekTemplateSoup.select(selectors["week-template-summaries"])
				pass

	pfr_schedule_weeks[LEAGUE_NFL][year].setdefault("href", scheduleHref)
	pfr_schedule_weeks[LEAGUE_NFL][year].setdefault("subseasons", dict())

	for weekSummary in weekSummaries:
		weekSummaryHref = weekSummary.attrs["href"]
		if weekSummaryHref[:1] == "#": continue
		weekSummaryText = weekSummary.text

		if weekSummaryText[:4] == "Week":
			week = int(weekSummaryText[5:])
			pfr_schedule_weeks[LEAGUE_NFL][year]["subseasons"].setdefault(0, dict())
			pfr_schedule_weeks[LEAGUE_NFL][year]["subseasons"][0].setdefault(week, dict())
			pfr_schedule_weeks[LEAGUE_NFL][year]["subseasons"][0][week].setdefault("events", dict())
			pfr_schedule_weeks[LEAGUE_NFL][year]["subseasons"][0][week]["href"] = weekSummaryHref
			pfr_schedule_weeks[LEAGUE_NFL][year]["subseasons"][0][week]["alias"] = weekSummaryText
			#print("Week >>%s<<" % week)
		elif weekSummaryText == "Wild Card":
			pfr_schedule_weeks[LEAGUE_NFL][year]["subseasons"].setdefault(1, dict())
			pfr_schedule_weeks[LEAGUE_NFL][year]["subseasons"][1].setdefault(1, dict())
			pfr_schedule_weeks[LEAGUE_NFL][year]["subseasons"][1][1].setdefault("events", dict())
			pfr_schedule_weeks[LEAGUE_NFL][year]["subseasons"][1][1]["href"] = weekSummaryHref
			pfr_schedule_weeks[LEAGUE_NFL][year]["subseasons"][1][1]["alias"] = "Wildcard Round"
		elif weekSummaryText == "Divisional":
			pfr_schedule_weeks[LEAGUE_NFL][year]["subseasons"].setdefault(1, dict())
			pfr_schedule_weeks[LEAGUE_NFL][year]["subseasons"][1].setdefault(2, dict())
			pfr_schedule_weeks[LEAGUE_NFL][year]["subseasons"][1][2].setdefault("events", dict())
			pfr_schedule_weeks[LEAGUE_NFL][year]["subseasons"][1][2]["href"] = weekSummaryHref
			pfr_schedule_weeks[LEAGUE_NFL][year]["subseasons"][1][2]["alias"] = "Divisional Round"
		elif weekSummaryText == "Conf Champ":
			pfr_schedule_weeks[LEAGUE_NFL][year]["subseasons"].setdefault(1, dict())
			pfr_schedule_weeks[LEAGUE_NFL][year]["subseasons"][1].setdefault(3, dict())
			pfr_schedule_weeks[LEAGUE_NFL][year]["subseasons"][1][3].setdefault("events", dict())
			pfr_schedule_weeks[LEAGUE_NFL][year]["subseasons"][1][3]["href"] = weekSummaryHref
			pfr_schedule_weeks[LEAGUE_NFL][year]["subseasons"][1][3]["alias"] = "Conference Championship"
		elif weekSummaryText == "Super Bowl":
			pfr_schedule_weeks[LEAGUE_NFL][year]["subseasons"].setdefault(1, dict())
			pfr_schedule_weeks[LEAGUE_NFL][year]["subseasons"][1].setdefault(4, dict())
			pfr_schedule_weeks[LEAGUE_NFL][year]["subseasons"][1][4].setdefault("events", dict())
			pfr_schedule_weeks[LEAGUE_NFL][year]["subseasons"][1][4]["href"] = weekSummaryHref
			pfr_schedule_weeks[LEAGUE_NFL][year]["subseasons"][1][4]["alias"] = prf_year_superbowls.get(year) or "Superbowl"

		#pprint(pfr_schedule_weeks)
	pass


def __process_nfl_schedule_page(year):
	print("    Collecting schedule for %s season ..." % year)
	selectors = pfr_year_schedule_selectors
	yearDict = pfr_schedule_weeks[LEAGUE_NFL][year]
	url = PFR_BASE_URL + yearDict["href"]
	soup = BeautifulSoup(GetResultFromNetwork(url, cacheExtension=".html"), "html5lib")

	yearDict.setdefault("subseasons", dict())
	pfr_teams.setdefault(LEAGUE_NFL, dict())

	gameTables = soup.select(selectors["game-table"])
	if gameTables:
		gameTable = gameTables[0]
		gameRows = gameTable.select(selectors["game-row"])
		for gameRow in gameRows:
			if gameRow.attrs.get("class") and "thead" in gameRow.attrs["class"]: continue
			subseason = 0	# TODO: What was I doing with event aliases again?
			weekNumber = None
			dow = None
			gameDate = None
			gameTime = None
			winner = None
			loser = None
			teams = dict()
			vs = None
			gameHref = None

			boxScoreNode = gameRow.select(selectors["box-score"])[0]

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

			teams["homeTeam"] = (homeTeam.text, homeTeam.attrs["href"])
			teams["awayTeam"] = (awayTeam.text, awayTeam.attrs["href"])

			for (teamName, teamLinkHref) in teams.values():
				abbrev = teamLinkHref.split("/")[-2].upper()
				franchiseLinkHref = "%s/" % "/".join(teamLinkHref.split("/")[:-1])
				(franchise, team) = __find_nfl_franchise(teamName, year)
				franchise.setdefault("abbrev", abbrev)
				franchise.setdefault("href", franchiseLinkHref)
				team.setdefault("href", teamLinkHref)


			gameLinkNodes = boxScoreNode.select(selectors["game-link"])
			if gameLinkNodes:
				gameHref = gameLinkNodes[0].attrs["href"]

			yearDict["subseasons"].setdefault(subseason, dict())
			yearDict["subseasons"][subseason].setdefault(week, dict())
			yearDict["subseasons"][subseason][week].setdefault("events", dict())

			homeTeamName = teams["homeTeam"][0]
			awayTeamName = teams["awayTeam"][0]
			key = "nfl%s-%s%svs%s" % (year, gameDate.strftime("%Y%m%d"), homeTeamName, awayTeamName)
			event = {
				"key": key,
				"league": LEAGUE_NFL,
				"year": year,
				"subseason": subseason,
				"week": week,
				"day": dow,
				"date": gameDate,
				"time": gameTime,
				"homeTeam": teams["homeTeam"][0],
				"awayTeam": teams["awayTeam"][0],
				"href": gameHref
				}
			if subseason == 1:
				(xFranchise, xTeam) = __find_nfl_franchise(teams["homeTeam"][0], year)
				conference = xTeam.get("conference")
				if week == 1:
					if conference: event["alias"] = "%s Wildcard Round" % conference
				if week == 2:
					if conference: event["alias"] = "%s Divisional Round" % conference
				if week == 3:
					if conference: event["alias"] = "%s Conference Championship" % conference
				elif week == 4 and yearDict["subseasons"][subseason][week].get("alias"):
					event["alias"] = yearDict["subseasons"][subseason][week]["alias"]
			yearDict["subseasons"][subseason][week]["events"].setdefault(key, event)
	pass


def __process_nfl_week_page(year, subseason, week):
	print("        Collecting all games for %s season, %s, week %s ..." % (year, __get_subseason_name(subseason), week))
	selectors = pfr_week_index_selectors
	weekDict = pfr_schedule_weeks[LEAGUE_NFL][year]["subseasons"][subseason][week]
	url = PFR_BASE_URL + weekDict["href"]
	soup = BeautifulSoup(GetResultFromNetwork(url, cacheExtension=".html"), "html5lib")

	pfr_teams.setdefault(LEAGUE_NFL, dict())
	weekDict.setdefault("events", dict())

	gameWidgets = soup.select(selectors["game-widgets"])
	for widget in gameWidgets:
		gameDateStr = None
		gameLinkHref = None
		teams = [] # [away, home]

		gameDateNodes = widget.select("%s %s" % (selectors["game-data"], selectors["game-date"]))
		if gameDateNodes:
			gameDateStr = gameDateNodes[0].text

		gameLinkNodes = widget.select("%s %s" % (selectors["game-data"], selectors["game-link"]))
		if gameLinkNodes:
			gameLinkHref = gameLinkNodes[0].attrs["href"]

		# TODO: gameTimeNodes when current season

		teamLinkNodes = widget.select("%s %s" % (selectors["game-data"], selectors["team-link"]))
		for teamLinkNode in teamLinkNodes:
			attrs = teamLinkNode.parent.attrs
			if not attrs.get("class") or "gamelink" not in attrs["class"]:
				teamName = teamLinkNode.text
				teamLinkHref = teamLinkNode.attrs["href"]
				abbrev = teamLinkHref.split("/")[:-2].upper()
				franchiseLinkHref = "%s/" % "/".join(teamLinkHref.split("/")[:-1])

				(franchise, team) = __find_nfl_franchise(teamName, year)
				franchise.setdefault("abbrev", abbrev)
				franchise.setdefault("href", franchiseLinkHref)
				team.setdefault("href", teamLinkHref)

				teams.append((teamName, teamLinkHref))

		pfr_schedule_weeks.setdefault(LEAGUE_NFL, dict())
		pfr_schedule_weeks[LEAGUE_NFL].setdefault(year, dict())
		pfr_schedule_weeks[LEAGUE_NFL][year].setdefault(subseason, dict())
		pfr_schedule_weeks[LEAGUE_NFL][year][subseason].setdefault(week, dict())
		pfr_schedule_weeks[LEAGUE_NFL][year][subseason][week].setdefault("events", dict())

		gameDate = parse(gameDateStr)	# TODO: figure from offset ((season start - (season start % 7) + (week -1) * 7 + dow)
										#	or something like that when gameDateStr is just a dow
		dow = gameDate.weekday
		homeTeamName = teams[0][0]
		awayTeamName = teams[1][0]
		key = "nfl%s-%s%svs%s" % (year, gameDate.strftime("%Y%m%d"), homeTeamName, awayTeamName)
		event = {
			"key": key,
			"league": LEAGUE_NFL,
			"year": year,
			"subseason": subseason,
			"week": week,
			"day": dow,
			"date": gameDate,
			"homeTeam": homeTeamName,
			"awayTeam": awayTeamName,
			"href": gameLinkHref
			}
		weekDict["events"].setdefault(key, event)
		

	#pprint(pfr_schedule_weeks)
	pass


def __process_nfl_game_page(event):
	# Skip out if there's nothing on this page we actually need to acquire
	year = event.get("year") 
	if event.get("time") or int(year or 0) <= 1969: return
	homeTeamName = event["homeTeam"]
	awayTeamName = event["awayTeam"]
	(homeTeamFranchise, homeTeam) = __find_nfl_franchise(homeTeamName, year)
	(awayTeamFranchise, awayTeam) = __find_nfl_franchise(awayTeamName, year)
	if homeTeam.get("href") and homeTeam.get("logo") and awayTeam.get("href") and awayTeam.get("logo"): pass

	print("            Collecting game details for %s %s vs %s ..." % (event["date"].strftime("%m/%d/%Y"), event["homeTeam"], event["awayTeam"]))
	selectors = pfr_game_selectors
	url = PFR_BASE_URL + event["href"]
	soup = BeautifulSoup(GetResultFromNetwork(url, cacheExtension=".html"), "html5lib")

	metaItems = soup.select("%s %s %s" % (selectors["scorebox"], selectors["scorebox-meta"], selectors["scorebox-meta-item"]))
	for metaItem in metaItems:
		metaItemLabel = metaItem.text
		if metaItemLabel == "Start Time":
			startTimeStr = metaItem.nextSibling
			while startTimeStr[:1] in [" ", ":", "-"]:
				startTimeStr = startTimeStr[1:]
			startTime = datetime.datetime.strptime(startTimeStr, '%I:%M%p')
			event["time"] = startTime.time()

	# Get information about the two teams since we're here
	teams = dict()
	teamBoxes = soup.select("%s %s" % (selectors["scorebox"], selectors["scorebox-team-box"]))
	for teamBox in teamBoxes:
		teamLink = teamBox.select(selectors["scorebox-team-name"])[0]
		teamName = teamLink.text
		teamHref = teamLink.attrs["href"]
		teamLogoSrc = teamBox.select(selectors["scorebox-team-logo"])[0].attrs["src"]
		teams.setdefault(teamName, dict())
		teams[teamName]["logo"] = teamLogoSrc
		teams[teamName]["href"] = teamHref


	# Augment with any team data not already gathered
	year = event["year"]
	for teamName in teams.keys():
		t = teams[teamName]

		# Synthesize franchise value for href
		(franchise, team) = __find_nfl_franchise(teamName, year)
		franchiseLinkHref = "%s%s/" % (PFR_TEAMS_INDEX, franchise["abbrev"].lower())
		franchise.setdefault("href", franchiseLinkHref)
		for key in t.keys():
			franchise.setdefault(key, t[key])
		
		isActive = franchise.get("active")
		if isActive: isActive = teamName == franchise["name"]
		elif isActive == None and year in [prf_current_season, prf_last_season]: isActive = True
		if isActive: franchise["teams"][teamName].setdefault("active", True)
		franchise["teams"][teamName].setdefault("name", teamName)
		for key in t.keys():
			team.setdefault(key, t[key])
	pass





def __process_nfl_year_team_page(franchise, team):
	print("    Collecting team info for the %s %s ..." % (team["year"], team["name"]))
	selectors = pfr_team_selectors
	url = PFR_BASE_URL + team["href"]
	soup = BeautifulSoup(GetResultFromNetwork(url, cacheExtension=".html"), "html5lib")

	if "logo" not in team.keys():
		teamLogoSrc = soup.select(selectors["team-logo"])[0].attrs["src"]
		team["logo"] = teamLogoSrc

	if "conference" not in team.keys() or "division" not in team.keys():
		teamName = team["name"]
		conference = None
		division = None
		labelNodes = soup.select("%s %s" % (selectors["team-summary"], selectors["team-summary-labels"]))
		for labelNode in labelNodes:
			labelText = labelNode.text
			while labelText[-1:] in [":", " "]:
				labelText = labelText[:-1]
			if labelText == "Record":
				confDivision = labelNode.nextSibling.nextSibling.text
				(conference, division) = __parse_conference_and_division(confDivision)
				if conference:
					team.setdefault("conference", conference)
					franchise["teams"][teamName].setdefault("conference", conference)
					franchise.setdefault("conference", conference)
				if division:
					team.setdefault("division", division)
					franchise["teams"][teamName].setdefault("division", division)
					franchise.setdefault("division", division)

	__worker_thread_semaphore.release()
	__worker_thread_queue.task_done()

	#pprint(team)
	pass



def __get_franchise_current_logo(franchise):
	if not franchise.get("logo"):
		print("    Collecting franchise info for %s ..." % franchise["name"])
		url = PFR_BASE_URL + franchise["href"]
		soup = BeautifulSoup(GetResultFromNetwork(url, cacheExtension=".html"), "html5lib")

		franchiseLogo = soup.select(pfr_franchise_selectors["franchise-logo"])
		if franchiseLogo:
			franchise["logo"] = franchiseLogo[0].attrs["src"]

	__worker_thread_semaphore.release()
	__worker_thread_queue.task_done()

def __process_franchise_index_page():
	print("Collecting all franchises/teams ...")
	selectors = pfr_franchise_selectors
	url = PFR_BASE_URL + PFR_TEAMS_INDEX
	soup = BeautifulSoup(GetResultFromNetwork(url, cacheExtension=".html"), "html5lib")

	pfr_teams.setdefault(LEAGUE_NFL, dict())


	def get_franchise_team_info(row):
		info = dict()
		
		teamNameNode = row.select(selectors["team-name"])[0]
		teamName = teamNameNode.text
		while teamName[-1] in ["*"]:
			teamName = teamName[0:-1]
		info["name"] = teamName
		
		teamLinkNodes = teamNameNode.select(selectors["team-link"])
		if teamLinkNodes:
			href = teamLinkNodes[0].attrs.get("href")
			if href:
				info["href"] = href
				info["abbrev"] = href.split("/")[-2].upper()

		fromNode = row.select(selectors["from"])[0]
		info["from"] = fromNode.text
		toNode = row.select(selectors["to"])[0]
		info["to"] = toNode.text

		return info

	def get_years(franchise, teamName):
		years = []

		spans = []
		teamMeta = franchise["teams"][teamName]
		if teamMeta and teamMeta.get("years"):
			for span in teamMeta["years"]:
				spans.append(span)
		else:
			span = {"from": franchise["from"],"to": franchise["to"]}
			spans.append(span)

		for span in spans:
			for i in range(int(span["from"]), int(span["to"])+1):
				year = str(i)
				years.append(year)

		return years


	allFranchiseTables = [soup.select(selectors["active-franchises"])[0]]
	inactiveFranchisesPlaceholder = soup.select(selectors["inactive-franchises-placeholder"])[0]
	inactiveFranchisesTemplate = inactiveFranchisesPlaceholder.next_sibling
	while inactiveFranchisesTemplate:
		if isinstance(inactiveFranchisesTemplate, bs4.Comment): break
		inactiveFranchisesTemplate = inactiveFranchisesTemplate.next_sibling
	if inactiveFranchisesTemplate:
		inactiveFranchisesSoup = BeautifulSoup(inactiveFranchisesTemplate, "html5lib")
		inactiveFranchisesNodes = inactiveFranchisesSoup.select(selectors["inactive-franchises"])
		if inactiveFranchisesNodes:
			allFranchiseTables.append(inactiveFranchisesNodes[0])

	for i in range(0, len(allFranchiseTables)):
		franchiseTable = allFranchiseTables[i]
		activeFranchises = (i == 0)

		teamNodes = franchiseTable.select(selectors["team"])
		franchise = None

		for i in range(0, len(teamNodes)):
			currentNode = teamNodes[i]
			if currentNode.attrs.get("class") and "thead" in currentNode.attrs["class"]: continue
			if not currentNode.attrs.get("class"): # Franchise
				franchiseNode = currentNode

				if franchise:	# Seal up any info on the franchise where there has only been one team
					franchiseName = franchise["name"]
					franchise["teams"].setdefault(franchiseName, dict())
					teamMeta = franchise["teams"][franchiseName]
					teamMeta.setdefault("name", franchiseName)
					span = {"from": franchise["from"], "to": franchise["to"]}
					if not teamMeta.get("years"):
						teamMeta.setdefault("years", [])
						teamMeta["years"].append(span)
					if franchise.get("active"): teamMeta.setdefault("active", franchise["active"])
					for year in get_years(franchise, franchiseName):
						if not teamMeta.get(year):
							teamLinkHref = "%s%s/%s.htm" % (PFR_TEAMS_INDEX, franchise["abbrev"].lower(), year)
							franchiseLogoSrc = "%s%s%s-%s.png" % (PFR_CDN_BASE_URL, PFR_LOGO_BASE_PATH, franchise["abbrev"].lower(), year)
							info = {
								"href": teamLinkHref,
								"logo": franchiseLogoSrc
								}
							teamMeta[year] = info
				
				# New franchise
				info = get_franchise_team_info(franchiseNode)
				franchiseName = info["name"]

				franchise = dict(info)
				franchise.setdefault("teams", dict())
				franchise.setdefault("active", activeFranchises)

				if not pfr_teams[LEAGUE_NFL].get(franchiseName):
					pfr_teams[LEAGUE_NFL][franchiseName] = franchise
				else:
					franchise = pfr_teams[LEAGUE_NFL][franchiseName]
					franchise.setdefault("teams", dict())
					for key in info.keys():
						franchise[key] = info[key]

				# Project logo url
				franchiseLogoSrc = "%s%s%s.png" % (PFR_CDN_BASE_URL, PFR_LOGO_BASE_PATH, franchise["abbrev"].lower())
				franchise.setdefault("logo", franchiseLogoSrc)

				# Set up at least the one team in the franchise
				franchise["teams"].setdefault(franchiseName, dict())
				teamMeta = franchise["teams"][franchiseName]
				teamMeta.setdefault("name", franchiseName)
				teamMeta.setdefault("years", [])
				teamMeta.setdefault("active", activeFranchises)

			elif franchise and currentNode.attrs.get("class") and "partial_table" in currentNode.attrs["class"]: # Team
				teamNode = currentNode

				info = get_franchise_team_info(teamNode)
				teamName = info["name"]
				span = {"from": info["from"], "to": info["to"]}

				franchise.setdefault("teams", dict())


				if not franchise["teams"].get(teamName):
					teamMeta = {"name": teamName, "years": []}
					franchise["teams"][teamName] = teamMeta
				else:
					franchise["teams"].setdefault(teamName, dict())
					teamMeta = franchise["teams"][teamName]
					teamMeta["name"] = teamName
					teamMeta.setdefault("years", [])

				if franchise.get("active") and franchise["name"] == teamName: teamMeta["active"] = True
				teamMeta["years"].append(span)

				for i in range(int(info["from"]), int(info["to"])+1):
					# Project team and logo urls
					year = str(i)
					teamLinkHref = "%s%s/%s.htm" % (PFR_TEAMS_INDEX, franchise["abbrev"].lower(), year)
					teamLogoSrc = "%s%s%s-%s.png" % (PFR_CDN_BASE_URL, PFR_LOGO_BASE_PATH, franchise["abbrev"].lower(), year)
					teamMeta.setdefault(year, dict())
					teamMeta[year].setdefault("href", teamLinkHref)
					teamMeta[year].setdefault("logo", teamLogoSrc)

	pass

def __export_nfl_teams(raw = False):
	print("Exporting NFL franchises/teams ...")
	
	outputPath = GetDataPathForLeague(LEAGUE_NFL) if not raw else GetCachesPathForLeague(LEAGUE_NFL)
	EnsureDirectory(outputPath)
	
	fileName = EXPORT_NFL_TEAMS_FILENAME
	path = os.path.join(outputPath, fileName)
	
	obj = pfr_teams[LEAGUE_NFL]
	if not raw: obj = __adapt_nfl_franchises(obj)
	jsonText = json.dumps(obj, default=SerializationDefaults, ensure_ascii=True, sort_keys=True, indent=2)
	
	f = open(path, "w")
	f.write(jsonText)
	f.close()
	
	pass

def __export_nfl_season(year, raw = False):
	if year not in pfr_schedule_weeks[LEAGUE_NFL].keys(): return

	print("Exporting NFL %s season ..." % year)
	
	outputPath = GetDataPathForLeague(LEAGUE_NFL) if not raw else GetCachesPathForLeague(LEAGUE_NFL)
	EnsureDirectory(outputPath)
	
	fileName = EXPORT_NFL_SCHEDULE_FILENAME % year
	path = os.path.join(outputPath, fileName)
	
	obj = pfr_schedule_weeks[LEAGUE_NFL][year]
	if not raw: obj = __adapt_nfl_season(year, obj)
	jsonText = json.dumps(obj, default=SerializationDefaults, ensure_ascii=True, sort_keys=True, indent=2)
	
	f = open(path, "w")
	f.write(jsonText)
	f.close()
	
	pass



def RestoreFromCaches():
	print("Restoring state from cache ...")
	
	nflCachesPath = GetCachesPathForLeague(LEAGUE_NFL)
	
	nflTeamsPath = os.path.join(nflCachesPath, EXPORT_NFL_TEAMS_FILENAME)
	print("    Restoring NFL Teams from cache ...")
	f = open(nflTeamsPath, "r")
	jsonText = f.read()
	f.close()
	pfr_teams[LEAGUE_NFL] = json.loads(jsonText, object_hook=DeserializationDefaults)
	print("    Done restoring NFL Teams.")

	pfr_schedule_weeks.setdefault(LEAGUE_NFL, dict())
	print("    Restoring NFL Schedules from cache ...")
	for y in range(1920, datetime.datetime.utcnow().year + 1):
		year = str(y)
		nflSchedulePath = os.path.join(nflCachesPath, EXPORT_NFL_SCHEDULE_FILENAME % year)
		if os.path.exists(nflSchedulePath):
			print("        Restoring NFL %s Schedule from cache ...")
			f = open(nflSchedulePath, "r")
			jsonText = f.read()
			f.close()
			season = json.loads(jsonText, object_hook=DeserializationDefaults)
			pfr_schedule_weeks[LEAGUE_NFL][year] = season
			print("        Done restoring NFL %s Schedule.")
	print("    Done restoring NFL Schedules.")
	print("Done restoring state.")

	pass

def Export():
	__export_nfl_teams(raw=False)
	for y in range(datetime.datetime.utcnow().year + 1, 1920, -1):
		year = str(y)
		__export_nfl_season(year)

def __adapt_nfl_franchises(franchises):

	def franchise_sort(x, y):
		xActive = x.get("active") == True
		yActive = y.get("active") == True
		if xActive != yActive: return -1 if xActive else 1

		xName = x["name"].upper()
		yName = y["name"].upper()
		cmp = 0 if xName == yName else -1 if xName < yName else 1
		if cmp != 0: return cmp

		return cmp

	output = {"base-url": PFR_BASE_URL,
		   "cdn-base-url": PFR_CDN_BASE_URL,
		   "team-base-path": PFR_TEAMS_INDEX,
		   "logo-base-path": PFR_LOGO_BASE_PATH,
		   "franchises":[]
		   }
	fs = franchises.values()
	fs.sort(cmp=franchise_sort)
	for franchise in fs:
		outFranchise = dict()
		outFranchise["abbrev"] = str(franchise["abbrev"])
		outFranchise["active"] = franchise.get("active") or False
		outFranchise["name"] = str(franchise["name"])
		outFranchise["from"] = int(franchise["from"])
		outFranchise["to"] = int(franchise["to"])
		outFranchise["teams"] = []
		for teamName in franchise["teams"].keys():
			teamMeta = franchise["teams"][teamName]
			outTeam = {"name": str(teamName),
			  "active": teamMeta.get("active") or False,
			  "years": []
			  }
			for span in teamMeta["years"]:
				outTeam["years"].append({"from": int(span["from"]), "to": int(span["to"])})
			outFranchise["teams"].append(outTeam)

		output["franchises"].append(outFranchise)

	return output


def __adapt_nfl_season(year, season):
	
	def sort_by_numeric_key(o):
		return int(o)
	def sort_by_date_and_time(event):
		if not event.get("time"): return event["date"]
		newDate = datetime.datetime.combine(event["date"].date(), event["time"])
		return newDate

	output = dict()
	
	for subseason in season["subseasons"].keys():
		outSubseason = dict()
		subseasonName = "regularseason"

		if subseason == "-1": subseasonName = "preseason"
		if subseason == "1": subseasonName = "playoffs"

		output.setdefault(subseasonName, [])
		weeks = season["subseasons"][subseason].keys()
		weeks.sort(key=sort_by_numeric_key)
		for week in weeks:
			subseasonWeek = season["subseasons"][subseason][week]

			outputSubseasonWeek = {"week": week, "events": []}
			output[subseasonName].append(outputSubseasonWeek)
			if subseasonWeek.get("alias"): outputSubseasonWeek["alias"] = subseasonWeek["alias"]

			events = subseasonWeek["events"].values()
			events.sort(key=sort_by_date_and_time)
			for event in events:
				outputEvent = dict()
				outputEvent["date"] = event["date"]
				if event.get("time"): outputEvent["time"] = event["time"]
				
				homeTeamName = event["homeTeam"]
				awayTeamName = event["awayTeam"]
				(homeFranchise, homeTeam) = __find_nfl_franchise(homeTeamName, year, create_if_not_found=False)
				(awayFranchise, awayTeam) = __find_nfl_franchise(awayTeamName, year, create_if_not_found=False)
				homeFranchiseAbbrev = homeFranchise["abbrev"].upper()
				awayFranchiseAbbrev = awayFranchise["abbrev"].upper()
				outputEvent["teams"] = "%svs%s" % (homeFranchiseAbbrev, awayFranchiseAbbrev)

				if event.get("alias"): outputEvent["alias"] = event["alias"]

				outputSubseasonWeek["events"].append(outputEvent)

	return output


if __name__ == "__main__":
	Scrape()
	
	#RestoreFromCaches()
	Export()
