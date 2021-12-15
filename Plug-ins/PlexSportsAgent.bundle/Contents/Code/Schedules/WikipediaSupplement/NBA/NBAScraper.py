import re, os, sys
import json
from datetime import datetime, date, time
from dateutil.relativedelta import relativedelta

from bs4 import BeautifulSoup
import bs4
from pprint import pprint

from Constants import *
from Matching import __expressions_from_literal
from TimeZoneUtils import *

from ....Data.WikipediaDownloader import *
from ..WikipediaSupplementUtils import *




# (expressions, event flag)
# Ordered by more specific to less
nba_all_star_saturday_night_expressions = [
	(__expressions_from_literal("3 Point Shootout"), NBA_EVENT_FLAG_3_POINT_SHOOTOUT),
	(__expressions_from_literal("3 Point Competition"), NBA_EVENT_FLAG_3_POINT_SHOOTOUT),
	(__expressions_from_literal("3 Point Contest"), NBA_EVENT_FLAG_3_POINT_SHOOTOUT),
	([r"3%sPoint%sShootout" % (EXPRESSION_SEPARATOR, EXPRESSION_SEPARATOR)], NBA_EVENT_FLAG_3_POINT_SHOOTOUT),
	([r"3%sPoint%sCompetition" % (EXPRESSION_SEPARATOR, EXPRESSION_SEPARATOR)], NBA_EVENT_FLAG_3_POINT_SHOOTOUT),
	([r"3%sPoint%sContest" % (EXPRESSION_SEPARATOR, EXPRESSION_SEPARATOR)], NBA_EVENT_FLAG_3_POINT_SHOOTOUT),
	(__expressions_from_literal("Three Point Shootout"), NBA_EVENT_FLAG_3_POINT_SHOOTOUT),
	(__expressions_from_literal("Three Point Competition"), NBA_EVENT_FLAG_3_POINT_SHOOTOUT),
	(__expressions_from_literal("Three Point Contest"), NBA_EVENT_FLAG_3_POINT_SHOOTOUT),
	([r"Three%sPoint%sShootout" % (EXPRESSION_SEPARATOR, EXPRESSION_SEPARATOR)], NBA_EVENT_FLAG_3_POINT_SHOOTOUT),
	([r"Three%sPoint%sCompetition" % (EXPRESSION_SEPARATOR, EXPRESSION_SEPARATOR)], NBA_EVENT_FLAG_3_POINT_SHOOTOUT),
	([r"Three%sPoint%sContest" % (EXPRESSION_SEPARATOR, EXPRESSION_SEPARATOR)], NBA_EVENT_FLAG_3_POINT_SHOOTOUT),

	(__expressions_from_literal("Slam Dunk Competition"), NBA_EVENT_FLAG_SLAM_DUNK_COMPETITION),
	(__expressions_from_literal("Slam Dunk Contest"), NBA_EVENT_FLAG_SLAM_DUNK_COMPETITION),
	(__expressions_from_literal("AT&T Slam Dunk"), NBA_EVENT_FLAG_SLAM_DUNK_COMPETITION),

	(__expressions_from_literal("Skills Challenge"), NBA_EVENT_FLAG_SKILLS_CHALLENGE),
	(__expressions_from_literal("Skill Challenge"), NBA_EVENT_FLAG_SKILLS_CHALLENGE),

	(__expressions_from_literal("Rising Stars Competition"), NBA_EVENT_FLAG_RISING_STARS_GAME),
	(__expressions_from_literal("Rising Stars Challenge"), NBA_EVENT_FLAG_RISING_STARS_GAME),
	(__expressions_from_literal("Rising Stars Game"), NBA_EVENT_FLAG_RISING_STARS_GAME),
	(__expressions_from_literal("Rising Stars"), NBA_EVENT_FLAG_RISING_STARS_GAME),
	(__expressions_from_literal("Rookie Challenge"), NBA_EVENT_FLAG_RISING_STARS_GAME),

	(__expressions_from_literal("Shooting Stars Competition"), NBA_EVENT_FLAG_SHOOTING_STARS_COMPETITION),
	(__expressions_from_literal("Shooting Stars Contest"), NBA_EVENT_FLAG_SHOOTING_STARS_COMPETITION),
	(__expressions_from_literal("Shooting Stars"), NBA_EVENT_FLAG_SHOOTING_STARS_COMPETITION),

	([r"All-Star%sCelebrity%sGame" % (EXPRESSION_SEPARATOR, EXPRESSION_SEPARATOR)], NBA_EVENT_FLAG_ALL_STAR_CELEBRITY_GAME),
	(__expressions_from_literal("All Star Celebrity Game"), NBA_EVENT_FLAG_ALL_STAR_CELEBRITY_GAME),
	(__expressions_from_literal("Celebrity Game"), NBA_EVENT_FLAG_ALL_STAR_CELEBRITY_GAME),
	]


