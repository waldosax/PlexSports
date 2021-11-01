import re
import json
from dateutil.tz import *
from pprint import pprint

from Constants import *
from Constants.Assets import *
from Hashes import *
from StringUtils import *
from TimeZoneUtils import *
from Vectors import *
from ..Data.TheSportsDBDownloader import *
from ScheduleEvent import *

THESPORTSDB_ROUND_PLAYOFF_1ST_ROUND = 1
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


def GetSchedule(sched, navigator, sport, league, season):
	# Retrieve data from TheSportsDB.com
	downloadedJsons = DownloadScheduleForLeagueAndSeason(league, season)
	if not downloadedJsons: return
	for downloadedJson in downloadedJsons:
		if not downloadedJson: continue
		try: sportsDbSchedule = json.loads(downloadedJson)
		except ValueError: return None

		if sportsDbSchedule and sportsDbSchedule["events"]:
			for schedEvent in sportsDbSchedule["events"]:

				# Known bad data
				if league in spdb_ignore_game_ids.keys():
					if schedEvent["idEvent"] in spdb_ignore_game_ids[league]:
						continue

				# Teams from this API are full names
				vs = deunicode(schedEvent["strEvent"])
				homeTeamFullName = deunicode(schedEvent["strHomeTeam"])
				awayTeamFullName = deunicode(schedEvent["strAwayTeam"])

				# Crazy crowdsourced data corrections
				if league == LEAGUE_NBA and awayTeamFullName == "Minnesota Wild":
					awayTeamFullName = "Minnesota Timberwolves"
					vs = "%s vs. %s" % (homeTeamFullName, awayTeamFullName)
				elif league == LEAGUE_NBA and schedEvent["strAwayTeam"] == "Philadelphia Flyers":
					awayTeamFullName = "Philadelphia 76ers"
					vs = "%s vs. %s" % (homeTeamFullName, awayTeamFullName)
				elif league == LEAGUE_NFL:
					if schedEvent["strAwayTeam"] == "San Diego":
						awayTeamFullName = "Sandiego Chargers"
						vs = "%s vs. %s" % (homeTeamFullName, awayTeamFullName)
					elif schedEvent["strHomeTeam"] == "San Diego":
						homeTeamFullName = "San Diego Chargers"
						vs = "%s vs. %s" % (homeTeamFullName, awayTeamFullName)


				homeTeam = navigator.GetTeam(season, homeTeamFullName)
				awayTeam = navigator.GetTeam(season, awayTeamFullName)

				homeTeamKey = homeTeam.key if homeTeam else create_scannable_key(homeTeamFullName)
				awayTeamKey = awayTeam.key if awayTeam else create_scannable_key(awayTeamFullName)
		
				date = __get_event_date(league, schedEvent)
				if date == None:
					continue

				id = deunicode(schedEvent["idEvent"])
				kwargs = {
					"sport": sport,
					"league": league,
					"season": season,
					"date": date,
					"TheSportsDBID": id,
					"vs": vs,
					"description": deunicode(normalize(schedEvent["strDescriptionEN"])),
					"homeTeam": homeTeamKey,
					"awayTeam": awayTeamKey,
					"networks": splitAndTrim(deunicode(schedEvent["strTVStation"]))
					}

				assets = dict()
				if schedEvent["strPoster"]: assets["poster"] = [EventAsset(source=ASSET_SOURCE_THESPORTSDB, url=deunicode(schedEvent["strPoster"]))]
				if schedEvent["strFanart"]: assets["fanArt"] = [EventAsset(source=ASSET_SOURCE_THESPORTSDB, url=deunicode(schedEvent["strFanart"]))]
				if schedEvent["strThumb"]: assets["thumbnail"] = [EventAsset(source=ASSET_SOURCE_THESPORTSDB, url=deunicode(schedEvent["strThumb"]))]
				if schedEvent["strBanner"]: assets["banner"] = [EventAsset(source=ASSET_SOURCE_THESPORTSDB, url=deunicode(schedEvent["strBanner"]))]
				if schedEvent["strVideo"]: assets["preview"] = [EventAsset(source=ASSET_SOURCE_THESPORTSDB, url=deunicode(schedEvent["strVideo"]))]
				if assets: kwargs["assets"] = assets

				SupplementScheduleEvent(league, schedEvent, kwargs)

				event = ScheduleEvent(**kwargs)

				if league == LEAGUE_NFL:
					event = __trashbucket_lookaround(sched, event)

				AddOrAugmentEvent(sched, event, 10) # Big time sensitivity because trashbucket


# Because the bucket is full of trash
def __trashbucket_lookaround(sched, event):

	origHash = sched_compute_augmentation_hash(event)
	if origHash in sched.keys(): return event

	homeaway = [
		[event.homeTeam, event.awayTeam],
		[event.awayTeam, event.homeTeam]
		]

	for teams in homeaway:
		datevariants = [
			event.date,
			event.date - timedelta(days=1),
			event.date.replace(hour=0,minute=0,second=0, tzinfo=UTC),
			event.date.replace(hour=0,minute=0,second=0, tzinfo=UTC) - timedelta(days=1),
			event.date + timedelta(days=1),
			event.date.replace(hour=0,minute=0,second=0, tzinfo=UTC) + timedelta(days=1)
			]
		for datevariant in datevariants:
			altEvent = __clone_event(event, homeTeam=teams[0], awayTeam=teams[1], date=datevariant)
			hash = sched_compute_augmentation_hash(altEvent)
			if hash in sched.keys(): return altEvent

	return event

