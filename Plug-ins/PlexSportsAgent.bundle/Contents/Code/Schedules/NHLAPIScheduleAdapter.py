import json

from Constants import *
from Hashes import *
from StringUtils import *
from TimeZoneUtils import *
from Vectors import *
from ..Data.NHL.NHLAPIDownloader import *
from ScheduleEvent import *



NHLAPI_GAMETYPE_PRESEASON = "PR"
NHLAPI_GAMETYPE_REGULAR_SEASON = "R"
NHLAPI_GAMETYPE_PLAYOFFS = "P"
NHLAPI_GAMETYPE_ALL_STAR_GAME = "A"


def GetSchedule(sched, navigator, sport, league, season):
	# Retrieve data from NHL API
	downloadedJson = DownloadScheduleForSeason(season)
	
	nhlApiSchedule = None
	if downloadedJson:
		try: nhlApiSchedule = json.loads(downloadedJson)
		except ValueError: pass

	if nhlApiSchedule and nhlApiSchedule.get("dates"):
		for eventDate in nhlApiSchedule["dates"]:
			dateGroup = eventDate["date"]
			for schedEvent in eventDate["games"]:
				id = schedEvent["gamePk"]

				date = None
				if schedEvent.get("gameDate"):
					date = ParseISO8601Date(schedEvent["gameDate"])
					# Zulu Time
					date = date.replace(tzinfo=UTC)
				elif schedEvent.get("officialDate"):
					date = ParseISO8601Date(schedEvent["officialDate"])
				else:
					date = ParseISO8601Date(dateGroup)

				# Teams from this API are full names
				homeTeamFullName = deunicode(schedEvent["teams"]["home"]["team"]["name"])
				awayTeamFullName = deunicode(schedEvent["teams"]["away"]["team"]["name"])

				homeTeam = navigator.GetTeam(season, homeTeamFullName)
				homeTeamKey = homeTeam.key if homeTeam else None
				awayTeam = navigator.GetTeam(season, awayTeamFullName)
				awayTeamKey = awayTeam.key if awayTeam else None

				subseason = None
				playoffRound = None
				eventIndicator = None
				gameNumber = None
	
				gameType = schedEvent["gameType"]
				if gameType == NHLAPI_GAMETYPE_PRESEASON: subseason = NHL_SUBSEASON_FLAG_PRESEASON
				elif gameType == NHLAPI_GAMETYPE_REGULAR_SEASON: subseason = NHL_SUBSEASON_FLAG_REGULAR_SEASON
				elif gameType == NHLAPI_GAMETYPE_PLAYOFFS:
					subseason = NHL_SUBSEASON_FLAG_POSTSEASON
					# TODO: Playoff Round?
				elif gameType == NHLAPI_GAMETYPE_ALL_STAR_GAME:
					eventIndicator = NHL_EVENT_FLAG_ALL_STAR_GAME

				# TODO: Game Number
				#if subseason == NHL_SUBSEASON_FLAG_POSTSEASON and schedEvent.get("gamesInSeries") > 1:
				#	gameNumber = schedEvent["seriesGameNumber"]

				description = None
				thumbnail = None
				if int(season) >= 2021 and schedEvent.get("content") and schedEvent["content"].get("link"):
					contentJson = DownloadGameContentData(id)
					if contentJson:
						try: content = json.loads(contentJson)
						except ValueError: pass
						(description, thumbnail) = __process_content(schedEvent, content)


				kwargs = {
					"sport": sport,
					"league": league,
					"season": season,
					"date": date,
					"NHLAPIID": id,
					"description": description,
					"homeTeam": homeTeamKey,
					"homeTeamName": homeTeamFullName if not homeTeamKey else None,
					"awayTeam": awayTeamKey,
					"awayTeamName": awayTeamFullName if not awayTeamKey else None,
					"vs": "%s vs. %s" % (homeTeamFullName, awayTeamFullName),
					"subseason": subseason,
					"eventindicator": eventIndicator}

				assets = {}

				if thumbnail:
					assets["thumbnail"] = [{"source": ASSET_SOURCE_MLBAPI, "url": deunicode(thumbnail)}]

				if assets:
					kwargs["assets"] = assets

				event = ScheduleEvent(**kwargs)

				AddOrAugmentEvent(sched, event)





