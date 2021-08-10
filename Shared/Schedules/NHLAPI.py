import json

from Constants import *
from Hashes import *
from StringUtils import *
from TimeZoneUtils import *
from Vectors import *
from ..Data.NHL.NHLAPI import *
from ScheduleEvent import *



NHLAPI_GAMETYPE_PRESEASON = "PR"
NHLAPI_GAMETYPE_REGULAR_SEASON = "R"
NHLAPI_GAMETYPE_PLAYOFFS = "P"
NHLAPI_GAMETYPE_ALL_STAR_GAME = "A"


def GetSchedule(sched, teams, sport, league, season):
	# Retrieve data from NHL API
	downloadedJson = DownloadScheduleForSeason(season)
	
	if downloadedJson:
		try: nhlApiSchedule = json.loads(downloadedJson)
		except ValueError: pass

	if nhlApiSchedule and nhlApiSchedule.get("dates"):
		for eventDate in nhlApiSchedule["dates"]:
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
				homeTeamKey = teams[homeTeamStripped] if teams.get(homeTeamStripped) else homeTeamStripped
				awayTeamKey = teams[awayTeamStripped] if teams.get(awayTeamStripped) else awayTeamStripped

				subseason = None
				playoffRound = None
				eventIndicator = None
				gameNumber = None
	
				gameType = schedEvent["gameType"]
				if gameType == NHLAPI_GAMETYPE_PRESEASON: subseason = NHL_SUBSEASON_FLAG_PRESEASON
				elif gameType == NHLAPI_GAMETYPE_REGULAR_SEASON: subseason = NHL_SUBSEASON_FLAG_REGULAR_SEASON
				elif gameType == NHLAPI_GAMETYPE_PLAYOFFS:
					subseason = NHL_SUBSEASON_FLAG_POSTSEASON
					# TODO: Playoff Round?
				elif gameType == NHLAPI_GAMETYPE_ALL_STAR_GAME:
					eventIndicator = NHL_EVENT_FLAG_ALL_STAR_GAME

				# TODO: Game Number
				#if subseason == NHL_SUBSEASON_FLAG_POSTSEASON and schedEvent.get("gamesInSeries") > 1:
				#	gameNumber = schedEvent["seriesGameNumber"]


				kwargs = {
					"sport": sport,
					"league": league,
					"season": season,
					"date": date,
					"NHLAPIID": schedEvent["gamePk"],
					"homeTeam": homeTeamKey,
					"awayTeam": awayTeamKey,
					"subseason": subseason,
					"eventindicator": eventIndicator}

				event = ScheduleEvent(**kwargs)

				hash = sched_compute_augmentation_hash(event)
				subhash = sched_compute_time_hash(event.date)
				#print("%s|%s" % (hash, subhash))
				if not hash in sched.keys():
					sched.setdefault(hash, {subhash:event})
				else:
					evdict = sched[hash]
					if (not subhash in evdict.keys()):
						sched[hash].setdefault(subhash, event)
					else:
						sched[hash][subhash].augment(**event.__dict__)



