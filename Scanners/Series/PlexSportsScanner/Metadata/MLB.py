# Python framework
import re

# Local package
from Constants import *
from Matching import __expressions_from_literal, Eat


mlb_league_expressions = [
	(MLB_LEAGUE_AL, [MLB_LEAGUE_AL]+__expressions_from_literal(MLB_LEAGUE_NAME_AL)),
	(MLB_LEAGUE_NL, [MLB_LEAGUE_NL]+__expressions_from_literal(MLB_LEAGUE_NAME_NL))
	]


mlb_subseason_indicator_expressions = [
	(MLB_SUBSEASON_FLAG_PRESEASON, __expressions_from_literal(MLB_SUBSEASON_PRESEASON) + __expressions_from_literal(MLB_SUBSEASON_SPRING_TRAINING)),
	(MLB_SUBSEASON_FLAG_POSTSEASON, __expressions_from_literal(MLB_SUBSEASON_POSTSEASON) + __expressions_from_literal(MLB_SUBSEASON_PLAYOFFS)),
	(MLB_SUBSEASON_FLAG_REGULAR_SEASON, __expressions_from_literal(MLB_SUBSEASON_REGULAR_SEASON))
	]

mlb_spring_trainging_leagues = [MLB_SPRING_TRAINING_CACTUS_LEAGUE, MLB_SPRING_TRAINING_GRAPEFRUIT_LEAGUE]
mlb_spring_trainging_league_expressions = [
	(MLB_SPRING_TRAINING_CACTUS_LEAGUE, __expressions_from_literal(MLB_SPRING_TRAINING_CACTUS_LEAGUE)),
	(MLB_SPRING_TRAINING_GRAPEFRUIT_LEAGUE, __expressions_from_literal(MLB_SPRING_TRAINING_GRAPEFRUIT_LEAGUE))
	]

