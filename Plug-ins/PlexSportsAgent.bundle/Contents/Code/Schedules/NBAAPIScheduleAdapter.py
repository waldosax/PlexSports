import re
import json

from Constants import *
from Hashes import *
from StringUtils import *
from TimeZoneUtils import *
from Vectors import *
from ..Data.NBA.NBAAPIDownloader import *
from ScheduleEvent import *




def GetSchedule(sched, teamKeys, teams, sport, league, season):

	# Retrieve data from NBA API
	downloadedJson = DownloadScheduleForSeason(season)
	nbaApiSchedule = None
	if downloadedJson:
		try: nbaApiSchedule = json.loads(downloadedJson)
		except ValueError: pass

	# Get Schedule supplement
	nbaapiScheduleSupplement = dict()
	nbaapiScheduleSupplementJson = DownloadScheduleSupplementForSeason(season)
	if nbaapiScheduleSupplementJson:
		try: nbaapiScheduleSupplement = json.loads(nbaapiScheduleSupplementJson)
		except ValueError: pass


	tracking = dict()
	if nbaApiSchedule and nbaApiSchedule.get("lscd"):
		for lscd in nbaApiSchedule["lscd"]:
			for game in lscd["mscd"]["g"]:

				if (game["stt"]) == "TBD": continue

				id = deunicode(game["gid"])
				date = ParseISO8601Date("%sT%s" % (game["gdtutc"], game["utctm"])).replace(tzinfo=UTC)

				# Teams from this API are abbreviations
				homeTeamName = deunicode("%s %s" % (game["h"]["tc"], game["h"]["tn"]))
				awayTeamName = deunicode("%s %s" % (game["v"]["tc"], game["v"]["tn"]))
				vs = "%s vs. %s" % (homeTeamName, awayTeamName)
				homeTeamAbbrev = deunicode(game["h"]["ta"])
				awayTeamAbbrev = deunicode(game["v"]["ta"])
				homeTeamKey = None
				awayTeamKey = None

				if homeTeamAbbrev in teams.keys(): homeTeamKey = homeTeamAbbrev
				else:
					homeTeamById = __find_team_by_nbaapiid(teams, str(game["h"]["tid"]))
					if homeTeamById : homeTeamKey = homeTeamById.abbreviation
					else:
						homeTeamStripped = create_scannable_key(homeTeamName)
						homeTeamKey = teamKeys[homeTeamStripped] if teamKeys.get(homeTeamStripped) else None

				if awayTeamAbbrev in teams.keys(): awayTeamKey = awayTeamAbbrev
				else:
					awayTeamById = __find_team_by_nbaapiid(teams, str(game["v"]["tid"]))
					if awayTeamById : awayTeamKey = awayTeamById.abbreviation
					else:
						awayTeamStripped = create_scannable_key(awayTeamName)
						awayTeamKey = teamKeys[awayTeamStripped] if teamKeys.get(awayTeamStripped) else None


				if not homeTeamKey or not awayTeamKey:
					print("  Skipping NBA game from NBA API %s, %s." % (date.strftime("%Y-%m-%d"), vs))
					continue

				networks = []
				for b in game["bd"]["b"]:
					if b["type"] == "tv" and b["scope"] == "natl":
						if not b.get("lan") or b["lan"] == "English":
							networks.append(b["disp"])


				seriesDescriptor = deunicode(game["seri"])
				subseason = None
				game = None
				playoffRound = None
				if seriesDescriptor:
					subseason = NBA_SUBSEASON_FLAG_POSTSEASON
					#m = re.match(".*(\d+)-(\d+).*", seriesDescriptor, re.IGNORECASE)
					#if m:
					#	game = int(m.groups(0)[0]) + int(m.groups(0)[1])
					gameNumber = int(id[-1])
					playoffRound = int(id[-3:-2])



				kwargs = {
					"sport": sport,
					"league": league,
					"season": season,
					"date": date,
					"NBAAPIID": id,
					"homeTeam": homeTeamKey,
					"awayTeam": awayTeamKey,
					"vs": vs,
					"subseason": subseason,
					"playoffround": playoffRound,
					"game": game,
					"networks": list(set(networks)),
					"altTitle": seriesDescriptor	# For reference later. If no good description, set description to this.
					}

				event = ScheduleEvent(**kwargs)

				newEvent = AddOrAugmentEvent(sched, event)
				tracking[id] = newEvent

	# Supplement data
	if nbaapiScheduleSupplement.get("league") and nbaapiScheduleSupplement["league"].get("standard"):
		for supplementalGame in nbaapiScheduleSupplement["league"]["standard"]:
			id = deunicode(supplementalGame["gameId"])

			event = None

			seriesDescriptor = None
			game = None
			playoffRound = None
			subseason = None
			eventIndicator = None
			eventTitle = None

			tags = supplementalGame.get("tags") or []
			nugget = deunicode(supplementalGame["nugget"]["text"])
			isAllStarSaturdayNight = False

			if supplementalGame.get("playoffs"):
				subseason = NBA_SUBSEASON_FLAG_POSTSEASON
				game = supplementalGame["playoffs"]["gameNumInSeries"]
				roundNum = supplementalGame["playoffs"].get("roundNum")
				if roundNum: playoffRound = roundNum
				else:
					if tags and ("E1" in tags or "W1" in tags): playoffRound = NBA_PLAYOFF_1ST_ROUND
					elif tags and ("E2" in tags or "W2" in tags): playoffRound = NBA_PLAYOFF_ROUND_QUARTERFINALS
					elif tags and ("E4" in tags or "W4" in tags): playoffRound = NBA_PLAYOFF_ROUND_SEMIFINALS
					elif tags and ("Finals" in tags): playoffRound = NBA_PLAYOFF_ROUND_FINALS
			else:
				seasonStageId = supplementalGame["seasonStageId"]
				if seasonStageId == 1: subseason = NBA_SUBSEASON_FLAG_PRESEASON
				elif seasonStageId == 2: subseason = NBA_SUBSEASON_FLAG_REGULAR_SEASON
				elif seasonStageId == 3: # All-Star
					if tags and "AWASG" in tags: eventIndicator = NBA_EVENT_FLAG_ALL_STAR_GAME
					if (tags and "AWSN" in tags) or id[-2:] == "99":
						# All-Star Saturday Night, create sub events
						isAllStarSaturdayNight = True
						eventIndicator = NBA_EVENT_FLAG_ALL_STAR_SATURDAY_NIGHT
						eventTitle = "All-Star Saturday Night"
		
			if id in tracking.keys():
				# Augment with supplemental data
				event = tracking[id]

				if nugget: event.altTitle = nugget
				if subseason: event.subseason = subseason
				if playoffRound: event.playoffround = playoffRound
				if game: event.game = game
				if eventIndicator: event.eventindicator = eventIndicator
				if eventTitle: event.eventTitle = eventTitle

			else:
				# Create new event and add it.
			
				date = ParseISO8601Date(supplementalGame["startTimeUTC"]).replace(tzinfo=UTC)

				if supplementalGame.get("playoffs"):
					seriesDescriptor = supplementalGame["playoffs"]["seriesSummaryText"]

				gameUrlCode = splitAndTrim(deunicode(supplementalGame["gameUrlCode"]), "/")
				homeTeamAbbrev = gameUrlCode[1][3:]
				awayTeamAbbrev = gameUrlCode[1][:3]

				homeTeam = None
				homeTeamKey = None
				homeTeamDisp = None
				if homeTeamAbbrev not in ["EST", "WST"]:
					homeTeamID = supplementalGame["hTeam"]["teamId"]
					homeTeam = __find_team_by_nbaapiid(teams, homeTeamID)
				if not homeTeam: homeTeam = teams.get(teamKeys.get(homeTeamAbbrev.lower()))
				if homeTeam:
					homeTeamKey = homeTeam.key or homeTeam.abbreviation
					homeTeamDisp = homeTeam.fullName
				else:
					homeTeamDisp = homeTeamAbbrev
			
				awayTeam = None
				awayTeamKey = None
				awayTeamDisp = None
				if awayTeamAbbrev not in ["EST", "WST"]:
					awayTeamID = supplementalGame["vTeam"]["teamId"]
					awayTeam = __find_team_by_nbaapiid(teams, awayTeamID)
				if not awayTeam: awayTeam = teams.get(teamKeys.get(awayTeamAbbrev.lower()))
				if awayTeam:
					awayTeamKey = awayTeam.key or awayTeam.abbreviation
					awayTeamDisp = awayTeam.fullName
				else:
					awayTeamDisp = awayTeamAbbrev

				vs = "%s vs. %s" % (homeTeamDisp, awayTeamDisp)

				if not homeTeamKey or not awayTeamKey:
					print("  Skipping NBA game from NBA API %s, %s." % (date.strftime("%Y-%m-%d"), vs))
					continue

				kwargs = {
					"sport": sport,
					"league": league,
					"season": season,
					"date": date,
					"NBAAPIID": id,
					"homeTeam": homeTeamKey,
					"awayTeam": awayTeamKey,
					"vs": vs,
					"subseason": subseason,
					"playoffround": playoffRound,
					"game": game,
					"eventindicator": eventIndicator,
					"eventTitle": eventTitle,
					"altTitle": nugget or seriesDescriptor	# For reference later. If no good description, set description to this.
					}

				event = ScheduleEvent(**kwargs)

				newEvent = AddOrAugmentEvent(sched, event)
				tracking[id] = newEvent
				event = newEvent

			if isAllStarSaturdayNight:
				# Create child events
				# {date} is Saturday
				#
				# Friday:
				#	7PM: All-Star Celebrity	(Need shedules that provide this and teams that provide this ID)
				#	9PM: Rising Stars		(Need shedules that provide this and teams that provide this ID)
				# Saturday:
				#	8PM: Skills Challenge
				#	9PM: 3-Point Contest
				#	10PM: Slam Dunk Contest
				# Sunday
				#	8PM: All-Star Game	(covered by actual data point, no need to synthesize)

				skillsChallenge = __cloneEvent(event)
				skillsChallenge.homeTeam = None
				skillsChallenge.awayTeam = None
				skillsChallenge.vs = None
				skillsChallenge.eventindicator = NBA_EVENT_FLAG_SKILLS_CHALLENGE
				skillsChallenge.eventTitle = "NBA Skills Challenge"
				skillsChallenge.date = event.date.astimezone(tz=UTC).replace(hour=20, minute=0, tzinfo=EasternTime).astimezone(tz=UTC)
				skillsChallenge.identity.NBAAPIID = "%s.%s" % (event.identity.NBAAPIID, NBA_EVENT_FLAG_SKILLS_CHALLENGE)
				newEvent = AddOrAugmentEvent(sched, skillsChallenge, timeSensitivity=0)
				tracking[newEvent.identity.NBAAPIID] = newEvent

				threePointContest = __cloneEvent(event)
				threePointContest.homeTeam = None
				threePointContest.awayTeam = None
				threePointContest.vs = None
				threePointContest.eventindicator = NBA_EVENT_FLAG_3_POINT_SHOOTOUT
				threePointContest.eventTitle = "3-Point Shootout"
				threePointContest.date = event.date.astimezone(tz=UTC).replace(hour=21, minute=0, tzinfo=EasternTime).astimezone(tz=UTC)
				threePointContest.identity.NBAAPIID = "%s.%s" % (event.identity.NBAAPIID, NBA_EVENT_FLAG_3_POINT_SHOOTOUT)
				newEvent = AddOrAugmentEvent(sched, threePointContest, timeSensitivity=0)
				tracking[newEvent.identity.NBAAPIID] = newEvent

				slamDunkContest = __cloneEvent(event)
				slamDunkContest.homeTeam = None
				slamDunkContest.awayTeam = None
				slamDunkContest.vs = None
				slamDunkContest.eventindicator = NBA_EVENT_FLAG_SLAM_DUNK_COMPETITION
				slamDunkContest.eventTitle = "Slam Dunk Contest"
				slamDunkContest.date = event.date.astimezone(tz=UTC).replace(hour=22, minute=0, tzinfo=EasternTime).astimezone(tz=UTC)
				slamDunkContest.identity.NBAAPIID = "%s.%s" % (event.identity.NBAAPIID, NBA_EVENT_FLAG_SLAM_DUNK_COMPETITION)
				newEvent = AddOrAugmentEvent(sched, slamDunkContest, timeSensitivity=0)
				tracking[newEvent.identity.NBAAPIID] = newEvent

				pass







	# Get metadata supplement
	ids = tracking.keys()
	for i in range(len(ids)-1,-1,-1):
		if indexOf(ids[i], ".") >= 0:
			del(ids[i])

	limit = 12
	l = len(ids)
	for i in range(0, l, limit):
		slice = ids[i:i+limit]

		nbaapiMetadataSupplement = dict()
		nbaapiMetadataSupplementJson = DownloadVideoMetadata(*slice)
		if nbaapiMetadataSupplementJson:
			try: nbaapiMetadataSupplement = json.loads(nbaapiMetadataSupplementJson)
			except ValueError: pass
	
		if nbaapiMetadataSupplement:
			for metadata in nbaapiMetadataSupplement["results"]["items"]:
				excerpt = metadata["excerpt"]
				featuredImage = metadata["featuredImage"]
				for id in metadata["taxonomy"]["games"].keys():

					if __is_game_id_all_star_saturday(id):
						if __recap_contains(metadata, "skills"): id = "%s.%s" % (id, NBA_EVENT_FLAG_SKILLS_CHALLENGE)
						elif __recap_contains(metadata, "slam", "dunk"): id = "%s.%s" % (id, NBA_EVENT_FLAG_SLAM_DUNK_COMPETITION)
						elif __recap_contains(metadata, "3-Point", "3 Point"): id = "%s.%s" % (id, NBA_EVENT_FLAG_3_POINT_SHOOTOUT)

					event = tracking.get(id)
					if event:
						if not event.description and excerpt: event.description = excerpt
						if featuredImage:
							event.assets.thumbnail.append(EventAsset(source=ASSET_SOURCE_NBAAPI, url=featuredImage))
		pass

	pass

