
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

NBA_PLAYOFF_ROUND_QUARTERFINALS = 1
NBA_PLAYOFF_ROUND_SEMIFINALS = 2
NBA_PLAYOFF_ROUND_FINALS = 3

# (expressions, conference, round)
# Ordered by more specific to less
nba_playoff_round_expressions = [
	(__expressions_from_literal("%s Quarterfinals" % NBA_CONFERENCE_NAME_EAST), NBA_CONFERENCE_EAST, NBA_PLAYOFF_ROUND_QUARTERFINALS),
	(__expressions_from_literal("%s Quarterfinals" % NBA_CONFERENCE_NAME_WEST), NBA_CONFERENCE_WEST, NBA_PLAYOFF_ROUND_QUARTERFINALS),
	(__expressions_from_literal("%s Quarterfinals" % NBA_CONFERENCE_EAST), NBA_CONFERENCE_EAST, NBA_PLAYOFF_ROUND_QUARTERFINALS),
	(__expressions_from_literal("%s Quarterfinals" % NBA_CONFERENCE_WEST), NBA_CONFERENCE_WEST, NBA_PLAYOFF_ROUND_QUARTERFINALS),
	(__expressions_from_literal("Quarterfinals"), None, NBA_PLAYOFF_ROUND_QUARTERFINALS),

	(__expressions_from_literal("%s Semifinals" % NBA_CONFERENCE_NAME_EAST), NBA_CONFERENCE_EAST, NBA_PLAYOFF_ROUND_SEMIFINALS),
	(__expressions_from_literal("%s Semifinals" % NBA_CONFERENCE_NAME_WEST), NBA_CONFERENCE_WEST, NBA_PLAYOFF_ROUND_SEMIFINALS),
	(__expressions_from_literal("%s Semifinals" % NBA_CONFERENCE_EAST), NBA_CONFERENCE_EAST, NBA_PLAYOFF_ROUND_SEMIFINALS),
	(__expressions_from_literal("%s Semifinals" % NBA_CONFERENCE_WEST), NBA_CONFERENCE_WEST, NBA_PLAYOFF_ROUND_SEMIFINALS),
	(__expressions_from_literal("%s Finals" % NBA_CONFERENCE_NAME_EAST), NBA_CONFERENCE_EAST, NBA_PLAYOFF_ROUND_SEMIFINALS),
	(__expressions_from_literal("%s Finals" % NBA_CONFERENCE_NAME_WEST), NBA_CONFERENCE_WEST, NBA_PLAYOFF_ROUND_SEMIFINALS),
	(__expressions_from_literal("Semifinals"), None, NBA_PLAYOFF_ROUND_SEMIFINALS),

	(__expressions_from_literal("Championship"), None, NBA_PLAYOFF_ROUND_FINALS),
	(__expressions_from_literal("Finals"), None, NBA_PLAYOFF_ROUND_FINALS)
	]

NBA_EVENT_FLAG_ALL_STAR_GAME = 1
NBA_EVENT_FLAG_3_POINT_SHOOTOUT = 2
NBA_EVENT_FLAG_SLAM_DUNK_COMPETITION = 3
NBA_EVENT_FLAG_SKILLS_CHALLENGE = 4

# (expressions, event flag)
# Ordered by more specific to less
nba_event_expressions = [
	(__expressions_from_literal("All Star Game"), NBA_EVENT_FLAG_ALL_STAR_GAME),
	([r"All%sStar%sGame" % (EXPRESSION_SEPARATOR, EXPRESSION_SEPARATOR)], NBA_EVENT_FLAG_ALL_STAR_GAME),
	(__expressions_from_literal("All-Star Game"), NBA_EVENT_FLAG_ALL_STAR_GAME),
	(__expressions_from_literal("3 Point Shootout"), NBA_EVENT_FLAG_3_POINT_SHOOTOUT),
	(__expressions_from_literal("3 Point Competition"), NBA_EVENT_FLAG_3_POINT_SHOOTOUT),
	([r"3%sPoint%sShootout" % (EXPRESSION_SEPARATOR, EXPRESSION_SEPARATOR)], NBA_EVENT_FLAG_3_POINT_SHOOTOUT),
	([r"3%sPoint%sCompetition" % (EXPRESSION_SEPARATOR, EXPRESSION_SEPARATOR)], NBA_EVENT_FLAG_3_POINT_SHOOTOUT),
	(__expressions_from_literal("Slam Dunk Competition"), NBA_EVENT_FLAG_SLAM_DUNK_COMPETITION),
	(__expressions_from_literal("Slam Dunk Contest"), NBA_EVENT_FLAG_SLAM_DUNK_COMPETITION),
	(__expressions_from_literal("AT&T Slam Dunk"), NBA_EVENT_FLAG_SLAM_DUNK_COMPETITION),
	(__expressions_from_literal("Skills Challenge"), NBA_EVENT_FLAG_SLAM_DUNK_COMPETITION),
	(__expressions_from_literal("Skill Challenge"), NBA_EVENT_FLAG_SKILLS_CHALLENGE)
	]