def __clone_event(event, **kwargs):

	srcdict = event.__dict__

	if kwargs:
		for key in kwargs.keys():
			if key in srcdict.keys():
				srcdict[key] = kwargs[key]

	altEvent = ScheduleEvent(**srcdict)
	return altEvent

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
			if schedEvent.get("intRound") == str(THESPORTSDB_ROUND_FINAL):
				kwargs.setdefault("subseason", NBA_SUBSEASON_FLAG_POSTSEASON)
				kwargs.setdefault("playoffround", NBA_PLAYOFF_ROUND_FINALS)
			elif schedEvent.get("intRound") == str(THESPORTSDB_ROUND_PLAYOFF_FINAL):
				kwargs.setdefault("subseason", NBA_SUBSEASON_FLAG_POSTSEASON)
				kwargs.setdefault("playoffround", NBA_PLAYOFF_ROUND_SEMIFINALS)
			elif schedEvent.get("intRound") == str(THESPORTSDB_ROUND_PLAYOFF_SEMIFINAL):
				kwargs.setdefault("subseason", NBA_SUBSEASON_FLAG_POSTSEASON)
				kwargs.setdefault("playoffround", NBA_PLAYOFF_ROUND_QUARTERFINALS)
			elif schedEvent.get("intRound") == str(THESPORTSDB_ROUND_PLAYOFF_1ST_ROUND):
				kwargs.setdefault("subseason", NBA_SUBSEASON_FLAG_POSTSEASON)
				kwargs.setdefault("playoffround", NBA_PLAYOFF_1ST_ROUND)

			if kwargs.get("subseason") == NBA_SUBSEASON_FLAG_POSTSEASON:
				m = re.match(".* - Game (\d+)", schedEvent.get("strDescriptionEN") or "", re.IGNORECASE)
				if m: kwargs.setdefault("game", int(m.groups(0)[0]))
	elif league == LEAGUE_NFL:
		if schedEvent.get("strDescriptionEN") == "Pro Football Hall of Fame Game":
			kwargs.setdefault("eventindicator", NFL_EVENT_FLAG_HALL_OF_FAME)
			del(kwargs["description"])
			kwargs["eventTitle"] = "Hall of Fame Game"

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
				elif schedEvent["intRound"] == 18:
					kwargs.setdefault("subseason", NFL_SUBSEASON_FLAG_POSTSEASON)
					kwargs.setdefault("playoffround", NFL_PLAYOFF_ROUND_WILDCARD)
				elif schedEvent["intRound"] == 19:
					kwargs.setdefault("subseason", NFL_SUBSEASON_FLAG_POSTSEASON)
					kwargs.setdefault("playoffround", NFL_PLAYOFF_ROUND_DIVISION)
				elif schedEvent["intRound"] == 20:
					kwargs.setdefault("subseason", NFL_SUBSEASON_FLAG_POSTSEASON)
					kwargs.setdefault("playoffround", NFL_PLAYOFF_ROUND_CHAMPIONSHIP)

def __fathom_time_zone(tzIndicator, defaultTz=EasternTime):
	"""Attempt to fathom Time Zone"""
	if tzIndicator.upper() == "CT": return CentralTime
	elif tzIndicator.upper() == "MT": return MountainTime
	elif tzIndicator.upper() == "PT": return PacificTime
	elif tzIndicator.upper() == "ET": return EasternTime
	
	return gettz(tzIndicator) or defaultTz

def __parse_local_date(dateStr, timeStr, defaultTz=EasternTime):
	tz = defaultTz
	indexOfPlus = indexOf(timeStr, "+")
	if indexOfPlus >= 0:
		tz = UTC
	else:
		indexOfSpace = indexOf(timeStr, " ")
		if indexOfSpace >= 0:
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
				tz = __fathom_time_zone(tail, defaultTz)

	if timeStr == None: timeStr = "00:00:00"
	date = ParseISO8601Date("%sT%s" % (dateStr, timeStr))
	# Relative to specified time zone (or East Coast if unspecified)
	date = date.replace(tzinfo=tz).astimezone(tz=UTC)

	return date

# All of this is why The SportsDB incurs the moniker "trashbucket"
def __get_event_date(league, schedEvent):
	date = None
	if schedEvent.get("dateEvent") and schedEvent.get("strTime"):
		dateStr = schedEvent["dateEvent"]
		timeStr = schedEvent["strTime"]

		if league == LEAGUE_NFL:
			if timeStr == "17:00:00": timeStr = "00:00:00"

		if re.match(r"\d{1,2}:\d{2}:\d{2}", timeStr):
			# Already expressed in Zulu Time
			date = __parse_local_date(dateStr, timeStr, UTC)
		else:

			if league == LEAGUE_MLB:
				# Expressed as an afternoon/evening time, relative to EST
				indexOfSpace = indexOf(timeStr, " ")
				if indexOfSpace < 0:
					date = __parse_local_date(dateStr, ("%s %s" % (timeStr, "PM ET")))
			elif league == LEAGUE_NFL:
				# Expressed as UTC
				date = __parse_local_date(dateStr, timeStr, UTC)

			if not date:
				date = __parse_local_date(dateStr, timeStr)

	elif schedEvent.get("dateEventLocal") and schedEvent.get("strTimeLocal"):
		# Presuming local time is Eastern time unless explicitly specified
		dateStr = schedEvent["dateEventLocal"]
		timeStr = schedEvent["strTimeLocal"]

		date = __parse_local_date(dateStr, timeStr)
	elif schedEvent.get("dateEvent") and not schedEvent.get("strTime"):
		if schedEvent["dateEvent"] == "0000-00-00": return None
		date = ParseISO8601Date(schedEvent["dateEvent"])
		# Time-naive
	elif schedEvent.get("strTimestamp"):
		date = ParseISO8601Date(schedEvent["strTimestamp"])
		# Zulu Time
		date = date.replace(tzinfo=UTC)

	return date