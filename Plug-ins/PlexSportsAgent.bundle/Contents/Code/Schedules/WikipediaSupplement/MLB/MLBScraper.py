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



__selectors = {
	"toc": "div.toc",
	"toc-first-level": "ul > li.toclevel-1",
	"toc-second-level": "ul > li.toclevel-2",
}


def ScrapeAllStarGame(season):
	supplement = dict()

	markup = DownloadAllStarGameSupplement(SPORT_BASEBALL, LEAGUE_MLB, season)
	if markup:
		soup = BeautifulSoup(markup, "html5lib")
		basicInfo = process_basic_info_box(soup)
		if basicInfo:
			supplement.setdefault(MLB_EVENT_FLAG_ALL_STAR_GAME, dict())
			merge_dictionaries(basicInfo, supplement[MLB_EVENT_FLAG_ALL_STAR_GAME])

		supplement.setdefault(MLB_EVENT_FLAG_ALL_STAR_GAME, dict())
		extendedInfo = __process_all_star_page(soup, supplement[MLB_EVENT_FLAG_ALL_STAR_GAME].get("date"))
		merge_dictionaries(extendedInfo, supplement)
		if extendedInfo and extendedInfo.get(MLB_EVENT_FLAG_ALL_STAR_GAME) and extendedInfo[MLB_EVENT_FLAG_ALL_STAR_GAME].get("date"): supplement[MLB_EVENT_FLAG_ALL_STAR_GAME]["date"] = extendedInfo[MLB_EVENT_FLAG_ALL_STAR_GAME]["date"]

	markup = DownloadMLBHomeRunDerbySupplement(SPORT_BASEBALL, LEAGUE_MLB, season)
	if markup:
		soup = BeautifulSoup(markup, "html5lib")
		basicInfo = process_basic_info_box(soup)
		if basicInfo:
			supplement.setdefault(MLB_EVENT_FLAG_HOME_RUN_DERBY, dict())
			merge_dictionaries(basicInfo, supplement[MLB_EVENT_FLAG_HOME_RUN_DERBY])

		supplement.setdefault(MLB_EVENT_FLAG_HOME_RUN_DERBY, dict())
		extendedInfo = __process_home_run_derby_page(soup)
		merge_dictionaries(extendedInfo, supplement)

	return supplement



def __process_all_star_page(soup, allStarGameDate):
	processed_info = dict()

	selectors = __selectors

	# Capture the IDs of known blocks to process
	tocIDs = __get_toc_ids(soup)


	# Get the blurb (1st paragraph) of the All-Star Game recap
	anchorID = None
	blurb = None
	if tocIDs.get("All-Star Game:Game Summary"): anchorID = tocIDs["All-Star Game:Game Summary"]
	elif tocIDs.get("All-Star Game:Game"): anchorID = tocIDs["All-Star Game:Game"]
	elif tocIDs.get("All-Star Game"): anchorID = tocIDs["All-Star Game"]
	if anchorID:
		blurb = get_blurb(soup, anchorID)
	if not blurb:
		blurb = get_first_paragraph(soup)
	if blurb:
		processed_info.setdefault(MLB_EVENT_FLAG_ALL_STAR_GAME, dict())
		processed_info[MLB_EVENT_FLAG_ALL_STAR_GAME]["description"] = blurb



	return processed_info

def __process_home_run_derby_page(soup):
	processed_info = dict()

	# Get the blurb (1st paragraph) of the Home Run Derby recap
	anchorID = None
	blurb = get_first_paragraph(soup)
	if blurb:
		processed_info.setdefault(MLB_EVENT_FLAG_HOME_RUN_DERBY, dict())
		processed_info[MLB_EVENT_FLAG_HOME_RUN_DERBY]["description"] = blurb

	return processed_info


def __get_toc_ids(soup):
	tocIDs = dict()

	selectors = __selectors

	toc = soup.select_one(selectors["toc"])
	if not toc: return tocIDs

	toc1Nodes = toc.select(selectors["toc-first-level"]) # li.toclevel-1
	for i in range(0, len(toc1Nodes)):
		toc1Node = toc1Nodes[i]

		toc1NodeText = toc1Node.text

		for toc1NodeChild in toc1Node.children:
			if not isinstance(toc1NodeChild, (bs4.Tag)): continue
			if toc1NodeChild.name == "a":
				a = toc1NodeChild
				if not a.attrs["href"][0] == "#": continue
				toc1NodeText = get_toc_link_text(a)
				if toc1NodeText == "Game summary":
					tocIDs["All-Star Game:Game Summary"] = a.attrs["href"][1:]
					break
				if toc1NodeText == "Game":
					tocIDs["All-Star Game:Game"] = a.attrs["href"][1:]
					break
				if toc1NodeText.find("All-Star Game") >= 0:
					tocIDs["All-Star Game"] = a.attrs["href"][1:]
					break

	return tocIDs

