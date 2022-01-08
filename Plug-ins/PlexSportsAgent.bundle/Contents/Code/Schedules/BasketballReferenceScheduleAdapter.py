import re
import datetime

from Constants import *
from Hashes import *
from StringUtils import *
from TimeZoneUtils import *
from BasketballReferenceScheduleScraper import *
from ScheduleEvent import *

def GetSchedule(sched, navigator, sport, league, season):
	# Retrieve data from basketball-reference.com
	brSchedule = ScrapeScheduleForSeason(season)
	
	if brSchedule:
		for dateKey in sorted(brSchedule.keys()):
			for schedEvent in brSchedule[dateKey]:
							
				date = ParseISO8601Date(schedEvent["date"])
				if type(date) == datetime.datetime:
					if date.time():
						date = date.replace(tzinfo=EasternTime).astimezone(tz=UTC)
					else:
						date = date.date()

				homeTeamFullName = deunicode(schedEvent["homeTeam"])
				homeTeam = navigator.GetTeam(season, homeTeamFullName)
				homeTeamKey = homeTeam.key if homeTeam else None

				awayTeamFullName = deunicode(schedEvent["awayTeam"])
				awayTeam = navigator.GetTeam(season, awayTeamFullName)
				awayTeamKey = awayTeam.key if awayTeam else None

				altTitle = None
				altDescription = None
				notes = deunicode(schedEvent.get("notes"))
				if notes and (notes[:3] == "at " or notes[:3] == "in "):
					altTitle = notes
				else:
					altDescription = notes

				kwargs = {
					"sport": sport,
					"league": league,
					"season": season,
					"date": date,
					"BasketballReferenceID": deunicode(schedEvent["id"]),
					"homeTeam": homeTeamKey,
					"homeTeamName": homeTeamFullName if not homeTeamKey else None,
					"awayTeam": awayTeamKey,
					"awayTeamName": awayTeamFullName if not awayTeamKey else None,
					"vs": deunicode(schedEvent.get("vs")),
					"subseason": schedEvent.get("subseason") or NBA_SUBSEASON_FLAG_REGULAR_SEASON,
					"subseasonTitle": deunicode(schedEvent.get("subseasonTitle")),
					"playoffround": schedEvent.get("playoffround"),
					"game": schedEvent.get("game"),
					"altTitle": altTitle,
					"altDescription": altDescription,
					}

				event = ScheduleEvent(**kwargs)
				event = __event_lookaround(sched, event)

				AddOrAugmentEvent(sched, event, 4)



def __correct_abbreviation(abbrev):
	if abbrev.upper() in br_abbreviation_corrections.keys():
		return br_abbreviation_corrections[abbrev.upper()]
	return abbrev.upper()

# Because BasketballReference can get home/away teams backwards sometimes
def __event_lookaround(sched, event):

	origHash = sched_compute_augmentation_hash(event)
	if origHash in sched.keys(): return event

	homeaway = [
		[event.homeTeam, event.awayTeam, event.homeTeamName, event.awayTeamName],
		[event.awayTeam, event.homeTeam, event.awayTeamName, event.homeTeamName]
		]

	for teams in homeaway:
		altEvent = __clone_event(event, homeTeam=teams[0], awayTeam=teams[1], homeTeamName=teams[2], awayTeamName=teams[3])
		hash = sched_compute_augmentation_hash(altEvent)
		if hash in sched.keys(): return altEvent

	return event

def __clone_event(event, **kwargs):

	srcdict = event.__dict__

	if kwargs:
		for key in kwargs.keys():
			if key in srcdict.keys():
				srcdict[key] = kwargs[key]

	altEvent = ScheduleEvent(**srcdict)
	return altEvent
