import json
import re
import threading
import Queue 

from Constants import *
from Hashes import *
from StringUtils import *
from TimeZoneUtils import *
from Vectors import *
from ..Data.ESPNAPIDownloader import *
from ScheduleEvent import *

espnapi_abbreviation_corrections = {
	LEAGUE_NBA: {
		"GS": "GSW",
		"NO": "NOP",
		"NY": "NYK",
		"SA": "SAS",
		"UTAH": "UTA",
		"WSH": "WAS",
		},
	LEAGUE_NFL: {
		"WSH": "WAS",
		}
	}


ESPN_SUBSEASON_FLAG_PRESEASON = 1
ESPN_SUBSEASON_FLAG_REGULAR_SEASON = 2
ESPN_SUBSEASON_FLAG_POSTSEASON = 3
ESPN_SUBSEASON_FLAG_OFFSEASON = 4

espn_subseason_flags_by_league = {
	LEAGUE_MLB: {
		ESPN_SUBSEASON_FLAG_PRESEASON: MLB_SUBSEASON_FLAG_PRESEASON,
		ESPN_SUBSEASON_FLAG_REGULAR_SEASON: MLB_SUBSEASON_FLAG_REGULAR_SEASON,
		ESPN_SUBSEASON_FLAG_POSTSEASON: MLB_SUBSEASON_FLAG_POSTSEASON,
		},
	LEAGUE_NBA: {
		ESPN_SUBSEASON_FLAG_PRESEASON: NBA_SUBSEASON_FLAG_PRESEASON,
		ESPN_SUBSEASON_FLAG_REGULAR_SEASON: NBA_SUBSEASON_FLAG_REGULAR_SEASON,
		ESPN_SUBSEASON_FLAG_POSTSEASON: NBA_SUBSEASON_FLAG_POSTSEASON,
		},
	LEAGUE_NFL: {
		ESPN_SUBSEASON_FLAG_PRESEASON: NFL_SUBSEASON_FLAG_PRESEASON,
		ESPN_SUBSEASON_FLAG_REGULAR_SEASON: NFL_SUBSEASON_FLAG_REGULAR_SEASON,
		ESPN_SUBSEASON_FLAG_POSTSEASON: NFL_SUBSEASON_FLAG_POSTSEASON,
		},
	LEAGUE_NHL: {
		ESPN_SUBSEASON_FLAG_PRESEASON: NHL_SUBSEASON_FLAG_PRESEASON,
		ESPN_SUBSEASON_FLAG_REGULAR_SEASON: NHL_SUBSEASON_FLAG_REGULAR_SEASON,
		ESPN_SUBSEASON_FLAG_POSTSEASON: NHL_SUBSEASON_FLAG_POSTSEASON,
		},
	}


__cached_schedule_dates = dict() # [league][yyyy][mm][dd] = True