def __find_team_by_nbaapiid(teams, nbaapiid):
	for franchise in teams.values():
		team = franchise.FindTeam(None, identity={"NBAAPIID": nbaapiid})
		if team: return team

def __is_game_id_all_star(gameID):
	return gameID[2] == "3"

def __is_game_id_all_star_saturday(gameID):
	if not __is_game_id_all_star(gameID): return False
	return gameID[-2:] == "99"

def __recap_contains(recap, *values):
	if not recap or not values: return False

	for value in values:
		if recap.get("categoryPrimary") and indexOf(recap["categoryPrimary"]["name"].lower(), value.lower()) >= 0: return True
		if recap.get("categoryPrimary") and indexOf(recap["categoryPrimary"]["slug"].lower(), value.lower()) >= 0: return True
		if recap.get("category") and indexOf(recap["category"].lower(), value.lower()) >= 0: return True
		if recap.get("name") and indexOf(recap["name"].lower(), value.lower()) >= 0: return True
		if recap.get("title") and indexOf(recap["title"].lower(), value.lower()) >= 0: return True
		if recap.get("slug") and indexOf(recap["slug"].lower(), value.lower()) >= 0: return True
		if recap.get("taxonomy") and recap["taxonomy"].get("categories"):
			for category in recap["taxonomy"]["categories"]:
				if indexOf(category[0].lower(), value.lower()) >= 0: return True
				if indexOf(category[1].lower(), value.lower()) >= 0: return True
		pass

	return False



def __cloneEvent(event):
	newEvent = ScheduleEvent(**event.__dict__)
	return newEvent

