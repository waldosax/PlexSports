# MLB API (statsapi.mlb.com)
# TEAMS

import uuid
import json
from datetime import datetime, date, time
import hashlib

from Constants import *
from StringUtils import *
from Data.MLB.MLBAPIDownloader import *


MLBAPI_SPORTID_MLB = 1


mlbapi_abbreviation_corrections = {
	LEAGUE_MLB: {
		"CHW": "CWS"
		}
	}


def DownloadAllFranchises(league):

	# Get all teams for current season
	mlbapiAllTeams = dict()
	mlbapiAllTeamsJson = DownloadAllTeams()
	try: mlbapiAllTeams = json.loads(mlbapiAllTeamsJson)
	except: pass

	# Get max id
	maxId = 0
	if mlbapiAllTeams and mlbapiAllTeams.get("teams"):
		for team in mlbapiAllTeams["teams"]:
			id = team.get("id") or 0
			if id > maxId: maxId = id

	# Get range from 1 through max id
	teamIds = []
	for teamId in range(1, maxId+1):
		teamIds.append(str(teamId))



	# Get team history for all ids in range (relevant fields only)
	mlbapiTeamHistories = dict()
	mlbapiTeamHistoriesJson = DownloadTeamHistories(teamIds, ["teams","id","teamCode","sport","league","name","teamName","clubName","season","abbreviation","teamName","shortName","clubName","active"])
	try: mlbapiTeamHistories = json.loads(mlbapiTeamHistoriesJson)
	except: pass

	# Filter histories for non-MLB teams
	histories = dict()
	if mlbapiTeamHistories and mlbapiTeamHistories.get("teams"):
		teamHistories = mlbapiTeamHistories["teams"]
		for i in range(len(teamHistories)-1, -1, -1):
			teamHistory = teamHistories[i]
			# If sport id != 1 (Pro baseball), remove
			if not teamHistory.get("sport") or not teamHistory["sport"].get("id") or teamHistory["sport"]["id"] != MLBAPI_SPORTID_MLB:
				del(teamHistories[i])
				continue
			# If doesn't have league id, remove
			if not teamHistory.get("league") or not teamHistory["league"].get("id"):
				del(teamHistories[i])
				continue

			#if teamHistory["name"] != "%s %s" % (teamHistory["shortName"], teamHistory["clubName"]):
			#	print("0-name:%s|teamName:%s|shortName:%s|clubName:%s" % (teamHistory["name"], teamHistory["teamName"], teamHistory["shortName"], teamHistory["clubName"]))
			#elif teamHistory["name"][-len(teamHistory["clubName"]):] != teamHistory["clubName"]:
			#	print("1-name:%s|teamName:%s|shortName:%s|clubName:%s" % (teamHistory["name"], teamHistory["teamName"], teamHistory["shortName"], teamHistory["clubName"]))
			#if teamHistory["teamName"] != teamHistory["clubName"]:
			#	print("2-name:%s|teamName:%s|shortName:%s|clubName:%s" % (teamHistory["name"], teamHistory["teamName"], teamHistory["shortName"], teamHistory["clubName"]))

			# If teamHistory is an MLB team, add it to histories dictionary
			# histories[franchiseId][season] = teamHistory
			histories.setdefault(teamHistory["id"], dict())
			histories[teamHistory["id"]][teamHistory["season"]] = teamHistory




	# Shape teams for current season into top-level franchises
	franchises = dict()
	activeTeamIds = []

	apiTeams = mlbapiAllTeams["teams"]

	mlbapiAllStarTeams = dict()
	mlbapiAllStarTeamsJson = DownloadTeamsByID(["159", "160"])
	try: mlbapiAllStarTeams = json.loads(mlbapiAllStarTeamsJson)
	except: pass
	if mlbapiAllStarTeams: apiTeams = apiTeams + mlbapiAllStarTeams["teams"]

	for apiTeam in apiTeams:

		currentSeason = maxSeason = apiTeam["season"]
		minSeason = 0
		seasonTracking = dict()

		aliases = []
		key = uuid.uuid4()
		abbrev = deunicode(apiTeam["abbreviation"])
		if mlbapi_abbreviation_corrections.get(league):
			if mlbapi_abbreviation_corrections[league].get(abbrev):
				aliases.append(abbrev)
				abbrev = sdio_abbreviation_corrections[league][abbrev]
		
		allStar = apiTeam.get("allStarStatus") == "Y"
		active = apiTeam["active"]

		# name:				Arizona Diamondbacks
		# teamName:			D-backs
		# shortName:		Arizona
		# franchiseName:	Arizona
		# clubName:			Diamondbacks
		# locationName:		Phoenix

		# name:				(None)
		# teamName:			NL All-Stars
		# shortName:		NL All-Stars
		# franchiseName:	National
		# clubName:			National
		# locationName:		Washington

		fullName = None
		city = None
		name = None
		teamName = None
		conference = None
		division = None

		if allStar:
			teamName = deunicode(apiTeam["teamName"])
			fullName = teamName
			city = deunicode(apiTeam["franchiseName"]) + " League"
			team = fullName[len(abbrev):].lstrip()
			conference = deunicode(apiTeam["league"]["name"])
			aliases.append("%s %s" % (city, team))
		else:
			teamName = deunicode(apiTeam["teamName"])
			fullName = deunicode(apiTeam["name"])
			name = deunicode(apiTeam["clubName"])
			city = deunicode(name[:-len(apiTeam["clubName"])].rstrip())
			conference = deunicode(apiTeam["league"]["name"])
			division = deunicode(apiTeam["division"]["name"])
			if teamName != name:
				aliases + [teamName, "%s %s" % (city, teamName)]

		franchise = {
			"name": fullName,
			"active": active,
			}

		teamId = apiTeam["id"]
		activeTeamIds.append(teamId)
		team = {
			"MLBAPIID": teamId,
			"active": True,
			"allStar": allStar,
			"fullName": fullName,
			"name": name,
			"city": city,
			"abbreviation": abbrev,
			"key": key,
			"conference": conference,
			"division": division,
			"years": []
			}

		if apiTeam["shortName"] != team["city"]: aliases.append(deunicode(apiTeam["shortName"]))
		if apiTeam["teamName"] != apiTeam["clubName"]: aliases.append(deunicode(apiTeam["teamName"]))
		if aliases: team["alisases"] = list(set(aliases))

		teams = dict()
		teams[name] = team

		# Collect inactive variants on active teams
		if teamId in histories.keys():
			for historySeason in sorted(histories[teamId].keys()):
				if historySeason == currentSeason: continue

				historicalTeam = histories[teamId][historySeason]
				fullName = deunicode(historicalTeam["name"])
				teamName = deunicode(historicalTeam["teamName"])
				seasonTracking.setdefault(int(historySeason), fullName)

				if fullName in teams.keys(): continue
				teamCode = deunicode(historicalTeam["teamCode"])
				inactiveID = "%s.%s.%s" % (teamId, teamCode, hashlib.md5(fullName.encode()).hexdigest()[:6])
				team = {
					"MLBAPIID": inactiveID,
					"active": False,
					"fullName": fullName,
					"name": teamName,
					"city": deunicode(fullName[:-len(teamName)].rstrip()),
					"years": []
					}
				teams.setdefault(fullName, team)




		# BackFill Years
		# Doing it this way should roll up venue changes as well.
		seasonTracking.setdefault(currentSeason, name)
		seasons = list(sorted(seasonTracking.keys()))
		for i in range(1, len(seasonTracking)):
			toYear = int(seasons[i])
			if toYear < maxSeason: toYear = toYear - 1
			fromYear = int(seasons[i-1])
			key = seasonTracking[seasons[i-1]]
			teams[key]["years"].append({"fromYear": fromYear, "toYear": toYear})
			if minSeason == 0: minSeason = fromYear
			elif fromYear < minSeason: minSeason = fromYear
		if minSeason == 0: minSeason = int(apiTeam["firstYearOfPlay"])
		franchise["fromYear"] = minSeason
		franchise["toYear"] = maxSeason






		franchise["teams"] = teams
		franchises[name] = franchise


		# *****************************************************
		# SCREW THIS
		# All of these inactive franchises are from before THE INVENTION OF THE TELEVISION
		#
		# FUCKEM.
		# *****************************************************
		## Create franchise dictionaries for inactive franchises
		##inactiveHistory = dict()
		##for historicalFranchiseId in sorted(histories.keys()):
		##	if historicalFranchiseId in activeTeamIds: continue
		##	inactiveHistory.setdefault(historicalFranchiseId, histories[historicalFranchiseId])


	return franchises