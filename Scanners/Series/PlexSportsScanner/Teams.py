# Python framework
import sys, os, json, re

# Plex native
import Utils

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
from Data import TheSportsDB, SportsDataIO

known_city_aliases = [
    ("NY", "New York"),
    ("NJ", "New Jersey"),
    ("LA", "Los Angeles"),
    ("LV", "Los Vegas"),
    ("DC", "Washington", "Washington DC"),
    ("NOLA", "New Orleans")
    ]

cached_teams = dict()
cities_with_multiple_teams = dict()
cached_team_keys = dict()

class TeamInfo:
    def __init__(self, **kwargs):
        self.League = str(kwargs.get("League") or "")
        self.Abbreviation = str(kwargs.get("Abbreviation") or "")
        self.Name = str(kwargs.get("Name") or "")
        self.FullName = str(kwargs.get("FullName") or "")
        self.City = str(kwargs.get("City") or "")
        self.SportsDBID = str(kwargs.get("SportsDBID") or "")
        self.SportsDataIOID = str(kwargs.get("SportsDataIO") or "")

        self.AlternateName = str(kwargs.get("AlternateName") or "")
        # Hard code until I can get teams as they existed in a given year, not just the current one.
        if self.League == LEAGUE_NFL and self.Abbreviation == "WAS":
            self.AlternateName = "Redskins"

def __add_or_override_team(teams, **kwargs):
    key = kwargs["Abbreviation"]
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

def GetTeams(league, download=False):
    if (league in known_leagues.keys() == False):
        return None # TODO: Throw
    teams = dict()
    
    # Nab from cache first
    if download == False:
        teams = __get_teams_from_cache(league)
    else:
        # Retrieve data from TheSportsDB.com
        downloadedJson = TheSportsDB.__the_sports_db_download_all_CHUNK_for_league(league)
        sportsDbTeams = json.loads(downloadedJson)
        for team in sportsDbTeams["teams"]:
            __add_or_override_team(teams, League=league, Abbreviation=team["strTeamShort"], Name=team["strTeam"], FullName=team["strTeam"], SportsDBID=team["idTeam"])
        
        # Augment/replace with data from SportsData.io
        downloadedJson = SportsDataIO.__sports_data_io_download_all_CHUNK_for_league(league)
        sportsDataIoTeams = json.loads(downloadedJson)
        for team in sportsDataIoTeams:
            __add_or_override_team(teams, League=league, Abbreviation=team["Key"], Name=team["Name"], FullName=team.get("FullName") or "%s %s" % (team["City"], team["Name"]), City=team["City"], SportsDataIOID=team["TeamID"])

    return teams


def GetAllTeams():
    allTeams = dict()
    for league in known_leagues.keys():
        teams = GetTeams(league)
        if (teams):
            allTeams.setdefault(league, teams)
    return allTeams


def __get_teams_from_cache(league):
    if (league in known_leagues.keys() == False):
        return None
    if (__team_cache_has_teams(league) == False):
        if __team_cache_file_exists(league) == False:
            __refresh_team_cache(league)
        else:
            jsonTeams = []
            cachedJson = __read_team_cache_file(league) #TODO: Try/Catch
            jsonTeams = json.loads(cachedJson)
            if (len(jsonTeams) == 0):
                __refresh_team_cache(league)
            else:
                teams = dict()
                for jsonTeam in jsonTeams:
                    team = TeamInfo(**jsonTeam)
                    teams.setdefault(team.Abbreviation, team)
                cached_teams.setdefault(league, teams)
                cached_teams[league] = teams
            cwmt = __get_cities_with_multiple_teams(teams)
            cities_with_multiple_teams.setdefault(league, cwmt)
            cities_with_multiple_teams[league] = cwmt
            teamKeys = __get_teams_keys(teams, cwmt)
            cached_team_keys.setdefault(league, teamKeys)
            cached_team_keys[league] = teamKeys
    return cached_teams[league]

def __refresh_team_cache(league):
    print("Refreshing %s teams cache ..." % league)
    teams = GetTeams(league, download=True)
    cached_teams.setdefault(league, teams)
    cached_teams[league] = teams
    cwmt = __get_cities_with_multiple_teams(teams)
    cities_with_multiple_teams.setdefault(league, cwmt)
    cities_with_multiple_teams[league] = cwmt
    teamKeys = __get_teams_keys(teams, cwmt)
    cached_team_keys.setdefault(league, teamKeys)
    cached_team_keys[league] = teamKeys
    jsonTeams = []
    for teamInfo in teams.values():
        jsonTeams.append(teamInfo.__dict__)
    __write_team_cache_file(league, json.dumps(jsonTeams, sort_keys=True, indent=4))



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
    if os.path.exists(dir) == False:
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

