# Python framework
import re

# Local package
from Constants import *
from Matching import __expressions_from_literal, Eat

MLB_DIVISION_AL = "AL"
MLB_DIVISION_NL = "NL"

MLB_DIVISION_NAME_AL = "American League"
MLB_DIVISION_NAME_NL = "National League"

mlb_divisions = {
    MLB_DIVISION_AL: MLB_DIVISION_NAME_AL,
    MLB_DIVISION_NL: MLB_DIVISION_NAME_NL
    }

mlb_division_expressions = [
    (MLB_DIVISION_AL, [MLB_DIVISION_AL]+__expressions_from_literal(MLB_DIVISION_NAME_AL)),
    (MLB_DIVISION_NL, [MLB_DIVISION_NL]+__expressions_from_literal(MLB_DIVISION_NAME_NL))
    ]

MLB_SUBSEASON_FLAG_PRESEASON = -1
MLB_SUBSEASON_FLAG_REGULAR_SEASON = 0
MLB_SUBSEASON_FLAG_POSTSEASON = 1

MLB_SUBSEASON_PRESEASON = "Preseason"
MLB_SUBSEASON_SPRING_TRAINING = "Spring Training"
MLB_SUBSEASON_POSTSEASON = "Postseason"
MLB_SUBSEASON_PLAYOFFS = "Playoffs"
MLB_SUBSEASON_REGULAR_SEASON = "Regular Season"

mlb_subseason_indicator_expressions = [
    (MLB_SUBSEASON_FLAG_PRESEASON, __expressions_from_literal(MLB_SUBSEASON_PRESEASON) + __expressions_from_literal(MLB_SUBSEASON_SPRING_TRAINING)),
    (MLB_SUBSEASON_FLAG_POSTSEASON, __expressions_from_literal(MLB_SUBSEASON_POSTSEASON) + __expressions_from_literal(MLB_SUBSEASON_PLAYOFFS)),
    (MLB_SUBSEASON_FLAG_REGULAR_SEASON, __expressions_from_literal(MLB_SUBSEASON_REGULAR_SEASON))
    ]

