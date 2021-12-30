# Boostrap necessary modules for debugging Plex Metadata agent

import os, sys, types, functools
import re, json, datetime
from pprint import pprint

import bootstrapper
import localscanner

from Constants import *

PlexSportsAgent = bootstrapper.BootstrapAgent()

from Code.Schedules.ScheduleEvent import *
#from Code.Schedules.MLBAPIScheduleAdapter import *
from Code.Schedules.MLBAPIScheduleAdapter import __process_content as __mlb_process_content
from Code.Schedules.MLBAPIScheduleAdapter import DownloadGameContentData as __mlb_DownloadGameContentData
from Code.Schedules.NHLAPIScheduleAdapter import __process_content as __nhl_process_content
from Code.Schedules.NHLAPIScheduleAdapter import DownloadGameContentData as __nhl_DownloadGameContentData


if __name__ == "__main__":

	__leagues = [ LEAGUE_MLB, LEAGUE_NHL ]
	
	for league in __league:
		(leagueName, sport) = known_leagues[league]

		minSeason = None
		minDate = None
	
		maxyear = datetime.datetime.now().year + 1

		for y in range(2021, maxyear, 1):
			season = str(y)

			sched = PlexSportsAgent.Schedules.GetSchedule(sport, league, season, computeHashes=False, noLoad=False)
		
			for daysEvents in sched.values():
				for schedEvent in daysEvents.values():
					date = schedEvent.date
					id = None
					downloadGameContentData = None
					processContent = None

					if league == LEAGUE_MLB:
						id = schedEvent.identity.MLBAPIID
						downloadGameContentData = __mlb_DownloadGameContentData
						processContent = __mlb_process_content
					elif league == LEAGUE_NHL:
						id = schedEvent.identity.NHLAPIID
						downloadGameContentData = __nhl_DownloadGameContentData
						processContent = __nhl_process_content

					if not id: continue

					contentJson = downloadGameContentData(id)
					if not contentJson: continue

					try: content = json.loads(contentJson)
					except ValueError: continue

					(description, thumbnail) = processContent(schedEvent, content)

					if description == None and thumbnail == None: continue

					if minDate == None:
						minDate = date
						minSeason = season
					elif date < minDate:
						minDate = date
						minSeason = season

			PlexSportsAgent.Schedules.cached_schedules = dict()
			PlexSportsAgent.Schedules.event_scan = dict()

		print("Earliest content season for %s: %s (%s)" % (league, minSeason, minDate))
