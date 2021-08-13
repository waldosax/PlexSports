import datetime

from Constants import *
from TimeZoneUtils import *
from Vectors import *


SCHEDULE_HASH_INDEX_SPORT = 0
SCHEDULE_HASH_INDEX_LEAGUE = 1
SCHEDULE_HASH_INDEX_SEASON = 2
SCHEDULE_HASH_INDEX_SUBSEASON = 3
SCHEDULE_HASH_INDEX_PLAYOFFROUND = 4
SCHEDULE_HASH_INDEX_WEEK = 5
SCHEDULE_HASH_INDEX_GAME = 6
SCHEDULE_HASH_INDEX_EVENT_INDICATOR = 7
SCHEDULE_HASH_INDEX_DATE = 8
SCHEDULE_HASH_INDEX_HOMETEAM = 9
SCHEDULE_HASH_INDEX_AWAYTEAM = 10

def sched_compute_meta_scan_hash2(meta):

	EXPRESSION_INDEX_SEASON = 0
	EXPRESSION_INDEX_SUBSEASON = 1
	EXPRESSION_INDEX_PLAYOFFROUND = 2
	EXPRESSION_INDEX_WEEK = 3
	EXPRESSION_INDEX_DATE = 4
	EXPRESSION_INDEX_TEAM1 = 5
	EXPRESSION_INDEX_TEAM2 = 6
	EXPRESSION_INDEX_EVENT_INDICATOR = 7
	EXPRESSION_INDEX_GAME = 8

	ANYTHING_EXPR = "(.*?)"
	PIPE_EXPR = r"\|"
	OPTIONAL_EXPR = "?"

	atom_defs = [
		("s", "season"),
		("ss", "subseason"),
		("pr", "playoffround"),
		("wk", "week"),
		("dt", "date"),
		("tm", "team1"),
		("tm", "team2"),
		("ei", "eventindicator"),
		("gm", "game")
		]

	#atom_group_name_defs = {
	#	"season": "s",
	#	"subseason": "ss",
	#	"playoffround": "pr",
	#	"week": "wk",
	#	"date": "dt",
	#	"team1": "tm",
	#	"team2": "tm",
	#	"eventindicator": "ei",
	#	"game": "gm"
	#	}

	optional_groups = [
		"subseason",
		"playoffround",
		"week",
		"eventindicator",
		"game"
		]

	# ss depends on s
	# pr depends on ss
	# wk depends on s+ss
	# tm depends on dt
	# gm depends on s+ss|s+pr|dt+tm+tm
	dependencies = {
		"subseason": [["season"]],
		"playoffround": [["subseason"]],
		"week": [["season", "subseason"]],
		"team1": [["date"]],
		"team2": [["team1"]],
		"game": [["season", "subseason"], ["season", "playoffround"], ["date", "team1", "team2"], ["eventindicator"]],
		}

	# Construct a value expression
	def construct_expression_fragment(groupName, atomName, value):
		if isinstance(value, (list)):
			if len(value) > 1:
				escaped = []
				for raw in value:
					escaped.append("(?:%s)" % re.escape(raw))
				valueExpression = "(?:%s)" % "|".join(escaped)
			else:
				valueExpression = re.escape(str(value[0]))
		else:
			valueExpression = re.escape(str(value))

		return r"(?P<%s>%s\:%s)" % (groupName, atomName, valueExpression)

	atoms = dict()
	elements = []
	
	league = meta.get(METADATA_LEAGUE_KEY)
	season = str(meta[METADATA_SEASON_BEGIN_YEAR_KEY]) if meta.get(METADATA_SEASON_BEGIN_YEAR_KEY) else meta.get(METADATA_SEASON_KEY)
	airdate = meta.get(METADATA_AIRDATE_KEY)
	seasons = [season]

	if not season and airdate:
		season = str(airdate.year)
		seasons = [season]

	if league in year_boundary_leagues:
		seasons += [str(int(season)-1)]

	#(atomName, groupName) = atom_defs[EXPRESSION_INDEX_SPORT]
	#elements.append(meta[METADATA_SPORT_KEY])
	#atoms[groupName] = construct_expression_fragment(groupName, atomName, meta[METADATA_SPORT_KEY])
	#(atomName, groupName) = atom_defs[EXPRESSION_INDEX_LEAGUE]
	#elements.append(league)
	#atoms[groupName] = construct_expression_fragment(groupName, atomName, league)

	(atomName, groupName) = atom_defs[EXPRESSION_INDEX_SEASON]
	atom = season
	elements.append("%s:%s" % (atomName, atom))
	atoms[groupName] = construct_expression_fragment(groupName, atomName, seasons)


	(atomName, groupName) = atom_defs[EXPRESSION_INDEX_SUBSEASON]
	if meta.get(METADATA_SUBSEASON_INDICATOR_KEY) != None:
		atom = meta[METADATA_SUBSEASON_INDICATOR_KEY]
		elements.append("%s:%s" % (atomName, atom))
		atoms[groupName] = construct_expression_fragment(groupName, atomName, atom)
	else:
		atoms[groupName] = None

	(atomName, groupName) = atom_defs[EXPRESSION_INDEX_PLAYOFFROUND]
	if meta.get(METADATA_PLAYOFF_ROUND_KEY):
		atom = meta[METADATA_PLAYOFF_ROUND_KEY]
		elements.append("%s:%s" % (atomName, atom))
		atoms[groupName] = construct_expression_fragment(groupName, atomName, atom)
	else:
		atoms[groupName] = None

	(atomName, groupName) = atom_defs[EXPRESSION_INDEX_WEEK]
	if meta.get(METADATA_WEEK_KEY) != None:
		atom = meta[METADATA_WEEK_KEY]
		elements.append("%s:%s" % (atomName, atom))
		atoms[groupName] = construct_expression_fragment(groupName, atomName, atom)
	else:
		atoms[groupName] = None

	(atomName, groupName) = atom_defs[EXPRESSION_INDEX_DATE]
	if meta.get(METADATA_AIRDATE_KEY):
		atom = sched_compute_date_hash(meta[METADATA_AIRDATE_KEY])
		elements.append("%s:%s" % (atomName, atom))
		atoms[groupName] = construct_expression_fragment(groupName, atomName, atom)
	else:
		atoms[groupName] = None

	(atomName, groupName) = atom_defs[EXPRESSION_INDEX_TEAM1]
	if meta.get(METADATA_HOME_TEAM_KEY):
		atom = meta[METADATA_HOME_TEAM_KEY]
		elements.append("%s:%s" % (atomName, atom))
		atoms[groupName] = construct_expression_fragment(groupName, atomName, atom)
	else:
		atoms[groupName] = None

	(atomName, groupName) = atom_defs[EXPRESSION_INDEX_TEAM2]
	if meta.get(METADATA_AWAY_TEAM_KEY):
		atom = meta[METADATA_AWAY_TEAM_KEY]
		elements.append("%s:%s" % (atomName, atom))
		atoms[groupName] = construct_expression_fragment(groupName, atomName, atom)
	else:
		atoms[groupName] = None

	(atomName, groupName) = atom_defs[EXPRESSION_INDEX_EVENT_INDICATOR]
	if meta.get(METADATA_EVENT_INDICATOR_KEY) != None:
		atom = meta[METADATA_EVENT_INDICATOR_KEY]
		elements.append("%s:%s" % (atomName, atom))
		atoms[groupName] = construct_expression_fragment(groupName, atomName, atom)
	else:
		atoms[groupName] = None

	(atomName, groupName) = atom_defs[EXPRESSION_INDEX_GAME]
	if meta.get(METADATA_GAME_NUMBER_KEY):
		atom = meta[METADATA_GAME_NUMBER_KEY]
		elements.append("%s:%s" % (atomName, atom))
		atoms[groupName] = construct_expression_fragment(groupName, atomName, atom)
	else:
		atoms[groupName] = None

	expr = ""
	previousAtomUsed = True
	for index in range(EXPRESSION_INDEX_SEASON, EXPRESSION_INDEX_GAME+1):
		(atomName, groupName) = atom_defs[index]
		atom = atoms[groupName]
		atomOptional = False
		if atom == None:
			if previousAtomUsed: expr = expr + ANYTHING_EXPR
			previousAtomUsed = False
		else:
			molecule = ""
			atomOptional = False
			#if previousAtomUsed == True and groupName in optional_groups: atomOptional = True
			if groupName in optional_groups: atomOptional = True
			if not index == EXPRESSION_INDEX_SEASON: molecule = molecule +  PIPE_EXPR
			molecule = molecule + atom
			molecule = "(?:" + molecule + ")" + (OPTIONAL_EXPR if atomOptional else "")
			if groupName in dependencies.keys():
				b = []
				for dependency in dependencies[groupName]:
					a = ""
					containsAllGroups = True
					for backref in dependency:
						if atoms[backref] == None:
							containsAllGroups = False
							break
					if not containsAllGroups: continue
					backrefs = dependency
					backrefs.reverse()
					for backref in backrefs:
						a = "(?(%s)%s)" % (backref, a)
					b.append(a)
				molecule = "(?:" + "|".join(b) + ")" + molecule
			
			expr = expr + molecule
			previousAtomUsed = True
			pass

	expr = expr + "$"
	repr = "|".join(elements)



	return (repr, expr)







