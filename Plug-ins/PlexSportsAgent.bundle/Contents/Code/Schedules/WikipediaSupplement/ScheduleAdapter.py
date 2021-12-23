import re
import datetime

from Constants import *
from ..Hashes import *
from StringUtils import *
from TimeZoneUtils import *
from Scraper import *
from ..ScheduleEvent import *

from .Scraper import *



def SupplementSchedule(sched, navigator, sport, league, season):

    supplement = ScrapeAllStarGame(sport, league, season)

    for key in supplement.keys():
        supplementalEvent = supplement[key]
        if not supplementalEvent: continue

        eventId = int(key)
        if key > 100: eventId = int(key) // 100

        # Find event in original schedule
        eligible = __find_events(sched, eventId)
        if eligible:
            foundEligible = False
            for eligibleEvent in eligible:
                isMatching = __is_matching_game(season, eligibleEvent, supplementalEvent, navigator)
                if isMatching:
                    foundEligible = True
                    __merge_events(navigator, sport, league, season, eligibleEvent, supplementalEvent, eventId)

            if not foundEligible:
                # Add Event
                __create_and_add_event(sched, navigator, sport, league, season, supplementalEvent, eventId)
        else:
            # Add Event
            __create_and_add_event(sched, navigator, sport, league, season, supplementalEvent, eventId)

    pass


def __is_matching_game(season, eligibleEvent, supplementalEvent, navigator):
    if supplementalEvent.get("game") and eligibleEvent.game and supplementalEvent["game"] == eligibleEvent.game:
       return True

    homeTeam = navigator.GetTeam(season, fullName=eligibleEvent.homeTeamName, key=eligibleEvent.homeTeam)
    awayTeam = navigator.GetTeam(season, fullName=eligibleEvent.awayTeamName, key=eligibleEvent.awayTeam)
    
    winner = navigator.GetTeam(season, fullName=supplementalEvent.get("winner"), name=supplementalEvent.get("winner"), abbreviation=supplementalEvent.get("winner"), city=supplementalEvent.get("winner"))
    loser = navigator.GetTeam(season, fullName=supplementalEvent.get("loser"), name=supplementalEvent.get("loser"), abbreviation=supplementalEvent.get("loser"), city=supplementalEvent.get("loser"))

    if homeTeam and winner and homeTeam.key == winner.key:
        if awayTeam and loser and awayTeam.key == loser.key:
            return True

    if homeTeam and loser and homeTeam.key == loser.key:
        if awayTeam and winner and awayTeam.key == winner.key:
            return True

    return False

def __create_and_add_event(sched, navigator, sport, league, season, supplementalEvent, eventId):
    newEvent = __convert_supplement(navigator, sport, league, season, supplementalEvent, eventId)
    if not newEvent.get("date"): return
    AddOrAugmentEvent(sched, ScheduleEvent(**newEvent), 0)
    pass

def __find_events(sched, eventId):
    qualifyingEvents = []

    for augmentationKey in sched.keys(): # Hashed augmentation keys
        for subkey in sched[augmentationKey].keys(): # Augmentation subkeys (hours)
            evt = sched[augmentationKey][subkey]

            if evt.eventindicator == eventId:
                qualifyingEvents.append(evt)
        
    return qualifyingEvents

def __convert_supplement(navigator, sport, league, season, augmentEvent, eventId):
    date = augmentEvent.get("date")
    if isinstance(date, datetime.datetime): pass
    elif isinstance(date, datetime.date): pass
    elif isinstance(date, basestring):
        if IsISO8601DateWithoutTime(date): date = ParseISO8601Date(date).date()
        elif IsISO8601Date(date): date = ParseISO8601Date(date)

    augmentHomeTeam = deunicode(augmentEvent.get("homeTeam") if augmentEvent.get("homeTeam") else augmentEvent.get("loser"))
    homeTeamKey = None
    homeTeamName = None
    homeTeamDisplay = None
    if augmentHomeTeam:
        discoveredHomeTeam = navigator.GetTeam(season, fullName=augmentHomeTeam, name=augmentHomeTeam, abbreviation=augmentHomeTeam, city=augmentHomeTeam)
        if discoveredHomeTeam:
            homeTeamKey = discoveredHomeTeam.key
            homeTeamDisplay = discoveredHomeTeam.fullName
        else:
            homeTeamName = augmentHomeTeam
            homeTeamDisplay = augmentHomeTeam

    augmentAwayTeam = deunicode(augmentEvent.get("awayTeam") if augmentEvent.get("awayTeam") else augmentEvent.get("winner"))
    awayTeamKey = None
    awayTeamName = None
    awayTeamDisplay = None
    if augmentAwayTeam:
        discoveredAwayTeam = navigator.GetTeam(season, fullName=augmentAwayTeam, name=augmentAwayTeam, abbreviation=augmentAwayTeam, city=augmentHomeTeam)
        if discoveredAwayTeam:
            awayTeamKey = discoveredAwayTeam.key
            awayTeamDisplay = discoveredAwayTeam.fullName
        else:
            awayTeamName = augmentAwayTeam
            awayTeamDisplay = augmentAwayTeam

    game = augmentEvent.get("game")

    enhancedEvent = {
        "sport": sport,
        "league": league,
        "season": season,
        "eventindicator": eventId,
        "eventTitle": deunicode(augmentEvent.get("caption")),
        "description": augmentEvent.get("description"),
        "date": date,
        "game": game
        }

    if homeTeamKey: enhancedEvent["homeTeam"] = homeTeamKey
    if homeTeamName: enhancedEvent["homeTeamName"] = homeTeamName
    if awayTeamKey: enhancedEvent["awayTeam"] = awayTeamKey
    if awayTeamName: enhancedEvent["awayTeamName"] = awayTeamName

    vs = "%s vs. %s" % (homeTeamDisplay, awayTeamDisplay)
    enhancedEvent.setdefault("vs", vs)

    assets = {}
    if augmentEvent.get("logo"):
        assets[ASSET_TYPE_THUMBNAIL] = [{"source": ASSET_SOURCE_WIKIPEDIA, "url": deunicode(augmentEvent["logo"])}]
        pass
    if assets:
        enhancedEvent.setdefault("assets", assets)

    networks = []
    if augmentEvent.get("networks"):
        for network in augmentEvent["networks"]:
            networks.append(deunicode(network))
    if networks:
        enhancedEvent.setdefault("networks", networks)

    gameKeyPart = (".%s" % game) if game else ""
    enhancedEvent["identity"] = {"WikipediaID": "%s.%s.%s%s" % (league, season, eventId, gameKeyPart)}

    return enhancedEvent



def __merge_events(navigator, sport, league, season, evt, augmentEvent, eventId):

    enhancedEvent = __convert_supplement(navigator, sport, league, season, augmentEvent, eventId)

    evt.augment(**enhancedEvent)

    if enhancedEvent.get("eventTitle") and evt.eventTitle and evt.eventTitle == evt.eventTitle.upper():
        # Existing event title is from ESPN API. Overwrite it.
        evt.eventTitle = enhancedEvent["eventTitle"]

    pass