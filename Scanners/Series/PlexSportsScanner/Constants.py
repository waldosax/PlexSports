known_video_codec_expressions = [ 
  ("[hH]\\.264", "H.264"),
  ("[hH]264", "H.264"),
  ("[hH]\\.265", "H.264"),
  ("[hH]265", "H.264"),
  ("[xX]\\.265", "H.264"),
  ("[xX]265", "H.264")
]

known_video_resolution_expressions = [ 
  ("480[iI]", "480i"),
  ("480[pP]", "480p"),
  ("720[iI]", "720i"),
  ("720[pP]", "720p"),
  ("1080[iI]", "1080i"),
  ("1080[pP]", "1080p"),
  ("2160[iI]", "2160i"),
  ("2160[pP]", "2160p")
]


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

supported_team_sports = supported_sports
supported_series_sports = [
	SPORT_BASEBALL,
	SPORT_BASKETBALL,
	SPORT_HOCKEY
	]

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

EXPRESSION_SEPARATOR = r"[\s\.\-+]"
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
  r"%s-%s-%s" % (EXPRESSION_VALID_MONTH, EXPRESSION_VALID_DAY, EXPRESSION_YEAR),   # 1-30-2021 or 1-30-21
  r"%s_%s_%s" % (EXPRESSION_VALID_MONTH, EXPRESSION_VALID_DAY, EXPRESSION_YEAR),   # 1_30_2021 or 1_30_21
  r"(%s)|(%s%s%s)" % (EXPRESSION_VALID_FULL_YEAR_NON_CAPTURING, EXPRESSION_VALID_MONTH, EXPRESSION_VALID_DAY, EXPRESSION_YEAR), # 7821 or 70821 or 7082021
]


versus_expressions = [
  r"\b\@\b",
  r"\bversus\b",
  r"\bvs?(\.|\b)"
]


season_expressions = [
  r"(?P<season_year_begin>%s)(([\s-]+)(?P<season_year_end>%s))?" % (EXPRESSION_VALID_FULL_YEAR_NON_CAPTURING, EXPRESSION_VALID_FULL_YEAR_NON_CAPTURING)
]


week_expressions = [
  r"Week%s+(?P<week_number>(\d+))" % EXPRESSION_SEPARATOR
]


game_number_expressions = [
    "Game%s?(?P<game_number>\d+)" % EXPRESSION_SEPARATOR
]

METADATA_PATH_KEY = "path"
METADATA_FILENAME_KEY = "filename"
METADATA_FOLDER_KEY = "folder"
METADATA_SPORT_KEY = "sport"
METADATA_LEAGUE_KEY = "league"
METADATA_SEASON_KEY = "season"
METADATA_SEASON_BEGIN_YEAR_KEY = "season begin year"
METADATA_SEASON_END_YEAR_KEY = "season_end year"
METADATA_SUBSEASON_INDICATOR_KEY = "subseason"
METADATA_SUBSEASON_KEY = "subseason name"
METADATA_CONFERENCE_KEY = "conference"
METADATA_DIVISION_KEY = "division"
METADATA_WEEK_KEY = "week"
METADATA_WEEK_NUMBER_KEY = "week number"
METADATA_PLAYOFF_ROUND_KEY = "playoff round"
METADATA_EVENT_INDICATOR_KEY = "event name"
METADATA_EVENT_NAME_KEY = "event name"
METADATA_AIRDATE_KEY = "air date"
METADATA_HOME_TEAM_KEY = "home team"
METADATA_AWAY_TEAM_KEY = "away team"
METADATA_GAME_NUMBER_KEY = "game number"
METADATA_VIDEO_CODEC_KEY = "video codec"
METADATA_VIDEO_RESOLUTION_KEY = "video resolution"
METADATA_AUDIO_CODEC_KEY = "audio codec"
METADATA_AUDIO_RESOLUTION_KEY = "audio resolution"




USER_AGENT = "Plex/PlexSportsScanner"

DATA_PATH = r"Data/"
DATA_PATH_LEAGUES = DATA_PATH + r"Leagues/"

ALPHANUMERIC_CHARACTERS = "abcdefghijklmnopqrstuvwxyz0123456789"
ALPHANUMERIC_CHARACTERS_AND_AT = ALPHANUMERIC_CHARACTERS + "@"