# (expressions, conference, round)
# Ordered by more specific to less
mlb_playoff_round_expressions = [
    (__expressions_from_literal("%s Wildcard Round" % MLB_DIVISION_NAME_AL) + __expressions_from_literal("%s Wildcard" % MLB_DIVISION_NAME_AL), MLB_DIVISION_AL, 1),
    (__expressions_from_literal("%s Wildcard Round" % MLB_DIVISION_NAME_NL) + __expressions_from_literal("%s Wildcard" % MLB_DIVISION_NAME_NL), MLB_DIVISION_NL, 1),
    (__expressions_from_literal("%s Wildcard Series" % MLB_DIVISION_NAME_AL) + __expressions_from_literal("%s Wildcard" % MLB_DIVISION_NAME_AL), MLB_DIVISION_AL, 1),
    (__expressions_from_literal("%s Wildcard Series" % MLB_DIVISION_NAME_NL) + __expressions_from_literal("%s Wildcard" % MLB_DIVISION_NAME_NL), MLB_DIVISION_NL, 1),
    (__expressions_from_literal("%s Wildcard Round" % MLB_DIVISION_AL) + __expressions_from_literal("%s Wildcard" % MLB_DIVISION_AL), MLB_DIVISION_AL, 1),
    (__expressions_from_literal("%s Wildcard Round" % MLB_DIVISION_NL) + __expressions_from_literal("%s Wildcard" % MLB_DIVISION_NL), MLB_DIVISION_NL, 1),
    (__expressions_from_literal("%s Wildcard Series" % MLB_DIVISION_AL) + __expressions_from_literal("%s Wildcard" % MLB_DIVISION_AL), MLB_DIVISION_AL, 1),
    (__expressions_from_literal("%s Wildcard Series" % MLB_DIVISION_NL) + __expressions_from_literal("%s Wildcard" % MLB_DIVISION_NL), MLB_DIVISION_NL, 1),
    (__expressions_from_literal("Wildcard Round") +__expressions_from_literal("Wildcard Series") + __expressions_from_literal("Wildcard"), None, 1),

    (__expressions_from_literal("%s Divisional Round" % MLB_DIVISION_NAME_AL) + __expressions_from_literal("%s Division Round" % MLB_DIVISION_NAME_AL) + __expressions_from_literal("%s Division Playoffs" % MLB_DIVISION_NAME_AL), MLB_DIVISION_AL, 2),
    (__expressions_from_literal("%s Divisional Round" % MLB_DIVISION_NAME_NL) + __expressions_from_literal("%s Division Round" % MLB_DIVISION_NAME_NL) + __expressions_from_literal("%s Division Playoffs" % MLB_DIVISION_NAME_NL), MLB_DIVISION_NL, 2),
    (__expressions_from_literal("%s Divisional Series" % MLB_DIVISION_NAME_AL) + __expressions_from_literal("%s Division Series" % MLB_DIVISION_NAME_AL) + __expressions_from_literal("%s Division Playoffs" % MLB_DIVISION_NAME_AL), MLB_DIVISION_AL, 2),
    (__expressions_from_literal("%s Divisional Series" % MLB_DIVISION_NAME_NL) + __expressions_from_literal("%s Division Series" % MLB_DIVISION_NAME_NL) + __expressions_from_literal("%s Division Playoffs" % MLB_DIVISION_NAME_NL), MLB_DIVISION_NL, 2),
    (__expressions_from_literal("%s Divisional Round" % MLB_DIVISION_AL) + __expressions_from_literal("%s Division Round" % MLB_DIVISION_AL) + __expressions_from_literal("%s Division Playoffs" % MLB_DIVISION_AL), MLB_DIVISION_AL, 2),
    (__expressions_from_literal("%s Divisional Round" % MLB_DIVISION_NL) + __expressions_from_literal("%s Division Round" % MLB_DIVISION_NL) + __expressions_from_literal("%s Division Playoffs" % MLB_DIVISION_NL), MLB_DIVISION_NL, 2),
    (__expressions_from_literal("%s Divisional Series" % MLB_DIVISION_AL) + __expressions_from_literal("%s Division Series" % MLB_DIVISION_AL) + __expressions_from_literal("%s Division Playoffs" % MLB_DIVISION_AL), MLB_DIVISION_AL, 2),
    (__expressions_from_literal("%s Divisional Series" % MLB_DIVISION_NL) + __expressions_from_literal("%s Division Series" % MLB_DIVISION_NL) + __expressions_from_literal("%s Division Playoffs" % MLB_DIVISION_NL), MLB_DIVISION_NL, 2),
    (__expressions_from_literal("Divisional Round") + __expressions_from_literal("Division Round") + __expressions_from_literal("Division Series") + __expressions_from_literal("Division Playoffs"), None, 2),
    (__expressions_from_literal("%sDS" % MLB_DIVISION_AL), MLB_DIVISION_AL, 2),
    (__expressions_from_literal("%sDS" % MLB_DIVISION_NL), MLB_DIVISION_NL, 2),

    (__expressions_from_literal("%s Championship Round" % MLB_DIVISION_NAME_AL) + __expressions_from_literal("%s Championship Playoffs" % MLB_DIVISION_NAME_AL), MLB_DIVISION_AL, 3),
    (__expressions_from_literal("%s Championship Round" % MLB_DIVISION_NAME_NL) + __expressions_from_literal("%s Championship Playoffs" % MLB_DIVISION_NAME_NL), MLB_DIVISION_NL, 3),
    (__expressions_from_literal("%s Championship Series" % MLB_DIVISION_NAME_AL) + __expressions_from_literal("%s Championship Playoffs" % MLB_DIVISION_NAME_AL), MLB_DIVISION_AL, 3),
    (__expressions_from_literal("%s Championship Series" % MLB_DIVISION_NAME_NL) + __expressions_from_literal("%s Championship Playoffs" % MLB_DIVISION_NAME_NL), MLB_DIVISION_NL, 3),
    (__expressions_from_literal("%s Championship Round" % MLB_DIVISION_AL) + __expressions_from_literal("%s Championship Playoffs" % MLB_DIVISION_AL), MLB_DIVISION_AL, 3),
    (__expressions_from_literal("%s Championship Round" % MLB_DIVISION_NL) + __expressions_from_literal("%s Championship Playoffs" % MLB_DIVISION_NL), MLB_DIVISION_NL, 3),
    (__expressions_from_literal("%s Championship Series" % MLB_DIVISION_AL) + __expressions_from_literal("%s Championship Playoffs" % MLB_DIVISION_AL), MLB_DIVISION_AL, 3),
    (__expressions_from_literal("%s Championship Series" % MLB_DIVISION_NL) + __expressions_from_literal("%s Championship Playoffs" % MLB_DIVISION_NL), MLB_DIVISION_NL, 3),
    (__expressions_from_literal("Championship Round") + __expressions_from_literal("Championship Series") + __expressions_from_literal("Championship Playoffs"), None, 3),
    (__expressions_from_literal("%sCS" % MLB_DIVISION_AL), MLB_DIVISION_AL, 3),
    (__expressions_from_literal("%sCS" % MLB_DIVISION_NL), MLB_DIVISION_NL, 3)
    ]

MLB_EVENT_FLAG_HALL_OF_FAME = -1
MLB_EVENT_FLAG_HOME_RUN_DERBY = 1
MLB_EVENT_FLAG_ALL_STAR_GAME = 2

