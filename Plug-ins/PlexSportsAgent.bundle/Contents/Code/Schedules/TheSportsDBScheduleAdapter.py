import re
import json
from dateutil.tz import *
from pprint import pprint

from Constants import *
from Hashes import *
from StringUtils import *
from TimeZoneUtils import *
from Vectors import *
from ..Data.TheSportsDBDownloader import *
from ScheduleEvent import *

THESPORTSDB_ROUND_QUARTERFINAL = 125
THESPORTSDB_ROUND_SEMIFINAL = 150
THESPORTSDB_ROUND_PLAYOFF = 160
THESPORTSDB_ROUND_PLAYOFF_SEMIFINAL = 170
THESPORTSDB_ROUND_PLAYOFF_FINAL = 180
THESPORTSDB_ROUND_FINAL = 200
THESPORTSDB_ROUND_PRESEASON = 500


spdb_ignore_game_ids = {
	LEAGUE_NFL: ["673824", "673825"]
	}


def GetSchedule(sched, teamKeys, teams, sport, league, season):
	# Retrieve data from TheSportsDB.com
	downloadedJson = DownloadScheduleForLeagueAndSeason(league, season)
	
	if downloadedJson:
		try: sportsDbSchedule = json.loads(downloadedJson)
		except ValueError: return None

	if sportsDbSchedule and sportsDbSchedule["events"]:
		for schedEvent in sportsDbSchedule["events"]:

			# Known bad data
			if league in spdb_ignore_game_ids.keys():
				if schedEvent["idEvent"] in spdb_ignore_game_ids[league]:
					continue

			# Teams from this API are full names, so teams dictionary is scanKeys
			homeTeamStripped = create_scannable_key(schedEvent["strHomeTeam"])
			awayTeamStripped = create_scannable_key(schedEvent["strAwayTeam"])
			homeTeamKey = teamKeys[homeTeamStripped]
			awayTeamKey = teamKeys[awayTeamStripped]
		
			date = __get_event_date(schedEvent)

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

			AddOrAugmentEvent(sched, event)




def SupplementScheduleEvent(league, schedEvent, kwargs):
	"""League-specific supplemental data."""
	# I wish thesportsdb were more comprehensive when it comes to playoff round/preseason
	# I wish thesportsdb were more comprehensive PERIOD
	if league == LEAGUE_MLB:
		if schedEvent.get("intRound") == THESPORTSDB_ROUND_FINAL:
			kwargs.setdefault("subseason", MLB_SUBSEASON_FLAG_POSTSEASON)
			kwargs.setdefault("playoffround", MLB_PLAYOFF_ROUND_WORLD_SERIES)
	elif league == LEAGUE_NBA:
		if schedEvent.get("intRound"):
			if schedEvent.get("intRound") == THESPORTSDB_ROUND_FINAL:
				kwargs.setdefault("subseason", NBA_SUBSEASON_FLAG_POSTSEASON)
				kwargs.setdefault("playoffround", NBA_PLAYOFF_ROUND_FINALS)
			elif schedEvent.get("intRound") == THESPORTSDB_ROUND_PLAYOFF_FINAL:
				kwargs.setdefault("subseason", NBA_SUBSEASON_FLAG_POSTSEASON)
				kwargs.setdefault("playoffround", NBA_PLAYOFF_ROUND_SEMIFINALS)
			elif schedEvent.get("intRound") == THESPORTSDB_ROUND_PLAYOFF_SEMIFINAL:
				kwargs.setdefault("subseason", NBA_SUBSEASON_FLAG_POSTSEASON)
				kwargs.setdefault("playoffround", NBA_PLAYOFF_ROUND_QUARTERFINALS)
			elif schedEvent["intRound"] == THESPORTSDB_ROUND_FINAL:
				kwargs.setdefault("subseason", NBA_SUBSEASON_FLAG_PRESEASON)
	elif league == LEAGUE_NFL:
		if schedEvent.get("strDesciptionEN") == "Pro Football Hall of Fame Game":
			kwargs.setdefault("eventindicator", NFL_EVENT_FLAG_HALL_OF_FAME)

		if schedEvent.get("intRound") != None:
			if schedEvent["intRound"] == THESPORTSDB_ROUND_FINAL:
				kwargs.setdefault("subseason", NFL_SUBSEASON_FLAG_POSTSEASON)
				kwargs.setdefault("playoffround", NFL_PLAYOFF_ROUND_SUPERBOWL)
				kwargs.setdefault("eventindicator", NFL_EVENT_FLAG_SUPERBOWL)
			elif schedEvent["intRound"] == 0:
				kwargs.setdefault("subseason", NFL_SUBSEASON_FLAG_PRESEASON)
			else:
				if schedEvent["intRound"] <= 17: # Guesstimate
					kwargs.setdefault("subseason", NFL_SUBSEASON_FLAG_REGULAR_SEASON)
					kwargs.setdefault("week", schedEvent["intRound"])


