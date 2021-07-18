# Python framework
import re

# Local package
from Constants import *
from Matching import __expressions_from_literal, Eat
from . import RomanNumerals

NFL_CONFERENCE_AFC = "AFC"
NFL_CONFERENCE_NFC = "NFC"

NFL_CONFERENCE_NAME_AFC = "American Football Conference"
NFL_CONFERENCE_NAME_NFC = "National Football Conference"

nfl_conferences = {
    NFL_CONFERENCE_AFC: NFL_CONFERENCE_NAME_AFC,
    NFL_CONFERENCE_NFC: NFL_CONFERENCE_NAME_NFC
    }

nfl_conference_expressions = [
    (NFL_CONFERENCE_AFC, [NFL_CONFERENCE_AFC]+__expressions_from_literal(NFL_CONFERENCE_NAME_AFC)),
    (NFL_CONFERENCE_NFC, [NFL_CONFERENCE_NFC]+__expressions_from_literal(NFL_CONFERENCE_NAME_NFC))
    ]

NFL_SUBSEASON_FLAG_PRESEASON = -1
NFL_SUBSEASON_FLAG_REGULAR_SEASON = 0
NFL_SUBSEASON_FLAG_POSTSEASON = 1

NFL_SUBSEASON_PRESEASON = "Preseason"
NFL_SUBSEASON_POSTSEASON = "Postseason"
NFL_SUBSEASON_PLAYOFFS = "Playoffs"
NFL_SUBSEASON_REGULAR_SEASON = "Regular Season"

nfl_superbowl_expressions = [
    "Superbowl((?P<sp>%s)+(?P<game_number>(\d+)|([MDCLXVI]+))?)" % EXPRESSION_SEPARATOR,
    "Super(?P<sp>%s)+bowl((?P=sp)+(?P<game_number>(\d+)|([MDCLXVI]+))?)" % EXPRESSION_SEPARATOR
    ]

nfl_subseason_indicator_expressions = [
    (NFL_SUBSEASON_FLAG_PRESEASON, __expressions_from_literal(NFL_SUBSEASON_PRESEASON)),
    (NFL_SUBSEASON_FLAG_POSTSEASON, __expressions_from_literal(NFL_SUBSEASON_POSTSEASON) + __expressions_from_literal(NFL_SUBSEASON_PLAYOFFS)),
    (NFL_SUBSEASON_FLAG_REGULAR_SEASON, __expressions_from_literal(NFL_SUBSEASON_REGULAR_SEASON))
    ]

NFL_PLAYOFF_ROUND_WILDCARD = 1
NFL_PLAYOFF_ROUND_DIVISION = 2
NFL_PLAYOFF_ROUND_CHAMPIONSHIP = 3
NFL_PLAYOFF_ROUND_SUPERBOWL = 4


# (expressions, conference, round)
# Ordered by more specific to less
nfl_playoff_round_expressions = [
    (__expressions_from_literal("%s Wildcard Round" % NFL_CONFERENCE_AFC) + __expressions_from_literal("%s Wildcard" % NFL_CONFERENCE_AFC), NFL_CONFERENCE_AFC, NFL_PLAYOFF_ROUND_WILDCARD),
    (__expressions_from_literal("%s Wildcard Round" % NFL_CONFERENCE_NFC) + __expressions_from_literal("%s Wildcard" % NFL_CONFERENCE_NFC), NFL_CONFERENCE_NFC, NFL_PLAYOFF_ROUND_WILDCARD),
    (__expressions_from_literal("Wildcard Round") + __expressions_from_literal("Wildcard"), None, NFL_PLAYOFF_ROUND_WILDCARD),
    (__expressions_from_literal("%s Divisional Round" % NFL_CONFERENCE_AFC) + __expressions_from_literal("%s Division Playoffs" % NFL_CONFERENCE_AFC), NFL_CONFERENCE_AFC, NFL_PLAYOFF_ROUND_DIVISION),
    (__expressions_from_literal("%s Divisional Round" % NFL_CONFERENCE_NFC) + __expressions_from_literal("%s Division Playoffs" % NFL_CONFERENCE_NFC), NFL_CONFERENCE_NFC, NFL_PLAYOFF_ROUND_DIVISION),
    (__expressions_from_literal("Divisional Round") + __expressions_from_literal("Division Playoffs"), None, NFL_PLAYOFF_ROUND_DIVISION),
    (__expressions_from_literal("%s Championship Round" % NFL_CONFERENCE_AFC) + __expressions_from_literal("%s Championship" % NFL_CONFERENCE_AFC), NFL_CONFERENCE_AFC, NFL_PLAYOFF_ROUND_CHAMPIONSHIP),
    (__expressions_from_literal("%s Championship Round" % NFL_CONFERENCE_NFC) + __expressions_from_literal("%s Championship" % NFL_CONFERENCE_NFC), NFL_CONFERENCE_NFC, NFL_PLAYOFF_ROUND_CHAMPIONSHIP),
    (__expressions_from_literal("Conference Championship Round") + __expressions_from_literal("Conference Championship"), None, NFL_PLAYOFF_ROUND_CHAMPIONSHIP),
    (__expressions_from_literal("Championship Round"), None, NFL_PLAYOFF_ROUND_CHAMPIONSHIP),
    (nfl_superbowl_expressions, None, NFL_PLAYOFF_ROUND_SUPERBOWL),
    ]

