import json

from Constants import *
from Hashes import *
from StringUtils import *
from TimeZoneUtils import *
from Vectors import *
from ..Data.MLB.MLBAPI import *
from ScheduleEvent import *



MLBAPI_GAMETYPE_SPRING_TRAINING = "S"
MLBAPI_GAMETYPE_REGULAR_SEASON = "R"
MLBAPI_GAMETYPE_WILDCARD_GAME = "F"
MLBAPI_GAMETYPE_DIVISION_SERIES = "D"
MLBAPI_GAMETYPE_LEAGUE_CHAMPIONSHIP_SERIES = "L"
MLBAPI_GAMETYPE_WORLD_SERIES = "W"
MLBAPI_GAMETYPE_CHAMPIONSHIP = "C"
MLBAPI_GAMETYPE_ALL_STAR_GAME = "A"


def GetSchedule(sched, teamKeys, teams, sport, league, season):
	# Retrieve data from MLB API
	downloadedJson = DownloadScheduleForSeason(season)
	
	if downloadedJson:
		try: mlbApiSchedule = json.loads(downloadedJson)
		except ValueError: pass

	if mlbApiSchedule and mlbApiSchedule.get("dates"):
		for eventDate in mlbApiSchedule["dates"]:
			dateGroup = eventDate["date"]
			for schedEvent in eventDate["games"]:
		
				date = None
				if schedEvent.get("gameDate"):
					date = ParseISO8601Date(schedEvent["gameDate"])
					# Zulu Time
					date = date.replace(tzinfo=UTC)
				elif schedEvent.get("officialDate"):
					date = ParseISO8601Date(schedEvent["officialDate"])
				else:
					date = ParseISO8601Date(dateGroup)

				# Teams from this API are full names, so teams dictionary is scanKeys
				homeTeamStripped = create_scannable_key(schedEvent["teams"]["home"]["team"]["name"])
				awayTeamStripped = create_scannable_key(schedEvent["teams"]["away"]["team"]["name"])
				homeTeamKey = teamKeys[homeTeamStripped] if teamKeys.get(homeTeamStripped) else homeTeamStripped
				awayTeamKey = teamKeys[awayTeamStripped] if teamKeys.get(awayTeamStripped) else awayTeamStripped

				subseason = None
				playoffRound = None
				eventIndicator = None
				gameNumber = None
	
				gameType = schedEvent["gameType"]
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

				if schedEvent.get("doubleHeader") == "Y":
					gameNumber = schedEvent["gameNumber"]
				elif subseason == MLB_SUBSEASON_FLAG_POSTSEASON and schedEvent.get("gamesInSeries") > 1:
					gameNumber = schedEvent["seriesGameNumber"]


				kwargs = {
					"sport": sport,
					"league": league,
					"season": season,
					"date": date,
					"MLBAPIID": schedEvent["gamePk"],
					"title": schedEvent.get("description"),
					"altTitle": schedEvent.get("seriesDescription"),
					"homeTeam": homeTeamKey,
					"awayTeam": awayTeamKey,
					"subseason": subseason,
					"playoffround": playoffRound,
					"eventindicator": eventIndicator,
					"game": gameNumber}

				event = ScheduleEvent(**kwargs)

				AddOrAugmentEvent(sched, event)



