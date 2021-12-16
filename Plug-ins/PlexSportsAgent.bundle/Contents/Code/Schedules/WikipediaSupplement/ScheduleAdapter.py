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

    augment = ScrapeAllStarGame(sport, league, season)

    for eventId in augment.keys():
        augmentEvent = augment[eventId]
        if not augmentEvent: continue

        # Find event in original schedule
        eligible = __find_events(sched, eventId)
        if eligible:
            for evt in eligible:
                __merge_events(navigator, sport, league, season, evt, augmentEvent, eventId)
        else:
            # Add Event
            newEvent = __convert_supplement(navigator, sport, league, season, augmentEvent, eventId)
            if not newEvent.get("date"): continue
            AddOrAugmentEvent(sched, ScheduleEvent(**newEvent), 0)

    pass


def __find_events(sched, eventId):
    qualifyingEvents = []

    for key1 in sched.keys():
        for key2 in sched[key1].keys():
            evt = sched[key1][key2]

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

    augmentHomeTeam = deunicode(augmentEvent.get("homeTeam"))
    homeTeamKey = None
    homeTeamName = None
    if augmentHomeTeam:
        discoveredHomeTeam = navigator.GetTeam(season, fullName=augmentHomeTeam, name=augmentHomeTeam, abbreviation=augmentHomeTeam)
        if discoveredHomeTeam: homeTeamKey = discoveredHomeTeam.key
        else: homeTeamName = augmentHomeTeam

    augmentAwayTeam = deunicode(augmentEvent.get("awayTeam"))
    awayTeamKey = None
    awayTeamName = None
    awayTeamKey = None
    awayTeamName = None
    if augmentAwayTeam:
        discoveredAwayTeam = navigator.GetTeam(season, fullName=augmentAwayTeam, name=augmentAwayTeam, abbreviation=augmentAwayTeam)
        if discoveredAwayTeam: awayTeamKey = discoveredAwayTeam.key
        else: awayTeamName = augmentAwayTeam


    enhancedEvent = {
        "sport": sport,
        "league": league,
        "season": season,
        "eventindicator": eventId,
        "eventTitle": deunicode(augmentEvent.get("caption")),
        "description": augmentEvent.get("description"),
        "date": date,
        }

    if homeTeamKey: enhancedEvent["homeTeam"] = homeTeamKey
    if homeTeamName: enhancedEvent["homeTeamName"] = homeTeamName
    if awayTeamKey: enhancedEvent["awayTeam"] = awayTeamKey
    if awayTeamName: enhancedEvent["awayTeamName"] = awayTeamName

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

    enhancedEvent["identity"] = {"WikipediaID": "%s.%s.%s" % (league, season, eventId)}

    return enhancedEvent



def __merge_events(navigator, sport, league, season, evt, augmentEvent, eventId):

    enhancedEvent = __convert_supplement(navigator, sport, league, season, augmentEvent, eventId)

    evt.augment(**enhancedEvent)

    if enhancedEvent.get("eventTitle") and evt.eventTitle and evt.eventTitle == evt.eventTitle.upper():
        # Existing event title is from ESPN API. Overwrite it.
        evt.eventTitle = enhancedEvent["eventTitle"]

    pass