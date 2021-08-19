# Pro-Football-Reference.com
# TEAMS

import re, os
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
		franchiseName = franchise.get("fullName") or franchise.get("name")
		if not franchise.get("fullName"): franchise["fullName"] = franchiseName

		franchise["fromYear"] = franchise["from"]
		del(franchise["from"])
		franchise["toYear"] = franchise["to"]
		del(franchise["to"])

		for team in franchise["teams"].values():
			abbrev = key = id = franchise["abbrev"]

			active = team.get("active") == True
			aliases = team.get("aliases") or []
			
			if active:
				for inactiveTeam in franchise["teams"].values():
					if inactiveTeam.get("active") == True: continue
					inactiveName = inactiveTeam.get("fullName") or inactiveTeam.get("name") or ""
					if inactiveName:
						aliases.append(inactiveName)
						if team.get("city"):
							if inactiveName[:len(team["city"])] == team["city"]:
								aliases.append(inactiveName[:len(team["city"])].strip())

			team["aliases"] = list(set(aliases))

			if abbrev in pfr_abbreviation_corrections.keys():
				if active: aliases.append(abbrev)
				abbrev = key = pfr_abbreviation_corrections[abbrev]

			if active: 
				team["key"] = key
				team["abbreviation"] = abbrev
			else:
				team["fullName"] = team["name"]
				del(team["name"])

			team["ProFootballReferenceID"] = id

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