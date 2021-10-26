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
from NBA import NBAAPIFranchiseAdapter
from NHL import NHLAPIFranchiseAdapter
import ESPNAPIFranchiseAdapter

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

cached_franchises = dict()
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

	def incorporate_franchises(allFranchises, franchises):
		for f in franchises.values():
			franchiseName = f["name"]
			(franchise, fteam) = __find_team(allFranchises, franchiseName, None)
			franchise.Augment(**f)
			
			incorporate_teams(allFranchises, f["teams"], franchiseName)

	def incorporate_teams(allFranchises, teams, franchiseName=None):
		for tm in teams.values():
			teamName = tm.get("fullName") or tm.get("FullName") # TODO: Phase out capitalized keys
			(franchise, team) = __find_team(allFranchises, franchiseName, teamName, TeamIdentity(**tm), tm.get("active"))
			team.Augment(**tm)


	if league == LEAGUE_MLB:
		# Retrieve data from MLB stats API
		mlbapiFranchises = MLBAPIFranchiseAdapter.DownloadAllFranchises(league)
		incorporate_franchises(franchises, mlbapiFranchises)
	elif league == LEAGUE_NBA:
		# Retrieve data from TheSportsDB.com
		#nbaapiTeams = NBAAPIFranchiseAdapter.DownloadAllTeams(league)
		#incorporate_teams(franchises, nbaapiTeams)
		nbaapiFranchises = NBAAPIFranchiseAdapter.DownloadAllFranchises(league)
		incorporate_franchises(franchises, nbaapiFranchises)
	elif league == LEAGUE_NFL:
		# Retrieve data from pro-football-reference.com
		pfrFranchises = ProFootballReferenceFranchiseAdapter.DownloadAllFranchises(league)
		incorporate_franchises(franchises, pfrFranchises)
	elif league == LEAGUE_NHL:
		# Retrieve data from NHL stats API
		nhlapiFranchises = NHLAPIFranchiseAdapter.DownloadAllFranchises(league)
		incorporate_franchises(franchises, nhlapiFranchises)
		
	# Augment/replace with data from ESPN API
	espnapiTeams = ESPNAPIFranchiseAdapter.DownloadAllTeams(league)
	incorporate_teams(franchises, espnapiTeams)
		
	# Augment/replace with data from SportsData.io
	sportsDataIoTeams = SportsDataIOFranchiseAdapter.DownloadAllTeams(league)
	incorporate_teams(franchises, sportsDataIoTeams)

	# Retrieve data from TheSportsDB.com
	sportsDbTeams = TheSportsDBFranchiseAdapter.DownloadAllTeams(league)
	incorporate_teams(franchises, sportsDbTeams)


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

	# Open-end all the active year sets
	for franchise in franchises.values():
		minYear = franchise.fromYear
		maxYear = franchise.toYear
		if franchise.fromYear or franchise.toYear:
			if not minYear or franchise.fromYear < minYear: minYear = franchise.fromYear
			if not maxYear or franchise.toYear > maxYear: maxYear = franchise.toYear
			for team in franchise.teams.values():
				for span in team.years:
					if span.fromYear:
						if not minYear or span.fromYear < minYear: minYear = span.fromYear
					if team.active == True and span.toYear:
						if not maxYear or span.toYear > maxYear: maxYear = span.toYear

		for team in franchise.teams.values():
			for span in team.years:
				if franchise.active and team.active and span.toYear == maxYear:
					span.toYear = None
					franchise.toYear = None



	return franchises



def __find_team(franchises, franchiseName, teamName, identity=None, active=None):
	
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
		team = f.FindTeam(None, identity, active)
		if not team:
			team = f.FindTeam(teamName, identity, active)


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

def __team_cache_has_teams(league): # TODO: Found a big ole bug in FranchiseDict
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
