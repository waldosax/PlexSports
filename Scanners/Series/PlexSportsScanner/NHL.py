
# Python framework
import re

# Local package
from Constants import *
from Matching import __expressions_from_literal, Eat

NHL_CONFERENCE_EAST = "East"
NHL_CONFERENCE_WEST = "West"

NHL_CONFERENCE_NAME_EAST = "Eastern Conference"
NHL_CONFERENCE_NAME_WEST = "Western Conference"

nhl_conferences = {
    NHL_CONFERENCE_EAST: NHL_CONFERENCE_NAME_EAST,
    NHL_CONFERENCE_WEST: NHL_CONFERENCE_NAME_WEST
    }

nhl_conference_expressions = [
    (NHL_CONFERENCE_EAST, [NHL_CONFERENCE_EAST]+__expressions_from_literal(NHL_CONFERENCE_NAME_EAST)),
    (NHL_CONFERENCE_WEST, [NHL_CONFERENCE_WEST]+__expressions_from_literal(NHL_CONFERENCE_NAME_WEST))
    ]

NHL_DIVISION_ATLANTIC = "Atlantic"
NHL_DIVISION_METROPOLITAN = "Metropolitan"
NHL_DIVISION_CENTRAL = "Central"
NHL_DIVISION_PACIFIC = "Pacific"

NHL_DIVISION_NAME_ATLANTIC = "Atlantic Division"
NHL_DIVISION_NAME_METROPOLITAN = "Metropolitan Division"
NHL_DIVISION_NAME_CENTRAL = "Central Division"
NHL_DIVISION_NAME_PACIFIC = "Pacific Division"

nhl_divisions = {
    NHL_DIVISION_ATLANTIC: NHL_DIVISION_NAME_ATLANTIC,
    NHL_DIVISION_METROPOLITAN: NHL_DIVISION_NAME_METROPOLITAN,
    NHL_DIVISION_CENTRAL: NHL_DIVISION_NAME_CENTRAL,
    NHL_DIVISION_PACIFIC: NHL_DIVISION_NAME_PACIFIC
    }

nhl_division_expressions = [
    (NHL_DIVISION_ATLANTIC, [NHL_DIVISION_ATLANTIC]+__expressions_from_literal(NHL_DIVISION_NAME_ATLANTIC)),
    (NHL_DIVISION_METROPOLITAN, [NHL_DIVISION_METROPOLITAN, "Metro"]+__expressions_from_literal(NHL_DIVISION_NAME_METROPOLITAN)+__expressions_from_literal("Metro Division")),
    (NHL_DIVISION_CENTRAL, [NHL_DIVISION_CENTRAL]+__expressions_from_literal(NHL_DIVISION_NAME_CENTRAL)),
    (NHL_DIVISION_PACIFIC, [NHL_DIVISION_PACIFIC]+__expressions_from_literal(NHL_DIVISION_NAME_PACIFIC)),
    ]

NHL_SUBSEASON_FLAG_PRESEASON = -1
NHL_SUBSEASON_FLAG_REGULAR_SEASON = 0
NHL_SUBSEASON_FLAG_POSTSEASON = 1

NHL_SUBSEASON_PRESEASON = "Preseason"
NHL_SUBSEASON_POSTSEASON = "Postseason"
NHL_SUBSEASON_PLAYOFFS = "Playoffs"
NHL_SUBSEASON_REGULAR_SEASON = "Regular Season"
NHL_SUBSEASON_STANLEY_CUP = "Stanley Cup"

nhl_stanley_cup_expressions = __expressions_from_literal(NHL_SUBSEASON_STANLEY_CUP) + __expressions_from_literal(NHL_SUBSEASON_STANLEY_CUP + " " + NHL_SUBSEASON_PLAYOFFS)

# TODO: Remove all '__expressions_from_literal' calls  from values that are a single word
nhl_subseason_indicator_expressions = [
    (NHL_SUBSEASON_FLAG_PRESEASON, __expressions_from_literal(NHL_SUBSEASON_PRESEASON)),
    (NHL_SUBSEASON_FLAG_POSTSEASON, __expressions_from_literal(NHL_SUBSEASON_POSTSEASON) + __expressions_from_literal(NHL_SUBSEASON_PLAYOFFS) + nhl_stanley_cup_expressions),
    (NHL_SUBSEASON_FLAG_REGULAR_SEASON, __expressions_from_literal(NHL_SUBSEASON_REGULAR_SEASON))
    ]

NHL_PLAYOFF_ROUND_1 = 1
NHL_PLAYOFF_ROUND_2 = 2
NHL_PLAYOFF_ROUND_3 = 3
NHL_PLAYOFF_ROUND_STANLEY_CUP = 4

nhl_stanley_cup_playoff_round_expressions = __expressions_from_literal(NHL_SUBSEASON_STANLEY_CUP + " Finals") + nhl_stanley_cup_expressions
    