def GetSchedule(sched, navigator, sport, league, season):
	# Retrieve data from MLB API

	processing = True

	def monitor():
		while True:	# processing:
			threadpool = []
			while q.unfinished_tasks:	# len(q.queue) > 0:
				date = q.get()
				semaphore.acquire()
				t = threading.Thread(target=process_date, kwargs={"date": date})
				threadpool.append(t)
				t.start()

			if not threadpool: break
			for t in threadpool:
				t.join()


	# Mmmmkay so this is how we gone have to do it:
	#
	# Because ESPN

	def process_date(date):
		try:
			downloadedJson = DownloadScheduleForLeagueAndDate(league, date)
			process_json(downloadedJson)
		finally:
			semaphore.release()
			q.task_done()

	def process_json(downloadedJson):
		if downloadedJson:
			try: espnApiSchedule = json.loads(downloadedJson)
			except ValueError: espnApiSchedule = None

		if espnApiSchedule:

			if espnApiSchedule.get("events"):
				for schedEvent in espnApiSchedule["events"]:

					if schedEvent and schedEvent.get("competitions"):

						seasonType = schedEvent["season"]["type"]
						subseason = __get_subseason(league, seasonType)

						for competition in schedEvent["competitions"]:
				
							id = deunicode(competition["id"])

							# Errant data
							if id in ["170501031", "170429031"] : continue

							date = __hashedDateParse(deunicode(competition["date"]))
							if id in ["250326006"]:
								date = date.replace(tzinfo=EasternTime).astimezone(tz=UTC)
							elif id in ["231030025"]: # 00:30Z, it's actually 00:30 EST
								date = date.replace(tzinfo=JapanStandardTime, month=10, day=30, hour=19).astimezone(tz=UTC)
							elif id in ["231031012"]: # 17:00Z, it's actually 22:00 EST (12:00 JST)
								date = date.replace(tzinfo=JapanStandardTime, month=11, day=1, hour=12).astimezone(tz=UTC)

							title = None
							altTitle = None
							altDescription = None
							for note in competition["notes"]:
								if note.get("type") == "event":
									if not altTitle: altTitle = deunicode(note["headline"])
									elif not title: title = deunicode(note["headline"])
									else: break
							if altTitle == "*": altTitle = None
							elif altTitle == "FINA": altTitle = None
							elif altTitle == "PPD": altTitle = None
							elif altTitle == "IF NECESSARY": altTitle = None
							elif altTitle and unicode(altTitle).isnumeric(): altTitle = None
							elif altTitle and type(date) == datetime.datetime and altTitle.upper() == ("%s%s" % (date.astimezone(tz=EasternTime).strftime("%A, %b. "), date.astimezone(tz=EasternTime).day)).upper(): altTitle = None
							elif altTitle and altTitle.upper().find("HURRICANE IRMA") >= 0:
								altDescription = altTitle[0:]
								altTitle = None
							elif altTitle and altTitle.upper().find("NFL PRESEASON") >= 0:
								altDescription = altTitle[0:]
								altTitle = None

							teams = dict()
							for competitor in competition["competitors"]:
								key = deunicode(competitor["homeAway"])
								teams.setdefault(key, {"fullName": None, "abbrev": None})
								abbrev = deunicode(competitor["team"].get("abbreviation"))
								if league in espnapi_abbreviation_corrections.keys() and abbrev in espnapi_abbreviation_corrections[league].keys():
									abbrev = espnapi_abbreviation_corrections[league][abbrev]
								teams[key]["abbrev"] = abbrev
								teams[key]["fullName"] = deunicode(competitor["team"]["displayName"])

							homeTeamKey = None
							awayTeamKey = None
							homeTeamName = teams["home"]["fullName"]
							awayTeamName = teams["away"]["fullName"]
							homeTeam = navigator.GetTeam(season, homeTeamName, abbreviation=teams["home"]["abbrev"])
							awayTeam = navigator.GetTeam(season, awayTeamName, abbreviation=teams["away"]["abbrev"])
							if homeTeam:
								homeTeamKey = homeTeam.key
								homeTeamName = homeTeam.fullName
							if awayTeam:
								awayTeamKey = awayTeam.key
								awayTeamName = awayTeam.fullName


							(xsubseason, playoffRound, eventIndicator, xaltTitle) = __get_playoffRound(league, subseason, title, altTitle, competition)
							if xaltTitle and xaltTitle != altTitle: altTitle = xaltTitle

							gameNumber = None
							if altTitle:
								foundGame = False
								for expr in [r"(?:^|\b)(?:Game\s+(?P<game_number>\d+))(?:\b|$)"]:
									if foundGame: break
									m = re.search(expr, altTitle, re.IGNORECASE)
									if m:
										gameNumber = int(m.group("game_number"))
										foundGame = True
										break

							ysubseason = None
							week = None
							if league == LEAGUE_NFL:
								(ysubseason, week) = __get_nfl_week(league, date, seasonType, calendar)
							if ysubseason != None and ysubseason != xsubseason: xsubseason = ysubseason

							if not gameNumber and \
								id not in ["400899377"] and \
								league in [LEAGUE_MLB, LEAGUE_NBA, LEAGUE_NHL]:
								if competition.get("series") and competition["series"].get("type") == "playoff":
									if not xsubseason:
										if league == LEAGUE_MLB:
											xsubseason = MLB_SUBSEASON_FLAG_POSTSEASON
										elif league == LEAGUE_NBA:
											xsubseason = NBA_SUBSEASON_FLAG_POSTSEASON
										elif league == LEAGUE_NHL:
											xsubseason = NHL_SUBSEASON_FLAG_POSTSEASON
									seriesSummary = competition["series"]["summary"]
									mss = re.search(r"(?:^|\b)(?P<wins>\d+)\s*[\-]\s*(?P<losses>\d+)(?:\b|$)", seriesSummary, re.IGNORECASE)
									if mss:
										gameNumber = int(mss.group("wins")) + int(mss.group("losses"))



							description = None
							if competition.get("headlines"):
								for headline in competition["headlines"]:
									if headline["type"] == "Recap":
										if headline.get("description"):
											description = deunicode(normalize(headline["description"]))
										elif headline.get("shortLinkText"):
											description = deunicode(normalize(headline["shortLinkText"]))
										# TODO Date strings as headlines
							while description and description[:1] == '\u2014': description = description[1:]
							while description and description[:3] == "\xe2\x80\x94": description = description[3:]
							if description: description = description.strip()

							networks = []
							if competition.get("broadcasts"):
								for broadcast in competition["broadcasts"]:
									networks += broadcast["names"]

							kwargs = {
								"sport": sport,
								"league": league,
								"season": season,
								"date": date,
								"ESPNAPIID": id,
								"eventTitle": title,
								"altTitle": altTitle,
								"description": description,
								"altDescription": altDescription,
								"homeTeam": homeTeamKey,
								"homeTeamName": homeTeamName if not homeTeamKey else None,
								"awayTeam": awayTeamKey,
								"awayTeamName": awayTeamName if not awayTeamKey else None,
								"subseason": xsubseason,
								"week": week,
								"playoffround": playoffRound,
								"eventindicator": eventIndicator,
								"game": gameNumber,
								"networks": networks,
								"vs": "%s vs. %s" % (homeTeamName, awayTeamName)
								}

							event = ScheduleEvent(**kwargs)
							if gameNumber != None and event.game == None: print("FAILED TO SET GAME FROM '%s'" % altTitle)

							event = AddOrAugmentEvent(sched, event)
							if gameNumber != None and event.game == None: print("FAILED TO SET GAME FROM '%s'" % altTitle)
	




	q = Queue.Queue()
	semaphore = threading.BoundedSemaphore(value = 25)




	datesToProcess = []
	calendarsToProcess = []


	# Verify Calendar matches season requested
	year = int(season)

	calendar = __process_calendar(league, season)
	if calendar:
	#	shouldIncrementYear = False
	#	if calendar["dates"] and calendar["dates"][0].year < year:
	#		shouldIncrementYear = True
	#	elif calendar.get("startDate") and calendar["startDate"].year < year:
	#		shouldIncrementYear = True

	#	if shouldIncrementYear:
	#		xyear += 1
	#		calendar = __process_calendar(league, str(xyear), True)

		calendarsToProcess.append(calendar)



	for calendar in calendarsToProcess:
		if calendar and calendar["dates"]:
			for date in calendar["dates"]:
				datesToProcess.append(date)


	monitorThread = threading.Thread(target=monitor)
	monitorThread.daemon = True
	monitorThread.start()


	now = datetime.datetime.utcnow().date()
	for date in sorted(set(datesToProcess)):
		if date > now: continue
		q.put(date)

	q.join()


	__calendar_parse_hashes.clear()
	__calendar_label_hashes.clear()

	pass






