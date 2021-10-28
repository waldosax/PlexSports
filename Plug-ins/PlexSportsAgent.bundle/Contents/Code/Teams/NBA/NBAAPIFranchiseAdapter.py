# NBA.com API
# TEAMS

import json
from datetime import datetime, date, time

from Constants import *
from Constants.Assets import *
from StringUtils import *
from Data.NBA.NBAAPIDownloader import *


__prodLogoTemplate = "https://cdn.nba.com/logos/nba/{teamId}/{local}/L/logo.svg"



def DownloadAllFranchises(league):

	# Get all NBA franchises, including histories
	nbaapiFranchiseHistory = dict()
	nbaapiFranchiseHistoryJson = DownloadAllFranchiseInfo()
	try: nbaapiFranchiseHistory = json.loads(nbaapiFranchiseHistoryJson)
	except: pass

	# Get SPA config, including all teams 
	nbaapiSPAConfig = dict()
	nbaapiSPAConfigJson = DownloadSPAConfig()
	try: nbaapiSPAConfig = json.loads(nbaapiSPAConfigJson)
	except: pass

	# Get Teams supplement
	nbaapiTeamsSupplement = dict()
	nbaapiTeamsSupplementJson = DownloadTeamsSupplement()
	try: nbaapiTeamsSupplement = json.loads(nbaapiTeamsSupplementJson)
	except: pass

	franchises = dict()

	__prodLogoTemplate = deunicode(nbaapiSPAConfig["ENV"]["PROD"]["TEAM_LOGO_URL"])

	spaLookup = {
		"byTeamID": dict(),
		"byAbbreviation": dict(),
		"byFullName": dict(),
		"allStar": dict()
		}
	for spaTeam in nbaapiSPAConfig["teams"].values():
		isIntl = spaTeam.get("isintl")
		if isIntl == True: continue

		abbrev = deunicode(spaTeam.get("code"))
		city = deunicode(spaTeam["city"])
		name = deunicode(spaTeam["name"])
		fullName = deunicode("%s %s" % (spaTeam["city"], spaTeam["name"]))

		if "id" in spaTeam.keys():
			spaLookup["byTeamID"][int(spaTeam["id"])] = spaTeam
		if "code" in spaTeam.keys():
			spaLookup["byAbbreviation"][abbrev] = spaTeam

		if city in ["All-Star", "All Stars", "Rising Stars"]:
			spaLookup["allStar"][abbrev] = spaTeam

		spaLookup["byFullName"][fullName] = spaTeam


	supplement = {
		"byTeamID": dict(),
		"byAbbrev": dict()
		}
	for supplementalTeam in nbaapiTeamsSupplement["league"]["standard"]:
		#if supplementalTeam.get("isNBAFranchise") == False: continue
		if supplementalTeam["confName"] == "Intl": continue
		teamID = deunicode(supplementalTeam["teamId"])
		abbrev = deunicode(supplementalTeam["tricode"])
		supplement["byTeamID"][teamID] = supplementalTeam
		supplement["byAbbrev"][abbrev] = supplementalTeam



	resultSets = dict()
	for resultSet in nbaapiFranchiseHistory["resultSets"]:
		resultSetName = resultSet["name"]
		resultSets[resultSetName] = resultSet
		pass

	# Screw PANDAS
	dataSets = {
		"FranchiseHistory": {
			"active": True,
			"key_indices": __get__resultset_key_indices(resultSets["FranchiseHistory"]),
			"rows": resultSets["FranchiseHistory"]["rowSet"]
			},
		"DefunctTeams": {
			"active": False,
			"key_indices": __get__resultset_key_indices(resultSets["DefunctTeams"]),
			"rows": resultSets["DefunctTeams"]["rowSet"]
			}
		}

	for dataSet in dataSets.values():
		active = dataSet["active"]

		keys = dataSet["key_indices"]
		lastTeamID = None
		currentFranchise = None

		for dataRow in dataSet["rows"]:
			teamID = dataRow[keys["TEAM_ID"]]
			city = deunicode(dataRow[keys["TEAM_CITY"]])
			name = deunicode(dataRow[keys["TEAM_NAME"]])
			fullName = deunicode("%s %s" % (city, name))

			if lastTeamID == None or teamID != lastTeamID:

				# If franchise did not have any child teams, synthesize one
				if lastTeamID != None and currentFranchise != None and len(currentFranchise["teams"]) == 0:
					lastFullName = currentFranchise["name"]
					team = __synthesize_team_from_franchise(currentFranchise, spaLookup)
					team.setdefault("key", team["abbreviation"] if team.get("abbreviation") else str(lastTeamID))
					supplementalTeam = __supplement_team(team, supplement, str(lastTeamID), None)
					currentFranchise["teams"][lastFullName] = team

				# New Team ID indicates a franchise
				currentFranchise = {
					"name": fullName,
					"active": active,
					"fromYear": int(dataRow[keys["START_YEAR"]]),
					"toYear": int(dataRow[keys["END_YEAR"]]),
					"_NBAdotcomID": teamID, # Just for context
					"_city": city, # Just for context
					"_name": name, # Just for context
					"teams": dict()
					}
				franchises[fullName] = currentFranchise
			else:
				if fullName in currentFranchise["teams"].keys():
					team = currentFranchise["teams"][fullName]
				else:
					# Add team to franchise
					teamActive = active and len(currentFranchise["teams"]) == 0
					team = {
						"fullName": fullName,
						"city": city,
						"name": name,
						"active": teamActive,
						"identity": {"NBAAPIID": teamID},
						"years": [],
						"aliases": [],
						"assets": {}
						}

					# Fold in SPA team
					spaTeam = __find_spa_team(spaLookup, teamID=teamID, fullName=fullName)
					if spaTeam:
						__fold_in_spa_team(team, spaTeam)

					supplementalTeam = __supplement_team(team, supplement, teamID, team.get("abbreviation")) if teamActive else None



					team.setdefault("key", team["abbreviation"] if team.get("abbreviation") else str(teamID))

					currentFranchise["teams"][fullName] = team

				if fullName == "Charlotte Hornets":
					# Data correction to account for name change to Charlotte Bobcats (2004-2013)
					# and back again to Charlotte Hornets (2014)
					__append_year_set(team, int(dataRow[keys["START_YEAR"]]), 2001)
					__append_year_set(team, 2014, int(dataRow[keys["END_YEAR"]]))
				elif fullName == "New Orleans Hornets":
					# Data correction to account for new franchise (New Orleans Hornets),
					# but also the location change due to damage from Hurricane Katrina (2005-2006)
					# and return in 2007
					__append_year_set(team, int(dataRow[keys["START_YEAR"]]), 2004)
					__append_year_set(team, 2007, int(dataRow[keys["END_YEAR"]]))
				else:
					__append_year_set(team, int(dataRow[keys["START_YEAR"]]), int(dataRow[keys["END_YEAR"]]))

			lastTeamID = teamID


		# Catch any stragglers
		if currentFranchise != None and len(currentFranchise["teams"]) == 0:
			# Franchise did not have any child teams, so synthesize one
			lastFullName = currentFranchise["name"]
			team = __synthesize_team_from_franchise(currentFranchise, spaLookup)
			team.setdefault("key", team["abbreviation"] if team.get("abbreviation") else str(teamID))
			supplementalTeam = __supplement_team(team, supplement, teamID, team.get("abbreviation"))
			currentFranchise["teams"][lastFullName] = team


	# Incorporate All-Star/Rising Stars teams
	for allStarTeam in spaLookup["allStar"].values():
		active = False

		abbrev = deunicode(allStarTeam.get("code"))
		teamID = allStarTeam.get("id") or abbrev
		supplementalTeam = __supplement_team(team, supplement, teamID, abbrev)


		teamID = teamID or supplementalTeam.get("teamId") if supplementalTeam else abbrev

		name = deunicode(allStarTeam["name"])
		city = deunicode(allStarTeam["city"])
		fullName = "%s %s" % (city, name)

		conference = deunicode(allStarTeam["conference"]) if allStarTeam.get("conference") else None
		division = deunicode(allStarTeam["division"]) if allStarTeam.get("division") else None
			
		team = {
				"active": active,
				"abbreviation": abbrev,
				"fullName": fullName,
				"city": city,
				"NBAAPIID": teamID,
				"aliases": [],
				"assets": {}
				}

		if city in ["All Stars", "Rising Stars"]:
			team["fullName"] = name
			fullName = name
		if city == "All-Star":
			team["conference"] = "%sern" % name
			team["active"] = True

		if supplementalTeam:
			altCityName = deunicode(supplementalTeam.get("altCityName") or "")
			if altCityName and altCityName != team["city"] and altCityName != team["fullName"] and altCityName not in team["aliases"]:
				team["aliases"].append(altCityName)

		__fold_in_spa_team(team, allStarTeam)

		franchise = {
			"name": fullName,
			"active": False,
			"teams": {
				fullName: team
				}
			}

		team.setdefault("key", teamID)
		franchises[fullName] = franchise


	return franchises