# (expressions, round)
nhl_playoff_round_expressions = [
    (
        __expressions_from_literal("1st Round") +
        __expressions_from_literal("First Round") +
        __expressions_from_literal("Round 1"), NHL_PLAYOFF_ROUND_1),
    (
        __expressions_from_literal("2nd Round") + 
        __expressions_from_literal("Second Round") + 
        __expressions_from_literal("Round 2"), NHL_PLAYOFF_ROUND_2),
    (
        __expressions_from_literal("3rd Round") + 
        __expressions_from_literal("Third Round") + 
        __expressions_from_literal("Round 3") + 
        __expressions_from_literal("Conference Finals"), NHL_PLAYOFF_ROUND_3),
    (
        __expressions_from_literal("4th Round") +
        __expressions_from_literal("Fourth Round") +
        __expressions_from_literal("Round 4") +
        nhl_stanley_cup_playoff_round_expressions +
        __expressions_from_literal("Finals"), NHL_PLAYOFF_ROUND_STANLEY_CUP)
    ]

NHL_EVENT_FLAG_HALL_OF_FAME = -1
NHL_EVENT_FLAG_ALL_STAR_GAME = 1
NHL_EVENT_FLAG_WINTER_CLASSIC = 2

# (expressions, event, flag)
# Ordered by more specific to less
nhl_event_expressions = [
    (__expressions_from_literal("Hall of Fame Game"), NHL_EVENT_FLAG_HALL_OF_FAME),
    (__expressions_from_literal("Hall of Fame"), NHL_EVENT_FLAG_HALL_OF_FAME),
    (__expressions_from_literal("HOF Game"), NHL_EVENT_FLAG_HALL_OF_FAME),
    (["HOF"], NHL_EVENT_FLAG_HALL_OF_FAME),
    (__expressions_from_literal("All Star Game"), NHL_EVENT_FLAG_ALL_STAR_GAME),
    (__expressions_from_literal("All-Star Game"), NHL_EVENT_FLAG_ALL_STAR_GAME),
    (__expressions_from_literal("Winter Classic"), NHL_EVENT_FLAG_WINTER_CLASSIC)
    ]






def InferSubseasonFromFolders(filename, folders, meta):
    league = meta.get(METADATA_LEAGUE_KEY)
    season = meta.get(METADATA_SEASON_KEY)
    if folders and league and season:
        foundSubseason = False

        # Test to see if next-level folder is a subseason indicator
        folder = folders[0]
        for (ind, exprs) in nhl_subseason_indicator_expressions:
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

                        # Stanley Cup can mean the playoff finals or THE ENTIRE playoffs
                        #   so if folder matches, short circuit the playoff round
                        if ind == NHL_SUBSEASON_FLAG_POSTSEASON:
                            isStanleyCup = False
                            for scexpr in nhl_stanley_cup_expressions:
                                if isStanleyCup == True:
                                    break
                                for scpattern in [r"^%s$" % scexpr, r"\b%s\b" % scexpr]:
                                    scm = re.match(scpattern, folder, re.IGNORECASE)
                                    if scm:
                                        isStanleyCup = True
                                        meta.setdefault(METADATA_PLAYOFF_ROUND_KEY, NHL_PLAYOFF_ROUND_STANLEY_CUP)
                                        meta.setdefault(METADATA_EVENT_NAME_KEY, folder)
                                        break

                        del(folders[0])
                        break

        if not foundSubseason:
            InferPlayoffRoundFromFolders(filename, folders, meta)

def InferPostseasonConferenceFromFolders(filename, folders, meta):
    league = meta.get(METADATA_LEAGUE_KEY)
    season = meta.get(METADATA_SEASON_KEY)
    ind = meta.get(METADATA_SUBSEASON_INDICATOR_KEY)
    if folders and league and season and ind == NHL_SUBSEASON_FLAG_POSTSEASON:
        foundConference = False

        # Test to see if next-level folder is a conference (postseason)
        folder = folders[0]
        for (conference, exprs) in nhl_conference_expressions:
            if foundConference == True:
                break
            for expr in exprs:
                if foundConference == True:
                    break
                for pattern in [r"^%s$" % expr, r"\b%s\b" % expr]:
                    m = re.match(pattern, folder, re.IGNORECASE)
                    if m:
                        foundConference = True

                        meta.setdefault(METADATA_CONFERENCE_KEY, conference)
                        del(folders[0])
                        break


def InferPlayoffRoundFromFolders(filename, folders, meta):
    playoffRound = meta.get(METADATA_PLAYOFF_ROUND_KEY)
    if playoffRound:
        pass
    league = meta.get(METADATA_LEAGUE_KEY)
    season = meta.get(METADATA_SEASON_KEY)
    if folders and league and season:
        foundRound = False

        # Test to see if next-level folder is a playoff round
        folder = folders[0]
        for (exprs, round) in nhl_playoff_round_expressions:
            if foundRound == True:
                break
            for expr in exprs:
                if foundRound == True:
                    break
                for pattern in [r"^%s$" % expr, r"\b%s\b" % expr]:
                    m = re.match(pattern, folder, re.IGNORECASE)
                    if m:
                        foundRound = True

                        meta.setdefault(METADATA_SUBSEASON_KEY, folder)
                        meta.setdefault(METADATA_SUBSEASON_INDICATOR_KEY, NHL_SUBSEASON_FLAG_POSTSEASON)
                        meta.setdefault(METADATA_PLAYOFF_ROUND_KEY, round)
                        meta.setdefault(METADATA_EVENT_NAME_KEY, folder)
                        del(folders[0])
                        break

def InferSingleEventFromFileName(filename, food, meta):
    if food:
        # Test to see if filename contains a single event, like Winter Classic or All-Star Game
        foundEvent = False
        for (exprs, ind) in nhl_event_expressions:
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