def __process_content(schedEvent, content):
	description = None
	thumbnail = None

	if not content: return (None, None)

	if content.get("editorial"):
		if content["editorial"].get("recap"):
			if content["editorial"]["recap"].get("items"):
				recapItems = content["editorial"]["recap"]["items"]
				for recapItem in recapItems:
				
					if not description: description = recapItem.get("seoDescription")
					if not description:
						description = recapItem.get("headline")
						if recapItem.get("subhead"):
							if not description: description = recapItem["subhead"]
							else: description = description + "\n\n" + recapItem["subhead"]

		if content["editorial"].get("preview"):
			if content["editorial"]["preview"].get("items"):
				previewItems = content["editorial"]["preview"]["items"]
				for previewItem in previewItems:
				
					if not description: description = previewItem.get("seoDescription")
					if not description:
						description = previewItem.get("headline")
						if previewItem.get("subhead"):
							if not description: description = previewItem["subhead"]
							else: description = description + "\n\n" + previewItem["subhead"]
	pass

	if content.get("highlights"):
		if content["highlights"].get("highlights"):
			if content["highlights"]["highlights"].get("items"):
				highlightItems = content["highlights"]["highlights"]["items"]
				for highlightItem in highlightItems:
				
					if not description: description = highlightItem.get("description")
					if not description: description = highlightItem.get("blurb")
					if description: break
	pass
	
	cuts = []
	if content.get("editorial"):
		if content["editorial"].get("recap"):
			if content["editorial"]["recap"].get("items"):
				recapItems = content["editorial"]["recap"]["items"]
				for recapItem in recapItems:
					if recapItem.get("media"):
						media = recapItem["media"]
						if not thumbnail and media.get("photo"):
							cuts = media["photo"]["cuts"]
							bestCut = __select_best_cut(cuts)
							if bestCut: thumbnail = bestCut["src"]
						if not thumbnail and media.get("image"):
							cuts = media["image"]["cuts"]
							bestCut = __select_best_cut(cuts)
							if bestCut: thumbnail = bestCut["src"]

		if content["editorial"].get("preview"):
			if content["editorial"]["preview"].get("items"):
				previewItems = content["editorial"]["preview"]["items"]
				for previewItem in previewItems:
					if previewItem.get("media"):
						media = previewItem["media"]
						if not thumbnail and media.get("photo"):
							cuts = media["photo"]["cuts"]
							bestCut = __select_best_cut(cuts)
							if bestCut: thumbnail = bestCut["src"]
						if not thumbnail and media.get("image"):
							cuts = media["image"]["cuts"]
							bestCut = __select_best_cut(cuts)
							if bestCut: thumbnail = bestCut["src"]

	pass

	if content.get("highlights"):
		if content["highlights"].get("gameCenter"):
			if content["highlights"]["gameCenter"].get("items"):
				highlightItems = content["highlights"]["gameCenter"]["items"]
				for highlightItem in highlightItems:
				
					if not thumbnail and highlightItem.get("photo"):
						cuts = highlightItem["photo"]["cuts"]
						bestCut = __select_best_cut(cuts)
						if bestCut: thumbnail = bestCut["src"]
					if not thumbnail and highlightItem.get("image"):
						cuts = highlightItem["image"]["cuts"]
						bestCut = __select_best_cut(cuts)
						if bestCut: thumbnail = bestCut["src"]

		if content["highlights"].get("scoreboard"):
			if content["highlights"]["scoreboard"].get("items"):
				highlightItems = content["highlights"]["scoreboard"]["items"]
				for highlightItem in highlightItems:
				
					if not thumbnail and highlightItem.get("photo"):
						cuts = highlightItem["photo"]["cuts"]
						bestCut = __select_best_cut(cuts)
						if bestCut: thumbnail = bestCut["src"]
					if not thumbnail and highlightItem.get("image"):
						cuts = highlightItem["image"]["cuts"]
						bestCut = __select_best_cut(cuts)
						if bestCut: thumbnail = bestCut["src"]
	pass


	return (description, thumbnail)

def __select_best_cut(cuts):
	
	__ranked_ratios = {
		"16:9": 4,
		"4:3": 3,
		"64:27": 2,
		}

	def __get_sortable_event_key(cut):	# ratio, pixels
		key = ""

		aspectRatio = cut["aspectRatio"]
		key = key + ("%d2" % (__ranked_ratios[aspectRatio] if __ranked_ratios.get(aspectRatio) else 0))
		width = cut["width"]
		height = cut["height"]
		pixels = width * height
		key = key + "%d8" % (pixels)

		return key

	for cut in sorted(cuts.values(), key=__get_sortable_event_key):
		return cut

	return None