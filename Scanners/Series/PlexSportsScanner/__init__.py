# Python framework
import re, os, os.path, random
from pprint import pprint

# Plex native
import Media, VideoFiles, Stack, Utils

# Local package
from Constants import *
from Teams import *
from Metadata import *




def Scan(path, files, mediaList, subdirs, language=None, root=None, **kwargs):
    """"""
    print("Scanning for files at '" + path + "' ...")

    # Scan for video files.
    VideoFiles.Scan(path, files, mediaList, subdirs, root)

    # Iterate over all the files
    for file in files:

        # Extract all the metadata possible from the folder structure/file name
        meta = __discover_metadata(path, file, root)

        if not __is_supported(meta):
            continue

        pprint(meta)
        #show, season, episode, title, year

        # When we introduce event-driven sports like boxing/mma, league becomes irrelevant in favor of sport
        show = meta[METADATA_LEAGUE_KEY]

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


    # See if we need to tie any parted video files (.part1.mp4, .part2.mp4, etc) to a single file
    if files:
        Stack.Scan(path, files, mediaList, subdirs)
        pprint(files)

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

def __synthesize_episode_title(meta):
    return None


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