__selectors = {
	"toc": "div.toc",
	"toc-first-level": "ul > li.toclevel-1",
	"toc-second-level": "ul > li.toclevel-2",
}


def ScrapeAllStarGame(season):
	supplement = dict()

	markup = DownloadAllStarGameSupplement(SPORT_BASKETBALL, LEAGUE_NBA, season)
	if markup:
		soup = BeautifulSoup(markup, "html5lib")
		basicInfo = process_basic_info_box(soup)
		if basicInfo:
			supplement.setdefault(NBA_EVENT_FLAG_ALL_STAR_GAME, dict())
			merge_dictionaries(basicInfo, supplement[NBA_EVENT_FLAG_ALL_STAR_GAME])

		supplement.setdefault(NBA_EVENT_FLAG_ALL_STAR_GAME, dict())
		extendedInfo = __process_page(soup, supplement[NBA_EVENT_FLAG_ALL_STAR_GAME].get("date"))
		merge_dictionaries(extendedInfo, supplement)
		if extendedInfo and extendedInfo.get(NBA_EVENT_FLAG_ALL_STAR_GAME) and extendedInfo[NBA_EVENT_FLAG_ALL_STAR_GAME].get("date"): supplement[NBA_EVENT_FLAG_ALL_STAR_GAME]["date"] = extendedInfo[NBA_EVENT_FLAG_ALL_STAR_GAME]["date"]

	return supplement



