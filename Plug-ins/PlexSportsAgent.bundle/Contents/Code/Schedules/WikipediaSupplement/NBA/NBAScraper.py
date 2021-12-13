from ....Data.WikipediaDownloader import *
from ..WikipediaSupplementUtils import *

import AllStarGamePost2000Processor

def ScrapeAllStarGame(season):
	supplement = dict()

	markup = DownloadAllStarGameSupplement(SPORT_BASKETBALL, LEAGUE_NBA, season)
	if markup:
		basicInfo = process_all_star_basic_info_box(markup)
		if basicInfo:
			supplement.setdefault(NBA_EVENT_FLAG_ALL_STAR_GAME, dict())
			merge_dictionaries(basicInfo, supplement[NBA_EVENT_FLAG_ALL_STAR_GAME])

		supplement.setdefault(NBA_EVENT_FLAG_ALL_STAR_GAME, dict())
		if int(season) >= 2000:
			extendedInfo = AllStarGamePost2000Processor.Process(markup)
			merge_dictionaries(extendedInfo, supplement)

	return supplement
