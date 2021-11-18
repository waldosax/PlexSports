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
	"CHW": "CWS"
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


	mlbapiAllStarTeams = dict()
	mlbapiAllStarTeamsJson = DownloadTeamsByID(["159", "160"])
	try: mlbapiAllStarTeams = json.loads(mlbapiAllStarTeamsJson)
	except: pass




	franchises = dict()
	apiTeams =mlbapiAllTeams["teams"]
	activeTeamIds = [] 

	# Shape teams for current season into top-level franchises
	for apiTeam in apiTeams:
		franchise = __process(apiTeam, histories, True)
		franchises[franchise["name"]] = franchise
		activeTeamIds.append(franchise["_MLBAPIID"])


	# Create franchise dictionaries for All-Star teams
	if mlbapiAllStarTeams:
		apiTeams = mlbapiAllStarTeams["teams"]
		for apiTeam in apiTeams:
			franchise = __process(apiTeam, histories, True)
			franchises[franchise["name"]] = franchise
			activeTeamIds.append(franchise["_MLBAPIID"])


	# Create franchise dictionaries for remaining inactive franchises
	for teamId in sorted(histories.keys()):
		if teamId in activeTeamIds: continue

		historyTeams = histories[teamId]
		apiTeam = historyTeams[historyTeams.keys()[-1]]
		franchise = __process(apiTeam, histories, False)
		franchises[franchise["name"]] = franchise

	return franchises


def __process(apiTeam, histories, active):

	currentSeason = maxSeason = apiTeam["season"]
	minSeason = 0
	seasonTracking = dict() # [season] = team.fullName

	parsedTeam = __parse(apiTeam)

	franchiseName = parsedTeam.fullName

	franchise = __create_franchise(parsedTeam)
	team = __create_team(parsedTeam, active)


	teams = dict()
	teams[franchiseName] = team

	# Collect inactive variants on active teams
	if parsedTeam.teamId in histories.keys():
		for historySeason in sorted(histories[parsedTeam.teamId].keys()):
			if historySeason == currentSeason: continue

			historicalTeam = histories[parsedTeam.teamId][historySeason]
			parsedHistorical = __parse(historicalTeam)

			seasonTracking.setdefault(int(historySeason), parsedHistorical.fullName)

			if parsedHistorical.fullName in teams.keys(): continue
			inactiveID = "%s.%s.%s" % (parsedHistorical.teamId, parsedHistorical.teamCode, hashlib.md5(parsedHistorical.fullName.encode()).hexdigest()[:6])

			team = __create_team(parsedHistorical, False)
			team["MLBAPIID"] = inactiveID
			teams.setdefault(parsedHistorical.fullName, team)




	# BackFill Years
	# Doing it this way should roll up venue changes as well.
	seasonTracking.setdefault(currentSeason, franchiseName)
	seasons = list(sorted(seasonTracking.keys()))
	for i in range(1, len(seasonTracking)):
		toYear = int(seasons[i])
		if toYear < maxSeason: toYear = toYear - 1
		fromYear = int(seasons[i-1])
		key = seasonTracking[seasons[i-1]]

		teams[key]["years"].append({"fromYear": fromYear, "toYear": toYear})

		if minSeason == 0: minSeason = fromYear
		elif fromYear < minSeason: minSeason = fromYear
	if minSeason == 0: minSeason = int(apiTeam["firstYearOfPlay"] if apiTeam.get("firstYearOfPlay") else 0)

	franchise["fromYear"] = minSeason
	franchise["toYear"] = maxSeason

	franchise["teams"] = teams

	return franchise


def __parse(apiTeam):
	class ParsedTeam:
		def __init__(self, apiTeam):
			self.teamId = apiTeam["id"]
			self.teamCode = apiTeam["teamCode"]
			self.season = apiTeam["season"]
			self.abbrev = deunicode(apiTeam["abbreviation"])
			self.allStar = apiTeam.get("allStarStatus") == "Y"
			self.active = apiTeam["active"]
			self.aliases = []

			if self.allStar:
				# name:				(None)
				# teamName:			NL All-Stars
				# shortName:		NL All-Stars
				# franchiseName:	National
				# clubName:			National
				# locationName:		Washington
				self.teamName = deunicode(apiTeam["teamName"])
				self.fullName = self.teamName
				self.city = deunicode(apiTeam["franchiseName"]) + " League"
				self.name = self.fullName[len(self.abbrev):].lstrip()
				self.conference = deunicode(apiTeam["league"]["name"])
				self.division = None
				self.aliases.append("%s %s" % (self.city, self.name))
			else:
				# name:				Arizona Diamondbacks
				# teamName:			D-backs
				# shortName:		Arizona
				# franchiseName:	Arizona
				# clubName:			Diamondbacks
				# locationName:		Phoenix
				self.teamName = deunicode(apiTeam["teamName"])
				self.fullName = deunicode(apiTeam["name"])
				self.name = deunicode(apiTeam["clubName"])
				self.city = deunicode(self.fullName[:-len(apiTeam["clubName"])].rstrip())
				self.conference = deunicode(apiTeam["league"]["name"])
				self.division = deunicode(apiTeam["division"]["name"]) if apiTeam.get("division") else None
				if self.teamName != self.name:
					self.aliases = self.aliases + [self.teamName, "%s %s" % (self.city, self.teamName)]

			if apiTeam["shortName"] != self.city: self.aliases.append(deunicode(apiTeam["shortName"]))
			if self.name and apiTeam["teamName"] != self.name: self.aliases.append(deunicode(apiTeam["teamName"]))
			self.aliases = list(set(self.aliases))

	return ParsedTeam(apiTeam)

def __create_franchise(parsedTeam):
	return {
		"name": parsedTeam.fullName,
		"active": parsedTeam.active,
		"_MLBAPIID": parsedTeam.teamId,
		}

def __create_team(parsedTeam, active):
	abbrev = parsedTeam.abbrev
	aliases = parsedTeam.aliases or []
	if mlbapi_abbreviation_corrections.get(abbrev):
		aliases.append(abbrev)
		abbrev = sdio_abbreviation_corrections[abbrev]

	team = {
		"MLBAPIID": parsedTeam.teamId,
		"active": active,
		"allStar": parsedTeam.allStar,
		"fullName": parsedTeam.fullName,
		"name": parsedTeam.name,
		"city": parsedTeam.city,
		"abbreviation": abbrev,
		"key": uuid.uuid4(),
		"conference": parsedTeam.conference,
		"division": parsedTeam.division,
		"years": [],
		"aliases": list(set(aliases))
		}
	
	return team