# TODO: more variations on all-star weekend event names






def InferSubseasonFromFolders(fileName, folders, meta):
	if meta.get(METADATA_SUBSEASON_INDICATOR_KEY): return

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

		if not foundSubseason:
			InferPlayoffRoundFromFolders(fileName, folders, meta)

def InferPostseasonConferenceFromFolders(fileName, folders, meta):
	if meta.get(METADATA_CONFERENCE_KEY): return

	league = meta.get(METADATA_LEAGUE_KEY)
	season = meta.get(METADATA_SEASON_KEY)
	ind = meta.get(METADATA_SUBSEASON_INDICATOR_KEY)
	if folders and league and season and ind == NBA_SUBSEASON_FLAG_POSTSEASON:
		foundLeague = False

		# Test to see if next-level folder is a league (postseason)
		folder = folders[0]
		for (conference, exprs) in nba_conference_expressions:
			if foundLeague == True:
				break
			for expr in exprs:
				if foundLeague == True:
					break
				for pattern in [r"^%s$" % expr, r"\b%s\b" % expr]:
					m = re.match(pattern, folder, re.IGNORECASE)
					if m:
						foundLeague = True

						meta.setdefault(METADATA_CONFERENCE_KEY, conference)
						del(folders[0])
						break




def InferPlayoffRoundFromFolders(fileName, folders, meta):
	if meta.get(METADATA_PLAYOFF_ROUND_KEY): return
	
	league = meta.get(METADATA_LEAGUE_KEY)
	season = meta.get(METADATA_SEASON_KEY)
	if folders and league and season:
		foundRound = False

		# Test to see if next-level folder is a subseason indicator
		folder = folders[0]
		for (exprs, conference, round) in nba_playoff_round_expressions:
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
						meta.setdefault(METADATA_SUBSEASON_INDICATOR_KEY, NBA_SUBSEASON_FLAG_POSTSEASON)
						if conference: meta.setdefault(METADATA_CONFERENCE_KEY, conference)
						meta.setdefault(METADATA_PLAYOFF_ROUND_KEY, round)

						eventName = ""
						if not conference: conference = meta.get(METADATA_CONFERENCE_KEY)
						if conference:
							eventName += nba_conferences[conference]
						elif round == 1:
							if eventName: eventName += " "
							eventName += "Quarterfinals"
						elif round == 2:
							if eventName: eventName += " "
							eventName += "Semifinals"
						elif round == 3:
							eventName = "Finals"
						meta.setdefault(METADATA_EVENT_NAME_KEY, eventName)

						del(folders[0])
						break


def InferSubseasonFromFileName(fileName, food, meta):
	if not food: return food
	if meta.get(METADATA_SUBSEASON_INDICATOR_KEY): return food

	league = meta.get(METADATA_LEAGUE_KEY)
	season = meta.get(METADATA_SEASON_KEY)
	if league and season:
		foundSubseason = False

		# Test to see if fileName contains a subseason indicator
		for (ind, exprs) in nba_subseason_indicator_expressions:
			if foundSubseason == True:
				break
			for expr in exprs:
				if foundSubseason == True:
					break
				for pattern in [r"^%s$" % expr, r"\b%s\b" % expr]:
					(bites, chewed, ms) = Eat(food, pattern)
					if bites:
						foundSubseason = True

						meta.setdefault(METADATA_SUBSEASON_INDICATOR_KEY, ind)
						meta.setdefault(METADATA_SUBSEASON_KEY, bites[0][1])
						food = chewed
						break

		if not foundSubseason:
			food = InferPlayoffRoundFromFileName(fileName, food, meta)

	return food