def __get__resultset_key_indices(resultSet):
	key_indices = dict()
	i = 0
	for key in resultSet["headers"]:
		key_indices[key] = i
		i += 1
	return key_indices

def __fold_in_spa_team(team, spaTeam):
	assets = team["assets"]
	aliases = team["aliases"]

	team.setdefault("name", deunicode(spaTeam["name"]))
	team.setdefault("city", deunicode(spaTeam["city"]))
	team.setdefault("fullName", deunicode("%s %s" % (spaTeam["city"], spaTeam["name"])))


	if team.get("active") == True:
		team.setdefault("abbreviation", deunicode(spaTeam.get("code")))
		team.setdefault("conference", deunicode(spaTeam["conference"]) if spaTeam.get("conference") else None)
		team.setdefault("division", deunicode(spaTeam["division"]) if spaTeam.get("division") else None)

	if spaTeam.get("color"):
		assets["colors"] = [
			{"source": ASSET_SOURCE_NBAAPI, "colortype": ASSET_COLOR_TYPE_PRIMARY, "value": deunicode(spaTeam["color"])}
			]
	# TODO: See if logos apply to defunct IDs
	if spaTeam.get("id"):
		assets["logo"] = [
			{"source":ASSET_SOURCE_NBAAPI, "url": __prodLogoTemplate.replace("{teamId}", spaTeam["id"]).replace("{local}", "primary")}
			]

	team["aliases"] = list(set(aliases))

	if not "key" in team.keys() and team.get("abbreviation"):
		team["key"] = team["abbreviation"]
	pass

