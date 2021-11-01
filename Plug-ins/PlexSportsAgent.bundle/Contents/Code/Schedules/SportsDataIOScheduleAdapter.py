import json

from Constants import *
from Hashes import *
from StringUtils import *
from TimeZoneUtils import *
from Vectors import *
from ..Data.SportsDataIODownloader import *
from ScheduleEvent import *

SPORTS_DATA_IO_SEASON_TYPE_REGULAR_SEASON = 1
SPORTS_DATA_IO_SEASON_TYPE_PRESEASON = 2
SPORTS_DATA_IO_SEASON_TYPE_POSTSEASON = 3
SPORTS_DATA_IO_SEASON_TYPE_OFFSEASON = 4
SPORTS_DATA_IO_SEASON_TYPE_ALLSTAR = 5


def GetSchedule(sched, navigator, sport, league, season):
	if league == LEAGUE_NFL and int(season) < 2017: return

	# Augment/replace with data from SportsData.io
	downloadedJsons = DownloadScheduleForLeagueAndSeason(league, season)
	for downloadedJson in downloadedJsons:
		if not downloadedJson: continue
		try: sportsDataIOSchedule = json.loads(downloadedJson)
		except ValueError: continue

		# If sportsdata.io returns an unauthorized message, log and bail
		if not isinstance(sportsDataIOSchedule, list) and "Code" in sportsDataIOSchedule.keys():
			#print("(200, but %s): %s" % (sportsDataIOSchedule["Code"], sportsDataIOSchedule["Description"]))
			pass
		elif isinstance(sportsDataIOSchedule, list):
			for schedEvent in sportsDataIOSchedule:
				if schedEvent["AwayTeam"] == "BYE":
					continue
				if schedEvent.get("Canceled") == True or schedEvent["Status"] != "Final":
					continue

				# Teams from this API are abbreviations
				homeTeamAbbrev = deunicode(schedEvent["HomeTeam"])
				homeTeam = navigator.GetTeam(season, abbreviation=homeTeamAbbrev)
				homeTeamKey = homeTeam.key if homeTeam else homeTeamAbbrev
				homeTeamFullName = homeTeam.fullName if homeTeam else homeTeamAbbrev

				awayTeamAbbrev = deunicode(schedEvent["AwayTeam"])
				awayTeam = navigator.GetTeam(season, abbreviation=awayTeamAbbrev)
				awayTeamKey = awayTeam.key if awayTeam else awayTeamAbbrev
				awayTeamFullName = awayTeam.fullName if awayTeam else awayTeamAbbrev

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
	
				gameID = str(schedEvent["GlobalGameID"])

				week = schedEvent.get("Week")
					
				kwargs = {
					"sport": sport,
					"league": league,
					"season": season,
					"date": date,
					"week": week,
					"SportsDataIOID": gameID,
					"vs": "%s vs %s" % (homeTeamFullName, awayTeamFullName),
					"homeTeam": homeTeamKey,
					"awayTeam": awayTeamKey,
					"networks": splitAndTrim(deunicode(schedEvent.get("Channel"))),
					}

				SupplementScheduleEvent(league, schedEvent, kwargs)

				event = ScheduleEvent(**kwargs)

				AddOrAugmentEvent(sched, event)


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
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_PRESEASON:
				kwargs["subseason"] = NFL_SUBSEASON_FLAG_PRESEASON
				if schedEvent["Week"] == 0:
					kwargs["eventindicator"] = NFL_EVENT_FLAG_HALL_OF_FAME
					kwargs["eventTitle"] = "Hall of Fame Game"
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_REGULAR_SEASON: kwargs["subseason"] = NFL_SUBSEASON_FLAG_REGULAR_SEASON
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_POSTSEASON:
				kwargs["subseason"] = NFL_SUBSEASON_FLAG_POSTSEASON
				kwargs["week"] = None
				kwargs["playoffround"] = schedEvent["Week"]
				if schedEvent["Week"] == NFL_PLAYOFF_ROUND_SUPERBOWL:
					kwargs["eventindicator"] = NFL_EVENT_FLAG_SUPERBOWL
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_ALLSTAR:
				kwargs["week"] = None
				kwargs["eventindicator"] = NFL_EVENT_FLAG_PRO_BOWL
				kwargs["eventTitle"] = "Pro Bowl"
		if league == LEAGUE_NHL:
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_PRESEASON: kwargs["subseason"] = NHL_SUBSEASON_FLAG_PRESEASON
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_REGULAR_SEASON: kwargs["subseason"] = NHL_SUBSEASON_FLAG_REGULAR_SEASON
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_POSTSEASON:
				kwargs["subseason"] = NHL_SUBSEASON_FLAG_POSTSEASON
				# TODO: Identify Playoff Round/Stanley Cup
			if schedEvent["SeasonType"] == SPORTS_DATA_IO_SEASON_TYPE_ALLSTAR: kwargs["eventindicator"] = NHL_EVENT_FLAG_ALL_STAR_GAME
