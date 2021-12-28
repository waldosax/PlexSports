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
	MLB_LEAGUE_AL + "WC",
	MLB_LEAGUE_AL,
	MLB_LEAGUE_NL + "CS",
	MLB_LEAGUE_NL + "DS",
	MLB_LEAGUE_NL + "WC",
	MLB_LEAGUE_NL,
	"WBC",
	LEAGUE_NBA,
	LEAGUE_NFL,
	NFL_CONFERENCE_AFC,
	NFL_CONFERENCE_NFC,
	LEAGUE_NHL,
	"AM", "PM", "GMT",
	"EST", "EDT", "CST", "CDT",
	"MST", "MDT", "PST", "PDT",
	roman_numerals_expression + "$",
	"JFK",
	"RFK"
	"US"
	r"U\.S\.\s*"
	]

__venue_suffix_words = [
	"PARK",
	"FIELD",
	"FIELD HOUSE",
	"FIELDHOUSE",
	"STADIUM",
	"ARENA",
	"DOME",
	"COMPLEX",
	"COLISEUM",
	]

__event_keywords = [
	"Civil Rights Game",
	"Jackie Robinson Day",
	"Lou Gehrig Day",
	"Roberto Clemente Day",
	"Old Timer's Day",
	"Oldtimer's Day",
	"Opening Day",
	"Opening Night",
	"Home Opener",
	"Classic",
	"World Series",
	"Superbowl",
	"Super Bowl",
	]

__combine_words_expressions = [
	"Super\s+Bowl"
	"Old\s+Timer"
	]

__box_score_expressions = [
	r"(?:^|\b)([a-z0-9\s\-]+)\s+(\d+), ([a-z0-9\s\-]+)\s+(\d+)(?:\b|$)"
	]

__ineligble_keyword_expressions = [
	r"TBD",
	r"PPD",
	r"FOLLOWING",
	r"COMPLETE(?:D?)",
	r"FIRST[\s\.\-_]+PITCH",
	r"DELAY(?:ED)?",
	r"REJOIN(?:ED)?",
	r"JOINED",
	r"SUSPEND(?:ED)?",
	r"SUSP",
	r"POSTPONE(?:D?)",
	r"CANCEL(?:L?(?:ED))?",
	r"CHANGE(?:D?)",
	r"D/N",
	r"DAY[\s\.\-_\/]*NIGHT",
	r"D/H",
	r"DH",
	r"DOUBLE[\s\.\-_]*HEADER",
	r"((?<!World[\s\.\-_])(?<!World))Series",
	r"WS",
	r"ST",
	r"RESUME(?:D?)",
	r"MOVE(?:D?)",
	r"MAEKUP",	# Deliberate because some numbnuts at ESPN can't spell
	r"MAKEUP",
	r"MAKE[\s\.\-_]+UP",
	r"RESCHEDULE(?:D?)",
	r"SCHEDULED\sGAME$",
	r"ORIGINALLY[\s\.\-_]+SCHEDULE(?:D?)",
	r"DST",
	r"DAYLIGHT[\s\.\-_]+SAVING(?:S?)",
	r"UPDATED",
	r"BLACKOUT",
	r"GAME[\s\.\-_]+CALLED",
	r"WAS\s(?:(?:0?[1-9])|(?:[12][0-9])|(?:2[0-4])):\d\d",

	r"(?:(?:1st)|(?:2nd))\sGame",
	r"INTERLEAGUE",
	r"^(?:(?:GAME\s+\d$)|(?:(?:1st|2nd|3rd|4th|5th|6th|7th)\sGAME))$",
	r"^(?:(?:AMERICAN|NATIONAL)\sLEAGUE[\s\-\u0096]*GAME\s\d)$",
	r"^PUERTO\sRICO$",
	r"^TOKYO,\sJAPAN$",
	]

# \u0096 - Unicode hyphen

def __titlecase_x(s):
	if not s: return s

	s = s.lower()
	for expr in __keep_uppercase_expressions:
		pattern = r"(?:^|\b)%s(?:\b|$)" % expr
		regex = re.compile(pattern, re.IGNORECASE)
		s = regex.sub(__keep_uppercase_match, s)

	return titlecase(s)