def sched_compute_scan_hashes(event):
	molecules = []

	orderedPieces = []
	keyPieces = event.key.split("|")
	orderedPieces.append(keyPieces)

	swappedPositions = list(keyPieces)
	tmp = swappedPositions[SCHEDULE_HASH_INDEX_AWAYTEAM]
	swappedPositions[SCHEDULE_HASH_INDEX_AWAYTEAM] = swappedPositions[SCHEDULE_HASH_INDEX_HOMETEAM]
	swappedPositions[SCHEDULE_HASH_INDEX_HOMETEAM] = tmp
	orderedPieces.append(swappedPositions)


	for keyPieces in orderedPieces:
		atoms = []
			
		#atom = "sp:%s" % keyPieces[SCHEDULE_HASH_INDEX_SPORT]
		#atoms.append(atom)
			
		#atom = "lg:%s" % keyPieces[SCHEDULE_HASH_INDEX_LEAGUE]
		#atoms.append(atom)
			
		atom = "s:%s" % keyPieces[SCHEDULE_HASH_INDEX_SEASON]
		atoms.append(atom)
			
		if keyPieces[SCHEDULE_HASH_INDEX_SUBSEASON]:
			atom = "ss:%s" % keyPieces[SCHEDULE_HASH_INDEX_SUBSEASON]
			atoms.append(atom)
			
		if keyPieces[SCHEDULE_HASH_INDEX_PLAYOFFROUND]:
			atom = "pr:%s" % keyPieces[SCHEDULE_HASH_INDEX_PLAYOFFROUND]
			atoms.append(atom)

		if keyPieces[SCHEDULE_HASH_INDEX_WEEK]:
			atom = "wk:%s" % keyPieces[SCHEDULE_HASH_INDEX_WEEK]
			atoms.append(atom)
			
		atom = "dt:%s" % keyPieces[SCHEDULE_HASH_INDEX_DATE]
		atoms.append(atom)
			
		atom = "tm:%s" % keyPieces[SCHEDULE_HASH_INDEX_HOMETEAM]
		atoms.append(atom)
			
		atom = "tm:%s" % keyPieces[SCHEDULE_HASH_INDEX_AWAYTEAM]
		atoms.append(atom)

		if keyPieces[SCHEDULE_HASH_INDEX_EVENT_INDICATOR]:
			atom = "ei:%s" % keyPieces[SCHEDULE_HASH_INDEX_EVENT_INDICATOR]
			atoms.append(atom)

		if keyPieces[SCHEDULE_HASH_INDEX_GAME]:
			atom = "gm:%s" % keyPieces[SCHEDULE_HASH_INDEX_GAME]
			atoms.append(atom)

		molecule = "|".join(atoms)
		molecules.append(molecule)

	return molecules


