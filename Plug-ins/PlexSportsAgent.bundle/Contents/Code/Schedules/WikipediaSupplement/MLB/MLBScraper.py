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


__cached_hof_games = {}

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

	if season in __cached_hof_games.keys():
		extendedInfo = __cached_hof_games[season]
		merge_dictionaries(extendedInfo, supplement)
	elif len(__cached_hof_games) == 0:
		markup = DownloadMLBHallOfFameGameSupplement(SPORT_BASEBALL, LEAGUE_MLB, season)
		if markup:
			soup = BeautifulSoup(markup, "html5lib")
			hof_games = __process_hof_game_page(soup)
			merge_dictionaries(hof_games, __cached_hof_games)
	if season in __cached_hof_games.keys():
		supplement.setdefault(MLB_EVENT_FLAG_HALL_OF_FAME, dict())
		extendedInfo = __cached_hof_games[season]
		merge_dictionaries(extendedInfo, supplement)

	return supplement



def __process_all_star_page(soup, allStarGameDate):
	processed_info = dict()

	selectors = __selectors

	# Capture the IDs of known blocks to process
	tocIDs = __get_all_star_toc_ids(soup)


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


def __get_all_star_toc_ids(soup):
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

def __get_hof_toc_ids(soup):
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

		toc2Nodes = toc1Node.select(selectors["toc-second-level"]) # li.toclevel-2
		if listNumber > 1 and not toc2Nodes: toc2Nodes = [toc1Node]
		for toc2Node in toc2Nodes:
			for toc2NodeChild in toc2Node.children:
				if not isinstance(toc2NodeChild, (bs4.Tag)): continue
				if toc2NodeChild.name == "a":
					a = toc2NodeChild
					if not a.attrs["href"][0] == "#": continue
					toc2NodeText = get_toc_link_text(a)
					if listNumber == 1 and toc2NodeText == "Results": tocIDs["HOF Game:Results"] = a.attrs["href"][1:]
					else:
						break
	return tocIDs

def __process_hof_game_page(soup):
	processed_info = dict()

	selectors = __selectors

	# Capture the IDs of known blocks to process
	tocIDs = __get_hof_toc_ids(soup)

	# Get the results table and categorize each applicable year
	anchorID = None
	if tocIDs.get("HOF Game:Results"): anchorID = tocIDs["HOF Game:Results"]

	anchorPoint = None
	heading = None
	legend = None
	resultsTable = None
	if anchorID: anchorPoint = soup.find(id=anchorID)
	if anchorPoint: heading = anchorPoint.parent
	if heading:
		for sibling in heading.find_next_siblings():
			if not isinstance(sibling, bs4.Tag): continue
			if sibling.name == heading.name: break;
			if sibling.name == "table":
				if not sibling.attrs["class"] or "wikitable" not in sibling.attrs["class"]: continue
				if legend == None:
					legend = sibling
					continue
				if legend != None:
					resultsTable = sibling
					break

	if resultsTable:
		for tr in resultsTable.select("tr"):
			tds = tr.select("td")

			date = None
			season = None
			winner = None
			loser = None

			if len(tds) >= 7:
				date = extract_date(strip_citations(tds[0]).strip())
				season = str(date.year)
				winner = strip_citations(tds[1]).strip()
				loser = strip_citations(tds[3]).strip()

				processed_info.setdefault(season, dict())
				processed_info[season].setdefault(MLB_EVENT_FLAG_HALL_OF_FAME, dict())
				processed_info[season][MLB_EVENT_FLAG_HALL_OF_FAME] = {
					"caption": "%s Major League Baseball Hall of Fame Game" % season,
					"date": date,
					"winner": winner,
					"loser": loser
					}

	return processed_info
