import Constants
import TheSportsDB
import SportsDataIO

class TeamInfo:
    def __init__(self, **kwargs):
        self.League = str(kwargs.get("League"))
        self.Abbreviation = str(kwargs.get("Abbreviation"))
        self.Name = str(kwargs.get("Name"))
        self.FullName = str(kwargs.get("FullName"))
        self.City = str(kwargs.get("City"))
        self.SportsDBID = str(kwargs.get("SportsDBID"))
        self.SportsDataIOID = str(kwargs.get("SportsDataIO"))

def __add_or_override_team(teams: dict, **kwargs):
    key = kwargs["Abbreviation"]
    if (key in teams.keys() = False):
        team = TeamInfo(kwargs)
        teams.setdefault(key, team)
    else:
        team = teams[key]
        if (kwargs.get("Name")) team.Name = str(kwargs["Name"])
        if (kwargs.get("FullName")) team.Name = str(kwargs["FullName"])
        if (kwargs.get("City")) team.City = str(kwargs["City"])
        if (kwargs.get("SportsDBID")) team.SportsDBID = str(kwargs["SportsDBID"])
        if (kwargs.get("SportsDataIOID")) team.SportsDataIOID = str(kwargs["SportsDataIOID"])



def GetTeams(league: str) -> dict:
    if (league in known_leagues.keys() == False) return None # TODO: Throw
    teams = dict()
    # TODO: Nab from cache first

    # Retrieve data from TheSportsDB.com
    json = TheSportsDB.__the_sports_db_download_all_teams_for_league(league)
    sportsDbTeams = JSON.ObjectFromString(json)
    for team in sportsDbTeams:
        __add_or_override_team(teams, League=league, Abbreviation=team["strTeamShort"], Name=team["strTeam"], FullName=team["strTeam"], SportsDBID=team["idTeam"])
    
    # Augment with data from SportsData.io
    json = SportsDataIO.__sports_data_io_download_all_teams_for_league(league)
    sportsDataIoTeams = JSON.ObjectFromString(json)
    for team in sportsDataIoTeams:
        __add_or_override_team(teams, League=league, Abbreviation=team["Key"], Name=team["Name"], FullName=team["FullName"], City=team["City"], SportsDataIOID=team["TeamID"])

    return teams


def GetAllTeams() -> dict:
    allTeams = dict()
    for league in known_leagues.keys():
        teams = GetTeams(league)
        if (teams):
            allTeams.setdefault(league, teams)
    return allTeams
