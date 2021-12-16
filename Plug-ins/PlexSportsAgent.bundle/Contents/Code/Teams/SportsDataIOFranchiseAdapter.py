# TheSportsDB.com
# TEAMS

import uuid
import json
from datetime import datetime, date, time

from Constants import *
from Constants.Assets import *
from StringUtils import *
from Data.SportsDataIODownloader import *

sdio_data_corrections = {
	LEAGUE_MLB: {
		"CHW": {
			"abbreviation": "CWS"
			}
		},
	LEAGUE_NBA: {
		"LEB": {
			"abbreviation": "LBN"
			},
		"DUR": {
			"abbreviation": "DRT",
			"nbaDotComTeamID": 1610616833
			},
		"LAC": {
			"city": "LA",
			"name": "Clippers",
			"fullName": "LA Clippers",
			}
		},
	LEAGUE_NHL: {
		"TAM": {
			"aliases": ["TB"]
			},
		"TB": {
			"aliases": ["TB"]
			},
		"MON": {
			"abbreviation": "MTL",
			},
		"NAS": {
			"abbreviation": "NSH",
			},
		"SJ": {
			"abbreviation": "SJS",
			},
		"VEG": {
			"abbreviation": "VGK",
			},
		"WAS": {
			"abbreviation": "WSH",
			},
		},
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


		city = deunicode(team["City"])
		if not city:
			continue

		key = uuid.uuid4()
		abbrev = deunicode(team["Key"]).upper()
		name = deunicode(team["Name"])
		fullName = deunicode(team.get("FullName")) or "%s %s" % (deunicode(city), deunicode(name))
		
		allStar = False
		if league == LEAGUE_MLB: allStar = abbrev.upper() in ["AL", "NL"]
		elif league == LEAGUE_NBA: allStar = city == "Team"
		elif league == LEAGUE_NFL: allStar = abbrev.upper() in ["AFC", "NFC"]
		active = allStar or abbrev.upper() in activeTeamKeys


		teamID = team["TeamID"]
		nbaDotComTeamID = team.get("NbaDotComTeamID")

		aliases = []

		if league == LEAGUE_NBA and city == "Team":
			name = "%s %s" % (city, name)
			city = "All Stars"
			fullName = "%s %s" % (city, name)

		if sdio_data_corrections.get(league):
			if sdio_data_corrections[league].get(abbrev):
				if sdio_data_corrections[league][abbrev].get("city"):
					city = sdio_data_corrections[league][abbrev]["city"]
				if sdio_data_corrections[league][abbrev].get("name"):
					name = sdio_data_corrections[league][abbrev]["name"]
				if sdio_data_corrections[league][abbrev].get("fullName"):
					fullName = sdio_data_corrections[league][abbrev]["fullName"]
				if sdio_data_corrections[league][abbrev].get("nbaDotComTeamID"):
					nbaDotComTeamID = sdio_data_corrections[league][abbrev]["nbaDotComTeamID"]
				if sdio_data_corrections[league][abbrev].get("abbreviation"):
					aliases.append(abbrev)
					abbrev = sdio_data_corrections[league][abbrev]["abbreviation"]
				if sdio_data_corrections[league][abbrev].get("aliases"):
					aliases = list(set(aliases = sdio_data_corrections[league][abbrev]["aliases"]))

		conference = deunicode(team.get("Conference") or team.get("League"))
		if conference == "None": conference = None
		division = deunicode(team["Division"])
		if division and (division == "None" or division == conference): division = None


		kwargs = {
			"key": key,
			"abbreviation": abbrev,
			"active": active,
			"allStar": allStar,
			"name": name,
			"fullName": fullName,
			"city": city,
			"conference": conference,
			"division": division,
			"SportsDataIOID": str(teamID),
			}

		if nbaDotComTeamID: kwargs["NBAAPIID"] = str(nbaDotComTeamID)

		__add_potential_alias(kwargs, aliases, team, "DraftKingsName")
		__add_potential_alias(kwargs, aliases, team, "FanDuelName")
		__add_potential_alias(kwargs, aliases, team, "YahooName")

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

def __add_potential_alias(kwargs, aliases, team, key):
	if team.get(key):
		value = deunicode(team[key])
		if value == "Scrambled": return
		if value == kwargs["fullName"]: return
		if value == kwargs["city"]: return
		if value == kwargs["name"]: return
		if value in aliases: return
		aliases.append(value)