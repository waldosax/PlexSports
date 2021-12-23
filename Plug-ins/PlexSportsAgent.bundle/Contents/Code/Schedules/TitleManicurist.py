# Python framework
import re
import threading
import datetime
from pprint import pprint

from Constants import *
from RomanNumerals import *
from StringUtils import *
from titlecase import *

from ScheduleEvent import *

__keep_uppercase_expressions = [
	LEAGUE_MLB,
	MLB_LEAGUE_AL + "CS",
	MLB_LEAGUE_AL + "DS",
	MLB_LEAGUE_AL,
	MLB_LEAGUE_NL + "CS",
	MLB_LEAGUE_NL + "DS",
	MLB_LEAGUE_NL,
	LEAGUE_NBA,
	LEAGUE_NFL,
	NFL_CONFERENCE_AFC,
	NFL_CONFERENCE_NFC,
	LEAGUE_NHL,
	roman_numerals_expression
	]

__combine_words_expressions = [
	"Super\s+Bowl"
	]

def Polish(sport, league, season, event):
	title = event.title
	altTitle = event.altTitle
	subseasonTitle = event.subseasonTitle
	description = event.description
	altDescription = event.altDescription

	eventTitle = None

	if subseasonTitle and title and title[:len(subseasonTitle)].upper() != subseasonTitle.upper():
		title = "%s %s" % (subseasonTitle, title)
				
	location = ""
	if altTitle:
		if altTitle.upper()[:3] == "IN " or altTitle.upper()[:3] == "AT ":
			location = titlecase(altTitle[3:].lower())
			m = re.search(r",?\s(?P<state>[A-Z]{2})$", location, re.IGNORECASE)
			if m:
				location = location[:m.start(0)] + ", " + m.group("state").upper()
				pass
			altTitle = altTitle[:3].lower() + location
		else:
			altTitle = titlecase(altTitle.lower())

	if title:
		if title.upper()[:3] == "IN " or title.upper()[:3] == "AT ":
			eventTitle = "Regular Season game played " + title.lower()[:3] + titlecase(title[3:])
		else:
			eventTitle = titlecase(title)

		if location and (title.replace(",", "").upper()[-len(location.replace(",", "")):] != location.replace(",", "").upper() and title.upper().find(location.upper()) < 0):
			eventTitle = eventTitle + " at " + location
		elif not location and altTitle:
			if not __comparable_string(eventTitle).find(__comparable_string(altTitle)) >= 0:
				eventTitle = eventTitle + " " + altTitle
	elif altTitle:
		eventTitle = titlecase(altTitle.lower())

	if eventTitle:
		for expr in __keep_uppercase_expressions:
			pattern = r"\b(%s)\b" % expr
			regex = re.compile(pattern, re.IGNORECASE)
			eventTitle = regex.sub(__keep_uppercase, eventTitle)
		if event.eventTitle and __comparable_string(eventTitle) != __comparable_string(event.eventTitle):
			event.eventTitle = eventTitle + " - " + event.eventTitle
		else:
			event.eventTitle = eventTitle

	if eventTitle and not event.description:
		event.eventTitle = None
		event.description = eventTitle

	if altDescription and not event.description:
		event.description = altDescription
		event.altDescription = None

	if __comparable_string(event.eventTitle) == __comparable_string(subseasonTitle):
		event.eventTitle = None

def __keep_uppercase(m):
	return m.string[m.start(0):m.end(0)].upper()


def __comparable_string(s):
	if s == None: return None
	return strip_to_alphanumeric(s).upper()