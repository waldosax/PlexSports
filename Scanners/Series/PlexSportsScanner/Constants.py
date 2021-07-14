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


air_date_expressions = [
  r"(?P<year>(\d{4}))[\.]?(?P<month>(\d{2}))[\.]?(?P<day>(\d{2}))", # 2021.01.30
  r"(?P<year>(\d{4}))[-]?(?P<month>(\d{2}))[-]?(?P<day>(\d{2}))",   # 2021-01-30
  r"(?P<year>(\d{4}))[_]?(?P<month>(\d{2}))[_]?(?P<day>(\d{2}))",   # 2021_01_30
  r"(?P<year>(\d{4}))[ ]?(?P<month>(\d{2}))[ ]?(?P<day>(\d{2}))",   # 2021 01 30
  r"(?P<year>(\d{4}))(?P<month>(\d{2}))(?P<day>(\d{2}))",           # 20210130
  r"(?P<month>(\d{1,2}))-(?P<day>(\d{1,2}))-(?P<year>(\d{2,4}))",   # 1-30-2021 or 1-30-21
  r"(?P<month>(\d{1,2}))_(?P<day>(\d{1,2}))_(?P<year>(\d{2,4}))"    # 1_30_2021 or 1_30_21
]


versus_expressions = [
  r"versus",
  r"vs\.",
  r"v\.",
  r"v",
  r"\@"
]


season_expressions = [
  r"(?P<season_year_begin>(\d{2,4}))(([\s-]+)(?P<season_year_end>(\d{2,4})))?"
]


week_expressions = [
  r"Week\s+(?P<week_number>(\d+))",
  r"week[\.-]?(?P<week_number>(\d+))"
]


double_header_expressions = [
  r"Game\s+(?P<game_number>(\d+))",
  r"game[\.-]?(?P<game_number>(\d+))"
]


METADATA_PATH_KEY = "path"
METADATA_FILENAME_KEY = "filename"
METADATA_FOLDER_KEY = "folder"
METADATA_SPORT_KEY = "sport"
METADATA_LEAGUE_KEY = "league"
METADATA_LEAGUE_NAME_KEY = "league name"
METADATA_SEASON_KEY = "season"
METADATA_SEASON_BEGIN_YEAR_KEY = "season begin year"
METADATA_SEASON_END_YEAR_KEY = "season_end year"
METADATA_SUBSEASON_INDICATOR_KEY = "subseason"
METADATA_SUBSEASON_KEY = "subseason name"
METADATA_CONFERENCE_KEY = "conference"
METADATA_WEEK_KEY = "week"
METADATA_WEEK_NUMBER_KEY = "week number"
METADATA_PLAYOFF_ROUND_KEY = "playoff round"
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