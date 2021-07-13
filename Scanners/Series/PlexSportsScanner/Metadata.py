# Python framework
import re, os, os.path, random
from pprint import pprint

# Local package
from Constants import *
from Teams import *
from Matching import *
from . import NFL



def Infer(relPath, meta):
    # Set base information
    fileName = os.path.basename(relPath)
    subfolder = os.path.dirname(relPath)
    meta.setdefault(METADATA_PATH_KEY, file)
    meta.setdefault(METADATA_FILENAME_KEY, fileName)
    meta.setdefault(METADATA_FOLDER_KEY, subfolder)

    # Infer all we can from the folder structure
    folders = Utils.SplitPath(relPath)[:-1]
    if folders:
        __infer_sport_from_folders(fileName, folders, meta)
        __infer_league_from_folders(fileName, folders, meta)
        __infer_season_from_folders(fileName, folders, meta)
        __infer_subseason_from_folders(fileName, folders, meta)
        # Anything else is your own organizational structure


def __infer_sport_from_folders(fileName, folders, meta):
    if folders:
        foundSport = False

        # Test to see if 1st-level folder is sport
        folder = folders[0]
        for sport in supported_sports:
            if foundSport == True:
                break
            for pattern in [r"^%s$" % re.escape(sport), r"\b%s\b" % re.escape(sport)]:
                if re.match(pattern, folder, re.IGNORECASE):
                    foundSport = True
                    meta.setdefault(METADATA_SPORT_KEY, sport)
                    del(folders[0])
                    break

def __infer_league_from_folders(fileName, folders, meta):
    if folders:
        foundLeague = False

        # Test to see if 1st/next-level folder is league
        folder = folders[0]
        for (league, expr) in known_leagues_expressions:
            if foundLeague == True:
                break
            for pattern in [r"^%s$" % re.escape(league), r"^%s$" % expr, r"\b%s\b" % expr]:
                if re.match(pattern, folder, re.IGNORECASE):
                    foundLeague = True
                    (leagueName, sport) = known_leagues[league]

                    meta.setdefault(METADATA_SPORT_KEY, sport)
                    meta.setdefault(METADATA_LEAGUE_KEY, league)
                    meta.setdefault(METADATA_LEAGUE_NAME_KEY, leagueName)
                    del(folders[0])
                    break

def __infer_season_from_folders(fileName, folders, meta):
    foundLeague = meta.get(METADATA_LEAGUE_KEY) is not None
    if folders and foundLeague:
        foundSeason = False

        # Test to see if next-level folder is season
        folder = folders[0]
        for expr in season_expressions:
            if foundSeason == True:
                break
            for pattern in [r"^%s$" % expr, r"\b%s\b" % expr]:
                m = re.match(pattern, folder, re.IGNORECASE)
                if m:
                    foundSeason = True
                    seasonBeginYear = __expand_year(m.group("season_year_begin") or m.string)
                    seasonEndYear = __expand_year(m.group("season_year_end"))
                    
                    if (seasonEndYear and seasonEndYear != seasonBeginYear):
                        season = "%s-%s" % (seasonBeginYear, seasonEndYear)
                    else:
                        season = str(seasonBeginYear)

                    meta.setdefault(METADATA_SEASON_KEY, season)
                    meta.setdefault(METADATA_SEASON_BEGIN_YEAR_KEY, seasonBeginYear)
                    meta.setdefault(METADATA_SEASON_END_YEAR_KEY, seasonEndYear)
                    del(folders[0])
                    break

def __infer_subseason_from_folders(fileName, folders, meta):
    league = meta.get(METADATA_LEAGUE_KEY)
    season = meta.get(METADATA_SEASON_KEY)
    if folders and league and season:

        # Test to see if next-level folder is subseason
        folder = folders[0]
        if league == LEAGUE_NFL:
            NFL.InferSubseasonFromFolder(fileName, folder, meta)
        
        #if meta.get(METADATA_SUBSEASON_KEY):
        #    del(folders[0])


def __expand_year(year):
    if not year:
        return None

    intYear = 0
    if type(year) is str:
        intYear = int(year)
    elif type(year) is int:
        intYear = year

    if intYear < 100:
        if intYear < 40:
            intYear = 2000 + intYear
        else:
            intYear = 1900 + intYear

    return str(intYear)