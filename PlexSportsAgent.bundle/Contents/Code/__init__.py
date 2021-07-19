# Python framework
import sys
from pprint import pprint

from Constants import *
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

        Schedules.foo()
        pass

    def update(self, metadata, media, lang):
        pass