def __find_spa_team(spaLookup, teamID=None, abbrev=None, fullName=None):
	if teamID and teamID in spaLookup["byTeamID"].keys():
		return spaLookup["byTeamID"][teamID]
	if abbrev and abbrev in spaLookup["byabbreviation"].keys():
		return spaLookup["byabbreviation"][fullName]
	if fullName and fullName in spaLookup["byFullName"].keys():
		return spaLookup["byFullName"][fullName]
	return None

def __append_year_set(team, fromYear, toYear):
	team.setdefault("years", [])
	team["years"].append({"fromYear": fromYear, "toYear": toYear})
	pass

def __synthesize_team_from_franchise(franchise, spaLookup):
	fullName = franchise["name"]
	teamID = franchise["_NBAdotcomID"]

	team = {
		"fullName": fullName,
		"city": franchise["_city"],
		"name": franchise["_name"],
		"active": franchise["active"],
		"identity": {"NBAAPIID": teamID},
		"years": [],
		"aliases": [],
		"assets": {}
		}

	# Fold in SPA team
	spaTeam = __find_spa_team(spaLookup, teamID=teamID, fullName=fullName)
	if spaTeam:
		__fold_in_spa_team(team, spaTeam)

	__append_year_set(team, franchise["fromYear"], franchise["toYear"])

	return team

def __supplement_team(team, supplement, teamID, abbrev=None):
	supplementalTeam = supplement["byTeamID"].get(str(teamID)) if teamID else supplement["byAbbrev"].get(abbrev) or supplement["byAbbrev"].get(abbrev)
	if not supplementalTeam: return None

	variants = []
	variants.append(deunicode(supplementalTeam.get("tricode")))
	if supplementalTeam.get("teamShortName") != supplementalTeam.get("fullName"):
		variants.append(deunicode(supplementalTeam.get("teamShortName")))
	if supplementalTeam.get("teamShortName") != supplementalTeam.get("city"):
		variants.append(deunicode(supplementalTeam.get("teamShortName")))
	if supplementalTeam.get("altCityName") != supplementalTeam.get("city"):
		variants.append(deunicode(supplementalTeam.get("altCityName")))
	variants.append(deunicode(supplementalTeam.get("nickname")))
	variants.append(deunicode(supplementalTeam.get("fullName")))
	if supplementalTeam.get("altCityName") != supplementalTeam.get("fullName"):
		variants.append(deunicode("%s %s" % (supplementalTeam.get("altCityName"), supplementalTeam.get("nickname"))))

	aliases = team["aliases"]
	variants = list(set(variants))
	for variant in variants:
		if variant == "Team": continue
		if variant == team["abbreviation"]: continue
		if variant == team["city"]: continue
		if variant == team["name"]: continue
		if variant == team["fullName"]: continue
		if variant in aliases: continue
		aliases.append(variant)

	return supplementalTeam














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
		else:
			if city == "LA" and name == "LA Clippers":
				city = "Los Angeles"
				name = "Clippers"
			fullName = deunicode("%s %s" % (city, name))
		team = {
			"key": abbrev,
			"NBAAPIID": str(teamId or abbrev),
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