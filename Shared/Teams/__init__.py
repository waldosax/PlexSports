# Python framework
import sys, os, json, re

# Local package
from Constants import *
from Matching import *
from PathUtils import *
from PluginSupport import *
from Serialization import *
from StringUtils import *
from Vectors import *
from Franchise import *
from Team import *
import TheSportsDBFranchiseAdapter, SportsDataIOFranchiseAdapter
from Data.CacheContainer import *
from NFL import ProFootballReferenceFranchiseAdapter
from MLB import MLBAPIFranchiseAdapter

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
		},
	LEAGUE_NHL: {
		"TB": "TBL"
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
		"~MTL": ("Montreal", "Expos", "MTL", "WSH") #NOTEAM, Unknown Team, Retired, Minor League
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
		"~ATL": ("Atlanta", "Thrashers", "ATL", "WP"),
		"~ANA": ("Anaheim", "Mighty Ducks", "ANA", "ANA")
		}
	}

cached_franchises = FranchiseDict()
cities_with_multiple_teams = dict()
cached_team_keys = dict()


def GetFranchises(league):
	return __get_franchises(league, download=False)

def GetAllFranchises():
	allTeams = dict()
	for league in known_leagues.keys():
		teams = GetFranchises(league)
		if (teams):
			allTeams.setdefault(league, teams)
	return allTeams





def __get_franchises(league, download=False):
	if (league in known_leagues.keys() == False):
		return None # TODO: Throw
	franchises = FranchiseDict()
	
	if download == False: # Nab from cache
		franchises = __get_teams_from_cache(league)

	else: # Download from APIs
		franchises = __download_all_team_data(league)

	franchises.invalidate()
	return franchises

def __download_all_team_data(league):
	franchises = FranchiseDict()

	if league == LEAGUE_MLB:
		# Retrieve data from MLB stats API
		mlbapiFranchises = MLBAPIFranchiseAdapter.DownloadAllFranchises(league)
		for f in mlbapiFranchises.values():
			franchiseName = f["name"]
			(franchise, fteam) = __find_team(franchises, franchiseName, None)
			franchise.Augment(**f)

			for tm in f["teams"].values():
				teamName = tm["fullName"]
				(franchise, team) = __find_team(franchises, franchiseName, teamName)
				team.Augment(**tm)
	elif league == LEAGUE_NFL:
		# Retrieve data from pro-football-reference.com
		pfrFranchises = ProFootballReferenceFranchiseAdapter.DownloadAllFranchises(league)
		for f in pfrFranchises.values():
			franchiseName = f["name"]
			(franchise, fteam) = __find_team(franchises, franchiseName, None)
			franchise.Augment(**f)

			for tm in f["teams"].values():
				teamName = tm["fullName"]
				(franchise, team) = __find_team(franchises, franchiseName, teamName)
				team.Augment(**tm)

		
	# Augment/replace with data from SportsData.io
	sportsDataIoTeams = SportsDataIOFranchiseAdapter.DownloadAllTeams(league)
	for tm in sportsDataIoTeams.values():
		teamName = tm["FullName"]
		(franchise, team) = __find_team(franchises, None, teamName)
		team.Augment(**tm)

	# Retrieve data from TheSportsDB.com
	sportsDbTeams = TheSportsDBFranchiseAdapter.DownloadAllTeams(league)
	for tm in sportsDbTeams.values():
		teamName = tm["FullName"]
		(franchise, team) = __find_team(franchises, None, teamName)
		team.Augment(**tm)


	# Incorporate defunct teams
	#if league in defunct_teams.keys():
	#	for key in defunct_teams[league]:
	#		(city, name, defunctAbbrev, mapAbbrev) = defunct_teams[league][key]
	#		kwargs = {
	#			"League": league,
	#			"Key": key.lower(),
	#			"Abbreviation": defunctAbbrev,
	#			"Name": name,
	#			"FullName": "%s %s" % (city, name),
	#			"City": city
	#			}
	#		__add_or_override_team(teams, **kwargs)

	# Activate franchises
	for franchise in franchises.values():
		if not franchise.active:
			anyActiveTeams = False
			for team in franchise.teams.values():
				if team.active:
					anyActiveTeams = True
					break
			if anyActiveTeams:
				franchise.active = True
	for franchise in franchises.values():
		if not franchise.fromYear or not franchise.toYear:
			minYear = None
			maxYear = None
			for team in franchise.teams.values():
				for span in team.years:
					if span.fromYear:
						if not minYear or span.fromYear < minYear: minYear = span.fromYear
					if span.toYear:
						if not maxYear or span.toYear < maxYear: maxYear = span.toYear

	return franchises



def __find_team(franchises, franchiseName, teamName):
	
	fs = franchises.values()
	franchise = None
	team = None

	# Try to find franchise by name
	if franchiseName:
		for fn in franchises.keys():
			if fn == franchiseName: # TODO: Strip Diacritics
				franchise = franchises[fn]
				fs = [franchise]
				break

	for f in fs:
		team = f.FindTeam(teamName)
		if team:
			franchise = f
			break

	if not franchise:
		fn = teamName if not franchiseName else franchiseName
		franchise = Franchise(fn)
		franchises[fn] = franchise

	if teamName and not team:
		team = Team(teamName)
		franchise.teams.setdefault(teamName, team)


	return (franchise, team)


















