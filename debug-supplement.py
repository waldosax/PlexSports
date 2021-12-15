# Boostrap necessary modules for debugging Plex Metadata agent

import os, sys, types, functools
from pprint import pprint

import bootstrapper
import localscanner

from Constants import *

PlexSportsAgent = bootstrapper.BootstrapAgent()



if __name__ == "__main__":
	
	#PlexSportsAgent.Schedules.WikipediaSupplement.Scraper.ScrapeAllStarGame(SPORT_BASEBALL, LEAGUE_MLB, 2017, True)
	#PlexSportsAgent.Schedules.WikipediaSupplement.Scraper.ScrapeAllStarGame(SPORT_BASKETBALL, LEAGUE_NBA, 2011, True)
	#PlexSportsAgent.Schedules.WikipediaSupplement.Scraper.ScrapeAllStarGame(SPORT_BASKETBALL, LEAGUE_NBA, 1996)
	#PlexSportsAgent.Schedules.WikipediaSupplement.Scraper.ScrapeAllStarGame(SPORT_FOOTBALL, LEAGUE_NFL, 2019, True)
	PlexSportsAgent.Schedules.WikipediaSupplement.Scraper.ScrapeAllStarGame(SPORT_HOCKEY, LEAGUE_NHL, 2007, True)

	pass
