import re, os, sys
import json
from datetime import datetime, date, time
from dateutil.relativedelta import relativedelta

from bs4 import BeautifulSoup
import bs4
from pprint import pprint

from Constants import *
from Matching import __expressions_from_literal
from StringUtils import *
from TimeZoneUtils import *

from ....Data.WikipediaDownloader import *
from ..WikipediaSupplementUtils import *
from ..WikipediaSupplementUtils import __basic_info_box_selectors



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

		if basicInfo:
			for key in extendedInfo.keys():
				toBackfill = extendedInfo[key]
				merge_dictionaries(basicInfo, toBackfill)

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


	# For NHL All-Star Games in the new format (3-3 tournament),
	#  capture the games/teams and subdivide them.
	if ind == NHL_EVENT_FLAG_ALL_STAR_GAME:
		games = __get_all_star_game_tournament(soup)
		if games:
			merge_dictionaries(games, processed_info)
		pass



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


def __get_all_star_game_tournament(soup):
	games = dict()

	infobox = soup.select_one(__basic_info_box_selectors["info-box"])
	if infobox:
		rows = infobox.select(__basic_info_box_selectors["section"])
		for row in rows:
			label = row.select_one(__basic_info_box_selectors["small-section-label"])
			if not label or not label.text or not label.text.strip(): continue

			labelText = label.text.strip()
			if labelText.find("Game ") < 0: continue;
			gameNumberLiteral = labelText[5:]
			gameNumber = converTextToInt(gameNumberLiteral)

			teamsNode = row.select_one(__basic_info_box_selectors["small-section-value"])
			if not teamsNode: continue
			teams = teamsNode.text

			# Since the layout of the table is Winner/Loser instead of Away/Home,
			#  organize them as team1, team2
			winnerLoser = teams.split(unichr(0x2013))
			if not winnerLoser or len(winnerLoser) < 1: continue

			winner = winnerLoser[0].strip()
			while winner and winner[-1].isdigit(): winner = winner[:-1].strip()
			while winner and winner[0].isdigit(): winner = winner[1:].strip()

			loser = winnerLoser[1].strip()
			while loser and loser[-1].isdigit(): loser = loser[:-1].strip()
			while loser and loser[0].isdigit(): loser = loser[1:].strip()

			if gameNumber == 3:
				games.setdefault(NHL_EVENT_FLAG_ALL_STAR_GAME, dict())
				games[NHL_EVENT_FLAG_ALL_STAR_GAME]["eventindicator"] = NHL_EVENT_FLAG_ALL_STAR_GAME
				games[NHL_EVENT_FLAG_ALL_STAR_GAME]["game"] = gameNumber
				games[NHL_EVENT_FLAG_ALL_STAR_GAME]["winner"] = winner
				games[NHL_EVENT_FLAG_ALL_STAR_GAME]["loser"] = loser
			else:
				key = (NHL_EVENT_FLAG_ALL_STAR_SEMIFINAL * 100) + gameNumber
				games.setdefault(key, dict())
				games[key]["eventindicator"] = NHL_EVENT_FLAG_ALL_STAR_SEMIFINAL
				games[key]["game"] = gameNumber
				games[key]["winner"] = winner
				games[key]["loser"] = loser
	
	# Now if I really want to go beyond the pale,
	#  Scrape the bracket to find out home/away teams


	return games