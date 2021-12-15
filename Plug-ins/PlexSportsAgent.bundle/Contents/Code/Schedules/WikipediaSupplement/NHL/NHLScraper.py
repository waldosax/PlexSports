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

	markup = DownloadAllStarGameSupplement(SPORT_HOCKEY, LEAGUE_NHL, season)
	if markup:
		soup = BeautifulSoup(markup, "html5lib")
		basicInfo = process_basic_info_box(soup)
		if basicInfo:
			supplement.setdefault(NHL_EVENT_FLAG_ALL_STAR_GAME, dict())
			merge_dictionaries(basicInfo, supplement[NHL_EVENT_FLAG_ALL_STAR_GAME])

		supplement.setdefault(NHL_EVENT_FLAG_ALL_STAR_GAME, dict())
		extendedInfo = __process_page(soup, NHL_EVENT_FLAG_ALL_STAR_GAME)
		merge_dictionaries(extendedInfo, supplement)
		if extendedInfo and extendedInfo.get(NHL_EVENT_FLAG_ALL_STAR_GAME) and extendedInfo[NHL_EVENT_FLAG_ALL_STAR_GAME].get("date"): supplement[NHL_EVENT_FLAG_ALL_STAR_GAME]["date"] = extendedInfo[NHL_EVENT_FLAG_ALL_STAR_GAME]["date"]

	markup = DownloadNHLWinterClassicSupplement(SPORT_HOCKEY, LEAGUE_NHL, season)
	if markup:
		soup = BeautifulSoup(markup, "html5lib")
		basicInfo = process_basic_info_box(soup)
		if basicInfo:
			supplement.setdefault(NHL_EVENT_FLAG_WINTER_CLASSIC, dict())
			merge_dictionaries(basicInfo, supplement[NHL_EVENT_FLAG_WINTER_CLASSIC])

		supplement.setdefault(NHL_EVENT_FLAG_WINTER_CLASSIC, dict())
		extendedInfo = __process_page(soup, NHL_EVENT_FLAG_WINTER_CLASSIC)
		merge_dictionaries(extendedInfo, supplement)

	return supplement



def __process_page(soup, ind):
	processed_info = dict()

	selectors = __selectors

	key = ""
	if ind == NHL_EVENT_FLAG_ALL_STAR_GAME : key = "All-Star Game"
	if ind == NHL_EVENT_FLAG_WINTER_CLASSIC : key = "Winter Classic"

	# Capture the IDs of known blocks to process
	tocIDs = __get_toc_ids(soup, key)


	# Get the blurb (1st paragraph) of the All-Star Game recap
	anchorID = None
	blurb = None
	if tocIDs.get("Game Summary"): anchorID = tocIDs["Game Summary"]
	elif tocIDs.get("Game"): anchorID = tocIDs["Game"]
	elif tocIDs.get(key): anchorID = tocIDs[key]
	if anchorID:
		blurb = get_blurb(soup, anchorID)
	if not blurb:
		blurb = get_first_paragraph(soup)
	if blurb:
		processed_info.setdefault(ind, dict())
		processed_info[ind]["description"] = blurb



	return processed_info


def __get_toc_ids(soup, key):
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
				if toc1NodeText.find(key) >= 0:
					tocIDs[key] = a.attrs["href"][1:]
					break

	return tocIDs