NFL_EVENT_FLAG_HALL_OF_FAME = -1
NFL_EVENT_FLAG_SUPERBOWL = 1
NFL_EVENT_FLAG_PRO_BOWL = 2

# (expressions, event, flag)
# Ordered by more specific to less
nfl_event_expressions = [
    (nfl_superbowl_expressions, NFL_EVENT_FLAG_SUPERBOWL),
    (__expressions_from_literal("Hall of Fame Game"), NFL_EVENT_FLAG_HALL_OF_FAME),
    (__expressions_from_literal("Hall of Fame"), NFL_EVENT_FLAG_HALL_OF_FAME),
    (__expressions_from_literal("HOF Game"), NFL_EVENT_FLAG_HALL_OF_FAME),
    (["HOF"], NFL_EVENT_FLAG_HALL_OF_FAME),
    (__expressions_from_literal("Pro Bowl"), NFL_EVENT_FLAG_PRO_BOWL)
    ]






def InferSubseasonFromFolders(filename, folders, meta):
    league = meta.get(METADATA_LEAGUE_KEY)
    season = meta.get(METADATA_SEASON_KEY)
    if folders and league and season:
        foundSubseason = False

        # Test to see if next-level folder is a subseason indicator
        folder = folders[0]
        for (ind, exprs) in nfl_subseason_indicator_expressions:
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

        if not foundSubseason:
            InferPlayoffRoundFromFolders(filename, folders, meta)

def InferWeekFromFolders(filename, folders, meta):
    league = meta.get(METADATA_LEAGUE_KEY)
    season = meta.get(METADATA_SEASON_KEY)
    ind = meta.get(METADATA_SUBSEASON_INDICATOR_KEY)
    if folders and league and season and ((not ind) or (ind == NFL_SUBSEASON_FLAG_PRESEASON or ind == NFL_SUBSEASON_FLAG_REGULAR_SEASON)):
        foundWeek = False

        # Test to see if next-level folder is a week indicator (preseason and regular season)
        folder = folders[0]
        for expr in week_expressions:
            if foundWeek == True:
                break
            for pattern in [r"^%s$" % expr, r"\b%s\b" % expr]:
                m = re.match(pattern, folder, re.IGNORECASE)
                if m:
                    foundWeek = True

                    meta.setdefault(METADATA_WEEK_KEY, folder)
                    meta.setdefault(METADATA_WEEK_NUMBER_KEY, int(m.group("week_number")))
                    del(folders[0])
                    break


def InferPostseasonConferenceFromFolders(filename, folders, meta):
    league = meta.get(METADATA_LEAGUE_KEY)
    season = meta.get(METADATA_SEASON_KEY)
    ind = meta.get(METADATA_SUBSEASON_INDICATOR_KEY)
    if folders and league and season and ind == NFL_SUBSEASON_FLAG_POSTSEASON:
        foundConference = False

        # Test to see if next-level folder is a conference (postseason)
        folder = folders[0]
        for (conf, exprs) in nfl_conference_expressions:
            if foundConference == True:
                break
            for expr in exprs:
                if foundConference == True:
                    break
                for pattern in [r"^%s$" % expr, r"\b%s\b" % expr]:
                    m = re.match(pattern, folder, re.IGNORECASE)
                    if m:
                        foundConference = True

                        meta.setdefault(METADATA_CONFERENCE_KEY, conf)
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

        # Test to see if next-level folder is a subseason indicator
        folder = folders[0]
        for (exprs, conf, round) in nfl_playoff_round_expressions:
            if foundRound == True:
                break
            for expr in exprs:
                if foundRound == True:
                    break
                for pattern in [r"^%s$" % expr, r"\b%s\b" % expr]:
                    m = re.match(pattern, folder, re.IGNORECASE)
                    if m:
                        foundRound = True

                        meta.setdefault(METADATA_SUBSEASON_INDICATOR_KEY, NFL_SUBSEASON_FLAG_POSTSEASON)
                        meta.setdefault(METADATA_SUBSEASON_KEY, folder)
                        meta.setdefault(METADATA_CONFERENCE_KEY, conf)
                        meta.setdefault(METADATA_PLAYOFF_ROUND_KEY, round)
                        meta.setdefault(METADATA_EVENT_NAME_KEY, folder)
                        del(folders[0])
                        break

def InferSingleEventFromFileName(filename, food, meta):
    if food:
        # Test to see if filename contains a single event, like Super Bowl, or Pro Bowl
        foundEvent = False
        for (exprs, ind) in nfl_event_expressions:
            if foundEvent == True:
                break
            for expr in exprs:
                for pattern in [r"^%s$" % expr, r"\b%s\b" % expr]:
                    (bites, chewed, ms) = Eat(food, pattern)
                    if bites:
                        foundEvent = True
                        meta.setdefault(METADATA_SPORT_KEY, SPORT_FOOTBALL)
                        meta.setdefault(METADATA_LEAGUE_KEY, LEAGUE_NFL)
                        meta.setdefault(METADATA_EVENT_INDICATOR_KEY, ind)
                        meta.setdefault(METADATA_EVENT_NAME_KEY, bites[0])
                        if "game_number" in ms[0].groupdict().keys():
                            meta.setdefault(METADATA_GAME_NUMBER_KEY, ms[0].group("game_number"))
                        return chewed
