# Python framework
import sys, os, json, re

# Local package
from Constants import *
from Matching import *
from Matching import __expressions_from_literal
from Matching import __index_of
from Matching import __strip_to_alphanumeric
from Matching import __strip_to_alphanumeric_and_at
from Matching import __sort_by_len
from Matching import __sort_by_len_key
from Matching import __sort_by_len_value
from Matching import Eat, Boil, Taste, Chew
from StringUtils import *
from Data import TheSportsDB, SportsDataIO
from Data.CacheContainer import *

CACHE_DURATION = 135
CACHE_VERSION = "1"

known_city_aliases = [
	("NY", "New York"),
	("NJ", "New Jersey"),
	("LA", "Los Angeles"),
	("LV", "Las Vegas"),
	("DC", "Washington", "Washington DC"),
	("NOLA", "New Orleans")
	]

# Abbreviation level-set (disparities in data). Corrections to any acquired data
data_corrections = {	# [League][OldAbbrev] = CurrentAbbrev
	LEAGUE_NFL: {
		"OAK": "LV",
		"LA": "LAR",
		"LVRAID": "LV"
		},
	LEAGUE_MLB: {
		"WAS": "WSH"
		}
	}

# Renames, Moves & Folds (This will work a lot better once I fold year into the mix
defunct_teams = {	#[League][RetroKey](City, Name, ThenAbbrev, NowAbbrev)
	LEAGUE_NFL: {
		"~BAL": ("Baltimore", "Colts", "BAL", "IND"),
		"~HOU": ("Houston", "Oilers", "HOU", "TEN"),
		"~LARAID1": ("L.A.", "Raiders", "LARAID", "LV"),
		"~LARAID": ("Los Angeles", "Raiders", "LARAID", "LV"),
		"~NAS": ("Nashville", "Oilers", "NAS", "TEN"),
		"~OAK": ("Oakland", "Raiders", "OAK", "LV"),
		"~PHX": ("Phoenix", "Cardinals", "PHX", "ARI"),
		"~SD": ("San Diego", "Chargers", "SD", "LAC"),
		"~STLR": ("St. Louis", "Rams", "STL", "LAR"),
		"~STLC": ("St. Louis", "Cardinals", "STL", "ARI"),
		"~WAS": ("Washington", "Redskins", "WAS", "WAS")
		},
	LEAGUE_MLB: {
		"~MTL": ("Montreal", "Expos", "MTL", "WSH")
		},
	LEAGUE_NBA: {
		"~WAS": ("Washington", "Bullets", "WAS", "WAS"),
		"~VAN": ("Vancouver", "Grizzlies", "VAN", "MEM"),
		"~CHA": ("Charlotte", "Hornets", "CHA", "NOH"), # This one might be tricky (multiple moves/renames)
		"~NOH": ("New Orleans", "Hornets", "NOH", "NOP"), # This one might be tricky (multiple moves/renames)
		"~NOOKCH": ("New Orleans/Oklahoma City", "Hornets", "NOH", "NOP"), # This one might be tricky (multiple moves/renames)
		"~SEA": ("Seattle", "SuperSonics", "SEA", "OKC"),
		"~TOR": ("Toronto/Tampa Bay", "Raptors", "TOR", "TOR")
		},
	LEAGUE_NHL: {
		"~MIN": ("Minnesota", "North Stars", "MIN", "DAL"),
		"~NORDS": ("Quebec", "Nordiques", "NORDS", "COL"),
		"~QUE": ("Quebec", "Nordiques", "QUE", "COL"), # TODO: Strip diacritics
		"~WIN": ("Winnipeg", "Jets", "WIN", "ARI"),
		"~HFD": ("Hartford", "Whalers", "HFD", "CAR"),
		"~ATL": ("Atlanta", "Thrashers", "ATL", "WP")
		}
	}

cached_teams = dict()
cities_with_multiple_teams = dict()
cached_team_keys = dict()

class TeamInfo:
	def __init__(self, **kwargs):
		self.League = str(kwargs.get("League") or "")
		self.Key = str(kwargs.get("Key") or "")
		self.Abbreviation = str(kwargs.get("Abbreviation") or "")
		self.Name = str(kwargs.get("Name") or "")
		self.FullName = str(kwargs.get("FullName") or "")
		self.City = str(kwargs.get("City") or "")
		self.SportsDBID = str(kwargs.get("SportsDBID") or "")
		self.SportsDataIOID = str(kwargs.get("SportsDataIOID") or "")


