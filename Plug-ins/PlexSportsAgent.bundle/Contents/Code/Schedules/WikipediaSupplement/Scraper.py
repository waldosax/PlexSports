
import re, os, sys
import json
from datetime import datetime, date, time
from dateutil.relativedelta import relativedelta
from Constants import *
from PathUtils import *
from PluginSupport import *
from Serialization import *

import MLB
import NBA
import NFL
import NHL



EXPORT_SUPPLEMENT_FILENAME = "wikipedia.%.%s.supplement.json" # (league, item)

EXPORT_SUPPLEMENT_TYPE_MLB_ALL_STAR_GAME = "all-star-game"
EXPORT_SUPPLEMENT_TYPE_NBA_ALL_STAR_GAME = "all-star-game"
EXPORT_SUPPLEMENT_TYPE_NFL_PRO_BOWL = "pro-bowl"
EXPORT_SUPPLEMENT_TYPE_NHL_ALL_STAR_GAME = "all-star-game"



def ScrapeAllStarGame(sport, league, season):
	if league == LEAGUE_MLB:
		return MLB.Scraper.ScrapeAllStarGame(season)
	if league == LEAGUE_NBA:
		return NBA.Scraper.ScrapeAllStarGame(season)
	if league == LEAGUE_NFL:
		return NFL.Scraper.ScrapeProBowl(season)
	if league == LEAGUE_NHL:
		return NHL.Scraper.ScrapeAllStarGame(season)
	pass