def sched_compute_augmentation_hash(event):
	molecules = []
	
	sport = sched_compute_sport_hash(event.sport) or ""
	molecules.append(sport)

	# TODO: Omit when taking on non-league sports, like Boxing
	league = sched_compute_league_hash(event.league) or ""
	molecules.append(league)

	# TODO: Omit when taking on non-seasonal sports, like Boxing
	season = sched_compute_league_hash(event.season) or ""
	molecules.append(season)

	date = sched_compute_date_hash(event.date) or ""
	molecules.append(date)
	
	# TODO: Modify when taking on non-team sports, like Boxing
	home = sched_compute_team_hash(event.homeTeam) or ""
	away = sched_compute_team_hash(event.awayTeam) or ""
	molecules.append(home)
	molecules.append(away)

	return "|".join(molecules)

def sched_compute_hash(event):
	molecules = []
	
	sport = sched_compute_sport_hash(event.sport) or ""
	molecules.append(sport)

	# TODO: Omit when taking on non-league sports, like Boxing
	league = sched_compute_league_hash(event.league) or ""
	molecules.append(league)

	# TODO: Omit when taking on non-seasonal sports, like Boxing
	season = sched_compute_league_hash(event.season) or ""
	molecules.append(season)

	subseason = sched_compute_subseason_hash(event.subseason) or ""
	molecules.append(subseason)

	playoffRound = sched_compute_playoff_round_hash(event.playoffround) or ""
	molecules.append(playoffRound)

	week = sched_compute_week_hash(event.week) or ""
	molecules.append(week)

	game = sched_compute_game_hash(event.game) or ""
	molecules.append(game)

	eventIndicator = sched_compute_game_hash(event.eventindicator) or ""
	molecules.append(eventIndicator)

	date = sched_compute_date_hash(event.date) or ""
	molecules.append(date)
	
	# TODO: Modify when taking on non-team sports, like Boxing
	home = sched_compute_team_hash(event.homeTeam) or ""
	away = sched_compute_team_hash(event.awayTeam) or ""
	molecules.append(home)
	molecules.append(away)

	return "|".join(molecules)

