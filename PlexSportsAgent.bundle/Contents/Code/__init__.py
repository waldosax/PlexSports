# Python framework
import sys
from pprint import pprint

from Constants import *
from StringUtils import *
from Teams import *
from Schedules import *

def Start():
    pass


class PlexSportsAgent(Agent.TV_Shows):
    name = 'PlexSportsAgent'
    
    def __init__(self, **kwargs):
        Agent.TV_Shows.__init__(self, **kwargs)
        self.languages = ['en']
    
    def search(self, results, media, lang, manual):

        meta = media.meta   # This is really the divining test. To see if meta persists from Scanner to Agent
        pprint(meta)
        internalSearchResults = Schedules.Find(meta)
        for result in internalSearchResults:
            results.Append(
                MetadataSearchResult(
                    id=result[1].key,
                    name=result.league, #name=known_leagues[result[1].league][0]
                    year=int(result[1].season),
                    lang='en',
                    score=result[0]
                )
            )

        pass

    def update(self, metadata, media, lang):



        pass