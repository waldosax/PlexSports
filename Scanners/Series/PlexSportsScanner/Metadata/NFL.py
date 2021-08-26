# Python framework
import re

# Local package
from Constants import *
from Matching import __expressions_from_literal, Eat
import RomanNumerals

nfl_conferences = {
	NFL_CONFERENCE_AFC: NFL_CONFERENCE_NAME_AFC,
	NFL_CONFERENCE_NFC: NFL_CONFERENCE_NAME_NFC
	}

nfl_conference_expressions = [
	(NFL_CONFERENCE_AFC, [NFL_CONFERENCE_AFC]+__expressions_from_literal(NFL_CONFERENCE_NAME_AFC)),
	(NFL_CONFERENCE_NFC, [NFL_CONFERENCE_NFC]+__expressions_from_literal(NFL_CONFERENCE_NAME_NFC))
	]

nfl_superbowl_expressions = [
	"Super(?:%s)+bowl((?:%s)+(?P<game_number>(\d+)|([MDCLXVI]+))?)" % (EXPRESSION_SEPARATOR, EXPRESSION_SEPARATOR),
	"Superbowl((?:%s)+(?P<game_number>(\d+)|([MDCLXVI]+))?)" % EXPRESSION_SEPARATOR,
	"Super(?P<sp>%s)+bowl((?P=sp)+(?P<game_number>(\d+)|([MDCLXVI]+))?)" % EXPRESSION_SEPARATOR,
	"Superbowl((?:%s)+(?P<game_number>(\d+)|([MDCLXVI]+))?)" % EXPRESSION_SEPARATOR,
	"Superbowl((?P<game_number>(\d+)|([MDCLXVI]+))?)"
	]

nfl_subseason_indicator_expressions = [
	(NFL_SUBSEASON_FLAG_PRESEASON, __expressions_from_literal(NFL_SUBSEASON_PRESEASON)),
	(NFL_SUBSEASON_FLAG_POSTSEASON, __expressions_from_literal(NFL_SUBSEASON_POSTSEASON) + __expressions_from_literal(NFL_SUBSEASON_PLAYOFFS)),
	(NFL_SUBSEASON_FLAG_REGULAR_SEASON, __expressions_from_literal(NFL_SUBSEASON_REGULAR_SEASON))
	]


