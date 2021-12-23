import datetime
from Extensions import *
from MetadataKeys import *
from MLBConstants import *
from NBAConstants import *
from NFLConstants import *
from NHLConstants import *

THIS_YEAR = datetime.datetime.now().year
LAST_YEAR = THIS_YEAR - 1
NEXT_YEAR = THIS_YEAR + 1

SPORT_BASEBALL = "Baseball"
SPORT_BASKETBALL = "Basketball"
SPORT_FOOTBALL = "Football"
SPORT_HOCKEY = "Hockey"

LEAGUE_MLB = "MLB"
LEAGUE_NBA = "NBA"
LEAGUE_NFL = "NFL"
LEAGUE_NHL = "NHL"

LEAGUE_NAME_MLB = "Major League Baseball"
LEAGUE_NAME_NBA = "National Basketball Association"
LEAGUE_NAME_NFL = "National Football League"
LEAGUE_NAME_NHL = "National Hockey League"

supported_sports = [
	SPORT_BASEBALL,
	SPORT_BASKETBALL,
	SPORT_FOOTBALL,
	SPORT_HOCKEY
	]

supported_league_sports = supported_sports
supported_seasonal_leagues = [
	LEAGUE_MLB,
	LEAGUE_NBA,
	LEAGUE_NFL,
	LEAGUE_NHL
	]
supported_team_sports = supported_sports
supported_series_sports = [
	SPORT_BASEBALL,
	SPORT_BASKETBALL,
	SPORT_HOCKEY
	]

# Leagues whose seasons cross over the new year's boundary
year_boundary_leagues = [LEAGUE_NBA, LEAGUE_NFL, LEAGUE_NHL]

#(Name, Sport)
known_leagues = {
  LEAGUE_MLB: (LEAGUE_NAME_MLB, SPORT_BASEBALL),
  LEAGUE_NBA: (LEAGUE_NAME_NBA, SPORT_BASKETBALL),
  LEAGUE_NFL: (LEAGUE_NAME_NFL, SPORT_FOOTBALL),
  LEAGUE_NHL: (LEAGUE_NAME_NHL, SPORT_HOCKEY)
}

#(League, Search)
known_leagues_expressions = [ 
  (LEAGUE_MLB, LEAGUE_MLB),
  (LEAGUE_NBA, LEAGUE_NBA),
  (LEAGUE_NFL, LEAGUE_NFL),
  (LEAGUE_NHL, LEAGUE_NHL)
]

EXPRESSION_SEPARATOR = r"[\s\.\-_]"
EXPRESSION_VALID_FULL_YEAR_NON_CAPTURING = r"(?:(19\d{2})|(20\d{2}))"
EXPRESSION_VALID_FULL_YEAR = r"(?P<year>%s)" % EXPRESSION_VALID_FULL_YEAR_NON_CAPTURING
EXPRESSION_YEAR = r"(?P<year>\d{2}|%s)" % EXPRESSION_VALID_FULL_YEAR_NON_CAPTURING
EXPRESSION_VALID_DAY = r"(?P<day>(?:(0?[0-9])|([12][0-9])|(3[01])))"
EXPRESSION_VALID_MONTH = r"(?P<month>(?:(0?[0-9])|(1[0-2])))"
EXPRESSION_VALID_FULL_DAY = r"(?P<day>(?:(0[0-9])|([12][0-9])|(3[01])))"
EXPRESSION_VALID_FULL_MONTH = r"(?P<month>(?:(0[0-9])|(1[0-2])))"

air_date_expressions = [
  r"%s\.%s\.%s" % (EXPRESSION_VALID_FULL_YEAR, EXPRESSION_VALID_FULL_MONTH, EXPRESSION_VALID_FULL_DAY), # 2021.01.30
  r"%s-%s-%s" % (EXPRESSION_VALID_FULL_YEAR, EXPRESSION_VALID_FULL_MONTH, EXPRESSION_VALID_FULL_DAY), # 2021-01-30
  r"%s_%s_%s" % (EXPRESSION_VALID_FULL_YEAR, EXPRESSION_VALID_FULL_MONTH, EXPRESSION_VALID_FULL_DAY), # 2021_01_30
  r"%s %s %s" % (EXPRESSION_VALID_FULL_YEAR, EXPRESSION_VALID_FULL_MONTH, EXPRESSION_VALID_FULL_DAY), # 2021 01 30
  r"%s%s%s" % (EXPRESSION_VALID_FULL_YEAR, EXPRESSION_VALID_FULL_MONTH, EXPRESSION_VALID_FULL_DAY), # 20210130
  r"%s\.%s\.%s" % (EXPRESSION_VALID_FULL_MONTH, EXPRESSION_VALID_FULL_DAY, EXPRESSION_VALID_FULL_YEAR), # 01.30.2021
  r"%s-%s-%s" % (EXPRESSION_VALID_FULL_MONTH, EXPRESSION_VALID_FULL_DAY, EXPRESSION_VALID_FULL_YEAR), # 01-30-2021
  r"%s_%s_%s" % (EXPRESSION_VALID_FULL_MONTH, EXPRESSION_VALID_FULL_DAY, EXPRESSION_VALID_FULL_YEAR), # 01_30_2021
  r"%s %s %s" % (EXPRESSION_VALID_FULL_MONTH, EXPRESSION_VALID_FULL_DAY, EXPRESSION_VALID_FULL_YEAR), # 01 30 2021
  r"%s%s%s" % (EXPRESSION_VALID_FULL_MONTH, EXPRESSION_VALID_FULL_DAY, EXPRESSION_VALID_FULL_YEAR), # 01302021
  r"%s-%s-%s" % (EXPRESSION_VALID_MONTH, EXPRESSION_VALID_DAY, EXPRESSION_YEAR),   # 1-30-2021 or 1-30-21
  r"%s_%s_%s" % (EXPRESSION_VALID_MONTH, EXPRESSION_VALID_DAY, EXPRESSION_YEAR),   # 1_30_2021 or 1_30_21
  r"(%s)|(%s%s%s)" % (EXPRESSION_VALID_FULL_YEAR_NON_CAPTURING, EXPRESSION_VALID_MONTH, EXPRESSION_VALID_DAY, EXPRESSION_YEAR), # 7821 or 70821 or 7082021
]


versus_expressions = [
  r"(?:^|\b|\W)(@)(?:\b|\W|$)",
  r"(?:^|\b|\W)(versus)(?:\b|\W|$)",
  r"(?:^|\b|\W)(vs?(?:\.|(?:\b|\W|$)))"
]


season_expressions = [
  r"(?P<season_year_begin>%s)(([\s-]+)(?P<season_year_end>%s))?" % (EXPRESSION_VALID_FULL_YEAR_NON_CAPTURING, EXPRESSION_VALID_FULL_YEAR_NON_CAPTURING)
]


week_expressions = [
  r"Week%s?(?P<week_number>(\d+))" % EXPRESSION_SEPARATOR
]


game_number_expressions = [
	r"Game%s?(?P<game_number>(\d+))" % EXPRESSION_SEPARATOR,
	r"Gm\.?%s?(?P<game_number>(\d+))" % EXPRESSION_SEPARATOR,
]




DATA_PATH = r"Data/"
DATA_PATH_LEAGUES = DATA_PATH + r"Leagues/"
