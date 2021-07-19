import sys, os, json, re
from datetime import datetime
from pprint import pprint

from Constants import *
from Matching import __strip_to_alphanumeric
import Teams
from Data import TheSportsDB

WEIGHT_SPORT = 1
WEIGHT_LEAGUE = 5
WEIGHT_SEASON = 10
WEIGHT_SUBSEASON = 6
WEIGHT_WEEK = 4
WEIGHT_EVENT_DATE = 20
WEIGHT_GAME = 1
WEIGHT_TEAM = 25
WEIGHT_VS = 30

class event_cache_dict(dict):
	def __init__(self, weight, *args, **kwargs):
		dict.__init__(self, *args, **kwargs)
		self.weight = weight
		self.sports = event_cache_dict(WEIGHT_SPORT, parent=self)
		self.leagues = event_cache_dict(WEIGHT_LEAGUE, parent=self)
		self.seasons = event_cache_dict(WEIGHT_SEASON, parent=self)
		self.subseasons = event_cache_dict(WEIGHT_SUBSEASON, parent=self)
		self.weeks = event_cache_dict(WEIGHT_WEEK, parent=self)
		self.dates = event_cache_dict(WEIGHT_EVENT_DATE, parent=self)
		self.games = event_cache_dict(WEIGHT_GAME, parent=self)
		self.teams = event_cache_dict(WEIGHT_TEAM, parent=self)
		self.vs = event_cache_dict(WEIGHT_VS, parent=self)
		self.parent = kwargs.get("parent")

class event:
	def __init__(self, **kwargs):
		self.sport = str(kwargs.get("sport"))
		self.league = str(kwargs.get("league"))
		self.season = str(kwargs.get("season"))
		self.date = str(kwargs.get("date"))
		self.title = str(kwargs.get("title"))
		self.altTitle = str(kwargs.get("altTitle"))
		self.description = str(kwargs.get("description"))
		self.homeTeam = str(kwargs.get("homeTeam"))
		self.awayTeam = str(kwargs.get("awayTeam"))
		# TODO: fields for non team-based sports, like Boxing

		# Additional metadata items (if provided)
		self.network = str(kwargs.get("network"))
		self.poster = str(kwargs.get("poster"))
		self.fanArt = str(kwargs.get("fanArt"))
		self.thumbnail = str(kwargs.get("thumbnail"))
		self.banner = str(kwargs.get("banner"))
		self.preview = str(kwargs.get("preview"))

		self.TheSportsDBID = str(kwargs.get("TheSportsDBID"))

	def augment(self, **kwargs):
		if not self.sport: self.sport = str(kwargs.get("sport"))
		if not self.league: self.league = str(kwargs.get("league"))
		if not self.season: self.season = str(kwargs.get("season"))
		if not self.date: self.date = str(kwargs.get("date"))

		if not kwargs.get("title"): self.title = str(kwargs.get("title"))
		if not kwargs.get("altTitle"): self.altTitle = str(kwargs.get("altTitle"))
		if not kwargs.get("description"): self.description = str(kwargs.get("description"))
		
		if not self.homeTeam: self.homeTeam = str(kwargs.get("homeTeam"))
		if not self.homeTeam: self.awayTeam = str(kwargs.get("awayTeam"))
		# TODO: fields for non team-based sports, like Boxing

		# Additional metadata items (if provided)
		if not self.network: self.network = str(kwargs.get("network"))
		if not self.poster: self.poster = str(kwargs.get("poster"))
		if not self.fanArt: self.fanArt = str(kwargs.get("fanArt"))
		if not self.thumbnail: self.thumbnail = str(kwargs.get("thumbnail"))
		if not self.banner: self.banner = str(kwargs.get("banner"))
		if not self.preview: self.preview = str(kwargs.get("preview"))
		
		if not self.TheSportsDBID: self.TheSportsDBID = str(kwargs.get("TheSportsDBID"))

def foo():
	league = LEAGUE_NFL
	season = 2020
	(leagueName, sport) = known_leagues[league]
	Teams.__get_teams_from_cache(league)
	downloadedJson = TheSportsDB.__the_sports_db_download_schedule_for_league_and_season(league, season)
	sportsDbSschedule = json.loads(downloadedJson)
	for schedEvent in sportsDbSschedule["events"]:
		homeTeamBoiled = __strip_to_alphanumeric(normalize_string(schedEvent["strHomeTeam"]))
		awayTeamBoiled = __strip_to_alphanumeric(normalize_string(schedEvent["strAwayTeam"]))
		homeTeam = Teams.cached_team_keys[league][homeTeamBoiled]
		awayTeam = Teams.cached_team_keys[league][awayTeamBoiled]

		kwargs = {
			"sport": sport,
			"season": season,
			"league": league,
			# TODO: Relate all date/times to UTC (currently presented as E[S|D]T (local))
			"date": datetime.strptime("%sT%s" % (schedEvent["dateEventLocal"], schedEvent["strTimeLocal"]), "%Y-%m-%dT%H:%M:%S"),
			"TheSportsDBID": normalize_string(schedEvent["idEvent"]),
			"title": normalize_string(schedEvent["strEvent"]),
			"altTitle": normalize_string(schedEvent["strEventAlternate"]),
			"description": normalize_string(schedEvent["strDescriptionEN"]),
			"homeTeam": homeTeam,
			"awayTeam": awayTeam,
			"network": normalize_string(schedEvent["strTVStation"]),
			"poster": normalize_string(schedEvent["strPoster"]),
			"fanArt": normalize_string(schedEvent["strFanart"]),
			"thumbnail": normalize_string(schedEvent["strThumb"]),
			"banner": normalize_string(schedEvent["strBanner"]),
			"preview": normalize_string(schedEvent["strVideo"])}
		ev = event(**kwargs)
		pprint(ev)
		#__add_or_override_team(teams, League=league, Abbreviation=team["strTeamShort"], Name=team["strTeam"], FullName=team["strTeam"], SportsDBID=team["idTeam"])
	#pprint(sportsDbTeams)

def normalize_string(s):
	if not s:
		return s
	return str(s.decode('utf-8', 'ignore'))