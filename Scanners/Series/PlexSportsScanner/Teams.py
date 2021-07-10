import json, os
from Constants import *
from PlexSportsScanner import *
import Utils

cached_teams = dict()

class TeamInfo:
    def __init__(self, **kwargs):
        self.League = str(kwargs.get("League"))
        self.Abbreviation = str(kwargs.get("Abbreviation"))
        self.Name = str(kwargs.get("Name"))
        self.FullName = str(kwargs.get("FullName"))
        self.City = str(kwargs.get("City"))
        self.SportsDBID = str(kwargs.get("SportsDBID"))
        self.SportsDataIOID = str(kwargs.get("SportsDataIO"))

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
        downloadedJson = Data.TheSportsDB.__the_sports_db_download_all_teams_for_league(league)
        sportsDbTeams = json.loads(downloadedJson)
        for team in sportsDbTeams["teams"]:
            __add_or_override_team(teams, League=league, Abbreviation=team["strTeamShort"], Name=team["strTeam"], FullName=team["strTeam"], SportsDBID=team["idTeam"])
        
        # Augment/replace with data from SportsData.io
        downloadedJson = Data.SportsDataIO.__sports_data_io_download_all_teams_for_league(league)
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
                    team = TeamInfo(kwargs = jsonTeam)
                    teams.setdefault(team.Abbreviation, team)
                cached_teams.setdefault(league, teams)
                cached_teams[league] = teams
    return cached_teams[league]

def __refresh_team_cache(league):
    print("Refreshing %s teams cache ..." % league)
    teams = GetTeams(league, download=True)
    cached_teams.setdefault(league, teams)
    cached_teams[league] = teams
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
        paths = Utils.SplitPath(dir)
        print(paths)
        os.mkdir(dir)
    f = open(path, "w")
    f.write(json)
    f.close()

def __get_team_cache_file_path(league):
    path = os.path.abspath(r"%s/%s%s/Teams.json" % (os.path.dirname(__file__), DATA_PATH_LEAGUES, league))
    return path