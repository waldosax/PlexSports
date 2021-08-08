import datetime
from TimeZoneUtils import *


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
	if not sport:
		return None
	return sport.lower()

def sched_compute_league_hash(league):
	if not league:
		return None
	return league.lower()

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
	if not abbrev:
		return None
	return abbrev.lower()