def __process_calendar(league, season, isWhitelist = False):

	def project_dates(obj):
		dates = []
		startDate = obj.get("startDate")
		endDate = obj.get("endDate")

		if startDate and endDate:
			startDate = startDate.astimezone(tz=EasternTime).date()
			endDate = endDate.astimezone(tz=EasternTime).date()

			if endDate < startDate:
				x = startDate
				startDate = endDate
				endDate = x

			current = startDate
			while current <= endDate:
				dates.append(current)
				current = current + datetime.timedelta(days=1)
		
		dates = list(sorted(set(dates)))
		return dates



	apiScores = None
	calendarJson = DownloadCalendarForLeagueAndSeason(league, season, isWhitelist)
	if calendarJson:
		try: apiScores = json.loads(calendarJson)
		except ValueError: apiScores = None

	apiLeague = {}
	apiCalendar = []
	apiCalendarObj = None
	if apiScores and apiScores.get("leagues"):
		apiLeague = apiScores["leagues"][0]
		apiCalendar = apiLeague.get("calendar") or []
		if apiCalendar: apiCalendarObj = apiCalendar[0]

	calendar = {
		"subseasons": [],
		"dates": [],
		"startDate": ParseISO8601Date(apiLeague["calendarStartDate"]) if apiLeague.get("calendarStartDate") else None,
		"endDate": ParseISO8601Date(apiLeague["calendarEndDate"]) if apiLeague.get("calendarEndDate") else None,
		}

	#apiLeague["calendarType]: 'list'/'day'
	if apiLeague.get("calendarIsWhitelist") == False and apiLeague.get("calendarType") == "day":
		dates = project_dates(calendar)
		blacklist = []
		for x in apiCalendar:
			blacklist.append(ParseISO8601Date(x).date())
		if blacklist:
			bl = list(sorted(set(blacklist)))
			for i in range(len(dates)-1, -1, -1):
				if not bl: break
				if dates[i] == bl[-1]:
					del(dates[i])
					del(bl[-1])

		calendar["dates"] = dates
	else:

		for x in apiCalendar:

			# x could be a date string
			if isinstance(x, basestring):
				calendar["dates"].append(ParseISO8601Date(x).date())
				continue

			apiSubseasonObj = x
			if apiSubseasonObj.get("label") == "Off Season": continue

			subseasonObj = dict()
			subseasonObj["label"] = deunicode(apiSubseasonObj["label"])
			subseasonObj["value"] = int(apiSubseasonObj["value"])
			subseasonObj["startDate"] = ParseISO8601Date(apiSubseasonObj["startDate"])
			subseasonObj["endDate"] = ParseISO8601Date(apiSubseasonObj["endDate"])

			dates = []
			entries = []
			subseasonObj["entries"] = entries
			if apiSubseasonObj.get("entries"):
				for apiEntry in apiSubseasonObj["entries"]:
					entry = dict()

					# Careful here. It looked like MLB was doin somethin DIFFERENT with entries
					if isinstance(apiEntry, basestring):
						entry["label"] = deunicode(apiEntry)
						dates += project_dates(subseasonObj)
					else:
						entry["label"] = deunicode(apiEntry["label"])
						entry["alternateLabel"] = deunicode(apiEntry["alternateLabel"])
						entry["value"] = apiEntry["value"]
						if apiEntry.get("startDate"): entry["startDate"] = ParseISO8601Date(apiEntry["startDate"])
						if apiEntry.get("endDate"): entry["endDate"] = ParseISO8601Date(apiEntry["endDate"])

						dates += project_dates(entry)

					entries.append(entry)

			dates = list(set(dates))
			subseasonObj["dates"] = sorted(dates)
			calendar["dates"] = calendar["dates"] + dates
			calendar["subseasons"].append(subseasonObj)


	if not calendar["dates"]:
		calendar["dates"] = project_dates(calendar)

	calendar["dates"] = list(sorted(set(calendar["dates"])))
	# TODO: if today in range, Project dates from greatest date prior to today, up to and including today (account for august gaps in MLB)

	return calendar




















