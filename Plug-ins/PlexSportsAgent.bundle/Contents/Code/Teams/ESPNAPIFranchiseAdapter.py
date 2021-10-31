# ESPN.com API
# TEAMS
import json
from datetime import datetime, date, time

from Constants import *
from Constants.Assets import *
from StringUtils import *
from Data.ESPNAPIDownloader import *

espnapi_abbreviation_corrections = {
	LEAGUE_NBA: {
		"GS": "GSW",
		"NO": "NOP",
		"NY": "NYK",
		"SA": "SAS",
		"UTAH": "UTA",
		"WSH": "WAS",
		},
	LEAGUE_NFL: {
		"WSH": "WAS",
		}
	}

def DownloadAllTeams(league):

	# Get teams from ESPN API
	response = dict()
	responseJson = DownloadAllTeamsForLeague(league)
	try: response = json.loads(responseJson)
	except: pass

	teams = dict()
	for apiTeamWrapper in response["sports"][0]["leagues"][0]["teams"]:
		apiTeam = apiTeamWrapper["team"]

		teamId = deunicode(apiTeam["id"])

		isActive = apiTeam["isActive"]
		key = abbrev = deunicode(apiTeam["abbreviation"])
		fullName = deunicode(apiTeam["displayName"])
		name = deunicode(apiTeam.get("name"))
		city = deunicode(apiTeam["location"])

		aliases = []

		if league in espnapi_abbreviation_corrections.keys():
			if key in espnapi_abbreviation_corrections[league].keys():
				aliases.append(key)
				key = abbrev = espnapi_abbreviation_corrections[league][key]

		if league == LEAGUE_NFL:
			if city == "Washington" and name == None:
				name = "Football Team"
				fullName = "Washington Football Team"

		team = {
			"key": key,
			"ESPNAPIID": teamId,
			"active": isActive,
			"fullName": fullName,
			"name": name,
			"city": city,
			"abbreviation": abbrev,
			}

		nickname = deunicode(apiTeam.get("nickname") or "")
		if nickname and not nickname in [city, name, fullName, abbrev]:
			aliases.append(nickname)
		shortDisplayName = deunicode(apiTeam.get("shortDisplayName") or "")
		if shortDisplayName and not shortDisplayName in [city, name, fullName, abbrev]:
			aliases.append(shortDisplayName)

		if aliases: team["aliases"] = list(set(aliases))


		assets = dict()

		if apiTeam.get("color"):
			assets.setdefault("colors", [])
			assets["colors"].append({"source": ASSET_SOURCE_ESPNAPI, "colortype": ASSET_COLOR_TYPE_PRIMARY, "value": "#" + deunicode(apiTeam["color"])})
		if apiTeam.get("alternateColor"):
			assets.setdefault("colors", [])
			assets["colors"].append({"source": ASSET_SOURCE_ESPNAPI, "colortype": ASSET_COLOR_TYPE_SECONDARY, "value": "#" + deunicode(apiTeam["alternateColor"])})

		if apiTeam.get("logos"):
			logo = apiTeam["logos"][0]
			assets.setdefault("logo", [])
			assets["logo"].append({"source": ASSET_SOURCE_ESPNAPI, "url": deunicode(logo["href"])})

		if assets: team["assets"] = assets

		teams[fullName] = team


	return teams


def CorrectNFLFranchiseHistory(league, franchises, espnapiTeams):
	for franchise in franchises.values():
		franchiseName = franchise.name
		if not franchiseName in espnapiTeams.keys(): continue
		if len(franchise.teams) < 2: continue

		activeTeam = franchise.teams[franchiseName]
		espnapiTeam = espnapiTeams[franchiseName]

		for teamName in franchise.teams.keys():
			team = franchise.teams[teamName]
			if teamName == franchiseName: continue
			for span in team.years:
				fromYear = int(span.fromYear)
				teamID = espnapiTeam["ESPNAPIID"]

				# Get team from ESPN API as of season
				espnapiTeamAsOf = dict()
				espnapiTeamAsOfJson = DownloadTeamForLeagueInSeason(league, fromYear, teamID, teamName)
				try: espnapiTeamAsOf = json.loads(espnapiTeamAsOfJson)
				except: pass

				if not espnapiTeamAsOf: continue
				if activeTeam.fullName == deunicode(espnapiTeamAsOf["displayName"]): continue
				if espnapiTeamAsOf["displayName"] == espnapiTeamAsOf["location"]: continue

				teamAsOf = {
					"city": espnapiTeamAsOf["location"],
					"name": espnapiTeamAsOf["name"],
					"fullName": espnapiTeamAsOf["displayName"],
					"abbreviation": espnapiTeamAsOf["abbreviation"]
					}

				team.identity.ESPNAPIID = "%s.%s" % (teamID, fromYear)

				if not team.abbreviation and activeTeam.abbreviation != deunicode(teamAsOf["abbreviation"]): team.abbreviation = deunicode(teamAsOf["abbreviation"])
				
				for testKey in teamAsOf.keys():
					indexOfKey = __list_indexOf(activeTeam.aliases, teamAsOf[testKey])
					if indexOfKey >= 0: del(activeTeam.aliases[indexOfKey])

				if team.city != teamAsOf["city"]: team.city = deunicode(teamAsOf["city"])
				if team.name != teamAsOf["name"]: team.name = deunicode(teamAsOf["name"])

				if espnapiTeamAsOf.get("color") and not __list_has(team.assets.colors, **{"colortype": ASSET_COLOR_TYPE_PRIMARY, "source": ASSET_SOURCE_ESPNAPI}):
					team.assets.colors.append({"colortype": ASSET_COLOR_TYPE_PRIMARY, "source": ASSET_SOURCE_ESPNAPI, "value": deunicode("#%s" % espnapiTeamAsOf["color"])})
				if espnapiTeamAsOf.get("alternateColor") and not __list_has(team.assets.colors, **{"colortype": ASSET_COLOR_TYPE_SECONDARY, "source": ASSET_SOURCE_ESPNAPI}):
					team.assets.colors.append({"colortype": ASSET_COLOR_TYPE_SECONDARY, "source": ASSET_SOURCE_ESPNAPI, "value": deunicode("#%s" % espnapiTeamAsOf["alternateColor"])})

				if espnapiTeamAsOf.get("logos") and not __list_has(team.assets.logo, **{"source": ASSET_SOURCE_ESPNAPI}):
					logo = espnapiTeamAsOf["logos"][0]
					team.assets.logo.append({"source": ASSET_SOURCE_ESPNAPI, "url": deunicode(logo["href"])})

	pass

def __list_indexOf(lst, item):
	try: return lst.index(item)
	except ValueError: return -1

def __list_findIndex(lst, **kwargs):
	i=0
	for itm in lst:
		xdct = itm if isinstance(itm, (dict)) else itm.__dict__
		foundItem = None
		for key in kwargs.keys():
			if foundItem == False: break
			if not key in xdct.keys(): foundItem = False
			if xdct[key] != kwargs[key]: foundItem = False
			else: foundItem = True

		if foundItem == True: return i
		i = i + 1
	
	return -1

def __list_find(lst, **kwargs):
	index = __list_findIndex(lst, **kwargs)
	if index >= 0: return lst[index]
	return None

def __list_has(lst, **kwargs):
	return __list_findIndex(lst, **kwargs) >= 0