def __process_page(soup, allStarGameDate):
	processed_info = dict()

	selectors = __selectors

	# Capture the IDs of known blocks to process
	tocIDs = __get_toc_ids(soup)


	# Get the blurb (1st paragraph) of the All-Star Game recap
	anchorID = None
	blurb = None
	if tocIDs.get(NBA_EVENT_NAME_ALL_STAR_GAME + ":Game"): anchorID = tocIDs[NBA_EVENT_NAME_ALL_STAR_GAME + ":Game"]
	elif tocIDs.get(NBA_EVENT_NAME_ALL_STAR_GAME): anchorID = tocIDs[NBA_EVENT_NAME_ALL_STAR_GAME]
	if anchorID:
		blurb = get_blurb(soup, anchorID)
	if not blurb:
		blurb = get_first_paragraph(soup)
	if blurb:
		processed_info.setdefault(NBA_EVENT_FLAG_ALL_STAR_GAME, dict())
		processed_info[NBA_EVENT_FLAG_ALL_STAR_GAME]["description"] = blurb
		eventDate = __synthesize_event_date_time(allStarGameDate, NBA_EVENT_FLAG_ALL_STAR_GAME)
		processed_info[NBA_EVENT_FLAG_ALL_STAR_GAME]["date"] = eventDate


	# Get anything we can about the All-Star Weekend subsections

	# Get the blurb (1st paragraph) of the 3-Point Shootout recap
	anchorID = tocIDs.get("%s:%s" % (NBA_EVENT_NAME_ALL_STAR_WEEKEND, NBA_EVENT_NAME_3_POINT_SHOOTOUT))
	if anchorID:
		caption = get_section_caption(soup, anchorID)
		blurb = get_blurb(soup, anchorID)
		eventDate = __synthesize_event_date_time(allStarGameDate, NBA_EVENT_FLAG_3_POINT_SHOOTOUT)
		if caption or blurb: processed_info.setdefault(NBA_EVENT_FLAG_3_POINT_SHOOTOUT, dict())
		if caption: processed_info[NBA_EVENT_FLAG_3_POINT_SHOOTOUT]["caption"] = caption
		if blurb: processed_info[NBA_EVENT_FLAG_3_POINT_SHOOTOUT]["description"] = blurb
		if len(processed_info[NBA_EVENT_FLAG_3_POINT_SHOOTOUT]) > 0 and eventDate: processed_info[NBA_EVENT_FLAG_3_POINT_SHOOTOUT]["date"] = eventDate

	# Get the blurb (1st paragraph) of the Slam Dunk Competition recap
	anchorID = tocIDs.get("%s:%s" % (NBA_EVENT_NAME_ALL_STAR_WEEKEND, NBA_EVENT_NAME_SLAM_DUNK_COMPETITION))
	if anchorID:
		caption = get_section_caption(soup, anchorID)
		blurb = get_blurb(soup, anchorID)
		eventDate = __synthesize_event_date_time(allStarGameDate, NBA_EVENT_FLAG_SLAM_DUNK_COMPETITION)
		if caption or blurb: processed_info.setdefault(NBA_EVENT_FLAG_SLAM_DUNK_COMPETITION, dict())
		if caption: processed_info[NBA_EVENT_FLAG_SLAM_DUNK_COMPETITION]["caption"] = caption
		if blurb: processed_info[NBA_EVENT_FLAG_SLAM_DUNK_COMPETITION]["description"] = blurb
		if len(processed_info[NBA_EVENT_FLAG_SLAM_DUNK_COMPETITION]) > 0 and eventDate: processed_info[NBA_EVENT_FLAG_SLAM_DUNK_COMPETITION]["date"] = eventDate

	# Get the blurb (1st paragraph) of the Skills Challenge recap
	anchorID = tocIDs.get("%s:%s" % (NBA_EVENT_NAME_ALL_STAR_WEEKEND, NBA_EVENT_NAME_SKILLS_CHALLENGE))
	if anchorID:
		caption = get_section_caption(soup, anchorID)
		blurb = get_blurb(soup, anchorID)
		eventDate = __synthesize_event_date_time(allStarGameDate, NBA_EVENT_FLAG_SKILLS_CHALLENGE)
		if caption or blurb: processed_info.setdefault(NBA_EVENT_FLAG_SKILLS_CHALLENGE, dict())
		if caption: processed_info[NBA_EVENT_FLAG_SKILLS_CHALLENGE]["caption"] = caption
		if blurb: processed_info[NBA_EVENT_FLAG_SKILLS_CHALLENGE]["description"] = blurb
		if len(processed_info[NBA_EVENT_FLAG_SKILLS_CHALLENGE]) > 0 and eventDate: processed_info[NBA_EVENT_FLAG_SKILLS_CHALLENGE]["date"] = eventDate

	# Get the blurb (1st paragraph) of the Rising Stars Game recap
	anchorID = tocIDs.get("%s:%s" % (NBA_EVENT_NAME_ALL_STAR_WEEKEND, NBA_EVENT_NAME_RISING_STARS_CHALLENGE))
	if anchorID:
		caption = get_section_caption(soup, anchorID)
		blurb = get_blurb(soup, anchorID)
		eventDate = __synthesize_event_date_time(allStarGameDate, NBA_EVENT_FLAG_RISING_STARS_GAME)
		if caption or blurb: processed_info.setdefault(NBA_EVENT_FLAG_RISING_STARS_GAME, dict())
		if caption: processed_info[NBA_EVENT_FLAG_RISING_STARS_GAME]["caption"] = caption
		if blurb: processed_info[NBA_EVENT_FLAG_RISING_STARS_GAME]["description"] = blurb
		if len(processed_info[NBA_EVENT_FLAG_RISING_STARS_GAME]) > 0 and eventDate: processed_info[NBA_EVENT_FLAG_RISING_STARS_GAME]["date"] = eventDate

	# Get the blurb (1st paragraph) of the Shooting Stars Competition recap
	anchorID = tocIDs.get("%s:%s" % (NBA_EVENT_NAME_ALL_STAR_WEEKEND, NBA_EVENT_NAME_SHOOTING_STARS_COMPETITION))
	if anchorID:
		caption = get_section_caption(soup, anchorID)
		blurb = get_blurb(soup, anchorID)
		eventDate = __synthesize_event_date_time(allStarGameDate, NBA_EVENT_FLAG_SHOOTING_STARS_COMPETITION)
		if caption or blurb: processed_info.setdefault(NBA_EVENT_FLAG_SHOOTING_STARS_COMPETITION, dict())
		if caption: processed_info[NBA_EVENT_FLAG_SHOOTING_STARS_COMPETITION]["caption"] = caption
		if blurb: processed_info[NBA_EVENT_FLAG_SHOOTING_STARS_COMPETITION]["description"] = blurb
		if len(processed_info[NBA_EVENT_FLAG_SHOOTING_STARS_COMPETITION]) > 0 and eventDate: processed_info[NBA_EVENT_FLAG_SHOOTING_STARS_COMPETITION]["date"] = eventDate

	# Get the blurb (1st paragraph) of the All-Star Celebrity Game recap
	anchorID = tocIDs.get("%s:%s" % (NBA_EVENT_NAME_ALL_STAR_WEEKEND, NBA_EVENT_NAME_ALL_STAR_CELEBRITY_GAME))
	if anchorID:
		caption = get_section_caption(soup, anchorID)
		blurb = get_blurb(soup, anchorID)
		eventDate = __synthesize_event_date_time(allStarGameDate, NBA_EVENT_FLAG_ALL_STAR_CELEBRITY_GAME)
		if caption or blurb: processed_info.setdefault(NBA_EVENT_FLAG_ALL_STAR_CELEBRITY_GAME, dict())
		if caption: processed_info[NBA_EVENT_FLAG_ALL_STAR_CELEBRITY_GAME]["caption"] = caption
		if blurb: processed_info[NBA_EVENT_FLAG_ALL_STAR_CELEBRITY_GAME]["description"] = blurb
		if len(processed_info[NBA_EVENT_FLAG_ALL_STAR_CELEBRITY_GAME]) > 0 and eventDate: processed_info[NBA_EVENT_FLAG_ALL_STAR_CELEBRITY_GAME]["date"] = eventDate


	return processed_info