def __get_subseason(league, seasonType):
	subseason = None
	if league in espn_subseason_flags_by_league.keys():
		subseason = espn_subseason_flags_by_league[league].get(seasonType)
	return subseason

def __get_playoffRound(league, subseason, title, altTitle, competition):
	"""League-specific analysis."""
	
	playoffRound = None
	eventIndicator = None

	subseason = subseason or 0
	title = title or ""
	altTitle = altTitle or ""
	typeAbbrev = competition["type"]["abbreviation"] if competition.get("type") and competition["type"].get("abbreviation") else None
	
	if league == LEAGUE_MLB and subseason == MLB_SUBSEASON_FLAG_POSTSEASON:
		pass # TODO
	elif league == LEAGUE_NBA:
		if subseason == NBA_SUBSEASON_FLAG_POSTSEASON:
			if typeAbbrev == "FINAL":
				subseason = NBA_SUBSEASON_FLAG_POSTSEASON
				playoffRound = NBA_PLAYOFF_ROUND_FINALS
			elif typeAbbrev == "SEMI":
				subseason = NBA_SUBSEASON_FLAG_POSTSEASON
				playoffRound = NBA_PLAYOFF_ROUND_SEMIFINALS
			elif typeAbbrev == "QTR":
				subseason = NBA_SUBSEASON_FLAG_POSTSEASON
				playoffRound = NBA_PLAYOFF_ROUND_QUARTERFINALS
			elif typeAbbrev == "RD16":
				subseason = NBA_SUBSEASON_FLAG_POSTSEASON
				playoffRound = NBA_PLAYOFF_1ST_ROUND
		elif subseason == NBA_SUBSEASON_FLAG_REGULAR_SEASON:
			if altTitle and altTitle.upper().find("ALL-STAR GAME") >= 0:
				eventIndicator = NBA_EVENT_FLAG_ALL_STAR_GAME
			elif competition["type"]["id"] == 4 or competition["type"].get("abbreviation") == "ALLSTAR":
				eventIndicator = NBA_EVENT_FLAG_ALL_STAR_GAME
			elif altTitle and altTitle.upper() == "RISING STARS":
				eventIndicator = NBA_EVENT_FLAG_RISING_STARS_GAME
	elif league == LEAGUE_NFL:
		if indexOf(altTitle.lower(), "hall of fame") >= 0:
			subseason = NFL_SUBSEASON_FLAG_PRESEASON
			eventIndicator = NFL_EVENT_FLAG_HALL_OF_FAME

		elif indexOf(altTitle.lower(), "wild card") >= 0 or indexOf(altTitle.lower(), "wildcard") >= 0 or typeAbbrev == "RD16":
			subseason = NFL_SUBSEASON_FLAG_POSTSEASON
			playoffRound = NFL_PLAYOFF_ROUND_WILDCARD

		elif indexOf(altTitle.lower(), "division") >= 0 or typeAbbrev == "QTR":
			subseason = NFL_SUBSEASON_FLAG_POSTSEASON
			playoffRound = NFL_PLAYOFF_ROUND_DIVISION

		elif indexOf(altTitle.lower(), "championship") >= 0 or indexOf(altTitle.lower(), "conference") >= 0 or typeAbbrev == "SEMI":
			subseason = NFL_SUBSEASON_FLAG_POSTSEASON
			playoffRound = NFL_PLAYOFF_ROUND_CHAMPIONSHIP

		elif indexOf(altTitle.lower(), "super") >= 0 or typeAbbrev == "FINAL":
			subseason = NFL_SUBSEASON_FLAG_POSTSEASON
			playoffRound = NFL_PLAYOFF_ROUND_SUPERBOWL
			eventIndicator = NFL_EVENT_FLAG_SUPERBOWL
			altTitle = altTitle.upper().replace("SUPER BOWL", "SUPERBOWL")

		elif indexOf(altTitle.lower(), "pro bowl") >= 0 or typeAbbrev == "ALLSTAR":
			eventIndicator = NFL_EVENT_FLAG_PRO_BOWL


	elif league == LEAGUE_NHL:
		if subseason == NHL_SUBSEASON_FLAG_POSTSEASON:
			if indexOf(altTitle.lower(), "1st round") >= 0:
				subseason = NHL_SUBSEASON_FLAG_POSTSEASON
				playoffRound = NHL_PLAYOFF_ROUND_1
			elif indexOf(altTitle.lower(), "2nd round") >= 0:
				subseason = NHL_SUBSEASON_FLAG_POSTSEASON
				playoffRound = NHL_PLAYOFF_ROUND_2
			elif indexOf(altTitle.lower(), "stanley cup final") >= 0:
				subseason = NHL_SUBSEASON_FLAG_POSTSEASON
				playoffRound = NHL_PLAYOFF_ROUND_3
			elif indexOf(altTitle.lower(), " finals") >= 0:
				subseason = NHL_SUBSEASON_FLAG_POSTSEASON
				playoffRound = NHL_PLAYOFF_ROUND_3
		else:
			if altTitle and altTitle.find("ALL-STAR") >= 0:
				if altTitle.find("SEMIFINAL") >= 0:
					eventIndicator = NHL_EVENT_FLAG_ALL_STAR_SEMIFINAL
				elif altTitle.find("FINAL") >= 0:
					eventIndicator = NHL_EVENT_FLAG_ALL_STAR_GAME
				else:
					eventIndicator = NHL_EVENT_FLAG_ALL_STAR_GAME
			elif competition.get("type") and competition["type"].get("id") == "4":
				eventIndicator = NHL_EVENT_FLAG_ALL_STAR_GAME

	return (subseason, playoffRound, eventIndicator, altTitle)


