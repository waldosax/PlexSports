# NBA.com API
# TEAMS

import json
from datetime import datetime, date, time

from Constants import *
from Constants.Assets import *
from StringUtils import *
from Data.NBA.NBAAPIDownloader import *



def DownloadAllTeams(league):

	# Get SPA config, including all teams 
	nbaapiSPAConfig = dict()
	nbaapiSPAConfigJson = DownloadSPAConfig()
	try: nbaapiSPAConfig = json.loads(nbaapiSPAConfigJson)
	except: pass

	prodLogoTemplate = nbaapiSPAConfig["ENV"]["PROD"]["TEAM_LOGO_URL"]

	teams = dict()
	for apiTeam in nbaapiSPAConfig["teams"].values():

		isIntl = apiTeam.get("isintl")
		if isIntl == True: continue

		isActive = False
		if apiTeam["conference"] and apiTeam["division"]: isActive = True
		abbrev = deunicode(apiTeam["code"])
		teamId = deunicode(apiTeam.get("id") or "") or None
		name = deunicode(apiTeam["name"])
		city = deunicode(apiTeam["city"])
		if city == "All Stars": fullName = name
		else: fullName = deunicode("%s %s" % (city, name))
		team = {
			"key": abbrev,
			"NBAdotcomID": str(teamId or abbrev),
			"active": isActive,
			"fullName": fullName,
			"name": name,
			"city": city,
			"abbreviation": abbrev,
			"conference": deunicode(apiTeam["conference"]),
			"division": deunicode(apiTeam["division"]),
			}

		assets = dict()

		if apiTeam.get("color"):
			assets["colors"] = [
				{"source": ASSET_SOURCE_NBAAPI, "colortype": ASSET_COLOR_TYPE_PRIMARY, "value": deunicode(apiTeam["color"])}
				]
		if teamId:
			assets["logo"] = [
				{"source":ASSET_SOURCE_NBAAPI, "url": prodLogoTemplate.replace("{teamId}", teamId).replace("{local}", "primary")}
				]

		if assets: team["assets"] = assets

		teams[fullName] = team


	return teams