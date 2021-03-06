# Pro-Football-Reference.com
# TEAMS

import re, os
import uuid
import json
from datetime import datetime, date, time
from bs4 import BeautifulSoup
import bs4


from Constants import *
from PathUtils import *
from PluginSupport import *
from Serialization import *
from StringUtils import *
import ProFootballReferenceFranchiseScraper as FranschiseScraper

pfr_cached_franchises = dict()


pfr_abbreviation_corrections = {
	"CRD": "ARI",
	"RAV": "BAL",
	"BBA": "BUF",
	"GNB": "GB",
	"HTX": "HOU",
	"CLT": "IND",
	"KAN": "KC",
	"RAI": "LV",
	"SDG": "LAC",
	"RAM": "LAR",
	"NWE": "NE",
	"NOR": "NO",
	"SFO": "SF",
	"TAM": "TB",
	"OTI": "TEN"
	}

def DownloadAllFranchises(league):
	pfrFranchises = dict(FranschiseScraper.GetFranchises())

	# Adapt franchises to global teams model
	for franchise in pfrFranchises.values():
		franchiseName = deunicode(franchise.get("fullName")) or deunicode(franchise.get("name"))
		if not franchise.get("fullName"): franchise["fullName"] = franchiseName
		franchiseName = franchise["fullName"]

		franchise["fromYear"] = franchise["from"]
		del(franchise["from"])
		franchise["toYear"] = franchise["to"]
		del(franchise["to"])

		for team in franchise["teams"].values():
			teamName = deunicode(team.get("fullName")) or deunicode(team.get("name"))

			# abbrev - NFL official abbreviation
			# id - identifier for the team, used by espn, relative to pfr
			abbrev = id = deunicode(franchise["abbrev"])

			active = team.get("active") == True
			aliases = team.get("aliases") or []
			
			if active:
				for inactiveTeam in franchise["teams"].values():
					if inactiveTeam.get("active") == True: continue
					inactiveName = deunicode(inactiveTeam.get("fullName")) or deunicode(inactiveTeam.get("name")) or ""
					if inactiveName:
						aliases.append(inactiveName)
						if team.get("city"):
							if inactiveName[:len(team["city"])] == team["city"]:
								# Get any deadname cities
								aliases.append(deunicode(inactiveName[:len(team["city"])].strip()))

			if abbrev in pfr_abbreviation_corrections.keys():
				if active: aliases.append(abbrev)
				abbrev = pfr_abbreviation_corrections[abbrev]

			team["aliases"] = list(set(aliases))

			team["key"] = uuid.uuid4()
			if active: 
				team["abbreviation"] = abbrev
			else:
				team["fullName"] = teamName
				del(team["name"])
				
				prefix = abbrev
				franchisePrefix = strip_to_capitals(franchiseName)
				if prefix != franchisePrefix: prefix = "%s.%s" % (prefix, franchisePrefix)
				id = prefix

				suffix = strip_to_capitals(teamName)
				if suffix != franchisePrefix:
					id = "%s.%s" % (prefix, suffix)
				
				if team.get("abbreviation"): del(team["abbreviation"])

			team["ProFootballReferenceID"] = id
			team["identity"] = {"ProFootballReferenceID": id}


			yrs = list(team["years"])
			team["years"] = []
			for span in yrs:
				team["years"].append({"fromYear":span["from"], "toYear":span["to"]})

			assets = dict()
			if franchise.get("logo"):
				assets.setdefault("logo", [])
				assets["logo"].append({"source": "profootballreference", "url": deunicode(franchise["logo"])})

			if team.get("years"):
				for span in team["years"]:
					for year in range(int(span["fromYear"]), int(span["toYear"])+1):
						season = str(year)
						if team.get(season) and team[season].get("logo"):
							assets.setdefault("logo", [])
							assets["logo"].append({"source": "profootballreference", "season": season, "url": deunicode(team[season]["logo"])})

			if assets:
				team["assets"] = assets

	return pfrFranchises
