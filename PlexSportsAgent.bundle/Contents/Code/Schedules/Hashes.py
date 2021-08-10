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

def sched_compute_meta_scan_hash(meta):

	# Construct an expression
	def construct_expression_fragment(key, molecule, value):
		return r"(?P<%s>%s\:%s)(?:.*?)(?:\||$)?" % (key, molecule, re.escape(str(value)))

	molecules = []
	atoms = []
	
	#molecules.append(construct_expression_fragment("sport", "sp", meta[METADATA_SPORT_KEY]))
	#molecules.append(construct_expression_fragment("league", "lg", meta[METADATA_LEAGUE_KEY]))
	
	if meta.get(METADATA_SEASON_BEGIN_YEAR_KEY):
		atom = meta[METADATA_SEASON_BEGIN_YEAR_KEY]
		atoms.append("s:%s" % atom)
		molecules.append(construct_expression_fragment("season", "s", atom))
	if meta.get(METADATA_SUBSEASON_INDICATOR_KEY) != None:
		atom = meta[METADATA_SUBSEASON_INDICATOR_KEY]
		atoms.append("ss:%s" % atom)
		molecules.append(construct_expression_fragment("subseason", "ss", atom))
	if meta.get(METADATA_PLAYOFF_ROUND_KEY):
		atom = meta[METADATA_PLAYOFF_ROUND_KEY]
		atoms.append("pr:%s" % atom)
		molecules.append(construct_expression_fragment("playoffround", "pr", atom))
	if meta.get(METADATA_WEEK_KEY) != None:
		atom = meta[METADATA_WEEK_KEY]
		atoms.append("wk:%s" % atom)
		molecules.append(construct_expression_fragment("week", "wk", atom))
	if meta.get(METADATA_AIRDATE_KEY):
		atom = sched_compute_date_hash(meta[METADATA_AIRDATE_KEY])
		atoms.append("dt:%s" % atom)
		molecules.append(construct_expression_fragment("date", "dt", atom))
	if meta.get(METADATA_HOME_TEAM_KEY):
		atom = meta[METADATA_HOME_TEAM_KEY]
		atoms.append("tm:%s" % atom)
		molecules.append(construct_expression_fragment("team1", "tm", atom))
	if meta.get(METADATA_AWAY_TEAM_KEY):
		atom = meta[METADATA_AWAY_TEAM_KEY]
		atoms.append("tm:%s" % atom)
		molecules.append(construct_expression_fragment("team2", "tm", atom))
	if meta.get(METADATA_EVENT_INDICATOR_KEY) != None:
		atom = meta[METADATA_EVENT_INDICATOR_KEY]
		atoms.append("ei:%s" % atom)
		molecules.append(construct_expression_fragment("eventindicator", "ei", atom))
	if meta.get(METADATA_GAME_NUMBER_KEY):
		atom = meta[METADATA_GAME_NUMBER_KEY]
		atoms.append("gm:%s" % atom)
		molecules.append(construct_expression_fragment("game", "gm", atom))

	repr = "|".join(atoms)
	expr = "".join(molecules)

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

def sched_compute_scan_hash(event):
	scanHashes = sched_compute_scan_hashes(event)
	return scanHashes[0]

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

	return eventDate.strftime("%H")

def sched_compute_team_hash(abbrev):
	return create_scannable_key(abbrev)


