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

	if nbaApiSchedule and nbaApiSchedule.get("lscd"):
		for lscd in nbaApiSchedule["lscd"]:
			for game in lscd["mscd"]["g"]:

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
				summary = str(seriesDescriptor)
				if seriesDescriptor:
					subseason = NBA_SUBSEASON_FLAG_POSTSEASON
					m = re.match(".*(\d+)-(\d+).*", seriesDescriptor, re.IGNORECASE)
					if m:
						game = int(m.groups(0)[0]) + int(m.groups(0)[1])



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
					"game": game,
					"networks": list(set(networks)),
					"altTitle": seriesDescriptor	# For reference later. If no good description, set description to this.
					}

				event = ScheduleEvent(**kwargs)

				AddOrAugmentEvent(sched, event)

def __find_team_by_nbaapiid(teams, nbaapiid):
	for franchise in teams.values():
		team = franchise.FindTeam(None, identity={"NBAdotcomID": nbaapiid})
		if team: return team