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
		"date": datetime.datetime(2020, 9, 30, 14, 0, 0),
		"altTitle": "NLWC - GAME 1",
		"altDescription": None,
		"description": "Freddie Freeman singled home the winning run in the 13th inning, finally ending the longest scoreless duel in postseason history as the Atlanta Braves defeated the Cincinnati Reds 1-0 in the opener of their NL wild-card series on Wednesday.",
		"eventTitle": None,
		"subseasonTitle": "Wild Card Game",
		"title": "NL Wild Card 'B'",
		"vs": "Atlanta Braves vs. Cincinnati Reds"
		}

	event = ScheduleEvent(**kwargs)

	PlexSportsAgent.Schedules.TitleManicurist.Polish(sport, league, season, event)

	pprint(event)
	pprint({
		"eventTitle": event.eventTitle,
		"description": event.description,
		"notes": event.notes
		})

