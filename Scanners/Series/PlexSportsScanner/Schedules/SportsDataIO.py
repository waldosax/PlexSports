import json

from Constants import *
from Hashes import *
from StringUtils import *
from TimeZoneUtils import *
from ..Data.SportsDataIO import *
from ScheduleEvent import *

SPORTS_DATA_IO_SEASON_TYPE_REGULAR_SEASON = 1
SPORTS_DATA_IO_SEASON_TYPE_PRESEASON = 2
SPORTS_DATA_IO_SEASON_TYPE_POSTSEASON = 3
SPORTS_DATA_IO_SEASON_TYPE_OFFSEASON = 4
SPORTS_DATA_IO_SEASON_TYPE_ALLSTAR = 5


def GetSchedule(sched, teams, sport, league, season):
	# Augment/replace with data from SportsData.io
	downloadedJsons = DownloadScheduleForLeagueAndSeason(league, season) #TODO: Rename this
	for downloadedJson in downloadedJsons:
		if not downloadedJson: continue
		try: sportsDataIOSchedule = json.loads(downloadedJson)
		except ValueError: continue

		# If sportsdata.io returns an unauthorized message, log and bail
		if not isinstance(sportsDataIOSchedule, list) and "Code" in sportsDataIOSchedule.keys():
			print("%s: %s" % (sportsDataIOSchedule["Code"], sportsDataIOSchedule["Description"]))
		elif isinstance(sportsDataIOSchedule, list):
			for schedEvent in sportsDataIOSchedule:
				homeTeamKey = deunicode(schedEvent["HomeTeam"])
				awayTeamKey = deunicode(schedEvent["AwayTeam"])
				if awayTeamKey == "BYE":
					continue
				homeTeam = teams[homeTeamKey]
				awayTeam = teams[awayTeamKey]

				date = None
				if schedEvent.get("DateTime"):
					date = datetime.datetime.strptime(schedEvent["DateTime"], "%Y-%m-%dT%H:%M:%S")
					date = date.replace(tzinfo=EasternTime).astimezone(tz=UTC)
				elif schedEvent.get("Date"):
					date = datetime.datetime.strptime(schedEvent["Date"], "%Y-%m-%dT%H:%M:%S")
					date = date.replace(tzinfo=EasternTime).astimezone(tz=UTC)
				elif schedEvent.get("Day"):
					date = datetime.datetime.strptime(schedEvent["Day"], "%Y-%m-%dT%H:%M:%S")
					date = date.replace(tzinfo=UTC)
	
				gameID = None
				if schedEvent.get("GameKey"):
					gameID = deunicode(schedEvent["GameKey"])
				if schedEvent.get("GameID"):
					gameID = deunicode(schedEvent["GameID"])

				kwargs = {
					"sport": sport,
					"league": league,
					"season": season,
					"date": date,
					"week": schedEvent.get("Week"),
					"SportsDataIOID": gameID,
					"title": "%s vs %s" % (homeTeam.FullName, awayTeam.FullName),
					"altTitle": "%s @ %s" % (awayTeam.FullName, homeTeam.FullName),
					"homeTeam": homeTeamKey,
					"awayTeam": awayTeamKey,
					"network": deunicode(schedEvent.get("Channel"))}

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
						evdict.setdefault(subhash, event)
					else:
						evdict[subhash].augment(**event.__dict__)


def SupplementScheduleEvent(league, schedEvent, kwargs):
	if schedEvent.get("SeasonType"):
		if league == LEAGUE_MLB:
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_PRESEASON: kwargs["subseason"] = MLB_SUBSEASON_FLAG_PRESEASON
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_REGULAR_SEASON: kwargs["subseason"] = MLB_SUBSEASON_FLAG_REGULAR_SEASON
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_POSTSEASON:
				kwargs["subseason"] = MLB_SUBSEASON_FLAG_POSTSEASON
				# TODO: Identify Playoff Round/World Series
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_ALLSTAR: kwargs["eventindicator"] = MLB_EVENT_FLAG_ALL_STAR_GAME
		if league == LEAGUE_NBA:
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_PRESEASON: kwargs["subseason"] = NBA_SUBSEASON_FLAG_PRESEASON
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_REGULAR_SEASON: kwargs["subseason"] = NBA_SUBSEASON_FLAG_REGULAR_SEASON
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_POSTSEASON:
				kwargs["subseason"] = NBA_SUBSEASON_FLAG_POSTSEASON
				# TODO: Identify Playoff Round
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_ALLSTAR: kwargs["eventindicator"] = NBA_EVENT_FLAG_ALL_STAR_GAME
		if league == LEAGUE_NFL:
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_PRESEASON: kwargs["subseason"] = NFL_SUBSEASON_FLAG_PRESEASON
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_REGULAR_SEASON: kwargs["subseason"] = NFL_SUBSEASON_FLAG_REGULAR_SEASON
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_POSTSEASON:
				kwargs["subseason"] = NFL_SUBSEASON_FLAG_POSTSEASON
				# TODO: Identify Playoff Round/Superbowl
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_ALLSTAR: kwargs["eventindicator"] = NFL_EVENT_FLAG_PRO_BOWL
		if league == LEAGUE_NHL:
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_PRESEASON: kwargs["subseason"] = NHL_SUBSEASON_FLAG_PRESEASON
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_REGULAR_SEASON: kwargs["subseason"] = NHL_SUBSEASON_FLAG_REGULAR_SEASON
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_POSTSEASON:
				kwargs["subseason"] = NHL_SUBSEASON_FLAG_POSTSEASON
				# TODO: Identify Playoff Round/Stanley Cup
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_ALLSTAR: kwargs["eventindicator"] = NHL_EVENT_FLAG_ALL_STAR_GAME
