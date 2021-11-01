# NHL API (statsapi.nhl.com)
# TEAMS

import uuid
import json
from datetime import datetime, date, time

from Constants import *
from StringUtils import *
from TimeZoneUtils import *
from Data.NHL.NHLAPIDownloader import *


def DownloadAllFranchises(league):

	# Get all franchises
	nhlapiAllFranchises = dict()
	nhlapiAllFranchisesJson = DownloadAllFranchiseInfo()
	try: nhlapiAllFranchises = json.loads(nhlapiAllFranchisesJson)
	except: pass

	# Get all teams for current season
	nhlapiAllTeams = dict()
	nhlapiAllTeamsJson = DownloadAllTeams()
	try: nhlapiAllTeams = json.loads(nhlapiAllTeamsJson)
	except: pass

	# Get all team history (relevant fields only)
	nhlapiTeamHistories = dict()
	nhlapiTeamHistoriesJson = DownloadTeamHistories() # ["teams", "id", "sport", "league", "name", "teamName", "season", "abbreviation", "teamName", "franchiseId", "firstYearOfPlay", "active"])
	try: nhlapiTeamHistories = json.loads(nhlapiTeamHistoriesJson)
	except: pass

	# Get seasons
	nhlapiSeasons = dict()
	nhlapiSeasonsJson = DownloadAllSeasons()
	try: nhlapiSeasons = json.loads(nhlapiSeasonsJson)
	except: pass

	utcnow = datetime.datetime.utcnow()
	thisYear = utcnow.year
	currentSeason = str(thisYear) # default
	currentSeasonId = None

	for i in range(len(nhlapiSeasons["seasons"])-1,-1,-1):
		nhlapiSeason = nhlapiSeasons["seasons"][i]
		seasonStartDate = ParseISO8601Date(nhlapiSeason["regularSeasonStartDate"])
		seasonEndDate = ParseISO8601Date(nhlapiSeason["seasonEndDate"])
		if seasonStartDate > utcnow: continue
		currentSeasonId = nhlapiSeason["seasonId"]
		currentSeason = str(seasonStartDate)
		break


	franchises = dict()
	franchisesById = dict()
	for nhlapiFranchise in nhlapiAllFranchises["franchises"]:
		franchiseName = deunicode("%s %s" % (strip_diacritics(nhlapiFranchise["locationName"]), strip_diacritics(nhlapiFranchise["teamName"])))
		franchiseId = nhlapiFranchise["franchiseId"]
		franchise = {
			"franchiseId": franchiseId,
			"name": franchiseName,
			"fromYear": int(str(nhlapiFranchise["firstSeasonId"])[:4]) if nhlapiFranchise.get("firstSeasonId") else None,
			"toYear": int(str(nhlapiFranchise["lastSeasonId"])[:4]) if nhlapiFranchise.get("lastSeasonId") else None,
			"teams": dict()
			}
		franchisesById[franchiseId] = franchise
		franchises[franchiseName] = franchise

	nhlapiTeamsById = dict()
	for nhlapiTeam in nhlapiAllTeams["teams"]:
		teamId = nhlapiTeam["id"]
		nhlapiTeamsById[teamId] = nhlapiTeam

	for apiHistory in nhlapiTeamHistories["teams"]:
		teamId = apiHistory["id"]
		franchiseId = apiHistory["franchiseId"]
		fullName = deunicode(strip_diacritics(apiHistory["name"]))
		name = deunicode(strip_diacritics(apiHistory["teamName"]))
		city = deunicode(strip_diacritics(apiHistory["locationName"]))
		abbreviation = deunicode(apiHistory["abbreviation"])
		active = apiHistory["active"]
		team = {
			"NHLAPIID": str(teamId),
			"key": uuid.uuid4(),
			"fullName": fullName,
			"name": name,
			"city": city,
			"abbreviation": abbreviation,
			"active": active,
			"years": [{"fromYear": int(apiHistory["firstYearOfPlay"])}]
			}
		
		nhlapiTeam = nhlapiTeamsById.get(teamId)
		if nhlapiTeam:
			team["conference"] = deunicode(nhlapiTeam["conference"]["name"]) if nhlapiTeam.get("conference") else None
			team["division"] = deunicode(nhlapiTeam["division"]["name"]) if nhlapiTeam.get("division") else None

			aliases = []
			if nhlapiTeam.get("shortName") and nhlapiTeam["shortName"] != city: aliases.append(deunicode(strip_diacritics(nhlapiTeam["shortName"])))
			if aliases: team["aliases"] = list(set(aliases))

		franchisesById[franchiseId]["teams"][fullName] = team




	def get_team_year_sort_key(team):
		return team["years"][0]["fromYear"]

	for franchise in franchises.values():
		# Backfill years and active
		teams = list(sorted(franchise["teams"].values(), key=get_team_year_sort_key))
		hasAnyActive = False
		for i in range(0, len(teams)-1):
			currentTeam = teams[i]
			nextTeam = teams[i+1]
			currentTeam["years"][0]["toYear"] = nextTeam["years"][0]["fromYear"]-1
			if currentTeam.get("active") == True: hasAnyActive = True
		currentTeam = teams[-1]
		currentTeam["years"][0]["toYear"] = franchise["toYear"] if franchise.get("toYear") else currentSeason if currentTeam["active"] == False else None
		if currentTeam.get("active") == True: hasAnyActive = True
		franchise["active"] = hasAnyActive
		pass

	return franchises