# (expressions, conference, round)
# Ordered by more specific to less
mlb_playoff_round_expressions = [
	(__expressions_from_literal("%s Wild card Round" % MLB_LEAGUE_NAME_AL), MLB_LEAGUE_AL, MLB_PLAYOFF_ROUND_WILDCARD),
	(__expressions_from_literal("%s Wild card Round" % MLB_LEAGUE_NAME_NL), MLB_LEAGUE_NL, MLB_PLAYOFF_ROUND_WILDCARD),
	(__expressions_from_literal("%s Wild card Series" % MLB_LEAGUE_NAME_AL) + __expressions_from_literal("%s Wild card" % MLB_LEAGUE_NAME_AL), MLB_LEAGUE_AL, MLB_PLAYOFF_ROUND_WILDCARD),
	(__expressions_from_literal("%s Wild card Series" % MLB_LEAGUE_NAME_NL) + __expressions_from_literal("%s Wild card" % MLB_LEAGUE_NAME_NL), MLB_LEAGUE_NL, MLB_PLAYOFF_ROUND_WILDCARD),
	(__expressions_from_literal("%s Wild card Round" % MLB_LEAGUE_AL), MLB_LEAGUE_AL, MLB_PLAYOFF_ROUND_WILDCARD),
	(__expressions_from_literal("%s Wild card Round" % MLB_LEAGUE_NL), MLB_LEAGUE_NL, MLB_PLAYOFF_ROUND_WILDCARD),
	(__expressions_from_literal("%s Wild card Series" % MLB_LEAGUE_AL) + __expressions_from_literal("%s Wild card" % MLB_LEAGUE_AL), MLB_LEAGUE_AL, MLB_PLAYOFF_ROUND_WILDCARD),
	(__expressions_from_literal("%s Wild card Series" % MLB_LEAGUE_NL) + __expressions_from_literal("%s Wild card" % MLB_LEAGUE_NL), MLB_LEAGUE_NL, MLB_PLAYOFF_ROUND_WILDCARD),

	(__expressions_from_literal("%s Wildcard Round" % MLB_LEAGUE_NAME_AL), MLB_LEAGUE_AL, MLB_PLAYOFF_ROUND_WILDCARD),
	(__expressions_from_literal("%s Wildcard Round" % MLB_LEAGUE_NAME_NL), MLB_LEAGUE_NL, MLB_PLAYOFF_ROUND_WILDCARD),
	(__expressions_from_literal("%s Wildcard Series" % MLB_LEAGUE_NAME_AL) + __expressions_from_literal("%s Wildcard" % MLB_LEAGUE_NAME_AL), MLB_LEAGUE_AL, MLB_PLAYOFF_ROUND_WILDCARD),
	(__expressions_from_literal("%s Wildcard Series" % MLB_LEAGUE_NAME_NL) + __expressions_from_literal("%s Wildcard" % MLB_LEAGUE_NAME_NL), MLB_LEAGUE_NL, MLB_PLAYOFF_ROUND_WILDCARD),
	(__expressions_from_literal("%s Wildcard Round" % MLB_LEAGUE_AL), MLB_LEAGUE_AL, MLB_PLAYOFF_ROUND_WILDCARD),
	(__expressions_from_literal("%s Wildcard Round" % MLB_LEAGUE_NL), MLB_LEAGUE_NL, MLB_PLAYOFF_ROUND_WILDCARD),
	(__expressions_from_literal("%s Wildcard Series" % MLB_LEAGUE_AL) + __expressions_from_literal("%s Wildcard" % MLB_LEAGUE_AL), MLB_LEAGUE_AL, MLB_PLAYOFF_ROUND_WILDCARD),
	(__expressions_from_literal("%s Wildcard Series" % MLB_LEAGUE_NL) + __expressions_from_literal("%s Wildcard" % MLB_LEAGUE_NL), MLB_LEAGUE_NL, MLB_PLAYOFF_ROUND_WILDCARD),

	(__expressions_from_literal("Wild card Round") +__expressions_from_literal("Wild card Series") + __expressions_from_literal("Wild card"), None, MLB_PLAYOFF_ROUND_WILDCARD),
	(__expressions_from_literal("Wildcard Round") +__expressions_from_literal("Wildcard Series") + __expressions_from_literal("Wildcard"), None, MLB_PLAYOFF_ROUND_WILDCARD),


	(__expressions_from_literal("%s Divisional Round" % MLB_LEAGUE_NAME_AL) + __expressions_from_literal("%s Division Round" % MLB_LEAGUE_NAME_AL), MLB_LEAGUE_AL, MLB_PLAYOFF_ROUND_DIVISION),
	(__expressions_from_literal("%s Divisional Round" % MLB_LEAGUE_NAME_NL) + __expressions_from_literal("%s Division Round" % MLB_LEAGUE_NAME_NL), MLB_LEAGUE_NL, MLB_PLAYOFF_ROUND_DIVISION),
	(__expressions_from_literal("%s Divisional Series" % MLB_LEAGUE_NAME_AL) + __expressions_from_literal("%s Division Series" % MLB_LEAGUE_NAME_AL), MLB_LEAGUE_AL, MLB_PLAYOFF_ROUND_DIVISION),
	(__expressions_from_literal("%s Divisional Series" % MLB_LEAGUE_NAME_NL) + __expressions_from_literal("%s Division Series" % MLB_LEAGUE_NAME_NL), MLB_LEAGUE_NL, MLB_PLAYOFF_ROUND_DIVISION),
	(__expressions_from_literal("%s Division Playoffs" % MLB_LEAGUE_NAME_AL), MLB_LEAGUE_AL, MLB_PLAYOFF_ROUND_DIVISION),
	(__expressions_from_literal("%s Division Playoffs" % MLB_LEAGUE_NAME_NL), MLB_LEAGUE_NL, MLB_PLAYOFF_ROUND_DIVISION),
	
	(__expressions_from_literal("%s Divisional Round" % MLB_LEAGUE_AL) + __expressions_from_literal("%s Division Round" % MLB_LEAGUE_AL) + __expressions_from_literal("%s Division Playoffs" % MLB_LEAGUE_AL), MLB_LEAGUE_AL, MLB_PLAYOFF_ROUND_DIVISION),
	(__expressions_from_literal("%s Divisional Round" % MLB_LEAGUE_NL) + __expressions_from_literal("%s Division Round" % MLB_LEAGUE_NL) + __expressions_from_literal("%s Division Playoffs" % MLB_LEAGUE_NL), MLB_LEAGUE_NL, MLB_PLAYOFF_ROUND_DIVISION),
	(__expressions_from_literal("%s Divisional Series" % MLB_LEAGUE_AL) + __expressions_from_literal("%s Division Series" % MLB_LEAGUE_AL), MLB_LEAGUE_AL, MLB_PLAYOFF_ROUND_DIVISION),
	(__expressions_from_literal("%s Divisional Series" % MLB_LEAGUE_NL) + __expressions_from_literal("%s Division Series" % MLB_LEAGUE_NL), MLB_LEAGUE_NL, MLB_PLAYOFF_ROUND_DIVISION),
	(__expressions_from_literal("%s Division Playoffs" % MLB_LEAGUE_AL), MLB_LEAGUE_AL, MLB_PLAYOFF_ROUND_DIVISION),
	(__expressions_from_literal("%s Division Playoffs" % MLB_LEAGUE_NL), MLB_LEAGUE_NL, MLB_PLAYOFF_ROUND_DIVISION),

	(__expressions_from_literal("%sDS" % MLB_LEAGUE_AL), MLB_LEAGUE_AL, MLB_PLAYOFF_ROUND_DIVISION),
	(__expressions_from_literal("%sDS" % MLB_LEAGUE_NL), MLB_LEAGUE_NL, MLB_PLAYOFF_ROUND_DIVISION),

	(__expressions_from_literal("Divisional Round"), None, MLB_PLAYOFF_ROUND_DIVISION),
	(__expressions_from_literal("Division Round"), None, MLB_PLAYOFF_ROUND_DIVISION),
	(__expressions_from_literal("Divisional Series"), None, MLB_PLAYOFF_ROUND_DIVISION),
	(__expressions_from_literal("Division Series"), None, MLB_PLAYOFF_ROUND_DIVISION),


	(__expressions_from_literal("%s Championship Round" % MLB_LEAGUE_NAME_AL), MLB_LEAGUE_AL, MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
	(__expressions_from_literal("%s Championship Round" % MLB_LEAGUE_NAME_NL), MLB_LEAGUE_NL, MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
	(__expressions_from_literal("%s Championship Series" % MLB_LEAGUE_NAME_AL), MLB_LEAGUE_AL, MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
	(__expressions_from_literal("%s Championship Series" % MLB_LEAGUE_NAME_NL), MLB_LEAGUE_NL, MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
	(__expressions_from_literal("%s Championship Playoffs" % MLB_LEAGUE_NAME_AL), MLB_LEAGUE_AL, MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
	(__expressions_from_literal("%s Championship Playoffs" % MLB_LEAGUE_NAME_NL), MLB_LEAGUE_NL, MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
	
	(__expressions_from_literal("%s Championship Round" % MLB_LEAGUE_AL), MLB_LEAGUE_AL, MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
	(__expressions_from_literal("%s Championship Round" % MLB_LEAGUE_NL), MLB_LEAGUE_NL, MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
	(__expressions_from_literal("%s Championship Series" % MLB_LEAGUE_AL), MLB_LEAGUE_AL, MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
	(__expressions_from_literal("%s Championship Series" % MLB_LEAGUE_NL), MLB_LEAGUE_NL, MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
	(__expressions_from_literal("%s Championship Playoffs" % MLB_LEAGUE_AL), MLB_LEAGUE_AL, MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
	(__expressions_from_literal("%s Championship Playoffs" % MLB_LEAGUE_NL), MLB_LEAGUE_NL, MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
	
	(__expressions_from_literal("%sCS" % MLB_LEAGUE_AL), MLB_LEAGUE_AL, MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
	(__expressions_from_literal("%sCS" % MLB_LEAGUE_NL), MLB_LEAGUE_NL, MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
	
	(__expressions_from_literal("Championship Round"), None, MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
	(__expressions_from_literal("Championship Series"), None, MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
	(__expressions_from_literal("Championship Playoffs"), None, MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
	

	(__expressions_from_literal("World Series"), None, MLB_PLAYOFF_ROUND_WORLD_SERIES)
	]

# (expressions, event flag)
# Ordered by more specific to less
mlb_event_expressions = [
	(__expressions_from_literal("Hall of Fame Game"), MLB_EVENT_FLAG_HALL_OF_FAME),
	(__expressions_from_literal("Hall of Fame"), MLB_EVENT_FLAG_HALL_OF_FAME),
	(__expressions_from_literal("HOF Game"), MLB_EVENT_FLAG_HALL_OF_FAME),
	(["HOF"], MLB_EVENT_FLAG_HALL_OF_FAME),
	(__expressions_from_literal("Home Run Derby"), MLB_EVENT_FLAG_HOME_RUN_DERBY),
	([r"All%sStar%sGame" % (EXPRESSION_SEPARATOR, EXPRESSION_SEPARATOR)], MLB_EVENT_FLAG_ALL_STAR_GAME),
	(__expressions_from_literal("All Star Game"), MLB_EVENT_FLAG_ALL_STAR_GAME),
	(__expressions_from_literal("All-Star Game"), MLB_EVENT_FLAG_ALL_STAR_GAME)
	]








def InferSubseasonFromFolders(fileName, folders, meta):
	if meta.get(METADATA_SUBSEASON_INDICATOR_KEY): return

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


		if not foundSubseason:
			InferPlayoffRoundFromFolders(fileName, folders, meta)

def InferPostseasonLeagueFromFolders(fileName, folders, meta):
	if meta.get(METADATA_CONFERENCE_KEY): return

	league = meta.get(METADATA_LEAGUE_KEY)
	season = meta.get(METADATA_SEASON_KEY)
	ind = meta.get(METADATA_SUBSEASON_INDICATOR_KEY)
	if folders and league and season and ind == MLB_SUBSEASON_FLAG_POSTSEASON:
		foundLeague = False

		# Test to see if next-level folder is a league (postseason)
		folder = folders[0]
		for (conference, exprs) in mlb_league_expressions:
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



def InferSpringTrainingLeagueFromFolders(fileName, folders, meta):
	if meta.get(METADATA_CONFERENCE_KEY): return

	league = meta.get(METADATA_LEAGUE_KEY)
	season = meta.get(METADATA_SEASON_KEY)
	ind = meta.get(METADATA_SUBSEASON_INDICATOR_KEY)
	if folders and league and season and ind == MLB_SUBSEASON_FLAG_PRESEASON:
		foundLeague = False

		# Test to see if next-level folder is a league (spring training)
		folder = folders[0]
		for (conference, exprs) in mlb_spring_trainging_league_expressions:
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

		# Test to see if next-level folder is a playoff round indicator
		folder = folders[0]
		for (exprs, conference, round) in mlb_playoff_round_expressions:
			if foundRound == True:
				break
			for expr in exprs:
				if foundRound == True:
					break
				for pattern in [r"^%s$" % expr, r"\b%s\b" % expr]:
					m = re.match(pattern, folder, re.IGNORECASE)
					if m:
						foundRound = True

						meta.setdefault(METADATA_SUBSEASON_INDICATOR_KEY, MLB_SUBSEASON_FLAG_POSTSEASON)
						meta.setdefault(METADATA_SUBSEASON_KEY, folder)
						if conference: meta.setdefault(METADATA_CONFERENCE_KEY, conference)
						meta.setdefault(METADATA_PLAYOFF_ROUND_KEY, round)

						eventName = ""
						if not conference: conference = meta.get(METADATA_CONFERENCE_KEY)
						if conference:
							eventName += conference
						if round == 1:
							if eventName: eventName += " "
							eventName += "Wildcard" + (" Series" if not conference else "")
						elif round == 2:
							eventName += "DS" if conference else "Division Series"
						elif round == 3:
							eventName += "CS" if conference else "Championship Series"
						elif round == 4:
							eventName = "World Series"
						meta.setdefault(METADATA_EVENT_NAME_KEY, eventName)

						del(folders[0])
						break

def InferSubseasonFromFileName(fileName, food, meta):
	if not food: return food

	league = meta.get(METADATA_LEAGUE_KEY)
	season = meta.get(METADATA_SEASON_KEY)
	if league and season:
		foundSubseason = False

		# Test to see if fileName contains a subseason indicator
		for (ind, exprs) in mlb_subseason_indicator_expressions:
			if foundSubseason == True:
				break
			for expr in exprs:
				if foundSubseason == True:
					break
				for pattern in [r"^%s$" % expr, r"\b%s\b" % expr]:
					(bites, chewed, ms) = Eat(food, pattern)
					if bites:

						# Check to see if existing values match. If they don't, eat, but leave values unchanged
						if meta.get(METADATA_SUBSEASON_INDICATOR_KEY) != None and meta[METADATA_SUBSEASON_INDICATOR_KEY] != ind:
							return chewed

						foundSubseason = True

						meta.setdefault(METADATA_SUBSEASON_INDICATOR_KEY, ind)
						meta.setdefault(METADATA_SUBSEASON_KEY, bites[0][1])

						food = chewed
						break

		if not foundSubseason:
			food = InferPlayoffRoundFromFileName(fileName, food, meta)

	return food

def InferSpringTrainingLeagueFromFileName(fileName, food, meta):
	if not food: return food
	if meta.get(METADATA_CONFERENCE_KEY): return food

	league = meta.get(METADATA_LEAGUE_KEY)
	season = meta.get(METADATA_SEASON_KEY)
	ind = meta.get(METADATA_SUBSEASON_INDICATOR_KEY)
	if league and season and ind == MLB_SUBSEASON_FLAG_PRESEASON:
		foundLeague = False

		# Test to see if fileName contains a league (spring training)
		for (conference, exprs) in mlb_spring_trainging_league_expressions:
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

def InferPlayoffRoundFromFileName(fileName, food, meta):
	if not food: return food
	
	league = meta.get(METADATA_LEAGUE_KEY)
	season = meta.get(METADATA_SEASON_KEY)
	if league and season:
		foundRound = False

		# Test to see if fileName contains a playoff round indicator
		for (exprs, conference, round) in mlb_playoff_round_expressions:
			if foundRound == True:
				break
			for expr in exprs:
				if foundRound == True:
					break
				for pattern in [r"^%s$" % expr, r"\b%s\b" % expr]:
					(bites, chewed, ms) = Eat(food, pattern)
					if bites:

						# Check to see if existing values match. If they don't, eat, but leave values unchanged
						if meta.get(METADATA_PLAYOFF_ROUND_KEY) != None and meta[METADATA_PLAYOFF_ROUND_KEY] != round:
							return chewed


						foundRound = True
						meta.setdefault(METADATA_SUBSEASON_INDICATOR_KEY, MLB_SUBSEASON_FLAG_POSTSEASON)
						meta.setdefault(METADATA_SUBSEASON_KEY, bites[0][1])
						if conference: meta.setdefault(METADATA_CONFERENCE_KEY, conference)
						meta.setdefault(METADATA_PLAYOFF_ROUND_KEY, round)

						eventName = ""
						if not conference: conference = meta.get(METADATA_CONFERENCE_KEY)
						if conference:
							eventName += conference
						if round == 1:
							if eventName: eventName += " "
							eventName += "Wildcard" + (" Series" if not conference else "")
						elif round == 2:
							eventName += "DS" if conference else "Division Series"
						elif round == 3:
							eventName += "CS" if conference else "Championship Series"
						elif round == 4:
							eventName = "World Series"
						meta.setdefault(METADATA_EVENT_NAME_KEY, eventName)

						return chewed

	return food

def InferPostseasonLeagueFromFileName(fileName, food, meta):
	if not food: return food
	if meta.get(METADATA_CONFERENCE_KEY): return food

	league = meta.get(METADATA_LEAGUE_KEY)
	season = meta.get(METADATA_SEASON_KEY)
	ind = meta.get(METADATA_SUBSEASON_INDICATOR_KEY)
	if league and season and ind == MLB_SUBSEASON_FLAG_POSTSEASON:
		foundLeague = False

		# Test to see if fileName contains a league (postseason)
		for (conference, exprs) in mlb_league_expressions:
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

	# Test to see if fileName contains a single event, like Super Bowl, or Pro Bowl
	foundEvent = False
	for (exprs, ind) in mlb_event_expressions:
		if foundEvent == True:
			break
		for expr in exprs:
			for pattern in [r"^%s$" % expr, r"\b%s\b" % expr]:
				(bites, chewed, ms) = Eat(food, pattern)
				if bites:

					# Check to see if existing values match. If they don't, eat, but leave values unchanged
					if meta.get(METADATA_EVENT_INDICATOR_KEY) != None and meta[METADATA_EVENT_INDICATOR_KEY] != ind:
						return chewed

					foundEvent = True
					meta.setdefault(METADATA_SPORT_KEY, SPORT_BASEBALL)
					meta.setdefault(METADATA_LEAGUE_KEY, LEAGUE_MLB)
					meta.setdefault(METADATA_EVENT_INDICATOR_KEY, ind)

					eventName = ""
					if ind == MLB_EVENT_FLAG_HALL_OF_FAME: eventName = "Hall of Fame Game"
					elif ind == MLB_EVENT_FLAG_HOME_RUN_DERBY: eventName = "Home Run Derby"
					elif ind == MLB_EVENT_FLAG_ALL_STAR_GAME: eventName = "All-Star Game"
					else: eventName = bites[0][1]

					meta.setdefault(METADATA_EVENT_NAME_KEY, eventName)
					return chewed

	return food