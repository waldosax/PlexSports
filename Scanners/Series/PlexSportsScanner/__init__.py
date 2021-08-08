# Python framework
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import re, os, os.path, random
from pprint import pprint

# Plex native
import Media, VideoFiles, Stack, Utils

# Local package
from Constants import *
from Matching import *
from StringUtils import *
from Teams import *
from Metadata import *




def Scan(path, files, mediaList, subdirs, language=None, root=None, **kwargs):
    """"""
    #print("Scanning for files at '" + path + "' ...")

    # Scan for video files.
    VideoFiles.Scan(path, files, mediaList, subdirs, root)

    # Iterate over all the files
    for file in files:

        # Extract all the metadata possible from the folder structure/file name
        meta = __discover_metadata(path, file, root)

        if not __is_supported(meta):
            continue

        #print(file)
        #pprint(meta)
        #show, season, episode, title, year

        # Synthesize show name (league/sport)
        show = __synthesize_show_name(meta)

        season = 0
        if meta.get(METADATA_SEASON_BEGIN_YEAR_KEY):
            season = meta[METADATA_SEASON_BEGIN_YEAR_KEY]
        elif meta.get(METADATA_AIRDATE_KEY):
            season = meta[METADATA_AIRDATE_KEY].year

        # We'll see how episode and display_offset is affected by organization
        episode = 0
        display_offset = 1

        # We'll re-synthesize title in the agent, when we've hydrated all the information
        title = __synthesize_episode_title(meta)

        # Year is used as a disambiguator between shows (in this case leagues, so unnecessary)
        year = None

        sporting_event = SportingEvent(show, season, episode, title, year, meta)
        sporting_event.display_offset = display_offset
        sporting_event.parts.append(file)
        mediaList.append(sporting_event)
        #pprint(mediaList)
        #print(show)
        #print(title)
        #print("")


    # See if we need to tie any parted video files (.part1.mp4, .part2.mp4, etc) to a single file
    if files:
        Stack.Scan(path, files, mediaList, subdirs)
        #pprint(files)

def __get_relative_path(path, file, root):
    relPath = os.path.relpath(file, root) if root else path + os.path.basename(file) if os.path.isabs(path) == False else os.path.relPath(file, path)
    return relPath

def __discover_metadata(path, file, root):
    """Learn everything we can learn from the folder/file structure."""
    meta = dict()
    relPath = __get_relative_path(path, file, root)

    Metadata.Infer(relPath, file, meta)

    return meta

def __is_supported(meta):
    if not meta:
        return False
    
    # For now, enforce that there is both a sport and a league
    # When we introduce event-driven sports like boxing/mma, league becomes irrelevant

    sport = meta.get(METADATA_SPORT_KEY)
    if not sport:
        return False
    if not sport in supported_sports:
        return False

    league = meta.get(METADATA_LEAGUE_KEY)
    if not league:
        return False
    if league not in known_leagues.keys():
        return False

    return True

# MLB Baseball
# NBA Basketball
# NFL Football
# NHL Hockey
# Boxing
# UFC
def __synthesize_show_name(meta):
    # When we introduce event-driven sports like boxing/mma, league becomes irrelevant in favor of sport
    show = sport = meta[METADATA_SPORT_KEY]
    league = meta.get(METADATA_LEAGUE_KEY)
    if league and league in known_leagues.keys():
        sport = known_leagues[league][1]
        show = league + " " + sport
    return show