def InferFromFileName(fileName, food, meta):
    league = meta.get(METADATA_LEAGUE_KEY)
    teams = dict()
    if league:
        teams.setdefault(league, __get_teams_from_cache(league))
    else:
        for league in known_leagues:
            teams.setdefault(league, __get_teams_from_cache(league))

    (foundLeague, team1, team2, vs, chewed) = __find_teams(teams, food)
    if vs == "@":
        if team1:
            meta.setdefault(METADATA_AWAY_TEAM_KEY, team1.Abbreviation)
        if team2:
            meta.setdefault(METADATA_HOME_TEAM_KEY, team2.Abbreviation)
    else:
        if team1:
            meta.setdefault(METADATA_HOME_TEAM_KEY, team1.Abbreviation)
        if team2:
            meta.setdefault(METADATA_AWAY_TEAM_KEY, team2.Abbreviation)
    
    if foundLeague:
        (leagueName, sport) = known_leagues[foundLeague]
        meta.setdefault(METADATA_SPORT_KEY, sport)
        meta.setdefault(METADATA_LEAGUE_KEY, foundLeague)

    return chewed

def __find_teams(teams, food):
    # A trie would be the right solution here, but I'm not doing all
    #   that work when I'm just learning Python
    
    team1League = None
    team1 = None
    team2 = None
    vs = None

    if not food:
        return (team1League, team1, team2, vs, food)

    origFood = food[0:]

    (boiled, grit) = Boil(food)
    if not boiled:
        return (None, None, None, None, food)

    # (boiledIndex, foodIndex, boiledLength, nextFoodIndex)
    
    team1Chunk = None
    team2Chunk = None
    vsChunk = None

    # Phillies| vs. |Red Sox| Game Highlights () _  Highlights
    # 01234567| 89  |012 345| 6789 0123456789       0123456789
    # 01234567|89012|3456789|012345678901234567890123456789012
    # 8-------| 2-  |6------|                                 
    # 8-------| 3-- |7------|                                 

    for league in teams.keys():
        if team1:
            break
        for (teamKey, abbrev) in sorted(cached_team_keys[league].items(), key=__sort_by_len_key, reverse=True):
            team1Chunk = Taste(boiled, grit, teamKey, 0)
            if team1Chunk:
                team1 = cached_teams[league][abbrev]
                team1League = league
                break

    if not team1:
        return (team1League, team1, team2, vs, food)

    if team1Chunk[CHUNK_NEXT_FOOD_INDEX] >= 0:
        for (teamKey, abbrev) in sorted(cached_team_keys[team1League].items(), key=__sort_by_len_key, reverse=True):
            team2Chunk = Taste(boiled, grit, teamKey, team1Chunk[CHUNK_BOILED_INDEX] + team1Chunk[CHUNK_BOILED_LENGTH])
            if team2Chunk:
                team2 = cached_teams[league][abbrev]
                break

    if team1 and team2:
        btw = food[team1Chunk[CHUNK_NEXT_FOOD_INDEX]:team2Chunk[CHUNK_FOOD_INDEX]]
        if btw:
            for expr in versus_expressions:
                m = re.search(expr, btw, re.IGNORECASE)
                if m:
                    vs = m.string[m.start(): m.end()]   # "vs. " (0,3)
                    boiledIndex = team1Chunk[CHUNK_BOILED_INDEX] + team1Chunk[CHUNK_BOILED_LENGTH] + m.start()
                    foodIndex = grit[boiledIndex]
                    boiledLength = len(Boil(vs))
                    nextFoodIndex = grit[boiledIndex + boiledLength] if (boiledIndex + boiledLength) <len(grit) else -1

                    vsChunk = (boiledIndex, foodIndex, boiledLength, nextFoodIndex)
                    break

    food = Chew([team1Chunk, vsChunk, team2Chunk], grit, food)
    return (team1League, team1, team2, vs, food)




# New York, LA
def __get_cities_with_multiple_teams(teams):
    cities = dict()
    for team in teams.values():
        city = team.City
        cityKey = __strip_to_alphanumeric(city)
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

def __get_teams_keys(teams, multi_team_city_keys):
    keys = dict()

    for team in teams.values():
        abbrev = team.Abbreviation
        (fullName, grit) = Boil(team.FullName, ALPHANUMERIC_CHARACTERS)
        (name, grit) = Boil(team.Name, ALPHANUMERIC_CHARACTERS)
        (city, grit) = Boil(team.City, ALPHANUMERIC_CHARACTERS)
        (alt, grit) = Boil(team.AlternateName, ALPHANUMERIC_CHARACTERS)

        if fullName:
            keys.setdefault(fullName, abbrev)
        if name:
            keys.setdefault(name, abbrev)
        if city:
            cityVariants = __get_city_variants(city)
            for v in cityVariants:
                keys.setdefault(v+name, abbrev)
                keys.setdefault(v+alt, abbrev)
                if v not in multi_team_city_keys:
                    keys.setdefault(v, abbrev)
        if alt:
            keys.setdefault(alt, abbrev)
        if abbrev:
            keys.setdefault(abbrev.lower(), abbrev)

    return keys
