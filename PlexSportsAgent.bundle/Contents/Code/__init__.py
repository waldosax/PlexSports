import sys

def Start():
    pass


class PlexSportsAgent(Agent.TV_Shows):
    name = 'PlexSportsAgent'
    
    def __init__(self, **kwargs):
        super().__init__()
        self.languages = ['en']
    