# Python framework
import re, os, datetime
from pprint import pprint

# Local package
from Constants import *
from StringUtils import *
from Teams import *
from Matching import __sort_by_len
from Matching import __sort_by_len_key
from Matching import __sort_by_len_value
from . import Teams
from . import Matching
from . import MLB
from . import NBA
from . import NFL
from . import NHL



def Infer(relPath, file, meta):
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
        __infer_game_number_from_folders(fileName, folders, meta)
        # Anything else is your own organizational structure

    # Infer all we can from the file name
    (food, ext) = os.path.splitext(fileName)
    food = __infer_league_from_filename(fileName, food, meta)
    food = __infer_game_number_from_filename(fileName, food, meta)
    food = __infer_airdate_from_filename(fileName, food, meta)
    food = __infer_season_from_filename(fileName, food, meta)


    # Attempt to infer single events.
    food = __infer_event_from_filename(fileName, food, meta)

    sport = meta.get(METADATA_SPORT_KEY)
    if not sport or sport in supported_team_sports:
        food = __infer_teams_from_filename(fileName, food, meta)


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
            for pattern in [
                r"^%s$" % re.escape(league),
                r"^%s$" % expr
                ]:
                if re.match(pattern, folder, re.IGNORECASE):
                    foundLeague = True
                    (leagueName, sport) = known_leagues[league]

                    meta.setdefault(METADATA_SPORT_KEY, sport)
                    meta.setdefault(METADATA_LEAGUE_KEY, league)
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
                    seasonBeginYear = int(expandYear(m.group("season_year_begin") or m.string))
                    seasonEndYear = int(expandYear(m.group("season_year_end"))) if m.group("season_year_end") else None
                    
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
        if league == LEAGUE_NFL:
            # We're calling week here first because it can exist at the season level,
            #   or the preseason/regular season subfolder level.
            NFL.InferWeekFromFolders(fileName, folders, meta)
            NFL.InferSubseasonFromFolders(fileName, folders, meta)
            # We're calling week here again because it can exist at the
            #   preseason/regular season subfolder level.
            NFL.InferWeekFromFolders(fileName, folders, meta)
            # We're calling Playoff round here first because values from postseason league could match prematurely on playoff round values
            #   'AFC' could match when folder is 'AFC Championship'
            NFL.InferPlayoffRoundFromFolders(fileName, folders, meta)
            NFL.InferPostseasonConferenceFromFolders(fileName, folders, meta)
            NFL.InferPlayoffRoundFromFolders(fileName, folders, meta)
        elif league == LEAGUE_MLB:
            MLB.InferSubseasonFromFolders(fileName, folders, meta)
            MLB.InferSpringTrainingLeagueFromFolders(fileName, folders, meta)
            # We're calling Playoff round here first because values from postseason league could match prematurely on playoff round values
            #   'American League' could match when folder is 'American League Division Series'
            MLB.InferPlayoffRoundFromFolders(fileName, folders, meta)
            MLB.InferPostseasonLeagueFromFolders(fileName, folders, meta)
            MLB.InferPlayoffRoundFromFolders(fileName, folders, meta)
        elif league == LEAGUE_NBA:
            NBA.InferSubseasonFromFolders(fileName, folders, meta)
            # We're calling Playoff round here first because values from postseason conference could match prematurely on playoff round values
            #   'East' could match when folder is 'Eastern Conference Finals'
            NBA.InferPlayoffRoundFromFolders(fileName, folders, meta)
            NBA.InferPostseasonConferenceFromFolders(fileName, folders, meta)
            NBA.InferPlayoffRoundFromFolders(fileName, folders, meta)
        elif league == LEAGUE_NHL:
            NHL.InferSubseasonFromFolders(fileName, folders, meta)
            # We're calling Playoff round here first because values from postseason conference could match prematurely on playoff round values
            #   'East' could match when folder is 'Eastern Conference Finals'
            NHL.InferPlayoffRoundFromFolders(fileName, folders, meta)
            NHL.InferPostseasonConferenceFromFolders(fileName, folders, meta)
            NHL.InferPlayoffRoundFromFolders(fileName, folders, meta)


# Could be Game in a series, or game in a double-header
# TODO: MLB schedule is a little more fluid. Games can be rescheduled. That's why double-headers exist.
def __infer_game_number_from_folders(filename, folders, meta):
    sport = meta.get(METADATA_SPORT_KEY)
    league = meta.get(METADATA_LEAGUE_KEY)
    season = meta.get(METADATA_SEASON_KEY)
    if folders and (not sport or (sport and league and season and sport in supported_series_sports)):
        foundGameNumber = False

        # Test to see if next-level folder contains game number
        folder = folders[0]
        for expr in game_number_expressions:
            if foundGameNumber == True:
                break
            for pattern in [r"^%s$" % expr, r"\b%s\b" % expr]:
                m = re.match(pattern, folder, re.IGNORECASE)
                if m:
                    foundGameNumber = True

                    meta.setdefault(METADATA_GAME_NUMBER_KEY, m.group("game_number"))
                    del(folders[0])
                    break


def __infer_event_from_filename(fileName, food, meta):
    event = meta.get(METADATA_EVENT_INDICATOR_KEY)
    if not event:
        food = MLB.InferSingleEventFromFileName(fileName, food, meta)
        food = NBA.InferSingleEventFromFileName(fileName, food, meta)
        food = NFL.InferSingleEventFromFileName(fileName, food, meta)
        food = NHL.InferSingleEventFromFileName(fileName, food, meta)
    
    return food