def InferPlayoffRoundFromFileName(fileName, food, meta):
	if not food: return food
	if meta.get(METADATA_PLAYOFF_ROUND_KEY): return food
	
	league = meta.get(METADATA_LEAGUE_KEY)
	season = meta.get(METADATA_SEASON_KEY)
	if league and season:
		foundRound = False

		# Test to see if fileName contains a playoff round indicator
		for (exprs, conference, round) in nba_playoff_round_expressions:
			if foundRound == True:
				break
			for expr in exprs:
				if foundRound == True:
					break
				for pattern in [r"^%s$" % expr, r"\b%s\b" % expr]:
					(bites, chewed, ms) = Eat(food, pattern)
					if bites:
						foundRound = True

						meta.setdefault(METADATA_SUBSEASON_INDICATOR_KEY, NBA_SUBSEASON_FLAG_POSTSEASON)
						meta.setdefault(METADATA_SUBSEASON_KEY, bites[0][1])
						if conference: meta.setdefault(METADATA_CONFERENCE_KEY, conference)
						meta.setdefault(METADATA_PLAYOFF_ROUND_KEY, round)

						eventName = ""
						if not conference: conference = meta.get(METADATA_CONFERENCE_KEY)
						if conference:
							eventName += nba_conferences[conference]
						elif round == 1:
							if eventName: eventName += " "
							eventName += "Quarterfinals"
						elif round == 2:
							if eventName: eventName += " "
							eventName += "Semifinals"
						elif round == 3:
							eventName = "Finals"
						meta.setdefault(METADATA_EVENT_NAME_KEY, eventName)

						return chewed

	return food

def InferPostseasonConferenceFromFileName(fileName, food, meta):
	if not food: return food
	if meta.get(METADATA_CONFERENCE_KEY): return food

	league = meta.get(METADATA_LEAGUE_KEY)
	season = meta.get(METADATA_SEASON_KEY)
	ind = meta.get(METADATA_SUBSEASON_INDICATOR_KEY)
	if league and season and ind == NBA_SUBSEASON_FLAG_POSTSEASON:
		foundLeague = False

		# Test to see if fileName contains a league (postseason)
		for (conference, exprs) in nba_conference_expressions:
			if foundLeague == True:
				break
			for expr in exprs:
				if foundLeague == True:
					break
				for pattern in [r"^%s$" % expr, r"\b%s\b" % expr]:
					(bites, chewed, ms) = Eat(food, pattern)
					if bites:
						foundLeague = True

						meta.setdefault(METADATA_CONFERENCE_KEY, conference)
						return chewed
	return food


def InferSingleEventFromFileName(fileName, food, meta):
	if not food: return food
	if meta.get(METADATA_EVENT_INDICATOR_KEY): return food

	# Test to see if fileName contains a single event, like All-Star Game or 3-Point Shootout
	foundEvent = False
	for (exprs, ind) in nba_event_expressions:
		if foundEvent == True:
			break
		for expr in exprs:
			for pattern in [r"^%s$" % expr, r"\b%s\b" % expr]:
				(bites, chewed, ms) = Eat(food, pattern)
				if bites:
					foundEvent = True
					meta.setdefault(METADATA_SPORT_KEY, SPORT_BASKETBALL)
					meta.setdefault(METADATA_LEAGUE_KEY, LEAGUE_NBA)
					meta.setdefault(METADATA_EVENT_INDICATOR_KEY, ind)

					eventName = ""
					if ind == NBA_EVENT_FLAG_ALL_STAR_GAME: eventName = "All-Star Game"
					elif ind == NBA_EVENT_FLAG_3_POINT_SHOOTOUT: eventName = "3-Point Shootout"
					elif ind == NBA_EVENT_FLAG_SLAM_DUNK_COMPETITION: eventName = "Slam Dunk Competition"
					elif ind == NBA_EVENT_FLAG_SKILLS_CHALLENGE: eventName = "Skills Challenge"
					else: eventName = bites[0][1]

					meta.setdefault(METADATA_EVENT_NAME_KEY, eventName)
					return chewed

	return food