import re, os, sys
import json
from datetime import datetime, date, time
from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup
import bs4
from pprint import pprint
import threading, Queue

from Constants import *
from bs4 import BeautifulSoup
import bs4
from pprint import pprint

from Constants import *
from TimeZoneUtils import *
from Matching import __expressions_from_literal

from Data.WikipediaDownloader import *
from ..WikipediaSupplementUtils import *


__selectors = {
	"toc": "div.toc",
	"toc-first-level": "ul > li.toclevel-1",
	"toc-second-level": "ul > li.toclevel-2",
}

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

	(__expressions_from_literal("Rising Stars Challenge"), NBA_EVENT_FLAG_RISING_STARS_GAME),
	(__expressions_from_literal("Rising Stars Game"), NBA_EVENT_FLAG_RISING_STARS_GAME),
	(__expressions_from_literal("Rising Stars"), NBA_EVENT_FLAG_RISING_STARS_GAME),

	(__expressions_from_literal("Shooting Stars Competition"), NBA_EVENT_FLAG_SHOOTING_STARS_COMPETITION),
	(__expressions_from_literal("Shooting Stars Contest"), NBA_EVENT_FLAG_SHOOTING_STARS_COMPETITION),
	(__expressions_from_literal("Shooting Stars"), NBA_EVENT_FLAG_SHOOTING_STARS_COMPETITION),

	([r"All-Star%sCelebrity%sGame" % (EXPRESSION_SEPARATOR, EXPRESSION_SEPARATOR)], NBA_EVENT_FLAG_ALL_STAR_CELEBRITY_GAME),
	(__expressions_from_literal("All Star Celebrity Game"), NBA_EVENT_FLAG_ALL_STAR_CELEBRITY_GAME),
	(__expressions_from_literal("Celebrity Game"), NBA_EVENT_FLAG_ALL_STAR_CELEBRITY_GAME),
	]


def Process(markup):
	processed_info = dict()

	selectors = __selectors
	if not markup: return processed_info
	soup = BeautifulSoup(markup, "html5lib")

	# Capture the IDs of known blocks to process
	tocIDs = __get_toc_ids(soup)



	# Get the blurb (1st paragraph) of the All-Star Game recap
	anchorID = None
	if tocIDs.get("All-Star Game:Game"): anchorID = tocIDs["All-Star Game:Game"]
	elif tocIDs.get("All-Star Game"): anchorID = tocIDs["All-Star Game"]
	if anchorID:
		blurb = get_blurb(soup, anchorID)
		if blurb:
			processed_info.setdefault(NBA_EVENT_FLAG_ALL_STAR_GAME, dict())
			processed_info[NBA_EVENT_FLAG_ALL_STAR_GAME]["description"] = blurb


	# Get anything we can about the All-Star Weekend subsections

	# Get the blurb (1st paragraph) of the 3-Point Shootout recap
	anchorID = tocIDs.get("All-Star Weekend:3-Point Shootout")
	if anchorID:
		blurb = get_blurb(soup, anchorID)
		if blurb:
			processed_info.setdefault(NBA_EVENT_FLAG_3_POINT_SHOOTOUT, dict())
			processed_info[NBA_EVENT_FLAG_3_POINT_SHOOTOUT]["description"] = blurb

	# Get the blurb (1st paragraph) of the Slam Dunk Competition recap
	anchorID = tocIDs.get("All-Star Weekend:Slam Dunk Competition")
	if anchorID:
		blurb = get_blurb(soup, anchorID)
		if blurb:
			processed_info.setdefault(NBA_EVENT_FLAG_SLAM_DUNK_COMPETITION, dict())
			processed_info[NBA_EVENT_FLAG_SLAM_DUNK_COMPETITION]["description"] = blurb

	# Get the blurb (1st paragraph) of the Skills Challenge recap
	anchorID = tocIDs.get("All-Star Weekend:Skills Challenge")
	if anchorID:
		blurb = get_blurb(soup, anchorID)
		if blurb:
			processed_info.setdefault(NBA_EVENT_FLAG_SKILLS_CHALLENGE, dict())
			processed_info[NBA_EVENT_FLAG_SKILLS_CHALLENGE]["description"] = blurb

	# Get the blurb (1st paragraph) of the Rising Stars Game recap
	anchorID = tocIDs.get("All-Star Weekend:Rising Stars Challenge")
	if anchorID:
		blurb = get_blurb(soup, anchorID)
		if blurb:
			processed_info.setdefault(NBA_EVENT_FLAG_RISING_STARS_GAME, dict())
			processed_info[NBA_EVENT_FLAG_RISING_STARS_GAME]["description"] = blurb

	# Get the blurb (1st paragraph) of the Shooting Stars Competition recap
	anchorID = tocIDs.get("All-Star Weekend:Shooting Stars Competition")
	if anchorID:
		blurb = get_blurb(soup, anchorID)
		if blurb:
			processed_info.setdefault(NBA_EVENT_FLAG_SHOOTING_STARS_COMPETITION, dict())
			processed_info[NBA_EVENT_FLAG_SHOOTING_STARS_COMPETITION]["description"] = blurb

	# Get the blurb (1st paragraph) of the All-Star Celebrity Game recap
	anchorID = tocIDs.get("All-Star Weekend:All-Star Celebrity Game")
	if anchorID:
		blurb = get_blurb(soup, anchorID)
		if blurb:
			processed_info.setdefault(NBA_EVENT_FLAG_ALL_STAR_CELEBRITY_GAME, dict())
			processed_info[NBA_EVENT_FLAG_ALL_STAR_CELEBRITY_GAME]["description"] = blurb


	return processed_info