def __infer_league_from_filename(fileName, food, meta):
    if food:
        foundLeague = False

        # Test to see if food contains known league
        for (league, expr) in known_leagues_expressions:
            if foundLeague == True:
                break
            for pattern in [r"\b%s\b" % expr]:
                (bites, chewed, ms) = Matching.Eat(food, pattern)
                if bites:
                    foundLeague = True
                    (leagueName, sport) = known_leagues[league]

                    meta.setdefault(METADATA_SPORT_KEY, sport)
                    meta.setdefault(METADATA_LEAGUE_KEY, league)
                    food = chewed
                    break
    return food

def __infer_airdate_from_filename(fileName, food, meta):
    if food:
        foundAirDate = False

        # Test to see if food contains an air date
        for expr in air_date_expressions:
            if foundAirDate == True:
                break
            for pattern in [r"\b%s\b" % expr]:
                (bites, chewed, ms) = Matching.Eat(food, pattern)
                if bites:
                    foundAirDate = True
                    
                    (m, value) = bites[0]
                    year = expandYear(m.group("year"))
                    month = m.group("month")
                    day = m.group("day")

                    if month and day:
                        airdate = datetime.date(int(year), int(month), int(day))

                        meta.setdefault(METADATA_AIRDATE_KEY, airdate)
                        food = chewed
                        break
    return food

def __infer_season_from_filename(fileName, food, meta):
    if food:
        foundSeason = False

        # Test to see if food contains season
        for expr in season_expressions:
            if foundSeason == True:
                break
            for pattern in [r"\b%s\b" % expr]:
                (bites, chewed, ms) = Matching.Eat(food, pattern)
                if bites:
                    foundSeason = True

                    (m, value) = bites[0]
                    seasonBeginYear = int(expandYear(m.group("season_year_begin") or m.string))
                    seasonEndYear = int(expandYear(m.group("season_year_end"))) if m.group("season_year_end") else None
                    
                    if (seasonEndYear and seasonEndYear != seasonBeginYear):
                        season = "%s-%s" % (seasonBeginYear, seasonEndYear)
                    else:
                        season = str(seasonBeginYear)

                    meta.setdefault(METADATA_SEASON_KEY, season)
                    meta.setdefault(METADATA_SEASON_BEGIN_YEAR_KEY, seasonBeginYear)
                    meta.setdefault(METADATA_SEASON_END_YEAR_KEY, seasonEndYear)
                    food = chewed
                    break
    return food


# Could be Game in a series, or game in a double-header
# TODO: MLB schedule is a little more fluid. Games can be rescheduled. That's why double-headers exist.
def __infer_game_number_from_filename(fileName, food, meta):
    sport = meta.get(METADATA_SPORT_KEY)
    league = meta.get(METADATA_LEAGUE_KEY)
    season = meta.get(METADATA_SEASON_KEY)
    if food and (not sport or (sport and league and season and sport in supported_series_sports)):
        foundGameNumber = False

        # Test to see if filename contains game number
        foundGameNumber = False
        for expr in game_number_expressions:
            if foundGameNumber == True:
                break
            for pattern in [r"^%s$" % expr, r"\b%s\b" % expr]:
                (bites, chewed, ms) = Eat(food, pattern)
                if bites:
                    meta.setdefault(METADATA_GAME_NUMBER_KEY, ms[0].group("game_number"))
                    return chewed




def __infer_teams_from_filename(fileName, food, meta):
	league = meta.get(METADATA_LEAGUE_KEY)
	teams = dict()
	if league:
		teams.setdefault(league, GetTeams(league))
	else:
		for league in known_leagues:
			teams.setdefault(league, GetTeams(league))

	(foundLeague, team1, team2, vs, chewed) = __find_teams(teams, food)
	if vs == "@":   # TODO: fix why vs = coming back as None
		if team1:
			meta.setdefault(METADATA_AWAY_TEAM_KEY, team1.Key)
		if team2:
			meta.setdefault(METADATA_HOME_TEAM_KEY, team2.Key)
	else:
		if team1:
			meta.setdefault(METADATA_HOME_TEAM_KEY, team1.Key)
		if team2:
			meta.setdefault(METADATA_AWAY_TEAM_KEY, team2.Key)
	
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
		return (None, None, None, None, food)

	origFood = food[0:] # Make a copy of food, just in case we need to reference the original

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
		scanKeys = sorted(cached_team_keys[league].items(), key=__sort_by_len_key, reverse=True)
		if team1:
			break
		for (scanKey, key) in scanKeys:
			team1Chunk = Taste(boiled, grit, scanKey, 0)
			if team1Chunk:
				team1 = teams[league][key]
				team1League = league
				break

	if not team1:
		return (team1League, team1, team2, vs, food)

	if team1Chunk[CHUNK_NEXT_FOOD_INDEX] >= 0:
		scanKeys = sorted(cached_team_keys[team1League].items(), key=__sort_by_len_key, reverse=True)
		for (scanKey, key) in scanKeys:
			team2Chunk = Taste(boiled, grit, scanKey, team1Chunk[CHUNK_BOILED_INDEX] + team1Chunk[CHUNK_BOILED_LENGTH])
			if team2Chunk:
				team2 = teams[league][key]
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


	# TODO: munge if unrecognized teams, but vs. found 


	food = Chew([team1Chunk, vsChunk, team2Chunk], grit, food)
	return (team1League, team1, team2, vs, food)