__nfl_week_title_expr = re.compile(r"(?P<preseason>(?:Preseason)\s)?Week\s(?P<week>\d+)", re.IGNORECASE)
__calendar_parse_hashes = dict() # [dateStr] = date()
__calendar_label_hashes = dict() # [label] = (subseason, week)
def __hashedDateParse(str):
	if str in __calendar_parse_hashes.keys():
		return __calendar_parse_hashes[str]

	# Time-aware in zulu time
	date = ParseISO8601Date(str)
	if date: date = date.astimezone(tz=UTC)

	if date.time() == datetime.time(5,0,0):
		date = date.date()

	__calendar_parse_hashes[str] = date
	return date

def __get_nfl_week(league, date, seasonType, calendar):

	subseason = None
	week = None

	if calendar.get("subseasons"):
		for subseasonObj in calendar["subseasons"]:
			xseasonType = int(subseasonObj["value"])
			if subseasonObj.get("entries"):
				for entry in subseasonObj["entries"]:
					fromDate = entry["startDate"]
					toDate = entry["endDate"]
					if __is_date_in_range(date, fromDate, toDate):
						weekStr = deunicode(entry["label"])
						key = weekStr.lower()
						if key in __calendar_label_hashes.keys():
							subseason = __calendar_label_hashes[key][0]
							week = __calendar_label_hashes[key][1]
						else:
							m = __nfl_week_title_expr.match(weekStr)
							if not m:
								__calendar_label_hashes.setdefault(key, (subseason, None))
								__calendar_label_hashes[key] = (__calendar_label_hashes[key][0], None)
							else:
								gd = m.groupdict()
								week = int(m.group("week"))
								subseason = __get_subseason(league, xseasonType)
								__calendar_label_hashes[key] = (subseason, week)

	return (subseason, week)



def __is_date_in_range(date, fromDate, toDate):
	"""Does specified date lie betwen the ends of a given date range?"""
	
	x = date
	if type(date) == datetime.date:
		x = datetime.datetime(date.year, date.month, date.day, tzinfo=UTC)
	
	# toDate is up-to-the-minute (inclusive)
	return x >= fromDate and x <= toDate