def __add_or_override_team(teams, **kwargs):
	key = kwargs["Key"]
	if (key in teams.keys() == False or len(teams) == 0 or teams.get(key) == None):
		team = TeamInfo(**kwargs)
		teams.setdefault(key, team)
	else:
		team = teams[key]
		if (kwargs.get("Name")):
			team.Name = str(kwargs["Name"])
		if (kwargs.get("FullName")):
			team.FullName = str(kwargs["FullName"])
		if (kwargs.get("City")):
			team.City = str(kwargs["City"])
		if (kwargs.get("SportsDBID")):
			team.SportsDBID = str(kwargs["SportsDBID"])
		if (kwargs.get("SportsDataIOID")):
			team.SportsDataIOID = str(kwargs["SportsDataIOID"])
		#teams.pop(key, None)
		#teams[key] = team
		## TODO: Find out why not updating

def GetTeams(league, download=False):
	if (league in known_leagues.keys() == False):
		return None # TODO: Throw
	teams = dict()
	
	if download == False: # Nab from cache
		teams = __get_teams_from_cache(league)
   
	else: # Download from APIs
		teams = __download_all_team_data(league)

	return teams

def GetAllTeams():
	allTeams = dict()
	for league in known_leagues.keys():
		teams = GetTeams(league)
		if (teams):
			allTeams.setdefault(league, teams)
	return allTeams


def __download_all_team_data(league):
	teams = dict()

	# Retrieve data from TheSportsDB.com
	downloadedJson = TheSportsDB.__the_sports_db_download_all_teams_for_league(league)
	sportsDbTeams = json.loads(downloadedJson)
	for team in sportsDbTeams["teams"]:
		abbrev = deunicode(team["strTeamShort"])
		if league in data_corrections.keys():
			if abbrev in data_corrections[league]:
				newAbbrev = data_corrections[league][abbrev]
				print("Correcting data error in TheSportsDB.com data. %s -> %s" % (abbrev, newAbbrev))
				abbrev = newAbbrev
		kwargs = {
			"League": league,
			"Key": abbrev,
			"Abbreviation": abbrev,
			"Name": deunicode(team["strTeam"]),
			"FullName": deunicode(team["strTeam"]),
			"SportsDBID": str(team["idTeam"])
			}
		__add_or_override_team(teams, **kwargs)
		
	# Augment/replace with data from SportsData.io
	downloadedJson = SportsDataIO.__sports_data_io_download_all_teams_for_league(league)
	sportsDataIoTeams = json.loads(downloadedJson)
	if not isinstance(sportsDataIoTeams, list) and "Code" in sportsDataIoTeams.keys():
		print("%s: %s" % (sportsDataIoTeams["Code"], sportsDataIoTeams["Description"]))
	elif isinstance(sportsDataIoTeams, list):
		for team in sportsDataIoTeams:
			kwargs = {
				"League": league,
				"Key": deunicode(team["Key"]),
				"Abbreviation": deunicode(team["Key"]),
				"Name": deunicode(team["Name"]),
				"FullName": deunicode(team.get("FullName")) or "%s %s" % (deunicode(team["City"]), deunicode(team["Name"])),
				"City": deunicode(team["City"]),
				"SportsDataIOID": str(team["TeamID"])
				}
			__add_or_override_team(teams, **kwargs)


	# Incorporate defunct teams
	if league in defunct_teams.keys():
		for key in defunct_teams[league]:
			(city, name, defunctAbbrev, mapAbbrev) = defunct_teams[league][key]
			kwargs = {
				"League": league,
				"Key": key,
				"Abbreviation": defunctAbbrev,
				"Name": name,
				"FullName": "%s %s" % (city, name),
				"City": city
				}
			__add_or_override_team(teams, **kwargs)

	return teams

def __get_teams_from_cache(league):
	if (league in known_leagues.keys() == False):
		return None
	if (__team_cache_has_teams(league) == False):
		if __team_cache_file_exists(league) == False:
			__refresh_team_cache(league)
		else:
			jsonTeams = []
			cachedJson = __read_team_cache_file(league) #TODO: Try/Catch
			cacheContainer = CacheContainer.Deserialize(cachedJson)

			if not cacheContainer or cacheContainer.IsInvalid(CACHE_VERSION):
				jsonTeams = __refresh_team_cache(league)
			else:
				jsonTeams = cacheContainer.Items

			if not jsonTeams:
				jsonTeams = __refresh_team_cache(league)
			else:
				teams = dict()
				for jsonTeam in jsonTeams:
					team = TeamInfo(**jsonTeam)
					teams.setdefault(team.Key, team)
				cached_teams.setdefault(league, teams)
				cached_teams[league] = teams
			cwmt = __get_cities_with_multiple_teams(league, teams)
			cities_with_multiple_teams.setdefault(league, cwmt)
			cities_with_multiple_teams[league] = cwmt
			teamKeys = __get_teams_keys(league, teams, cwmt)
			cached_team_keys.setdefault(league, teamKeys)
			cached_team_keys[league] = teamKeys
	return cached_teams[league]

