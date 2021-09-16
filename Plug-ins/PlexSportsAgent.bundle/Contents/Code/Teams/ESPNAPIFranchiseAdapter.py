# ESPN.com API
# TEAMS

import json
from datetime import datetime, date, time

from Constants import *
from Constants.Assets import *
from StringUtils import *
from Data.ESPNAPIDownloader import *


def DownloadAllTeams(league):

	# Get SPA config, including all teams 
	response = dict()
	responseJson = DownloadAllTeamsForLeague(league)
	try: response = json.loads(responseJson)
	except: pass

	teams = dict()
	for apiTeamWrapper in response["sports"][0]["leagues"][0]["teams"]:
		apiTeam = apiTeamWrapper["team"]

		teamId = deunicode(apiTeam["id"])

		isActive = apiTeam["isActive"]
		abbrev = deunicode(apiTeam["abbreviation"])
		fullName = deunicode(apiTeam["displayName"])
		name = deunicode(apiTeam["name"])
		city = deunicode(apiTeam["location"])

		if league == LEAGUE_NBA:
			if city == "LA" and name == "Clippers":
				city = "Los Angeles"
				fullName = "Los Angeles Clippers"

		team = {
			"key": abbrev,
			"ESPNAPIID": teamId,
			"active": isActive,
			"fullName": fullName,
			"name": name,
			"city": city,
			"abbreviation": abbrev,
			}

		aliases = []

		nickname = deunicode(apiTeam.get("nickname") or "")
		if nickname and not nickname in [city, name, fullName]:
			aliases.append(nickname)
		shortDisplayName = deunicode(apiTeam.get("shortDisplayName") or "")
		if shortDisplayName and not shortDisplayName in [city, name, fullName]:
			aliases.append(shortDisplayName)

		if aliases: team["aliases"] = list(set(aliases))


		assets = dict()

		if apiTeam.get("color"):
			assets.setdefault("colors", [])
			assets["colors"].append({"source": ASSET_SOURCE_ESPNAPI, "colortype": ASSET_COLOR_TYPE_PRIMARY, "value": "#" + deunicode(apiTeam["color"])})
		if apiTeam.get("alternateColor"):
			assets.setdefault("colors", [])
			assets["colors"].append({"source": ASSET_SOURCE_ESPNAPI, "colortype": ASSET_COLOR_TYPE_SECONDARY, "value": "#" + deunicode(apiTeam["alternateColor"])})

		if assets: team["assets"] = assets

		teams[fullName] = team


	return teams