def __get_toc_ids(soup):
	tocIDs = dict()

	selectors = __selectors

	toc = None
	tocNodes = soup.select(selectors["toc"])
	if tocNodes: toc = tocNodes[0]

	toc1Nodes = toc.select(selectors["toc-first-level"])
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
				if listNumber == 1 and toc1NodeText == "All-Star Game": tocIDs["All-Star Game"] = a.attrs["href"][1:]


		for toc2Node in toc1Node.select(selectors["toc-second-level"]):
			for toc2NodeChild in toc2Node.children:
				if not isinstance(toc2NodeChild, (bs4.Tag)): continue
				if toc2NodeChild.name == "a":
					a = toc2NodeChild
					if not a.attrs["href"][0] == "#": continue
					toc2NodeText = get_toc_link_text(a)
					if listNumber == 1 and toc2NodeText == "Game": tocIDs["All-Star Game:Game"] = a.attrs["href"][1:]
					if listNumber > 1 and toc1NodeText == "All-Star Weekend":
						foundEvent = False
						for (exprs, ind) in nba_all_star_saturday_night_expressions:
							if foundEvent == True: break
							for expr in exprs:
								if foundEvent == True: break
								for pattern in [r"^%s$" % expr, r"\b%s\b" % expr]:
									m = re.findall(pattern, toc2NodeText, re.IGNORECASE)
									if m:
										foundEvent = True

										normalizedName = a.text
										if ind == NBA_EVENT_FLAG_3_POINT_SHOOTOUT: normalizedName = "3-Point Shootout"
										elif ind == NBA_EVENT_FLAG_SLAM_DUNK_COMPETITION: normalizedName = "Slam Dunk Competition"
										elif ind == NBA_EVENT_FLAG_SKILLS_CHALLENGE: normalizedName = "Skills Challenge"
										elif ind == NBA_EVENT_FLAG_RISING_STARS_GAME: normalizedName = "Rising Stars Challenge"
										elif ind == NBA_EVENT_FLAG_SHOOTING_STARS_COMPETITION: normalizedName = "Shooting Stars Competition"
										elif ind == NBA_EVENT_FLAG_ALL_STAR_CELEBRITY_GAME: normalizedName = "All-Star Celebrity Game"
										tocIDs[("All-Star Weekend:%s" % normalizedName)] = a.attrs["href"][1:]

										break






	return tocIDs
