import json

from Constants import *
from Hashes import *
from Matching import __strip_to_alphanumeric
from StringUtils import *
from TimeZoneUtils import *
from ..Data.TheSportsDB import *
from ScheduleEvent import *

THESPORTSDB_ROUND_QUARTERFINAL = 125
THESPORTSDB_ROUND_SEMIFINAL = 150
THESPORTSDB_ROUND_PLAYOFF = 160
THESPORTSDB_ROUND_PLAYOFF_SEMIFINAL = 170
THESPORTSDB_ROUND_PLAYOFF_FINAL = 180
THESPORTSDB_ROUND_FINAL = 200
THESPORTSDB_ROUND_PRESEASON = 500






def GetSchedule(sched, teams, sport, league, season):
	# Retrieve data from TheSportsDB.com
	downloadedJson = DownloadScheduleForLeagueAndSeason(league, season)
	
	if downloadedJson:
		try: sportsDbSchedule = json.loads(downloadedJson)
		except ValueError: pass

	if sportsDbSchedule and sportsDbSchedule["events"]:
		for schedEvent in sportsDbSchedule["events"]:
			homeTeamStripped = __strip_to_alphanumeric(deunicode(schedEvent["strHomeTeam"]))
			awayTeamStripped = __strip_to_alphanumeric(deunicode(schedEvent["strAwayTeam"]))
			homeTeamKey = teams[homeTeamStripped]
			awayTeamKey = teams[awayTeamStripped]
		
			date = None
			if schedEvent.get("dateEventLocal") and schedEvent.get("strTimeLocal"):
				date = ParseISO8601Date("%sT%s" % (schedEvent["dateEventLocal"], schedEvent["strTimeLocal"]))
				# Relative to East Coast
				date = date.replace(tzinfo=EasternTime).astimezone(tz=UTC)
			elif schedEvent.get("dateEvent") and schedEvent.get("strTime"):
				date = ParseISO8601Date("%sT%s" % (schedEvent["dateEvent"], schedEvent["strTime"]))
				## Zulu Time
				#date = date.replace(tzinfo=UTC)
				# Relative to East Coast
				date = date.replace(tzinfo=EasternTime).astimezone(tz=UTC)
			elif schedEvent.get("dateEvent") and not schedEvent.get("strTime"):
				date = ParseISO8601Date(schedEvent["dateEvent"])
			elif schedEvent.get("strTimestamp"):
				date = ParseISO8601Date(schedEvent["strTimestamp"])
				# Zulu Time
				date = date.replace(tzinfo=UTC)

			kwargs = {
				"sport": sport,
				"league": league,
				"season": season,
				"date": date,
				"TheSportsDBID": schedEvent["idEvent"],
				"title": schedEvent["strEvent"],
				"altTitle": schedEvent["strEventAlternate"],
				"description": normalize(schedEvent["strDescriptionEN"]),
				"homeTeam": homeTeamKey,
				"awayTeam": awayTeamKey,
				"network": deunicode(schedEvent["strTVStation"]),
				"poster": deunicode(schedEvent["strPoster"]),
				"fanArt": deunicode(schedEvent["strFanart"]),
				"thumbnail": deunicode(schedEvent["strThumb"]),
				"banner": deunicode(schedEvent["strBanner"]),
				"preview": deunicode(schedEvent["strVideo"])}

			SupplementScheduleEvent(league, schedEvent, kwargs)

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





def SupplementScheduleEvent(league, schedEvent, kwargs):
	# I wish thesportsdb were more comprehensive when it comes to playoff round/preseason
	if league == LEAGUE_MLB:
		if schedEvent.get("intRound") == THESPORTSDB_ROUND_FINAL:
			kwargs.setdefault("subseason", MLB_SUBSEASON_POSTSEASON)
			kwargs.setdefault("playoffround", MLB_PLAYOFF_ROUND_WORLD_SERIES)
	elif league == LEAGUE_NFL:
		if schedEvent.get("intRound") == THESPORTSDB_ROUND_FINAL:
			kwargs.setdefault("subseason", NFL_SUBSEASON_POSTSEASON)
			kwargs.setdefault("playoffround", NFL_PLAYOFF_ROUND_SUPERBOWL)
			kwargs.setdefault("eventindicator", NFL_EVENT_FLAG_SUPERBOWL)