# (expressions, event, flag)
# Ordered by more specific to less
mlb_event_expressions = [
    (__expressions_from_literal("Hall of Fame Game"), MLB_EVENT_FLAG_HALL_OF_FAME),
    (__expressions_from_literal("Hall of Fame"), MLB_EVENT_FLAG_HALL_OF_FAME),
    (__expressions_from_literal("HOF Game"), MLB_EVENT_FLAG_HALL_OF_FAME),
    (["HOF"], MLB_EVENT_FLAG_HALL_OF_FAME),
    (__expressions_from_literal("Home Run Derby"), MLB_EVENT_FLAG_HOME_RUN_DERBY),
    (__expressions_from_literal("All Star Game"), MLB_EVENT_FLAG_ALL_STAR_GAME),
    (__expressions_from_literal("All-Star Game"), MLB_EVENT_FLAG_ALL_STAR_GAME)
    ]

world_series_expressions = [
    __expressions_from_literal("World Series")
]







def InferSubseasonFromFolders(filename, folders, meta):
    league = meta.get(METADATA_LEAGUE_KEY)
    season = meta.get(METADATA_SEASON_KEY)
    if folders and league and season:
        foundSubseason = False

        # Test to see if next-level folder is a subseason indicator
        folder = folders[0]
        for (ind, exprs) in mlb_subseason_indicator_expressions:
            if foundSubseason == True:
                break
            for expr in exprs:
                if foundSubseason == True:
                    break
                for pattern in [r"^%s$" % expr, r"\b%s\b" % expr]:
                    m = re.match(pattern, folder, re.IGNORECASE)
                    if m:
                        foundSubseason = True

                        meta.setdefault(METADATA_SUBSEASON_INDICATOR_KEY, ind)
                        meta.setdefault(METADATA_SUBSEASON_KEY, folder)
                        del(folders[0])
                        break

def InferPostseasonDivisionFromFolders(filename, folders, meta):
    league = meta.get(METADATA_LEAGUE_KEY)
    season = meta.get(METADATA_SEASON_KEY)
    ind = meta.get(METADATA_SUBSEASON_INDICATOR_KEY)
    if folders and league and season and ind == MLB_SEASON_FLAG_POSTSEASON:
        foundDivision = False

        # Test to see if next-level folder is a division (postseason)
        folder = folders[0]
        for (division, exprs) in mlb_division_expressions:
            if foundDivision == True:
                break
            for expr in exprs:
                if foundDivision == True:
                    break
                for pattern in [r"^%s$" % expr, r"\b%s\b" % expr]:
                    m = re.match(pattern, folder, re.IGNORECASE)
                    if m:
                        foundDivision = True

                        meta.setdefault(METADATA_DIVISION_KEY, division)
                        del(folders[0])
                        break



def InferPlayoffRoundFromFolders(filename, folders, meta):
    league = meta.get(METADATA_LEAGUE_KEY)
    season = meta.get(METADATA_SEASON_KEY)
    if folders and league and season:
        foundRound = False

        # Test to see if next-level folder is a subseason indicator
        folder = folders[0]
        for (exprs, division, round) in mlb_playoff_round_expressions:
            if foundRound == True:
                break
            for expr in exprs:
                if foundRound == True:
                    break
                for pattern in [r"^%s$" % expr, r"\b%s\b" % expr]:
                    m = re.match(pattern, folder, re.IGNORECASE)
                    if m:
                        foundRound = True

                        meta.setdefault(METADATA_SUBSEASON_INDICATOR_KEY, 1)
                        meta.setdefault(METADATA_DIVISION_KEY, division)
                        meta.setdefault(METADATA_PLAYOFF_ROUND_KEY, round)
                        meta.setdefault(METADATA_EVENT_NAME_KEY, folder)
                        del(folders[0])
                        break

def InferSingleEventFromFileName(filename, food, meta):
    if food:
        # Test to see if filename contains a single event, like Super Bowl, or Pro Bowl
        foundEvent = False
        for (exprs, ind) in mlb_event_expressions:
            if foundEvent == True:
                break
            for expr in exprs:
                for pattern in [r"^%s$" % expr, r"\b%s\b" % expr]:
                    (bites, chewed, ms) = Eat(food, pattern)
                    if bites:
                        foundEvent = True
                        meta.setdefault(METADATA_SPORT_KEY, SPORT_BASEBALL)
                        meta.setdefault(METADATA_LEAGUE_KEY, LEAGUE_MLB)
                        meta.setdefault(METADATA_EVENT_INDICATOR_KEY, ind)
                        meta.setdefault(METADATA_EVENT_NAME_KEY, bites[0])
                        return chewed
