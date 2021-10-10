# TheSportsDB.com
# TEAMS

import json
from datetime import datetime, date, time

from Constants import *
from Constants.Assets import *
from StringUtils import *
from Data.SportsDataIODownloader import *

sdio_abbreviation_corrections = {
	LEAGUE_MLB: {
		"CHW": "CWS"
		},
	LEAGUE_NBA: {
		"LEB": "LBN",
		"DUR": "DRT"
		}
	}

def DownloadAllTeams(league):

	activeTeamsJson = DownloadActiveTeamsForLeague(league)
	allTeamsJson = DownloadAllTeamsForLeague(league)

	teams = dict()

	hasAnyTeamData = False
	activeTeams = json.loads(activeTeamsJson) # TODO: try/catch
	if activeTeams is not None and not isinstance(activeTeams, list) and "Code" in activeTeams.keys():
		print("%s: %s" % (activeTeams["Code"], activeTeams["Description"]))
	else : hasAnyTeamData = True

	allTeams = json.loads(allTeamsJson) # TODO: try/catch
	if allTeams is not None and not isinstance(allTeams, list) and "Code" in allTeams.keys():
		print("%s: %s" % (allTeams["Code"], allTeams["Description"]))
	else : hasAnyTeamData = True

	if not hasAnyTeamData: return teams

	activeTeamKeys = []
	for team in activeTeams:
		activeTeamKeys.append(deunicode(team["Key"]).upper())

	for team in allTeams:
		if league == LEAGUE_NFL and team.get("TeamID") == 18:
			# Skip dead team (bad data)
			continue

		active = deunicode(team["Key"]).upper() in activeTeamKeys

		city = deunicode(team["City"])
		if not city:
			continue

		key = abbrev = deunicode(team["Key"]).upper()
		name = deunicode(team["Name"])
		fullName = deunicode(team.get("FullName")) or "%s %s" % (deunicode(city), deunicode(name))
			
		aliases = []

		if league == LEAGUE_NBA and city == "Team":
			fullName = name = "%s %s" % (city, name)
			city = "All Stars"

		if sdio_abbreviation_corrections.get(league):
			if sdio_abbreviation_corrections[league].get(abbrev):
				aliases.append(abbrev)
				key = abbrev = sdio_abbreviation_corrections[league][abbrev]

		conference = deunicode(team.get("Conference") or team.get("League"))
		if conference == "None": conference = None
		division = deunicode(team["Division"])
		if division and (division == "None" or division == conference): division = None


		kwargs = {
			"key": key,
			"abbreviation": abbrev,
			"active": active,
			"name": name,
			"fullName": fullName,
			"city": city,
			"conference": conference,
			"division": division,
			"SportsDataIOID": str(team["TeamID"]),
			}

		if team.get("NbaDotComTeamID"): kwargs["NBAdotcomID"] = str(team["NbaDotComTeamID"])

		if aliases:
			kwargs["aliases"] = list(set(aliases))


		assets = dict()
		if team.get("WikipediaWordMarkUrl"):
			assets.setdefault("wordmark", [])
			assets["wordmark"].append({"source": "wikipedia", "url": deunicode(team["WikipediaWordMarkUrl"])})
		if team.get("WikipediaLogoUrl"):
			assets.setdefault("logo", [])
			assets["logo"].append({"source": "wikipedia", "url": deunicode(team["WikipediaLogoUrl"])})

		colors = []
		if team.get("PrimaryColor"): colors.append({"source": ASSET_SOURCE_SPORTSDATAIO, "colortype": ASSET_COLOR_TYPE_PRIMARY, "value": "#"+team["PrimaryColor"]})
		if team.get("SecondaryColor"): colors.append({"source": ASSET_SOURCE_SPORTSDATAIO, "colortype": ASSET_COLOR_TYPE_SECONDARY, "value": "#"+team["SecondaryColor"]})
		if team.get("TertiaryColor"): colors.append({"source": ASSET_SOURCE_SPORTSDATAIO, "colortype": ASSET_COLOR_TYPE_TERTIARY, "value": "#"+team["TertiaryColor"]})
		if team.get("QuaternaryColor"): colors.append({"source": ASSET_SOURCE_SPORTSDATAIO, "colortype": ASSET_COLOR_TYPE_QUATERNARY, "value": "#"+team["QuaternaryColor"]})
		if colors: assets[ASSET_TYPE_COLORS] = colors
			
		if assets:
			kwargs["assets"] = assets

		teams[key] = kwargs

	return teams