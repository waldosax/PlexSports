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

from ...Data.ScoresAndStatsDownloader import *


__selectors = {
	"articles-block": "div#pr-articles",
	"article": "article",
	"thumbnail": "a.pr-image",
	"header": "h4 a",
	"recap-block": "div#previews",
	}


def ProcessRecaps(sport, league, season):
	if int(season) < datetime.datetime.now().year: return None

	recaps = []

	markup = DownloadLeagueRecapsForCurrentCalendarYear(sport, league, season)
	if not markup: return None

	soup = BeautifulSoup(markup, "html5lib")

	selectors = __selectors
	
	articlesBlock = soup.select_one(selectors["articles-block"])
	if not articlesBlock: return None

	for article in articlesBlock.select(selectors["article"]):
		thumbnail = None

		thumbnailNode = article.select_one(selectors["thumbnail"])
		if thumbnailNode:
			thumbnailStyle = thumbnailNode.get("style")
			thumbnail = __parse_css_background_image(style)

		link = thumbnailNode if thumbnailNode else article.select_one(selectors["header"])
		if not link: continue
		
		caption = link.text.strip()
		parsedInfo = __parse_header_text(caption)
		if not parsedInfo: continue

		url = link.attrs["href"]

		# TODO: Put in thread queue
		supplement = __process_page(sport, league, season, parsedInfo, caption, url)
		if not supplement: continue

		recaps.append(supplement)

	return recaps

def __process_page(sport, league, season, supplement, caption, url):
	print "  Acquiring recap for % from scoresandstats.com ..." % (caption)

	markup = DownloadPage(sport, league, season, url)
	if not markup: return None

	soup = BeautifulSoup(markup, "html5lib")

	selectors = __selectors

	article = soup.select_one(selectors["article"])
	if not article: return None

	recapBlock = article.select_one(selectors["recap-block"])
	if not recapBlock: return None

	ps = recapBlock.select("p")
	if not ps: return None

	description = None
	for p in ps:
		if description: description = description + "\r\n\r\n"
		description = description + p.text

	description = description.strip()
	if not description: return None

	supplement["description"] = description

	return supplement 


def __parse_css_background_image(style):
	url = None

	properties = splitAndTrim(style, ";")
	for property in properties:
		kvp = splitAndTrim(property, ":", 1)
		if kvp[0] == "background" or kvp[0] == "background-url":
			m = re.search(r"url\(['\"](?P<url>[^'\"]+)['\"]\)")
			if m:
				url = m.group("url")
				break
	
	return url


__date_expression = r"%s-%s-%s" % (EXPRESSION_VALID_FULL_MONTH, EXPRESSION_VALID_FULL_DAY, EXPRESSION_VALID_FULL_YEAR)
__recap_expression = r"\bRecap\s+(?P<airdate>%s)(?:\b|$)" % __date_expression

# San Francisco Giants vs. Seattle Mariners Recap 04-04-2021
def __parse_header_text(text):
	if not text: return None
	
	mrecap = re.search(__recap_expression, text, re.IGNORECASE)
	if not mrecap: return None

	parsed = dict()
	parsed["date"] = datetime.dateteime.strptime(mrecap.group("airdate"), "%B %d, %Y").date()

	teams = text[:mrecap.start()].strip()
	if not teams: return None

	mvs = re.search(versus_expressions, teams, re.IGNORECASE)
	if not mvs: return None

	if mvs.group(0) == "@" or mvs.group(0) == "at":
		parsed["awayTeam"] = teams[:mvs.start()].strip()
		parsed["homeTeam"] = teams[mvs.end():].strip()
	else:
		parsed["homeTeam"] = teams[:mvs.start()].strip()
		parsed["awayTeam"] = teams[mvs.end():].strip()

	return parsed