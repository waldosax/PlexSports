# Boostrap necessary modules for debugging Plex Metadata agent

import os, sys, types, functools
from pprint import pprint

import bootstrapper
import localscanner

from Constants import *

PlexSportsAgent = bootstrapper.BootstrapAgent()



if __name__ == "__main__":
	# argv1 = argv[1]
	# argv1 = "Z:\\Staging\\Sports"
	# argv1 = "L:\\Staging\\Sports"
	argv1 = "F:\\Code\\Plex\\PlexSportsLibrary"

	root = argv1

	league_mins = {
		LEAGUE_MLB: 1920,
		LEAGUE_NBA: 1947,
		LEAGUE_NFL: 1922,
		LEAGUE_NHL: 1920
		}

	#leagues_to_do = known_leagues.keys()
	leagues_to_do = [
		LEAGUE_NFL,
		LEAGUE_NBA,
		LEAGUE_MLB,
		LEAGUE_NHL
		]


	for league in leagues_to_do:
		(leagueName, sport) = known_leagues[league]
	
		#franchises = PlexSportsAgent.Teams.GetFranchises(league)
		maxyear = datetime.datetime.now().year + 2

		for y in range(league_mins[league], maxyear):
			season = str(y)
			#PlexSportsAgent.Schedules.GetSchedule(sport, league, season, computeHashes=False, noLoad=True)
			PlexSportsAgent.Schedules.WikipediaSupplement.Scraper.ScrapeAllStarGame(sport, league, season)
			pass

	pass
