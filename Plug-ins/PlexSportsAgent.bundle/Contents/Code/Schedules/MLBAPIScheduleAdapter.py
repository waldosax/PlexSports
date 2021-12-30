import re, unicodedata
import json

from Constants import *
from Hashes import *
from StringUtils import *
from TimeZoneUtils import *
from Vectors import *
from ..Data.MLB.MLBAPIDownloader import *
from ScheduleEvent import *



MLBAPI_GAMETYPE_SPRING_TRAINING = "S"
MLBAPI_GAMETYPE_REGULAR_SEASON = "R"
MLBAPI_GAMETYPE_WILDCARD_GAME = "F"
MLBAPI_GAMETYPE_DIVISION_SERIES = "D"
MLBAPI_GAMETYPE_LEAGUE_CHAMPIONSHIP_SERIES = "L"
MLBAPI_GAMETYPE_WORLD_SERIES = "W"
MLBAPI_GAMETYPE_CHAMPIONSHIP = "C"
MLBAPI_GAMETYPE_ALL_STAR_GAME = "A"


def GetSchedule(sched, navigator, sport, league, season):
	# Retrieve data from MLB API
	downloadedJson = DownloadScheduleForSeason(season)
	
	if downloadedJson:
		try: mlbApiSchedule = json.loads(downloadedJson)
		except ValueError: pass

	if mlbApiSchedule and mlbApiSchedule.get("dates"):
		for eventDate in mlbApiSchedule["dates"]:
			dateGroup = eventDate["date"]
			for schedEvent in eventDate["games"]:
				id = schedEvent["gamePk"]

				date = None
				if schedEvent.get("gameDate"):
					date = ParseISO8601Date(schedEvent["gameDate"])
					# Zulu Time
					date = date.replace(tzinfo=UTC)
				elif schedEvent.get("officialDate"):
					date = ParseISO8601Date(schedEvent["officialDate"])
				else:
					date = ParseISO8601Date(dateGroup)

				# Teams from this API are full names
				homeTeamName = deunicode(schedEvent["teams"]["home"]["team"]["name"])
				awayTeamName = deunicode(schedEvent["teams"]["away"]["team"]["name"])

				homeTeam = navigator.GetTeam(season, homeTeamName)
				awayTeam = navigator.GetTeam(season, awayTeamName)

				homeTeamKey = homeTeam.key if homeTeam else None
				awayTeamKey = awayTeam.key if awayTeam else None

				subseason = None
				playoffRound = None
				eventIndicator = None
				gameNumber = None
	
				gameType = schedEvent["gameType"]
				title = deunicode(schedEvent.get("description"))
				altDescription = None
				if gameType == MLBAPI_GAMETYPE_SPRING_TRAINING: subseason = MLB_SUBSEASON_FLAG_PRESEASON
				elif gameType == MLBAPI_GAMETYPE_REGULAR_SEASON: subseason = MLB_SUBSEASON_FLAG_REGULAR_SEASON
				elif gameType in [MLBAPI_GAMETYPE_WILDCARD_GAME, MLBAPI_GAMETYPE_DIVISION_SERIES, MLBAPI_GAMETYPE_LEAGUE_CHAMPIONSHIP_SERIES, MLBAPI_GAMETYPE_WORLD_SERIES]:
					subseason = MLB_SUBSEASON_FLAG_POSTSEASON
					if gameType == MLBAPI_GAMETYPE_WILDCARD_GAME: playoffRound = MLB_PLAYOFF_ROUND_WILDCARD
					elif gameType == MLBAPI_GAMETYPE_DIVISION_SERIES: playoffRound = MLB_PLAYOFF_ROUND_DIVISION
					elif gameType == MLBAPI_GAMETYPE_LEAGUE_CHAMPIONSHIP_SERIES: playoffRound = MLB_PLAYOFF_ROUND_CHAMPIONSHIP
					elif gameType == MLBAPI_GAMETYPE_WORLD_SERIES:
						playoffRound = MLB_PLAYOFF_ROUND_WORLD_SERIES
					# TODO: MLBAPI_GAMETYPE_CHAMPIONSHIP?
				elif gameType == MLBAPI_GAMETYPE_ALL_STAR_GAME:
					eventIndicator = MLB_EVENT_FLAG_ALL_STAR_GAME
				elif gameType == MLBAPI_GAMETYPE_ALL_STAR_GAME:
					eventIndicator = MLB_EVENT_FLAG_ALL_STAR_GAME

				if schedEvent.get("doubleHeader") == "Y":
					gameNumber = schedEvent["gameNumber"]
				
				if title and title.find("Hall of Fame Game") >= 0:
					eventIndicator = MLB_EVENT_FLAG_HALL_OF_FAME

				if title and title == "Night":
					title = None
				elif title and title.upper().find("ALL-STAR") >= 0:
					pass
				elif title and title.upper().find("D-BACK") >= 0:
					pass
				elif title and title.upper().find("SINGLE-GAME") >= 0:
					pass
				elif title and title.upper().find("OLD-TIMER") >= 0:
					pass
				elif title and title.upper().find("MAKE-UP") >= 0:
					pass
				elif title and title.upper().find("DAY-NIGHT") >= 0:
					pass
				elif title:
					m = re.search(ur"(?:(?:\([\w]+\s*(?:[\-])\s*[\w]+\))|(?:\s*[\-]\s*))", title.replace(unichr(0x0096), "-"), re.IGNORECASE)
					if m:
						altDescription = title[m.end():].strip(", ")
						title = title[:m.start()].strip(", ")
				
				if not gameNumber and title and subseason == MLB_SUBSEASON_FLAG_POSTSEASON:
					for expr in game_number_expressions:
						m = re.search(expr, title, re.IGNORECASE)
						if m:
							gameNumber = int(m.group("game_number"))
							title = (m.string[:m.start()] + m.string[m.end():]).strip(", ")
							break

				subseasonTitle = deunicode(schedEvent.get("seriesDescription"))
				if subseasonTitle == "Regular Season": subseasonTitle = None

				description = None
				thumbnail = None
				if int(season) >= 2021 and schedEvent.get("content") and schedEvent["content"].get("link"):
					contentJson = DownloadGameContentData(id)
					if contentJson:
						try: content = json.loads(contentJson)
						except ValueError: pass
						(description, thumbnail) = __process_content(schedEvent, content)


				kwargs = {
					"sport": sport,
					"league": league,
					"season": season,
					"date": date,
					"MLBAPIID": str(id),
					"title": title,
					"subseasonTitle": subseasonTitle,
					"altDescription": altDescription,
					"description": description,
					"homeTeam": homeTeamKey,
					"homeTeamName": homeTeamName if not homeTeamKey else None,
					"awayTeam": awayTeamKey,
					"awayTeamName": awayTeamName if not awayTeamKey else None,
					"vs": "%s vs. %s" % (homeTeamName, awayTeamName),
					"subseason": subseason,
					"playoffround": playoffRound,
					"eventindicator": eventIndicator,
					"game": gameNumber}

				assets = {}

				if thumbnail:
					assets["thumbnail"] = [{"source": ASSET_SOURCE_MLBAPI, "url": deunicode(thumbnail)}]

				if assets:
					kwargs["assets"] = assets

				event = ScheduleEvent(**kwargs)

				AddOrAugmentEvent(sched, event)


