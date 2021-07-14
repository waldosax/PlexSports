# Python framework
import re

# Local package
from Constants import *
from Matching import __expressions_from_literal
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

NFL_SEASON_FLAG_PRESEASON = -1
NFL_SEASON_FLAG_REGULAR_SEASON = 0
NFL_SEASON_FLAG_POSTSEASON = 1

NFL_SUBSEASON_PRESEASON = "Preseason"
NFL_SUBSEASON_POSTSEASON = "Postseason"
NFL_SUBSEASON_PLAYOFFS = "Playoffs"
NFL_SUBSEASON_REGULAR_SEASON = "Regular Season"


nfl_subseason_indicator_expressions = [
    (NFL_SEASON_FLAG_PRESEASON, __expressions_from_literal(NFL_SUBSEASON_PRESEASON)),
    (NFL_SEASON_FLAG_POSTSEASON, __expressions_from_literal(NFL_SUBSEASON_POSTSEASON) + __expressions_from_literal(NFL_SUBSEASON_PLAYOFFS)),
    (NFL_SEASON_FLAG_REGULAR_SEASON, __expressions_from_literal(NFL_SUBSEASON_REGULAR_SEASON))
    ]

# (expressions, conference, round)
# Ordered by more specific to less
nfl_playoff_round_expressions = [
    (__expressions_from_literal("%s Wildcard Round" % NFL_CONFERENCE_AFC) + __expressions_from_literal("%s Wildcard" % NFL_CONFERENCE_AFC), NFL_CONFERENCE_AFC, 1),
    (__expressions_from_literal("%s Wildcard Round" % NFL_CONFERENCE_NFC) + __expressions_from_literal("%s Wildcard" % NFL_CONFERENCE_NFC), NFL_CONFERENCE_NFC, 1),
    (__expressions_from_literal("Wildcard Round") + __expressions_from_literal("Wildcard"), None, 1),
    (__expressions_from_literal("%s Divisional Round" % NFL_CONFERENCE_AFC) + __expressions_from_literal("%s Division Playoffs" % NFL_CONFERENCE_AFC), NFL_CONFERENCE_AFC, 2),
    (__expressions_from_literal("%s Divisional Round" % NFL_CONFERENCE_NFC) + __expressions_from_literal("%s Division Playoffs" % NFL_CONFERENCE_NFC), NFL_CONFERENCE_NFC, 2),
    (__expressions_from_literal("Divisional Round") + __expressions_from_literal("Division Playoffs"), None, 2),
    (__expressions_from_literal("%s Championship Round" % NFL_CONFERENCE_AFC) + __expressions_from_literal("%s Championship" % NFL_CONFERENCE_AFC), NFL_CONFERENCE_AFC, 3),
    (__expressions_from_literal("%s Championship Round" % NFL_CONFERENCE_NFC) + __expressions_from_literal("%s Championship" % NFL_CONFERENCE_NFC), NFL_CONFERENCE_NFC, 3),
    (__expressions_from_literal("Conference Championship Round") + __expressions_from_literal("Conference Championship"), None, 3),
    (__expressions_from_literal("Championship Round"), None, 3),
    ]

def Touchdown():
    print("Six points!")
    for roman in [
        "I", "II", "III", "IV", "V", "VI", "VII", "viii", "IX", "X",
        "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX",
        "MCMLXXXIV"
        ]:
        print("\t%s: %s" % (roman, RomanNumerals.Parse(roman)))






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

def InferWeekFromFolders(filename, folders, meta):
    league = meta.get(METADATA_LEAGUE_KEY)
    season = meta.get(METADATA_SEASON_KEY)
    ind = meta.get(METADATA_SUBSEASON_INDICATOR_KEY)
    if folders and league and season and ((not ind) or (ind == NFL_SEASON_FLAG_PRESEASON or ind == NFL_SEASON_FLAG_REGULAR_SEASON)):
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
    if folders and league and season and ind == NFL_SEASON_FLAG_POSTSEASON:
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

                        meta.setdefault(METADATA_SUBSEASON_INDICATOR_KEY, 1)
                        meta.setdefault(METADATA_CONFERENCE_KEY, conf)
                        meta.setdefault(METADATA_PLAYOFF_ROUND_KEY, round)
                        meta.setdefault(METADATA_EVENT_NAME_KEY, folder)
                        del(folders[0])
                        break