def __get_teams_from_cache(league):
	if (league in known_leagues.keys() == False):
		return None
	if (__team_cache_has_teams(league) == False):
		if __team_cache_file_exists(league) == False:
			__refresh_team_cache(league)
		else:
			franchises = FranchiseDict()
			jsonFranchises = []
			cachedJson = __read_team_cache_file(league) #TODO: Try/Catch
			cacheContainer = CacheContainer.Deserialize(cachedJson)

			if not cacheContainer or cacheContainer.IsInvalid(CACHE_VERSION):
				jsonFranchises = __refresh_team_cache(league)
			else:
				jsonFranchises = cacheContainer.Items[0] # Assuming we have one item

			if not jsonFranchises:
				jsonFranchises = __refresh_team_cache(league)
				franchises = FranchiseDict(jsonFranchises)
			else:
				franchises = FranchiseDict()
				for franchiseName in sorted(jsonFranchises.keys()):
					jsonFranchise = jsonFranchises[franchiseName]
					franchise = Franchise(**jsonFranchise)
					franchises.setdefault(franchiseName, franchise)
				franchises.invalidate()
				cached_franchises.setdefault(league, franchises)
				cached_franchises[league] = franchises
			cwmt = __get_cities_with_multiple_teams(league, franchises)
			cities_with_multiple_teams.setdefault(league, cwmt)
			cities_with_multiple_teams[league] = cwmt
			teamKeys = __get_teams_keys(league, franchises, cwmt)
			cached_team_keys.setdefault(league, teamKeys)
			cached_team_keys[league] = teamKeys
	return cached_franchises[league]

def __refresh_team_cache(league):
	print("Refreshing %s franchises/teams cache ..." % league)
	franchises = __get_franchises(league, download=True)
	cached_franchises.setdefault(league, franchises)
	cached_franchises[league] = franchises
	cwmt = __get_cities_with_multiple_teams(league, franchises)
	cities_with_multiple_teams.setdefault(league, cwmt)
	cities_with_multiple_teams[league] = cwmt
	teamKeys = __get_teams_keys(league, franchises, cwmt)
	cached_team_keys.setdefault(league, teamKeys)
	cached_team_keys[league] = teamKeys
	jsonFranchises = [franchises]
	cacheContainer = CacheContainer(jsonFranchises, CacheType="%sFRANCHISES" % league, Version=CACHE_VERSION, Duration=CACHE_DURATION)
	__write_team_cache_file(league, cacheContainer.Serialize())

	return jsonFranchises

def __team_cache_has_teams(league):
	if len(cached_franchises) == 0:
		return False
	if league in cached_franchises.keys() == False:
		return False
	if (cached_franchises.get(league) == None):
		return False
	return len(cached_franchises[league]) > 0

def __team_cache_file_exists(league):
	path = __get_team_cache_file_path(league)
	return os.path.exists(path)

def __read_team_cache_file(league):
	path = __get_team_cache_file_path(league)
	return open(path, "r").read() # TODO: Invalidate cache

def __write_team_cache_file(league, json):
	print("Writing %s franchises/teams cache to disk ..." % league)
	path = __get_team_cache_file_path(league)
	dir = os.path.dirname(path)
	EnsureDirectory(dir)
	f = open(path, "w")
	f.write(json)
	f.close()


FRANCHISES_FILE_NAME = "Franchises.json"
def __get_team_cache_file_path(league):
	path = os.path.join(GetDataPathForLeague(league), FRANCHISES_FILE_NAME)
	return path




# New York, LA
def __get_cities_with_multiple_teams(league, franchises):
	cities = dict()
	for franchise in franchises.values():
		for team in franchise.teams.values():
			if not team.active: continue
			city = team.city
			cityKey = strip_to_alphanumeric(city)
			#if not team.Key[:1] == "~":
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
			if create_scannable_key(c[i]) == cityKey:
				for j in range(len(c)):
					variants.append(create_scannable_key(c[j]))
				return variants

	return variants

def __get_teams_keys(league, franchises, multi_team_city_keys):
	keys = dict()

	for franchise in franchises.values():
		for team in franchise.teams.values():
			key = team.key
			if not key: continue
			abbrev = team.abbreviation
			fullName = create_scannable_key(team.fullName)
			name = create_scannable_key(team.name)
			city = create_scannable_key(team.city)

			if fullName:
				keys.setdefault(fullName, key)
			keys.setdefault(name, key)

			for alias in team.aliases:
				keys.setdefault(create_scannable_key(alias), key)

			if city:
				cityVariants = __get_city_variants(city)
				if (cityVariants):
					for v in cityVariants:
						keys.setdefault(v+name, key)
						if v not in multi_team_city_keys:
							keys.setdefault(v, key)
							for alias in team.aliases:
								keys.setdefault(v + create_scannable_key(alias), key)
				if city not in multi_team_city_keys:
					keys.setdefault(city, key)
				for alias in team.aliases:
					keys.setdefault(city + create_scannable_key(alias), key)



			if key[:1] == "~":
				keys.setdefault("~" + create_scannable_key(key), key)

			keys.setdefault(create_scannable_key(abbrev), key)

	#if league in data_corrections.keys():
	#	for key in data_corrections[league].keys():
	#		keys.setdefault(create_scannable_key(key), data_corrections[league][key])


	return keys