def __process_content(schedEvent, content):
	description = None
	thumbnail = None

	if not content: return (None, None)

	if content.get("editorial"):
		if content["editorial"].get("recap"):
			if content["editorial"]["recap"].get("mlb"):
				mlbRecap = content["editorial"]["recap"]["mlb"]
				
				if not description: description = mlbRecap.get("blurb")
				if not description: description = mlbRecap.get("headline")
				if not description: description = mlbRecap.get("seoTitle")
	pass

	if content.get("highlights"):
		if content["highlights"].get("highlights"):
			if content["highlights"]["highlights"].get("items"):
				highlightItems = content["highlights"]["highlights"]["items"]
				for highlightItem in highlightItems:
				
					if not description: description = highlightItem.get("description")
					if not description: description = highlightItem.get("blurb")
					if description: break
	pass
	
	cuts = []
	if content.get("editorial"):
		if content["editorial"].get("recap"):
			if content["editorial"]["recap"].get("mlb"):
				mlbRecap = content["editorial"]["recap"]["mlb"]
				if not thumbnail and mlbRecap.get("photo"):
					cuts = mlbRecap["photo"]["cuts"]
					bestCut = __select_best_cut(cuts)
					if bestCut: thumbnail = bestCut["src"]
				if not thumbnail and mlbRecap.get("image"):
					cuts = mlbRecap["image"]["cuts"]
					bestCut = __select_best_cut(cuts)
					if bestCut: thumbnail = bestCut["src"]
	pass

	if content.get("highlights"):
		if content["highlights"].get("highlights"):
			if content["highlights"]["highlights"].get("items"):
				highlightItems = content["highlights"]["highlights"]["items"]
				for highlightItem in highlightItems:
				
					if not thumbnail and highlightItem.get("photo"):
						cuts = highlightItem["photo"]["cuts"]
						bestCut = __select_best_cut(cuts)
						if bestCut: thumbnail = bestCut["src"]
					if not thumbnail and highlightItem.get("image"):
						cuts = highlightItem["image"]["cuts"]
						bestCut = __select_best_cut(cuts)
						if bestCut: thumbnail = bestCut["src"]
	pass


	return (description, thumbnail)

def __select_best_cut(cuts):
	
	__ranked_ratios = {
		"16:9": 4,
		"4:3": 3,
		"64:27": 2,
		}

	def __get_sortable_event_key(cut):	# ratio, pixels
		key = ""

		aspectRatio = cut["aspectRatio"]
		key = key + ("%d2" % (__ranked_ratios[aspectRatio] if __ranked_ratios.get(aspectRatio) else 0))
		width = cut["width"]
		height = cut["height"]
		pixels = width * height
		key = key + "%d8" % (pixels)

		return key

	for cut in sorted(cuts, key=__get_sortable_event_key):
		return cut

	return None