
# Python framework
import re

# Local package
from Constants import *
from Matching import __expressions_from_literal, Eat

NBA_CONFERENCE_EAST = "East"
NBA_CONFERENCE_WEST = "West"

NBA_CONFERENCE_NAME_EAST = "Eastern Conference"
NBA_CONFERENCE_NAME_WEST = "Western Conference"

nba_conferences = {
    NBA_CONFERENCE_EAST: NBA_CONFERENCE_NAME_EAST,
    NBA_CONFERENCE_WEST: NBA_CONFERENCE_NAME_WEST
    }

nba_conference_expressions = [
    (NBA_CONFERENCE_EAST, [NBA_CONFERENCE_EAST]+__expressions_from_literal(NBA_CONFERENCE_NAME_EAST)),
    (NBA_CONFERENCE_WEST, [NBA_CONFERENCE_WEST]+__expressions_from_literal(NBA_CONFERENCE_NAME_WEST))
    ]

NBA_SUBSEASON_FLAG_PRESEASON = -1
NBA_SUBSEASON_FLAG_REGULAR_SEASON = 0
NBA_SUBSEASON_FLAG_POSTSEASON = 1

NBA_SUBSEASON_PRESEASON = "Preseason"
NBA_SUBSEASON_POSTSEASON = "Postseason"
NBA_SUBSEASON_PLAYOFFS = "Playoffs"
NBA_SUBSEASON_REGULAR_SEASON = "Regular Season"

nba_subseason_indicator_expressions = [
    (NBA_SUBSEASON_FLAG_PRESEASON, __expressions_from_literal(NBA_SUBSEASON_PRESEASON)),
    (NBA_SUBSEASON_FLAG_POSTSEASON, __expressions_from_literal(NBA_SUBSEASON_POSTSEASON) + __expressions_from_literal(NBA_SUBSEASON_PLAYOFFS)),
    (NBA_SUBSEASON_FLAG_REGULAR_SEASON, __expressions_from_literal(NBA_SUBSEASON_REGULAR_SEASON))
    ]

# (expressions, conference, round)
# Ordered by more specific to less
nba_playoff_round_expressions = [
    (__expressions_from_literal("%s Quarterfinals" % NBA_CONFERENCE_NAME_EAST), NBA_CONFERENCE_EAST, 1),
    (__expressions_from_literal("%s Quarterfinals" % NBA_CONFERENCE_NAME_WEST), NBA_CONFERENCE_WEST, 1),
    (__expressions_from_literal("%s Quarterfinals" % NBA_CONFERENCE_EAST), NBA_CONFERENCE_EAST, 1),
    (__expressions_from_literal("%s Quarterfinals" % NBA_CONFERENCE_WEST), NBA_CONFERENCE_WEST, 1),
    (__expressions_from_literal("Quarterfinals"), None, 1),

    (__expressions_from_literal("%s Semifinals" % NBA_CONFERENCE_NAME_EAST), NBA_CONFERENCE_EAST, 2),
    (__expressions_from_literal("%s Semifinals" % NBA_CONFERENCE_NAME_WEST), NBA_CONFERENCE_WEST, 2),
    (__expressions_from_literal("%s Semifinals" % NBA_CONFERENCE_EAST), NBA_CONFERENCE_EAST, 2),
    (__expressions_from_literal("%s Semifinals" % NBA_CONFERENCE_WEST), NBA_CONFERENCE_WEST, 2),
    (__expressions_from_literal("Semifinals"), None, 2),

    (__expressions_from_literal("Championship"), None, 3),
    (__expressions_from_literal("Finals"), None, 3)
    ]

NBA_EVENT_FLAG_ALL_STAR_GAME = 1
NBA_EVENT_FLAG_3_POINT_SHOOTOUT = 2
NBA_EVENT_FLAG_SLAM_DUNK_COMPETITION = 3

# (expressions, event, flag)
# Ordered by more specific to less
nba_event_expressions = [
    (__expressions_from_literal("All Star Game"), NBA_EVENT_FLAG_ALL_STAR_GAME),
    (__expressions_from_literal("All-Star Game"), NBA_EVENT_FLAG_ALL_STAR_GAME),
    (__expressions_from_literal("3 Point Shootout"), NBA_EVENT_FLAG_3_POINT_SHOOTOUT),
    (__expressions_from_literal("Slam Dunk Competition"), NBA_EVENT_FLAG_SLAM_DUNK_COMPETITION),
    (__expressions_from_literal("Slam Dunk Contest"), NBA_EVENT_FLAG_SLAM_DUNK_COMPETITION)
    ]
# TODO: more variations on all-star weekend event names






def InferSubseasonFromFolders(filename, folders, meta):
    league = meta.get(METADATA_LEAGUE_KEY)
    season = meta.get(METADATA_SEASON_KEY)
    if folders and league and season:
        foundSubseason = False

        # Test to see if next-level folder is a subseason indicator
        folder = folders[0]
        for (ind, exprs) in nba_subseason_indicator_expressions:
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

def InferPostseasonConferenceFromFolders(filename, folders, meta):
    league = meta.get(METADATA_LEAGUE_KEY)
    season = meta.get(METADATA_SEASON_KEY)
    ind = meta.get(METADATA_SUBSEASON_INDICATOR_KEY)
    if folders and league and season and ind == NBA_SUBSEASON_FLAG_POSTSEASON:
        foundLeague = False

        # Test to see if next-level folder is a league (postseason)
        folder = folders[0]
        for (league, exprs) in nba_conference_expressions:
            if foundLeague == True:
                break
            for expr in exprs:
                if foundLeague == True:
                    break
                for pattern in [r"^%s$" % expr, r"\b%s\b" % expr]:
                    m = re.match(pattern, folder, re.IGNORECASE)
                    if m:
                        foundLeague = True

                        meta.setdefault(METADATA_CONFERENCE_KEY, league)
                        del(folders[0])
                        break




def InferPlayoffRoundFromFolders(filename, folders, meta):
    league = meta.get(METADATA_LEAGUE_KEY)
    season = meta.get(METADATA_SEASON_KEY)
    if folders and league and season:
        foundRound = False

        # Test to see if next-level folder is a subseason indicator
        folder = folders[0]
        for (exprs, league, round) in nba_playoff_round_expressions:
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
                        meta.setdefault(METADATA_LEAGUE_KEY, league)
                        meta.setdefault(METADATA_PLAYOFF_ROUND_KEY, round)
                        meta.setdefault(METADATA_EVENT_NAME_KEY, folder)
                        del(folders[0])
                        break

def InferSingleEventFromFileName(filename, food, meta):
    if food:
        # Test to see if filename contains a single event, like Super Bowl, or Pro Bowl
        foundEvent = False
        for (exprs, ind) in nba_event_expressions:
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