def __split_on_paren_groups(s):
	if not s: return []
	
	vals = []
	startIndex = 0
	findStartIndex = 0
	depth = 0

	while True:
		if findStartIndex >= len(s): break

		indexOfL = s.find("(", findStartIndex)
		if indexOfL >= findStartIndex:
			depth = depth + 1
			findStartIndex = indexOfL + 1
		else:
			if len(s[startIndex:]) > 0: vals.append(s[startIndex:])
			break


		indexOfR = s.find(")", findStartIndex)
		if indexOfR >= findStartIndex:
			depth = depth - 1
			findStartIndex = indexOfR + 1

			if depth == 0:
				vals.append(s[startIndex:indexOfL])
				vals.append(s[indexOfL:findStartIndex])
				startIndex = findStartIndex
		else:
			vals.append(s[indexOfL:])
			break

	return vals

def __split_on_semicolon(s):
	if not s: return []
	return splitAndTrim(s, ";", True)

def __eligible_value(sport, league, season, s):
	if not s: return s

	nodes = []

	sbps = __split_on_paren_groups(s)
	for sbp in sbps:
		if sbp and sbp[0] == "(":
			shouldSkipNode = False
			for expr in __ineligble_keyword_expressions:
				pattern = r"(?:^|\b)%s(?:\b|^)" % expr
				if re.search(pattern, sbp, re.IGNORECASE):
					shouldSkipNode = True
					break
			if shouldSkipNode: continue
			else:
				nodes.append(__titlecase_x(sbp))
		else:
			sbscs = __split_on_semicolon(sbp)
			for sbsc in sbscs:
				shouldSkipNode = False
				for expr in __ineligble_keyword_expressions:
					pattern = r"(?:^|\b)%s(?:\b|^)" % expr
					if re.search(pattern, sbsc, re.IGNORECASE):
						shouldSkipNode = True
						break
				if shouldSkipNode: continue
				else:
					nodes.append(__titlecase_x(sbsc))


	if len(nodes) == 0: return None
	if len(nodes) == 1: return nodes[0]
	return " ".join(nodes)

def __is_venue(s):
	if not s: return False

	for suffix in __venue_suffix_words:
		if s.upper()[0-len(suffix):] == suffix.upper(): return True

	return False

def __contains_event_keyword(s):
	if not s: return False
	for expr in __event_keywords:
		pattern = r"(?:^|\b)%s(?:\b|$)" % re.escape(expr)
		m = re.search(pattern, s, re.IGNORECASE)
		if m: return True
	return False

def __isolate_location(s):
	if not s: return (s, None)

	firstPart = None
	location = None

	mloc = re.search(r"(?:^|\b)(?:((?:at)|(?:in))\b(.+))$", s, re.IGNORECASE)
	if mloc:
		firstPart = s[:mloc.start(0)].strip(", ")

		location = s[mloc.start(0):mloc.end(0)].lower() + s[mloc.start(1):]
		if location:
			mstate = re.search(r",?\s(?P<state>[A-Z]{2})$", location, re.IGNORECASE)
			if mstate:
				location = location[:mstate.start(0)] + ", " + mstate.group("state").upper()
	else:
		firstPart = s

	return (firstPart, location)

def __isolate_classification(s):
	if not s: return (s, None)

	firstPart = None
	classification = None

	mcls = re.search(r"\s+([\'\"]\w+[\'\"])$", s, re.IGNORECASE)
	if mcls:
		firstPart = s[:mcls.start()].strip()
		classification = s[mcls.start(0):mcls.end(0)]
	else:
		firstPart = s

	return (firstPart, classification)







