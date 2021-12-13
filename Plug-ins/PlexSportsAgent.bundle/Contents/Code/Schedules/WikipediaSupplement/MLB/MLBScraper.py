from ....Data.WikipediaDownloader import *



def ScrapeAllStarGame(season):
	supplement = dict()

	markup = DownloadAllStarGameSupplement(SPORT_BASEBALL, LEAGUE_MLB, season)
	if markup:
		basicInfo = process_all_star_basic_info_box(markup)
		if basicInfo:
			supplement.setdefault(MLB_EVENT_FLAG_ALL_STAR_GAME, dict())
			merge_dictionaries(basicInfo, supplement[MLB_EVENT_FLAG_ALL_STAR_GAME])

		#supplement.setdefault(MLB_EVENT_FLAG_ALL_STAR_GAME, dict())
		#extendedInfo = AllStarGameProcessor.Process(markup)
		#merge_dictionaries(extendedInfo, supplement)

	return supplement
