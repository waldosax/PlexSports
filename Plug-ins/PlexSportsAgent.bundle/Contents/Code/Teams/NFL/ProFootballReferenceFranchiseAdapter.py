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
from Data.NFL.ProFootballReferenceDownloader import *

EXPORT_NFL_FRANCHISES_FILENAME = "pro-football-reference.Franchises" + EXTENSION_JSON

pfr_cdn_selectors = {
	"dns-prefetch":"head link[rel='dns-prefetch']"
	}

pfr_franchises_index_selectors = {	# /teams/
	"active-franchises": "table#teams_active",
	"inactive-franchises": "table#teams_inactive",
	"inactive-franchises-placeholder": "div#all_teams_inactive div.placeholder",
	"team": "tbody > tr",
	"team-name": "th[data-stat='team_name']",
	"team-link": "a",
	"from": "td[data-stat='year_min']",
	"to": "td[data-stat='year_max']",
	"footer-menu": "div#footer_general div#site_menu",
	"footer-menu-items": "ul li"
	}

pfr_franchise_selectors = {	# /teams/crd/
	"franchise-logo": "div.logo img.teamlogo"
	}

pfr_team_selectors = {	# /teams/ram/2020.htm
	"team-logo": "div.logo img.teamlogo",
	"team-summary": "div#info div#meta div[data-template='Partials/Teams/Summary']",
	"team-summary-labels": "p strong"
	}

pfr_cdn_url = PFR_CDN_DEFAULT_URL


pfr_cached_franchises = dict()



def __parse_conference_and_division(s):
	conference = None
	division = None

	if s:
		s = s.strip()
		if s[:3].upper() in ["AFC", "NFC"]: # TODO: Pull in NFL constants in a way that isnt confusing. Might need to invert some modules
			conference = s[:3]
			s = s[3:].lstrip()
		if s[-8:].upper() == "DIVISION":
			division = s[:-8].strip()
		else:
			division = s.strip()

	return (conference, division)

def __read_cdn_base_url(soup):
	selectors = pfr_cdn_selectors

	prefetchNodes = soup.select(selectors["dns-prefetch"])
	if (prefetchNodes):
		prefetchLink = prefetchNodes[0]
		cdnUrl = str(prefetchLink.attrs["href"])
		lastGenDate = __extract_last_generated_date(cdnUrl)
		return (cdnUrl, lastGenDate)

	cdnBaseUrl = PFR_CDN_DEFAULT_URL
	lastGenDate = __extract_last_generated_date(cdnBaseUrl)
	return (cdnUrl, lastGenDate)

def __extract_last_generated_date(cdnBaseUrl):
	parts = cdnBaseUrl.rstrip("/").split("/")
	lastPart = parts[-1]
	dateStr = lastPart[:8]
	lastGenDate = datetime.datetime.strptime(dateStr, "%Y%m%d")
	return lastGenDate


def __extract_team_abbrev_from_team_url(teamLink):
	parts = teamLink.split("/")
	return parts[-2].upper()


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

# TODO: Split scraper and adapter
def DownloadAllFranchises(league):
	pfrFranchises = dict(__get_franchises())

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

def __get_franchises(download=False):
	franchises = dict()
	
	if download == False: # Nab from cache
		franchises = __get_franchises_from_cache()

	else: # Download from APIs
		franchises = __download_all_franchise_data()

	return franchises

