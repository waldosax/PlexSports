# TheSportsDB.com
# TEAMS

import json
from datetime import datetime, date, time

from Constants import *
from StringUtils import *
from Data.TheSportsDBDownloader import *

spdb_abbreviation_corrections = {
	LEAGUE_MLB: {
		"WAS": "WSH",
		},
	LEAGUE_NFL: {
		"OAK": "LV",
		}
	}

def DownloadAllTeams(league):
	downloadedJson = DownloadAllTeamsForLeague(league)
	sportsDbTeams = json.loads(downloadedJson)
	teams = dict()
	for team in sportsDbTeams["teams"]:
		abbrev = key = deunicode(team.get("strTeamShort"))
		fullName = deunicode(team["strTeam"])
		city = None
		name = fullName

		aliases = []
		if spdb_abbreviation_corrections.get(league):
			if spdb_abbreviation_corrections[league].get(abbrev):
				aliases.append(abbrev)
				key = abbrev = spdb_abbreviation_corrections[league][abbrev]

		if league == LEAGUE_NBA:
			if name == "Los Angeles Clippers":
				print("Correcting known data error in TheSportsDB.com data. Incorrect team name for %s -> LA Clippers" % (team.get("strTeam")))
				aliases.append(name)
				fullName = "LA Clippers"
				city = "LA"
				name = "Clippers"
		elif league == LEAGUE_NFL:
			if name == "Washington":
				print("Correcting known data error in TheSportsDB.com data. Incorrect team name for %s -> Washington Football Team" % (team.get("strTeam")))
				fullName = deunicode(team["strAlternate"])
				city = name
				name = fullName[len(city):].strip()

		alternate = deunicode(team["strAlternate"]) if team.get("strAlternate") != abbrev else None
		if alternate: aliases += splitAndTrim(alternate)

		if not abbrev:
			if league == LEAGUE_NHL and deunicode(team.get("strAlternate")) == "Kraken ":
				print("Correcting known data error in TheSportsDB.com data. Missing abbreviation for %s -> SEA" % (team.get("strTeam")))
				abbrev = key = "SEA"
				name = deunicode(team["strAlternate"].strip())
				fullName = deunicode(team["strTeam"])
				city = "Seattle"
			else:
				print("No abbbreviation for %s team %s (TheSportsDb.com)" % (team["strLeague"], team["strTeam"]))
				continue
		else: abbrev = abbrev.upper()


		kwargs = {
			"key": key,
			"abbreviation": abbrev,
			"active": True,
			"name": name,
			"fullName": fullName,
			"city": city,
			"SportsDBID": str(team["idTeam"])
			}
		
		if aliases:
			kwargs["aliases"] = aliases

		assets = dict()
		if team.get("strTeamBadge"):
			assets.setdefault("badge", [])
			assets["badge"].append({"source": "thesportsdb", "url": deunicode(team["strTeamBadge"])})
		if team.get("strTeamJersey"):
			assets.setdefault("jersey", [])
			assets["jersey"].append({"source": "thesportsdb", "url": deunicode(team["strTeamJersey"])})
		if team.get("strTeamLogo"):
			assets.setdefault("wordmark", [])
			assets["wordmark"].append({"source": "thesportsdb", "url": deunicode(team["strTeamLogo"])})
		for i in range(1, 5):
			if team.get("strTeamFanart%s" % i):
				assets.setdefault("fanArt", [])
				assets["fanArt"].append({"source": "thesportsdb", "url": deunicode(team["strTeamFanart%s" % i])})
		if team.get("strBanner"):
			assets.setdefault("banner", [])
			assets["banner"].append({"source": "thesportsdb", "url": deunicode(team["strBanner"])})
		if assets:
			kwargs["assets"] = assets
		
		teams[key] = kwargs

	return teams