def __get_toc_ids(soup):
	tocIDs = dict()

	selectors = __selectors

	toc = soup.select_one(selectors["toc"])
	if not toc: return tocIDs

	toc1Nodes = toc.select(selectors["toc-first-level"]) # li.toclevel-1
	for i in range(0, len(toc1Nodes)):
		listNumber = i + 1
		toc1Node = toc1Nodes[i]

		toc1NodeText = toc1Node.text

		for toc1NodeChild in toc1Node.children:
			if not isinstance(toc1NodeChild, (bs4.Tag)): continue
			if toc1NodeChild.name == "a":
				a = toc1NodeChild
				if not a.attrs["href"][0] == "#": continue
				toc1NodeText = get_toc_link_text(a)
				if listNumber == 1 and toc1NodeText == "All-Star Game": tocIDs[NBA_EVENT_NAME_ALL_STAR_GAME] = a.attrs["href"][1:]

		toc2Nodes = toc1Node.select(selectors["toc-second-level"]) # li.toclevel-2
		if listNumber > 1 and not toc2Nodes: toc2Nodes = [toc1Node]
		for toc2Node in toc2Nodes:
			for toc2NodeChild in toc2Node.children:
				if not isinstance(toc2NodeChild, (bs4.Tag)): continue
				if toc2NodeChild.name == "a":
					a = toc2NodeChild
					if not a.attrs["href"][0] == "#": continue
					toc2NodeText = get_toc_link_text(a)
					if listNumber == 1 and toc2NodeText == "Game": tocIDs[NBA_EVENT_NAME_ALL_STAR_GAME + ":Game"] = a.attrs["href"][1:]
					if listNumber > 1 and (toc1NodeText == "All-Star Weekend" or toc2Node == toc1Node):
						foundEvent = False
						for (exprs, ind) in nba_all_star_saturday_night_expressions:
							if foundEvent == True: break
							for expr in exprs:
								if foundEvent == True: break
								for pattern in [r"^%s$" % expr, r"\b%s\b" % expr]:
									ms = re.findall(pattern, toc2NodeText, re.IGNORECASE)
									if ms:
										foundEvent = True
										tocIDs[("%s:%s" % (NBA_EVENT_NAME_ALL_STAR_WEEKEND, nba_events[ind]))] = a.attrs["href"][1:]
										break

	return tocIDs


def __synthesize_event_date_time(allStarGameDate, eventIndicator):
	if allStarGameDate == None: return None

	# Friday:
	#	7PM: All-Star Celebrity	(Need shedules that provide this and teams that provide this ID)
	#	8PM: Shooting Stars Competition	(Need shedules that provide this and teams that provide this ID)
	#	9PM: Rising Stars		(Need shedules that provide this and teams that provide this ID)
	# Saturday:
	#	8PM: Skills Challenge
	#	9PM: 3-Point Contest
	#	10PM: Slam Dunk Contest
	# Sunday
	#	8PM: All-Star Game	(covered by actual data point, no need to synthesize)

	event_dow_and_times = {
		NBA_EVENT_FLAG_ALL_STAR_GAME: (6, 20),
		NBA_EVENT_FLAG_SKILLS_CHALLENGE: (5, 20),
		NBA_EVENT_FLAG_3_POINT_SHOOTOUT: (5, 21),
		NBA_EVENT_FLAG_SLAM_DUNK_COMPETITION: (5, 22),
		NBA_EVENT_FLAG_ALL_STAR_CELEBRITY_GAME: (4, 19),
		NBA_EVENT_FLAG_RISING_STARS_GAME: (4, 21),
		NBA_EVENT_FLAG_SHOOTING_STARS_COMPETITION: (4, 20),
		}

	if eventIndicator == NBA_EVENT_FLAG_ALL_STAR_GAME:
		if isinstance(allStarGameDate, date): return datetime.datetime.combine(allStarGameDate, datetime.time(event_dow_and_times[eventIndicator][1], 0, 0, tzinfo=EasternTime)).astimezone(UTC)
	else:
		# Rewind to day of week and assign arbitrary time
		stamp = event_dow_and_times[eventIndicator]
		relativeDate = allStarGameDate
		while relativeDate.weekday() != stamp[0]: relativeDate = relativeDate - datetime.timedelta(days=1)
		return datetime.datetime.combine(relativeDate, datetime.time(stamp[1], 0, 0, tzinfo=EasternTime)).astimezone(UTC)


	return None