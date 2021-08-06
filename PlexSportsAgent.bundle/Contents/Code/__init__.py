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
		for internalSearchResult in internalSearchResults:
			result = MetadataSearchResult(
				id=internalSearchResult[1].key,
				name=known_leagues[internalSearchResult[1].league][0],
				#year=int(internalSearchResult[1].season), # Year is show disambiguator like Archer (2009)
				lang='en',
				score=internalSearchResult[0]
				)
			results.append(result)
			#pprint(result.__dict__)
		pass

	def update(self, metadata, media, lang):



		pass