def __refresh_team_cache(league):
	print("Refreshing %s teams cache ..." % league)
	teams = GetTeams(league, download=True)
	cached_teams.setdefault(league, teams)
	cached_teams[league] = teams
	cwmt = __get_cities_with_multiple_teams(league, teams)
	cities_with_multiple_teams.setdefault(league, cwmt)
	cities_with_multiple_teams[league] = cwmt
	teamKeys = __get_teams_keys(league, teams, cwmt)
	cached_team_keys.setdefault(league, teamKeys)
	cached_team_keys[league] = teamKeys
	jsonTeams = list(teams.values())
	#for teamInfo in teams.values():
	#    jsonTeams.append(teamInfo.__dict__)
	cacheContainer = CacheContainer(jsonTeams, CacheType="%sTEAMS" % league, Version=CACHE_VERSION, Duration=CACHE_DURATION)
	__write_team_cache_file(league, cacheContainer.Serialize())

	return jsonTeams

def __team_cache_has_teams(league):
	if len(cached_teams) == 0:
		return False
	if league in cached_teams.keys() == False:
		return False
	if (cached_teams.get(league) == None):
		return False
	return len(cached_teams[league]) > 0

def __team_cache_file_exists(league):
	path = __get_team_cache_file_path(league)
	return os.path.exists(path)

def __read_team_cache_file(league):
	path = __get_team_cache_file_path(league)
	return open(path, "r").read() # TODO: Invalidate cache

def __write_team_cache_file(league, json):
	print("Writing %s teams cache to disk ..." % league)
	path = __get_team_cache_file_path(league)
	dir = os.path.dirname(path)
	if not os.path.exists(dir):
		nodes = Utils.SplitPath(dir)
		agg = None
		for node in nodes:
			agg = os.path.join(agg, node) if agg else node
			if os.path.exists(agg) == False:
				os.mkdir(agg)
	f = open(path, "w")
	f.write(json)
	f.close()

def __get_team_cache_file_path(league):
	path = os.path.abspath(r"%s/%s%s/Teams.json" % (os.path.dirname(__file__), DATA_PATH_LEAGUES, league))
	return path




# New York, LA
def __get_cities_with_multiple_teams(league, teams):
	cities = dict()
	for team in teams.values():
		city = team.City
		cityKey = __strip_to_alphanumeric(city)
		if not team.Key[:1] == "~":
			if cities.has_key(cityKey):
				cities[cityKey] = True
			else:
				cities.setdefault(cityKey, False)
	ret = list()
	for cityKey in cities.keys():
		if cities[cityKey]:
			ret.append(cityKey)
	return ret

def __get_city_variants(cityKey):
	variants = []

	for c in known_city_aliases:
		for i in range(len(c)):
			if __strip_to_alphanumeric(c[i]) == cityKey:
				for j in range(len(c)):
					variants.append(__strip_to_alphanumeric(c[j]))
				return variants

	return variants

def __get_teams_keys(league, teams, multi_team_city_keys):
	keys = dict()

	for team in teams.values():
		key = team.Key
		abbrev = team.Abbreviation
		fullName = __strip_to_alphanumeric(team.FullName)
		name = __strip_to_alphanumeric(team.Name)
		city = __strip_to_alphanumeric(team.City)

		if fullName:
			keys.setdefault(fullName, key)
		keys.setdefault(name, key)
		if city:
			cityVariants = __get_city_variants(city)
			if (cityVariants):
				for v in cityVariants:
					keys.setdefault(v+name, key)
					if v not in multi_team_city_keys:
						keys.setdefault(v, key)
			if city not in multi_team_city_keys:
				keys.setdefault(city, key)
		
		if key[0:1] == "~":
			keys.setdefault(key.lower(), key)

		keys.setdefault(abbrev.lower(), key)



	return keys
