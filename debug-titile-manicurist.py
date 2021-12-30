# Boostrap necessary modules for debugging Plex Metadata agent

import os, sys, types, functools
import re, json, datetime
from pprint import pprint

import bootstrapper
import localscanner

from Constants import *

PlexSportsAgent = bootstrapper.BootstrapAgent()

from Code.Schedules.ScheduleEvent import *


if __name__ == "__main__":

	sport = SPORT_BASEBALL
	league = LEAGUE_MLB
	season = "1999"

	kwargs = {
		"sport": sport,
		"league": league,
		"season": season,
		"date": datetime.datetime(1999, 7, 6, 14, 0, 0),
		"altTitle": None,
		"altDescription": None,
		"description": None,
		"eventTitle": None,
		"subseasonTItle": "League Championship Series",
		"title": "ALCS  (FOX and FS1)",
		"vs": "Houston Astros vs. Boston Red Sox"
		}

	event = ScheduleEvent(**kwargs)

	PlexSportsAgent.Schedules.TitleManicurist.Polish(sport, league, season, event)

	pprint(event)
	pprint({
		"eventTitle": event.eventTitle,
		"description": event.description,
		"notes": event.notes
		})