# 4/5/2009 - {HOME_TEAM} vs. {AWAY_TEAM}, Game 1
# 4/5/2009 - Preseason - {WEEK}, {HOME_TEAM} vs. {AWAY_TEAM}
# 4/5/2009 - Playoffs - {ROUND}, Game 7, {HOME_TEAM} vs. {AWAY_TEAM}
# 4/5/2009 - ALDS, Game 7, {HOME_TEAM} vs. {AWAY_TEAM}
# 4/5/2009 - Superbowl LII, {HOME_TEAM} vs. {AWAY_TEAM}
def __synthesize_episode_title(meta):

    sport = meta[METADATA_SPORT_KEY]
    league = meta[METADATA_LEAGUE_KEY]
    season = (str(meta[METADATA_SEASON_BEGIN_YEAR_KEY]) if meta.get(METADATA_SEASON_BEGIN_YEAR_KEY) else meta.get(METADATA_SEASON_KEY) or "")
    title = ""
    hasAirdate = False
    hasPrefix = False
    hasGameIndicator = False

    if meta.get(METADATA_AIRDATE_KEY):
        airdate = meta[METADATA_AIRDATE_KEY]
        title += "%s/%s/%s" % (airdate.month, airdate.day, airdate.year)
        hasAirdate = True

    if meta.get(METADATA_SUBSEASON_INDICATOR_KEY):
        ind = meta.get(METADATA_SUBSEASON_INDICATOR_KEY)
        if meta.get(METADATA_EVENT_INDICATOR_KEY): # Single-game, named events
            if title: title += " - "
            title += meta[METADATA_EVENT_NAME_KEY]
            hasPrefix = True
        else:
            if ind == -1:
                if title: title += " - "
                title += "Preseason"
                if meta.get(METADATA_WEEK_NUMBER_KEY) != None:
                    title += " - Week %s" % meta[METADATA_WEEK_NUMBER_KEY]
            elif ind == 0 or ind == None:
                if meta.get(METADATA_WEEK_NUMBER_KEY) != None:
                    if title: title += " - "
                    title += "Week %s" % meta[METADATA_WEEK_NUMBER_KEY]
            elif ind == 1:
                if title: title += " - "
                if (meta.get(METADATA_EVENT_NAME_KEY)):
                    if season: title += season + " "
                    title += meta[METADATA_EVENT_NAME_KEY]
                elif (meta.get(METADATA_PLAYOFF_ROUND_KEY)):
                    if season: title += season + " "
                    title += "Playoffs - Round " + meta[METADATA_PLAYOFF_ROUND_KEY]
                if sport in supported_series_sports and meta.get(METADATA_GAME_NUMBER_KEY):
                    if title: title += ", "
                    title += "Game " + meta[METADATA_GAME_NUMBER_KEY]
                    hasGameIndicator = True
            hasPrefix = True
    elif meta.get(METADATA_EVENT_INDICATOR_KEY): # Single-game, named events
        if title: title += " - "
        if season: title += season + " "
        title += meta[METADATA_EVENT_NAME_KEY]
        hasPrefix = True

    if sport in supported_team_sports and league in known_leagues:
        homeTeam = meta.get(METADATA_HOME_TEAM_KEY)
        awayTeam = meta.get(METADATA_AWAY_TEAM_KEY)
        homeTeamKey = Matching.__strip_to_alphanumeric(meta.get(METADATA_HOME_TEAM_KEY))
        awayTeamKey = Matching.__strip_to_alphanumeric(meta.get(METADATA_AWAY_TEAM_KEY))

        teams = Teams.GetTeams(league)
        keys = Teams.cached_team_keys[league]
        if teams:
            if homeTeamKey in keys: homeTeam = teams[keys[homeTeamKey]].FullName
            if awayTeamKey in keys: awayTeam = teams[keys[awayTeamKey]].FullName

            if homeTeam:
                if title: title += ", " if hasPrefix else " - " if hasAirdate else ""
                title += homeTeam
                if awayTeam:
                    title += " vs. " + awayTeam
            elif awayTeam:
                if title: title += ", " if hasPrefix else " - " if hasAirdate else ""
                title += awayTeam

    if not hasGameIndicator and meta.get(METADATA_GAME_NUMBER_KEY):
        if title: title += ", "
        title += "Game " + str(meta[METADATA_GAME_NUMBER_KEY])
        hasGameIndicator = True

    return title


class SportingEvent(Media.MediaRoot):
    def __init__(self, show, season, episode, title=None, year=None, meta=None):
        Media.MediaRoot.__init__(self, 'SportingEvent') # Episode
        self.show = show
        self.season = season
        self.episode = episode
        self.name = title
        self.year = year
        self.episodic = True
        self.meta = meta or dict()