def __get_event_date(schedEvent):
	date = None
	if schedEvent.get("dateEventLocal") and schedEvent.get("strTimeLocal"):
		dateStr = schedEvent["dateEventLocal"]
		timeStr = schedEvent["strTimeLocal"]

		tz = EasternTime
		indexOfPlus = indexOf(timeStr, "+")
		if indexOfPlus >= 0:
			tz = UTC
		else:
			indexOfSpace = indexOf(timeStr, " ")
			if indexOfSpace >= 0:
				print("0-dateEventLocal:%s|strTimeLocal:%s" % (schedEvent.get("dateEventLocal"), schedEvent.get("strTimeLocal")))
				ampm = None
				tail = timeStr[indexOfSpace+1:]
				timeStr = timeStr[:indexOfSpace]
				if tail[:2] in ["AM", "PM"]:
					ampm = tail[:2].upper()
					tail = tail[2:].lstrip()
				if ampm == "PM":
					indexOfColon = indexOf(timeStr, ":")
					hrString = timeStr[:indexOfColon]
					hr = int(hrString)
					if hr != 12:
						hr += 12
						if hr == 24:
							hr = 0
							tmpDt = ParseISO8601Date(dateStr)
							tmpDt = tmpDt + datetime.timedelta(days=1)
							dateStr = tmpDt.strftime("%Y:%m:%d")
						timeStr = ("0%s" % hr)[-2:] + timeStr[indexOfColon:]
				if tail:
					# Attempt to fathom Time Zone
					if tail.upper() == "CT": tz = CentralTime
					elif tail.upper() == "MT": tz = MountainTime
					elif tail.upper() == "PT": tz = PacificTime
					elif tail.upper() == "ET": pass
					else: tz = gettz(tail) or EasternTime

		date = ParseISO8601Date("%sT%s" % (dateStr, timeStr))
		# Relative to specified time zone (or East Coast if unspecified)
		date = date.replace(tzinfo=tz).astimezone(tz=UTC)
	elif schedEvent.get("dateEvent") and schedEvent.get("strTime"):
		timeStr = schedEvent["strTime"]

		date = ParseISO8601Date("%sT%s" % (schedEvent["dateEvent"], timeStr))
		if re.match(r"\d{2}:\d{2}:\d{2}", timeStr): # Already expressed in Zulu Time
			date = date.replace(tzinfo=UTC)
		else: # Relative to East Coast
			date = date.replace(tzinfo=EasternTime).astimezone(tz=UTC)
	elif schedEvent.get("dateEvent") and not schedEvent.get("strTime"):
		date = ParseISO8601Date(schedEvent["dateEvent"])
		# Time-naive
	elif schedEvent.get("strTimestamp"):
		date = ParseISO8601Date(schedEvent["strTimestamp"])
		# Zulu Time
		date = date.replace(tzinfo=UTC)

	return date