def sched_compute_sport_hash(sport):
	return create_scannable_key(sport)

def sched_compute_league_hash(league):
	return create_scannable_key(league)

def sched_compute_season_hash(season):
	if not season:
		return None

	s = ""
	if (isinstance(season, basestring)):
		s = season
		for expr in season_expressions:
			p = re.compile(expr, re.IGNORECASE)
			m = p.search(s)
			if m:
				return expandYear(m.group("season_begin_year")).lower()
	elif (isinstance(season, int)):
		s = str(season)
	
	return None

def sched_compute_week_hash(week):
	if week == None: return None
	if isinstance(week, int): week = str(week)
	return week.lower()

def sched_compute_subseason_hash(subseason):
	if subseason == None: return None
	if isinstance(subseason, int): subseason = str(subseason)
	return subseason.lower()

def sched_compute_playoff_round_hash(playoffRound):
	if playoffRound == None: return None
	if isinstance(playoffRound, int): playoffRound = str(playoffRound)
	return playoffRound.lower()

def sched_compute_game_hash(game):
	if not game: return None
	if isinstance(game, int): game = str(game)
	return game.lower()

def sched_compute_date_hash(eventDate):
	if not eventDate:
		return None

	if not isinstance(eventDate, (datetime.datetime, datetime.date)):
		return None

	if isinstance(eventDate, datetime.datetime):
		if eventDate.tzinfo != None:
			eventDate = eventDate.astimezone(tz=EasternTime)

	return eventDate.strftime("%Y%m%d")

def sched_compute_time_hash(eventDate):
	if not eventDate:
		return None

	if not isinstance(eventDate, (datetime.datetime, datetime.time)):
		return None

	if eventDate.tzinfo != None:
		eventDate = eventDate.astimezone(tz=EasternTime)

	if isinstance(eventDate, (datetime.datetime)) and not eventDate.time():
		return None

	return eventDate.strftime("%H")

def sched_compute_team_hash(abbrev):
	return create_scannable_key(abbrev)