def __download_all_franchise_data():
	selectors = pfr_franchises_index_selectors
	html = DownloadTeamsIndexPage()
	soup = BeautifulSoup(html, "html5lib")

	franchises = dict()
	franchiseLookup = dict()


	def get_franchise_team_info(row):
		info = dict()
		
		teamNameNode = row.select(selectors["team-name"])[0]
		teamName = teamNameNode.text
		while teamName[-1] in ["*"]:
			teamName = teamName[0:-1]
		info["name"] = teamName
		
		teamLinkNodes = teamNameNode.select(selectors["team-link"])
		if teamLinkNodes:
			href = teamLinkNodes[0].attrs.get("href")
			if href:
				info["href"] = href
				info["abbrev"] = __extract_team_abbrev_from_team_url(href)

		fromNode = row.select(selectors["from"])[0]
		info["from"] = fromNode.text
		toNode = row.select(selectors["to"])[0]
		info["to"] = toNode.text

		return info

	def get_years(franchise, teamName):
		years = []

		spans = []
		teamMeta = franchise["teams"][teamName]
		if teamMeta and teamMeta.get("years"):
			for span in teamMeta["years"]:
				spans.append(span)
		else:
			span = {"from": franchise["from"],"to": franchise["to"]}
			spans.append(span)

		for span in spans:
			for i in range(int(span["from"]), int(span["to"])+1):
				year = str(i)
				years.append(year)

		return years


	(cdnUrl, lastGenDate) = __read_cdn_base_url(soup)
	pfr_cdn_url = cdnUrl

	allFranchiseTables = [soup.select(selectors["active-franchises"])[0]]
	inactiveFranchisesPlaceholder = soup.select(selectors["inactive-franchises-placeholder"])[0]
	inactiveFranchisesTemplate = inactiveFranchisesPlaceholder.next_sibling
	while inactiveFranchisesTemplate:
		if isinstance(inactiveFranchisesTemplate, bs4.Comment): break
		inactiveFranchisesTemplate = inactiveFranchisesTemplate.next_sibling
	if inactiveFranchisesTemplate:
		inactiveFranchisesSoup = BeautifulSoup(inactiveFranchisesTemplate, "html5lib")
		inactiveFranchisesNodes = inactiveFranchisesSoup.select(selectors["inactive-franchises"])
		if inactiveFranchisesNodes:
			allFranchiseTables.append(inactiveFranchisesNodes[0])

	for i in range(0, len(allFranchiseTables)):
		franchiseTable = allFranchiseTables[i]
		activeFranchises = (i == 0)

		teamNodes = franchiseTable.select(selectors["team"])
		franchise = None

		for i in range(0, len(teamNodes)):
			currentNode = teamNodes[i]
			if currentNode.attrs.get("class") and "thead" in currentNode.attrs["class"]: continue
			if not currentNode.attrs.get("class"): # Franchise
				franchiseNode = currentNode

				if franchise:	# Seal up any info on the franchise where there has only been one team
					franchiseName = franchise["name"]
					franchise["teams"].setdefault(franchiseName, dict())
					teamMeta = franchise["teams"][franchiseName]
					teamMeta.setdefault("name", franchiseName)
					span = {"from": franchise["from"], "to": franchise["to"]}
					if not teamMeta.get("years"):
						teamMeta.setdefault("years", [])
						teamMeta["years"].append(span)
					if franchise.get("active"): teamMeta.setdefault("active", franchise["active"])
					for season in get_years(franchise, franchiseName):
						if not teamMeta.get(season):
							teamLinkHref = GetTeamUrl(franchise["name"], franchise["abbrev"].lower(), season)
							teamLogoSrc = GetTeamLogoUrl(franchise["name"], franchise["abbrev"].lower(), season, cdnUrl=cdnUrl)
							info = {
								"href": teamLinkHref,
								"logo": teamLogoSrc
								}
							teamMeta[season] = info
				
				# New franchise
				info = get_franchise_team_info(franchiseNode)
				franchiseName = info["name"]

				franchise = dict(info)
				franchise.setdefault("teams", dict())
				franchise.setdefault("active", activeFranchises)

				if not franchises.get(franchiseName):
					franchises[franchiseName] = franchise
					abbrev = info["abbrev"]
					franchiseLookup[abbrev] = franchiseName
				else:
					franchise = franchises[franchiseName]
					franchise.setdefault("teams", dict())
					for key in info.keys():
						franchise[key] = info[key]

				# Project logo url
				franchiseLogoSrc = GetTeamLogoUrl(franchise["name"], franchise["abbrev"].lower(), season=None, cdnUrl=cdnUrl)
				franchise.setdefault("logo", franchiseLogoSrc)

				# Set up at least the one team in the franchise
				franchise["teams"].setdefault(franchiseName, dict())
				teamMeta = franchise["teams"][franchiseName]
				teamMeta.setdefault("fullName", franchiseName)
				teamMeta.setdefault("name", franchiseName)
				teamMeta.setdefault("years", [])
				teamMeta.setdefault("active", activeFranchises)

			elif franchise and currentNode.attrs.get("class") and "partial_table" in currentNode.attrs["class"]: # Team
				teamNode = currentNode

				info = get_franchise_team_info(teamNode)
				teamName = info["name"]
				span = {"from": info["from"], "to": info["to"]}

				franchise.setdefault("teams", dict())


				if not franchise["teams"].get(teamName):
					teamMeta = {"name": teamName, "years": []}
					franchise["teams"][teamName] = teamMeta
				else:
					franchise["teams"].setdefault(teamName, dict())
					teamMeta = franchise["teams"][teamName]
					teamMeta["name"] = teamName
					teamMeta.setdefault("years", [])

				if franchise.get("active") and franchise["name"] == teamName: teamMeta["active"] = True
				teamMeta["years"].append(span)

				#for i in range(int(info["from"]), int(info["to"])+1):
				#	# Project team and logo urls
				#	season = str(i)
				#	teamLinkHref = GetTeamUrl(franchise["name"], franchise["abbrev"].lower(), season)
				#	teamLogoSrc = GetTeamLogoUrl(franchise["name"], franchise["abbrev"].lower(), season, cdnUrl=cdnUrl)
				#	teamMeta.setdefault(season, dict())
				#	teamMeta[season].setdefault("href", teamLinkHref)
				#	teamMeta[season].setdefault("logo", teamLogoSrc)


	footerMenu = soup.select(selectors["footer-menu"])
	if footerMenu:
		footerMenuItems = footerMenu[0].select(selectors["footer-menu-items"])
		if footerMenuItems:
			foundMenuItem = False
			for footerMenuItem in footerMenuItems:
				links = footerMenuItem.select("a")
				if links and links[0].text == "Teams":
					foundMenuItem = True
					break;
			if foundMenuItem and footerMenuItem:
				divisionNodes = footerMenuItem.select("div")
				if divisionNodes:
					for divisionNode in divisionNodes:
						if divisionNode.children:
							divisionText = divisionNode.contents[0]
							(conference, division) = __parse_conference_and_division(divisionText.rstrip(": "))
							for teamLink in divisionNode.select("a"):
								teamName = teamLink.text
								teamLinkHref = teamLink.attrs["href"]
								abbrev = __extract_team_abbrev_from_team_url(teamLinkHref)
								franchise = franchises[franchiseLookup[abbrev]]
								city = franchise["name"][:-len(teamName)].strip()

								team = franchise["teams"].get(franchise["name"])
								if team:
									team["name"] = teamName
									team["city"] = city
									team["conference"] = conference
									team["division"] = division

	return franchises


