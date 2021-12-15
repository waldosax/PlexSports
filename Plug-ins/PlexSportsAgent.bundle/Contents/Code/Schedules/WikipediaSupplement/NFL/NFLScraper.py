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


def ScrapeProBowl(season):
	supplement = dict()

	markup = DownloadAllStarGameSupplement(SPORT_FOOTBALL, LEAGUE_NFL, season)
	if markup:
		soup = BeautifulSoup(markup, "html5lib")
		basicInfo = process_basic_info_box(soup)
		if basicInfo:
			supplement.setdefault(NFL_EVENT_FLAG_PRO_BOWL, dict())
			merge_dictionaries(basicInfo, supplement[NFL_EVENT_FLAG_PRO_BOWL])

		supplement.setdefault(NFL_EVENT_FLAG_PRO_BOWL, dict())
		extendedInfo = __process_page(soup, supplement[NFL_EVENT_FLAG_PRO_BOWL].get("date"))
		merge_dictionaries(extendedInfo, supplement)
		if extendedInfo and extendedInfo.get(NFL_EVENT_FLAG_PRO_BOWL) and extendedInfo[NFL_EVENT_FLAG_PRO_BOWL].get("date"): supplement[NFL_EVENT_FLAG_PRO_BOWL]["date"] = extendedInfo[NFL_EVENT_FLAG_PRO_BOWL]["date"]

	return supplement



def __process_page(soup, allStarGameDate):
	processed_info = dict()

	selectors = __selectors

	# Capture the IDs of known blocks to process
	tocIDs = __get_toc_ids(soup)


	# Get the blurb (1st paragraph) of the All-Star Game recap
	anchorID = None
	blurb = None
	if tocIDs.get("Pro Bowl:Game Summary"): anchorID = tocIDs["Pro Bowl:Game Summary"]
	elif tocIDs.get("Pro Bowl:Game"): anchorID = tocIDs["Pro Bowl:Game"]
	elif tocIDs.get("Pro Bowl"): anchorID = tocIDs["Pro Bowl"]
	if anchorID:
		blurb = get_blurb(soup, anchorID)
	if not blurb:
		blurb = get_first_paragraph(soup)
	if blurb:
		processed_info.setdefault(NFL_EVENT_FLAG_PRO_BOWL, dict())
		processed_info[NFL_EVENT_FLAG_PRO_BOWL]["description"] = blurb



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
					tocIDs["Pro Bowl:Game Summary"] = a.attrs["href"][1:]
					break
				if toc1NodeText == "Game":
					tocIDs["Pro Bowl:Game"] = a.attrs["href"][1:]
					break
				if toc1NodeText.find("Pro Bowl") >= 0:
					tocIDs["Pro Bowl"] = a.attrs["href"][1:]
					break

	return tocIDs

