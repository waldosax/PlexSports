import re
import datetime

from Constants import *
from Hashes import *
from StringUtils import *
from TimeZoneUtils import *
from ProFootballReferenceScheduleScraper import *
from ScheduleEvent import *


pfr_abbreviation_corrections = {
	"CRD": "ARI",
	"RAV": "BAL",
	"BBA": "BUF",
	"GNB": "GB",
	"HTX": "HOU",
	"CLT": "IND",
	"KAN": "KC",
	"RAI": "LV",
	"SDG": "LAC",
	"RAM": "LAR",
	"NWE": "NE",
	"NOR": "NO",
	"SFO": "SF",
	"TAM": "TB",
	"OTI": "TEN"
	}


def GetSchedule(sched, navigator, sport, league, season):
	# Retrieve data from pro-foorball-reference
	pfrSchedule = ScrapeScheduleForSeason(season)
	
	if pfrSchedule and pfrSchedule.get("subseasons"):
		for subseason in sorted(pfrSchedule["subseasons"].keys()):
			if pfrSchedule["subseasons"][subseason]:
				for week in sorted(pfrSchedule["subseasons"][subseason].keys()):
					if pfrSchedule["subseasons"][subseason][week].get("events"):
						for key in sorted(pfrSchedule["subseasons"][subseason][week]["events"].keys()):
							schedEvent = pfrSchedule["subseasons"][subseason][week]["events"][key]
							
							date = schedEvent["date"]
							time = schedEvent.get("time")
							if time:
								if isinstance(time, basestring) and IsISO8601Time(time):
									time = ParseISO8601Time(time)
								date = datetime.datetime.combine(date.date(), time)
								date = date.replace(tzinfo=EasternTime).astimezone(tz=UTC)
							elif type(date) == datetime.datetime:
								date = date.date()

							homeTeamFullName = deunicode(schedEvent["homeTeam"])
							homeTeamAbbrev = __correct_abbreviation(deunicode(schedEvent["homeTeamAbbrev"]))
							homeTeam = navigator.GetTeam(season, homeTeamFullName, abbreviation=homeTeamAbbrev)
							homeTeamKey = homeTeam.key if homeTeam else create_scannable_key(homeTeamFullName)

							awayTeamFullName = deunicode(schedEvent["awayTeam"])
							awayTeamAbbrev = __correct_abbreviation(deunicode(schedEvent["awayTeamAbbrev"]))
							awayTeam = navigator.GetTeam(season, awayTeamFullName, abbreviation=awayTeamAbbrev)
							awayTeamKey = awayTeam.key if awayTeam else create_scannable_key(awayTeamFullName)

							kwargs = {
								"sport": sport,
								"league": league,
								"season": season,
								"date": date,
								"ProFootballReferenceID": deunicode(schedEvent["id"]),
								"homeTeam": homeTeamKey,
								"homeTeamName": homeTeamFullName if not homeTeamKey else None,
								"awayTeam": awayTeamKey,
								"awayTeamName": awayTeamFullName if not awayTeamKey else None,
								"vs": deunicode(schedEvent["vs"]),
								"subseason": schedEvent["subseason"],
								"subseasonTitle": deunicode(schedEvent.get("subseasonTitle")),
								"week": schedEvent.get("week") if schedEvent["subseason"] != NFL_SUBSEASON_FLAG_POSTSEASON else None,
								"playoffround": schedEvent.get("week") if schedEvent["subseason"] == NFL_SUBSEASON_FLAG_POSTSEASON else None,
								"eventindicator": schedEvent.get("eventindicator") or NFL_EVENT_FLAG_SUPERBOWL if schedEvent["subseason"] == NFL_SUBSEASON_FLAG_POSTSEASON and schedEvent.get("week") == NFL_PLAYOFF_ROUND_SUPERBOWL else None,
								"eventTitle": deunicode(schedEvent.get("alias")),
								}

							event = ScheduleEvent(**kwargs)
							event = __event_lookaround(sched, event)

							AddOrAugmentEvent(sched, event)



def __correct_abbreviation(abbrev):
	if abbrev.upper() in pfr_abbreviation_corrections.keys():
		return pfr_abbreviation_corrections[abbrev.upper()]
	return abbrev.upper()

# Because ProFootballReference can get home/away teams backwards sometimes
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