# (expressions, conference, round)
# Ordered by more specific to less
nfl_playoff_round_expressions = [
	(__expressions_from_literal("%s Wild card Round" % NFL_CONFERENCE_AFC) + __expressions_from_literal("%s Wild card" % NFL_CONFERENCE_AFC), NFL_CONFERENCE_AFC, NFL_PLAYOFF_ROUND_WILDCARD),
	(__expressions_from_literal("%s Wild card Round" % NFL_CONFERENCE_NFC) + __expressions_from_literal("%s Wild card" % NFL_CONFERENCE_NFC), NFL_CONFERENCE_NFC, NFL_PLAYOFF_ROUND_WILDCARD),
	(__expressions_from_literal("%s Wildcard Round" % NFL_CONFERENCE_AFC) + __expressions_from_literal("%s Wildcard" % NFL_CONFERENCE_AFC), NFL_CONFERENCE_AFC, NFL_PLAYOFF_ROUND_WILDCARD),
	(__expressions_from_literal("%s Wildcard Round" % NFL_CONFERENCE_NFC) + __expressions_from_literal("%s Wildcard" % NFL_CONFERENCE_NFC), NFL_CONFERENCE_NFC, NFL_PLAYOFF_ROUND_WILDCARD),
	(__expressions_from_literal("Wild card Round") + __expressions_from_literal("Wild card"), None, NFL_PLAYOFF_ROUND_WILDCARD),
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






def InferSubseasonFromFolders(fileName, folders, meta):
	if meta.get(METADATA_SUBSEASON_INDICATOR_KEY): return

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
			InferPlayoffRoundFromFolders(fileName, folders, meta)

def InferWeekFromFolders(fileName, folders, meta):
	if meta.get(METADATA_WEEK_NUMBER_KEY): return

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


def InferPostseasonConferenceFromFolders(fileName, folders, meta):
	if meta.get(METADATA_CONFERENCE_KEY): return

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

def InferPlayoffRoundFromFolders(fileName, folders, meta):
	if meta.get(METADATA_PLAYOFF_ROUND_KEY): return

	league = meta.get(METADATA_LEAGUE_KEY)
	season = meta.get(METADATA_SEASON_KEY)
	if folders and league and season:
		foundRound = False

		# Test to see if next-level folder is a subseason indicator
		folder = folders[0]
		for (exprs, conference, round) in nfl_playoff_round_expressions:
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
						if conference: meta.setdefault(METADATA_CONFERENCE_KEY, conference)
						meta.setdefault(METADATA_PLAYOFF_ROUND_KEY, round)

						eventName = ""
						if not conference: conference = meta.get(METADATA_CONFERENCE_KEY)
						if conference:
							eventName += conference
						if round == 1:
							if eventName: eventName += " "
							eventName += "Wildcard" + (" Round" if not conference else "")
						elif round == 2:
							if eventName: eventName += " "
							eventName += "Divisional Round"
						elif round == 3:
							if eventName: eventName += " "
							eventName += "Conference" + (" Championship" if not conference else "Round")
						elif round == 4:
							gameNumber = None
							if "game_number" in m.groupdict().keys():
								gameNumber = RomanNumerals.Parse(m.group("game_number"))
								#meta.setdefault(METADATA_GAME_NUMBER_KEY, gameNumber)
							eventName = "Superbowl"
							if gameNumber: eventName += " " + RomanNumerals.Format(gameNumber)
							meta.setdefault(METADATA_EVENT_INDICATOR_KEY, NFL_EVENT_FLAG_SUPERBOWL)
						else: eventName = folder
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
		for (ind, exprs) in nfl_subseason_indicator_expressions:
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

def InferWeekFromFileName(fileName, food, meta):
	if not food: return food
	if meta.get(METADATA_WEEK_NUMBER_KEY): return food

	league = meta.get(METADATA_LEAGUE_KEY)
	season = meta.get(METADATA_SEASON_KEY)
	ind = meta.get(METADATA_SUBSEASON_INDICATOR_KEY)
	if league and season and ((not ind) or (ind == NFL_SUBSEASON_FLAG_PRESEASON or ind == NFL_SUBSEASON_FLAG_REGULAR_SEASON)):
		foundWeek = False

		# Test to see if fileName contains a week indicator (preseason and regular season)
		for expr in week_expressions:
			if foundWeek == True:
				break
			for pattern in [r"^%s$" % expr, r"\b%s\b" % expr]:
				(bites, chewed, ms) = Eat(food, pattern)
				if bites:
					weekNumber = int(bites[0][0].group("week_number"))

					# Check to see if existing values match. If they don't, eat, but leave values unchanged
					if meta.get(METADATA_WEEK_NUMBER_KEY) != None and meta[METADATA_WEEK_NUMBER_KEY] != weekNumber:
						return chewed

					foundWeek = True

					meta.setdefault(METADATA_WEEK_KEY, bites[0][1])
					meta.setdefault(METADATA_WEEK_NUMBER_KEY, weekNumber)
					return chewed
	return food

def InferPostseasonConferenceFromFileName(fileName, food, meta):
	if not food: return food
	if meta.get(METADATA_CONFERENCE_KEY) : return food

	league = meta.get(METADATA_LEAGUE_KEY)
	season = meta.get(METADATA_SEASON_KEY)
	ind = meta.get(METADATA_SUBSEASON_INDICATOR_KEY)
	if league and season and ind == NFL_SUBSEASON_FLAG_POSTSEASON:
		foundConference = False

		# Test to see if fileName contains a conference (postseason)
		for (conference, exprs) in nfl_conference_expressions:
			if foundConference == True:
				break
			for expr in exprs:
				if foundConference == True:
					break
				for pattern in [r"^%s$" % expr, r"\b%s\b" % expr]:
					(bites, chewed, ms) = Eat(food, pattern)
					if bites:
						foundConference = True

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
		for (exprs, conference, round) in nfl_playoff_round_expressions:
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

						meta.setdefault(METADATA_SUBSEASON_INDICATOR_KEY, NFL_SUBSEASON_FLAG_POSTSEASON)
						meta.setdefault(METADATA_SUBSEASON_KEY, bites[0][1])
						if conference: meta.setdefault(METADATA_CONFERENCE_KEY, conference)
						meta.setdefault(METADATA_PLAYOFF_ROUND_KEY, round)

						eventName = ""
						if not conference: conference = meta.get(METADATA_CONFERENCE_KEY)
						if conference:
							eventName += conference
						if round == 1:
							if eventName: eventName += " "
							eventName += "Wildcard" + (" Round" if not conference else "")
						elif round == 2:
							if eventName: eventName += " "
							eventName += "Divisional Round"
						elif round == 3:
							if eventName: eventName += " "
							eventName += "Conference" + (" Championship" if not conference else "Round")
						elif round == 4:
							gameNumber = None
							if "game_number" in ms[0].groupdict().keys():
								gameNumber = RomanNumerals.Parse(ms[0].group("game_number"))
								#meta.setdefault(METADATA_GAME_NUMBER_KEY, gameNumber)
							eventName = "Superbowl"
							if gameNumber: eventName += " " + RomanNumerals.Format(gameNumber)
							meta.setdefault(METADATA_EVENT_INDICATOR_KEY, NFL_EVENT_FLAG_SUPERBOWL)
						else: eventName = bites[0][1]
						meta.setdefault(METADATA_EVENT_NAME_KEY, eventName)

						return chewed

	return food


def InferSingleEventFromFileName(fileName, food, meta):
	if not food: return food

	# Test to see if fileName contains a single event, like Super Bowl, or Pro Bowl
	foundEvent = False
	for (exprs, ind) in nfl_event_expressions:
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
					meta.setdefault(METADATA_SPORT_KEY, SPORT_FOOTBALL)
					meta.setdefault(METADATA_LEAGUE_KEY, LEAGUE_NFL)
					meta.setdefault(METADATA_EVENT_INDICATOR_KEY, ind)

					eventName = ""
					if ind == NFL_EVENT_FLAG_HALL_OF_FAME: eventName = "Hall of Fame Game"
					elif ind == NFL_EVENT_FLAG_PRO_BOWL: eventName = "Pro Bowl"
					elif ind == NFL_EVENT_FLAG_SUPERBOWL:
						gameNumber = None
						if "game_number" in ms[0].groupdict().keys():
							gameNumber = RomanNumerals.Parse(ms[0].group("game_number"))
							#meta.setdefault(METADATA_GAME_NUMBER_KEY, gameNumber)
						eventName = "Superbowl"
						if gameNumber: eventName += " " + RomanNumerals.Format(gameNumber)
					else: eventName = bites[0][1]

					meta.setdefault(METADATA_EVENT_NAME_KEY, eventName)
					return chewed

	return food