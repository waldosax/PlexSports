import re
import datetime

from Constants import *
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


def GetSchedule(sched, teamKeys, teams, sport, league, season):
	# Retrieve data from MLB API
	pfrSchedule = ScrapeScheduleForSeason(season)
	
	if pfrSchedule and pfrSchedule.get("subseasons"):
		for subseason in sorted(pfrSchedule["subseasons"].keys()):
			if pfrSchedule["subseasons"][subseason]:
				for week in sorted(pfrSchedule["subseasons"][subseason].keys()):
					if pfrSchedule["subseasons"][subseason][week].get("events"):
						for key in sorted(pfrSchedule["subseasons"][subseason][week]["events"].keys()):
							schedEvent = pfrSchedule["subseasons"][subseason][week]["events"][key]
							
							__correct_abbreviations(schedEvent)

							date = schedEvent["date"]
							time = schedEvent.get("time")
							if time:
								if isinstance(time, basestring) and IsISO8601Time(time):
									time = ParseISO8601Time(time)
								date = datetime.datetime.combine(date.date(), time)
							date = date.replace(tzinfo=EasternTime).astimezone(tz=UTC)

							kwargs = {
								"sport": sport,
								"league": league,
								"season": season,
								"date": date,
								"ProFootballReferenceID": schedEvent["id"],
								"homeTeam": schedEvent["homeTeam"],
								"awayTeam": schedEvent["awayTeam"],
								"vs": schedEvent["vs"],
								"subseason": schedEvent["subseason"],
								"subseasonTitle": schedEvent.get("subseasonTitle"),
								"playoffround": schedEvent.get("week") if subseason == NFL_SUBSEASON_FLAG_POSTSEASON else None,
								"eventindicator": schedEvent.get("eventindicator") or NFL_EVENT_FLAG_SUPERBOWL if subseason == NFL_SUBSEASON_FLAG_POSTSEASON and week == NFL_PLAYOFF_ROUND_SUPERBOWL else None,
								"eventTitle": schedEvent.get("alias"),
								}

							event = ScheduleEvent(**kwargs)

							AddOrAugmentEvent(sched, event)



PFR_SCHEDULEEVENT_KEY_REGEX = re.compile(r"nfl\d{4}\-\d{8}(?P<team1>\w+)vs(?P<team2>\w+)", re.IGNORECASE)

def __correct_abbreviations_in_key(key):
	m = PFR_SCHEDULEEVENT_KEY_REGEX.match(key)
	if m:
		team1Abbrev = __correct_abbreviation(m.groupdict()["team1"])
		team2Abbrev = __correct_abbreviation(m.groupdict()["team2"])
		return "%s%svs%s" % (key[:m.start(0)], team1Abbrev, team2Abbrev)
	return key

def __correct_abbreviation(abbrev):
	if abbrev.upper() in pfr_abbreviation_corrections.keys():
		return pfr_abbreviation_corrections[abbrev.upper()]
	return abbrev.upper()

def __correct_abbreviations(schedEvent):
	schedEvent["key"] = __correct_abbreviations_in_key(schedEvent["key"])
	schedEvent["homeTeam"] = __correct_abbreviation(schedEvent["homeTeam"])
	schedEvent["awayTeam"] = __correct_abbreviation(schedEvent["awayTeam"])