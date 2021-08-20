# TheSportsDB.com
# TEAMS

import json
from datetime import datetime, date, time

from Constants import *
from Constants.Assets import *
from StringUtils import *
from Data.SportsDataIODownloader import *

sdio_abbreviation_corrections = {
	LEAGUE_MLB: {
		"CHW": "CWS"
		}
	}

def DownloadAllTeams(league):
	downloadedJson = DownloadAllTeamsForLeague(league)
	sportsDataIoTeams = json.loads(downloadedJson) # TODO: try/catch
	teams = dict()
	if not isinstance(sportsDataIoTeams, list) and "Code" in sportsDataIoTeams.keys():
		print("%s: %s" % (sportsDataIoTeams["Code"], sportsDataIoTeams["Description"]))
	elif isinstance(sportsDataIoTeams, list):
		for team in sportsDataIoTeams:
			city = deunicode(team["City"])
			if not city: continue

			key = abbrev = deunicode(team["Key"]).upper()
			name = deunicode(team["Name"])
			fullName = deunicode(team.get("FullName")) or "%s %s" % (deunicode(city), deunicode(name))
			
			aliases = []
			if sdio_abbreviation_corrections.get(league):
				if sdio_abbreviation_corrections[league].get(abbrev):
					aliases.append(abbrev)
					key = abbrev = sdio_abbreviation_corrections[league][abbrev]

			kwargs = {
				"Key": key,
				"Abbreviation": abbrev,
				"Active": True,
				"Name": name,
				"FullName": fullName,
				"City": city,
				"Conference": deunicode(team.get("Conference") or team.get("League")),
				"Division": deunicode(team["Division"]),
				"SportsDataIOID": str(team["TeamID"]),
				}

			assets = {}

			colors = []
			if team.get("PrimaryColor"): colors.append({"source": ASSET_SOURCE_SPORTSDATAIO, "colortype": ASSET_COLOR_TYPE_PRIMARY, "value": "#"+team["PrimaryColor"]})
			if team.get("SecondaryColor"): colors.append({"source": ASSET_SOURCE_SPORTSDATAIO, "colortype": ASSET_COLOR_TYPE_SECONDARY, "value": "#"+team["SecondaryColor"]})
			if team.get("TertiaryColor"): colors.append({"source": ASSET_SOURCE_SPORTSDATAIO, "colortype": ASSET_COLOR_TYPE_TERTIARY, "value": "#"+team["TertiaryColor"]})
			if team.get("QuaternaryColor"): colors.append({"source": ASSET_SOURCE_SPORTSDATAIO, "colortype": ASSET_COLOR_TYPE_QUATERNARY, "value": "#"+team["QuaternaryColor"]})
			if colors: assets[ASSET_TYPE_COLORS] = colors

			if assets:
				kwargs["assets"] = assets

			if aliases:
				kwargs["aliases"] = list(set(aliases))

			assets = dict()
			if team.get("WikipediaWordMarkUrl"):
				assets.setdefault("wordmark", [])
				assets["wordmark"].append({"source": "wikipedia", "url": deunicode(team["WikipediaWordMarkUrl"])})
			if team.get("WikipediaLogoUrl"):
				assets.setdefault("logo", [])
				assets["logo"].append({"source": "wikipedia", "url": deunicode(team["WikipediaLogoUrl"])})
			if assets:
				kwargs["assets"] = assets

			teams[key] = kwargs

	return teams