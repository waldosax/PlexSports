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

			seriesDescriptor = None
			game = None
			playoffRound = None
			subseason = None
			eventIndicator = None

			nugget = deunicode(supplementalGame["nugget"]["text"])
			if supplementalGame.get("playoffs"):
				subseason = NBA_SUBSEASON_POSTSEASON
				game = supplementalGame["playoffs"]["gameNumInSeries"]
				roundNum = supplementalGame["playoffs"].get("roundNum")
				if roundNum: playoffRound = roundNum
				else:
					tags = supplementalGame.get("tags")
					if tags and ("E1" in tags or "W1" in tags): playoffRound = NBA_PLAYOFF_1ST_ROUND
					elif tags and ("E2" in tags or "W2" in tags): playoffRound = NBA_PLAYOFF_ROUND_QUARTERFINALS
					elif tags and ("E4" in tags or "W4" in tags): playoffRound = NBA_PLAYOFF_ROUND_SEMIFINALS
					elif tags and ("Finals" in tags): playoffRound = NBA_PLAYOFF_ROUND_FINALS
			else:
				seasonStageId = supplementalGame["seasonStageId"]
				if seasonStageId == 1: subseason = NBA_SUBSEASON_FLAG_PRESEASON
				elif seasonStageId == 2: subseason = NBA_SUBSEASON_FLAG_REGULAR_SEASON
				elif seasonStageId == 3: # All-Star
					tags = supplementalGame.get("tags")
					if tags and "AWASG" in tags: eventIndicator = NBA_EVENT_FLAG_ALL_STAR_GAME
		
			if id in tracking.keys():
				# Augment with supplemental data
				event = tracking[id]

				if nugget: event.altTitle = nugget
				if subseason: event.subseason = subseason
				if playoffRound: event.playoffround = playoffRound
				if game: event.game = game
				if eventIndicator: event.eventindicator = eventIndicator

			else:
				# Create new event and add it.
			
				date = ParseISO8601Date(supplementalGame["startTimeUTC"]).replace(tzinfo=UTC)

				if supplementalGame.get("playoffs"):
					seriesDescriptor = supplementalGame["playoffs"]["seriesSummaryText"]

				gameUrlCode = splitAndTrim(deunicode(supplementalGame["gameUrlCode"]), "/")
				homeTeamAbbrev = gameUrlCode[1][3:]
				awayTeamAbbrev = gameUrlCode[1][:3]

				homeTeamKey = None
				homeTeamDisp = None
				homeTeamID = supplementalGame["hTeam"]["teamId"]
				homeTeam = __find_team_by_nbaapiid(teams, homeTeamID)
				if not homeTeam: homeTeam = teams.get(teamKeys.get(homeTeamAbbrev.lower()))
				if homeTeam:
					homeTeamKey = homeTeam.key or homeTeam.abbreviation
					homeTeamDisp = homeTeam.fullName
				else:
					homeTeamDisp = homeTeamAbbrev
			
				awayTeamKey = None
				awayTeamDisp = None
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
					"altTitle": nugget or seriesDescriptor	# For reference later. If no good description, set description to this.
					}

				event = ScheduleEvent(**kwargs)

				newEvent = AddOrAugmentEvent(sched, event)
				tracking[id] = newEvent









	# Get metadata supplement
	ids = tracking.keys()
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






