from ....Data.WikipediaDownloader import *



def ScrapeProBowl(season):
	supplement = dict()

	markup = DownloadAllStarGameSupplement(SPORT_FOOTBALL, LEAGUE_MLB, season)
	if markup:
		basicInfo = process_all_star_basic_info_box(markup)
		if basicInfo:
			supplement.setdefault(NFL_EVENT_FLAG_PRO_BOWL, dict())
			merge_dictionaries(basicInfo, supplement[NFL_EVENT_FLAG_PRO_BOWL])

		#supplement.setdefault(NFL_EVENT_FLAG_PRO_BOWL, dict())
		#extendedInfo = AllStarGameProcessor.Process(markup)
		#merge_dictionaries(extendedInfo, supplement)

	return supplement