def __get_franchises_from_cache():
	if (__franchise_cache_has_franchises() == False):
		if __franchise_cache_file_exists() == False:
			__refresh_franchise_cache()
		else:
			cachedJson = __read_franchise_cache_file() #TODO: Try/Catch
			jsonFranchises = json.loads(cachedJson)

			if not jsonFranchises:
				jsonFranchises = __refresh_franchise_cache()

			pfr_cached_franchises.clear()
			for key in jsonFranchises.keys():
				pfr_cached_franchises[key] = jsonFranchises[key]
	return pfr_cached_franchises

def __refresh_franchise_cache():
	print("Refreshing NFL franchises cache from pro-footbal-reference.com ...")
	franchises = __get_franchises(download=True)
	pfr_cached_franchises.clear()
	for key in franchises.keys():
		pfr_cached_franchises[key] = franchises[key]
	jsonFranchises = json.dumps(franchises, sort_keys=True, indent=4)
	__write_franchise_cache_file(jsonFranchises)

	return jsonFranchises

def __franchise_cache_has_franchises():
	return len(pfr_cached_franchises) > 0

def __franchise_cache_file_exists():
	path = __get_franchise_cache_file_path()
	return os.path.exists(path)

def __read_franchise_cache_file():
	path = __get_franchise_cache_file_path()
	return open(path, "r").read() # TODO: Invalidate cache

def __write_franchise_cache_file(json):
	print("Writing NFL franchise cache from pro-footbal-reference.com to disk ...")
	path = __get_franchise_cache_file_path()
	dir = os.path.dirname(path)
	EnsureDirectory(dir)
	f = open(path, "w")
	f.write(json)
	f.close()

def __get_franchise_cache_file_path():
	path = os.path.join(GetDataPathForLeague(LEAGUE_NFL), EXPORT_NFL_FRANCHISES_FILENAME)
	return path