def __polish_eventTitle(sport, league, season, event):
	title = __eligible_value(sport, league, season, event.title)
	altTitle = __eligible_value(sport, league, season, event.altTitle)
	subseasonTitle = __eligible_value(sport, league, season, event.subseasonTitle)

	eventTitle = event.eventTitle
	if eventTitle: return eventTitle

	if title and __contains_event_keyword(title):
		(xTitle, titLocation) = __isolate_location(title)
		if xTitle:
			(isot, classification) = __isolate_classification(xTitle)
			eventTitle = __titlecase_x(isot)
		else:
			(isot, classification) = __isolate_classification(title)
			eventTitle = __titlecase_x(isot)
		return eventTitle

	if title:
		(xTitle, titLocation) = __isolate_location(title)
		if xTitle:
			(isot, classification) = __isolate_classification(xTitle)
			title = __titlecase_x(isot)
		else:
			(isot, classification) = __isolate_classification(title)
			title = __titlecase_x(isot)

	if subseasonTitle and title:
		if __comparable_string(title).find(__comparable_string(subseasonTitle)) >= 0:
			pass
		elif __comparable_string(subseasonTitle).find(__comparable_string(title)) >= 0:
			title = subseasonTitle
		else:
			if __is_venue(title):
				title = "%s at %s" % (subseasonTitle, title)
			else:
				title = "%s %s" % (subseasonTitle, title)
				
	altLocation = ""
	titLocation = ""
	location = ""
	if altTitle:
		(xAltTitle, altLocation) = __isolate_location(altTitle)
		if xAltTitle:
			altTitle = xAltTitle

	if title:
		(xTitle, titLocation) = __isolate_location(title)
		if xTitle:
			eventTitle = xTitle

	elif altTitle:
		eventTitle = altTitle

	if eventTitle:
		eventTitle = __titlecase_x(eventTitle)

	return eventTitle

def __polish_description(sport, league, season, event):
	description = event.description
	altDescription = event.altDescription
	if not description: description = altDescription
	elif altDescription: description = description + ", " + altDescription
	if not description: return None

	description = description.replace("\r\n", " ")
	description = description.replace("\r", " ")
	description = description.replace("\n", " ")
	description = description.replace("  ", " ")

	return description

def __polish_notes(sport, league, season, event):
	notes = []
	
	title = event.title
	altTitle = event.altTitle
	subseasonTitle = event.subseasonTitle
	eventTitle = event.eventTitle
	altDescription = event.altDescription

	if eventTitle: notes.append(eventTitle)
	if title and (title.upper()[:3] == "IN " or title.upper()[:3] == "AT "):
		if subseasonTitle:
			notes.append("%s %s%s" % (subseasonTitle, title[:3].lower(), title[3:]))
		else:
			notes.append("Regular Season game played  %s%s" % (title[:3].lower(), title[3:]))
	else:
		if title and subseasonTitle:
			if __comparable_string(title).find(__comparable_string(subseasonTitle)) >= 0:
				notes.append(title)
			elif __comparable_string(subseasonTitle).find(__comparable_string(title)) >= 0:
				notes.append(subseasonTitle)
			else:
				notes.append(subseasonTitle)
				notes.append(title)
		else:
			if subseasonTitle: notes.append(subseasonTitle)
			if title: notes.append(title)
	if altTitle: notes.append(altTitle)
	if altDescription: notes.append(altDescription)

	notesStr = ""
	for note in notes:
		if notesStr: notesStr = notesStr + ", "
		notesStr = notesStr + note

	if not notesStr: return None
	return notesStr




def Polish(sport, league, season, event):

	subseasonTitle = event.subseasonTitle
	notes = __polish_notes(sport, league, season, event)
	eventTitle = __polish_eventTitle(sport, league, season, event)
	description = __polish_description(sport, league, season, event)


	# Notes is notes. Notes is ALWAYS Notes except when
	#	notes is eventTitle, or
	#	notes is description, or
	#	notes is subseasonTitle

	if notes and __comparable_string(notes) == __comparable_string(eventTitle):
		notes = None
	elif notes and __comparable_string(notes) == __comparable_string(description):
		notes = None
	elif notes and __comparable_string(notes) == __comparable_string(subseasonTitle):
		notes = None


	# If eventTitle is just subseasonTitle
	#	unless eventTitle contains a title keyword,
	#	eventTitle is null

	if eventTitle:
		if __comparable_string(eventTitle) == __comparable_string(subseasonTitle):
			if not __contains_event_keyword(eventTitle):
				eventTitle = None
		elif eventTitle[:3].upper() == "AT " or eventTitle[:3].upper() == "IN ":
			eventTitle = None


	# If description is eventTitle
	#	description is null

	if eventTitle and __comparable_string(eventTitle) == __comparable_string(description):
		description = None


	if notes and  not description:
		description = notes


	if not event.eventTitle: event.eventTitle = eventTitle
	event.subseasonTitle = subseasonTitle
	event.description = description
	event.notes = notes

def __keep_uppercase_match(m):
	return m.string[m.start(0):m.end(0)].upper()


def __comparable_string(s):
	if s == None: return None
	return strip_to_alphanumeric(s).upper()