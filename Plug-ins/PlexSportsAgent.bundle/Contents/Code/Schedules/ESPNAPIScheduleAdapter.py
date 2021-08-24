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

def GetSchedule(sched, teamKeys, teams, sport, league, season):
	# Retrieve data from MLB API

	processing = True

	def monitor():
		threadpool = []
		#while processing:
		while len(q.queue) > 0:
			date = q.get()
			semaphore.acquire()
			t = threading.Thread(target=process_date, kwargs={"date": date})
			threadpool.append(t)
			t.start()

		for t in threadpool:
			t.join()

		threadpool = []


	# Mmmmkay so this is how we gone have to do it:
	#
	# Because ESPN

	def process_date(date):
		try:
			downloadedJson = DownloadScheduleForLeagueAndDate(league, date)
			process_json(downloadedJson)
		finally:
			semaphore.release()

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
				
							id = competition["id"]
							date = __hashedDateParse(deunicode(competition["date"]))

							title = None
							altTitle = None
							for note in competition["notes"]:
								if note.get("type") == "event":
									if not title: title = deunicode(note["headline"])
									#elif not altTitle: altTitle = deunicode(note["headline"])
									else: break

							teams = dict()
							for competitor in competition["competitors"]:
								key = deunicode(competitor["homeAway"])
								teams[key] = deunicode(competitor["team"]["abbreviation"])
							homeTeamKey = teams["home"]
							awayTeamKey = teams["away"]


							(xsubseason, playoffRound, eventIndicator, xtitle) = __get_playoffRound(league, subseason, title, competition)
							if xtitle != None and xtitle != title: title = xtitle
							# TODO: Normalize title (Title Case)

							gameNumber = None

							ysubseason = None
							week = None
							if league == LEAGUE_NFL:
								(ysubseason, week) = __get_nfl_week(league, date, seasonType, calendar)
							if ysubseason != None and ysubseason != xsubseason: xsubseason = ysubseason


							description = None
							if competition.get("headlines"):
								for headline in competition["headlines"]:
									if headline["type"] == "Recap":
										description = deunicode(normalize(headline["description"]))
										# TODO Date strings as headlines

							# TODO: network?

							kwargs = {
								"sport": sport,
								"league": league,
								"season": season,
								"date": date,
								"ESPNAPIID": id,
								"eventTitle": title,
								#"altTitle": altTitle,
								"description": description,
								"homeTeam": homeTeamKey,
								"awayTeam": awayTeamKey,
								"subseason": xsubseason,
								"week": week,
								"playoffround": playoffRound,
								"eventindicator": eventIndicator,
								} # We'll see how ESPN handles double-headers
								#"game": gameNumber}

							event = ScheduleEvent(**kwargs)

							AddOrAugmentEvent(sched, event)
	




	q = Queue.Queue()
	semaphore = threading.BoundedSemaphore(value = 25)




	datesToProcess = []
	calendarsToProcess = []


	# Verify Calendar matches season requested
	year = int(season)
	xyear = int(season)
	if league in year_boundary_leagues:
		xyear += 1
	calendar = __process_calendar(league, str(xyear))
	if calendar:
		shouldIncrementYear = False
		if calendar["dates"] and calendar["dates"][0].year < year:
			shouldIncrementYear = True
		elif calendar.get("startDate") and calendar["startDate"].year < year:
			shouldIncrementYear = True

		if shouldIncrementYear:
			xyear += 1
			calendar = __process_calendar(league, str(xyear))

		calendarsToProcess.append(calendar)
		whitelist = __process_calendar(league, str(xyear), True)
		if whitelist:
			calendarsToProcess.append(whitelist)



	for calendar in calendarsToProcess:
		if calendar and calendar["dates"]:
			for date in calendar["dates"]:
				datesToProcess.append(date)

	now = datetime.datetime.utcnow().date()
	for date in sorted(set(datesToProcess)):
		if date > now: continue
		q.put(date)



	monitor()
	processing = False

	#monitorThread = threading.Thread(target=monitor)
	#monitorThread.start()
	#monitorThread.join()


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

	apiCalendar = []
	apiCalendarObj = None
	if apiScores and apiScores.get("leagues"):
		apiLeague= apiScores["leagues"][0]
		apiCalendar = apiLeague.get("calendar") or []
		if apiCalendar: apiCalendarObj = apiCalendar[0]

	calendar = {
		"subseasons": [],
		"dates": [],
		"startDate": ParseISO8601Date(apiLeague["calendarStartDate"]) if apiLeague.get("calendarStartDate") else None,
		"endDate": ParseISO8601Date(apiLeague["calendarEndDate"]) if apiLeague.get("calendarEndDate") else None,
		}

	for x in apiCalendar:

		# x could be a date string
		if isinstance(x, basestring):
			calendar["dates"].append(ParseISO8601Date(x).date())
			continue

		apiSubseasonObj = x
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

def __get_playoffRound(league, subseason, title, competition):
	"""League-specific analysis."""
	
	playoffRound = None
	eventIndicator = None

	subseason = subseason or 0
	title = title or ""
	typeAbbrev = competition["type"]["abbreviation"]
	
	if league == LEAGUE_MLB and subseason == MLB_SUBSEASON_FLAG_POSTSEASON:
		pass # TODO
	elif league == LEAGUE_NBA and subseason == NBA_SUBSEASON_FLAG_POSTSEASON:
		if typeAbbrev == "FINAL":
			subseason = NBA_SUBSEASON_FLAG_POSTSEASON
			playoffRound = NBA_PLAYOFF_ROUND_FINALS
		elif typeAbbrev == "SEMI":
			subseason = NBA_SUBSEASON_FLAG_POSTSEASON
			playoffRound = NBA_PLAYOFF_ROUND_SEMIFINALS
		elif typeAbbrev == "QTR":
			subseason = NBA_SUBSEASON_FLAG_POSTSEASON
			playoffRound = NBA_PLAYOFF_ROUND_QUARTERFINALS
	elif league == LEAGUE_NFL:
		if indexOf(title.lower(), "hall of fame") >= 0:
			subseason = NFL_SUBSEASON_FLAG_PRESEASON
			eventIndicator = NFL_EVENT_FLAG_HALL_OF_FAME

		elif indexOf(title.lower(), "wild card") >= 0 or indexOf(title.lower(), "wildcard") >= 0 or typeAbbrev == "RD16":
			subseason = NFL_SUBSEASON_FLAG_POSTSEASON
			playoffRound = NFL_PLAYOFF_ROUND_WILDCARD

		elif indexOf(title.lower(), "division") >= 0 or typeAbbrev == "QTR":
			subseason = NFL_SUBSEASON_FLAG_POSTSEASON
			playoffRound = NFL_PLAYOFF_ROUND_DIVISION

		elif indexOf(title.lower(), "championship") >= 0 or indexOf(title.lower(), "conference") >= 0 or typeAbbrev == "SEMI":
			subseason = NFL_SUBSEASON_FLAG_POSTSEASON
			playoffRound = NFL_PLAYOFF_ROUND_CHAMPIONSHIP

		elif indexOf(title.lower(), "super") >= 0 or typeAbbrev == "FINAL":
			subseason = NFL_SUBSEASON_FLAG_POSTSEASON
			playoffRound = NFL_PLAYOFF_ROUND_SUPERBOWL
			eventIndicator = NFL_EVENT_FLAG_SUPERBOWL

		elif indexOf(title.lower(), "pro bowl") >= 0 or typeAbbrev == "ALLSTAR":
			eventIndicator = NFL_EVENT_FLAG_PRO_BOWL

		else:
			# TODO: Only week out if date string
			title = ""

	elif league == LEAGUE_NHL and subseason == NHL_SUBSEASON_FLAG_POSTSEASON:
		if indexOf(title.lower(), "1st round") >= 0:
			subseason = NHL_SUBSEASON_FLAG_POSTSEASON
			playoffRound = NHL_PLAYOFF_ROUND_1
		elif indexOf(title.lower(), "2nd round") >= 0:
			subseason = NHL_SUBSEASON_FLAG_POSTSEASON
			playoffRound = NHL_PLAYOFF_ROUND_2
		elif indexOf(title.lower(), "stanley cup final") >= 0:
			subseason = NHL_SUBSEASON_FLAG_POSTSEASON
			playoffRound = NHL_PLAYOFF_ROUND_3
		elif indexOf(title.lower(), " finals") >= 0:
			subseason = NHL_SUBSEASON_FLAG_POSTSEASON
			playoffRound = NHL_PLAYOFF_ROUND_3


	return (subseason, playoffRound, eventIndicator, title)


__nfl_week_title_expr = re.compile(r"(?P<preseason>(?:Preseason)\s)?Week\s(?P<week>\d+)", re.IGNORECASE)
__calendar_parse_hashes = dict() # [dateStr] = date()
__calendar_label_hashes = dict() # [label] = (subseason, week)
def __hashedDateParse(str):
	if str in __calendar_parse_hashes.keys():
		return __calendar_parse_hashes[str]

	# Date-aware in zulu time
	date = ParseISO8601Date(str)
	if date: date = date.astimezone(tz=UTC)
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
	
	# toDate is up-to-the-minute (inclusive)
	return date >= fromDate and date <= toDate