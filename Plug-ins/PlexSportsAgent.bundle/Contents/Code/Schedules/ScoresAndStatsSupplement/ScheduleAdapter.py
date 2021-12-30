import re
import datetime

from Constants import *
from ..Hashes import *
from StringUtils import *
from TimeZoneUtils import *
from ..ScheduleEvent import *

from .Scraper import *

__season_start_months = {
    LEAGUE_MLB: 0,
    LEAGUE_NBA: 10,
    LEAGUE_NFL: 7,
    LEAGUE_NHL: 10
    }

def SupplementSchedule(sched, navigator, sport, league, season):

    supplement = ScrapeRecaps(sport, league, season)
    if not supplement: return

    for supplementalEvent in supplement:
        eligible = __find_events(sched, navigator, sport, league, supplementalEvent)
        if eligible:
            if not eliegible[0].description and supplementalEvent.get("description"):
                eliegible[0].description = supplementalEvent["description"]


def __infer_season(league, date):
    if __season_start_months.get(league) and date.month < __season_start_months[league]:
        return str(date.year - 1)

    return str(date.year)

def __find_events(sched, navigator, sport, league, supplementalEvent):
    qualifyingEvents = []

    date = supplementalEvent["date"]
    season = __infer_season(league, date)

    homeTeamName = supplementalEvent["homeTeam"]
    homeTeam = navigator.GetTeam(homeTeamName)
    homeTeamKey = homeTeam.key if homeTeam else "" #homeTeamName

    awayTeamName = supplementalEvent["awayTeam"]
    awayTeam = navigator.GetTeam(awayTeamName)
    awayTeamKey = awayTeam.key if awayTeam else "" #awayTeamName

    comparand = {
        "sport": sport,
        "league": league,
        "season": season,
        "date": date,
        "homeTeam": homeTeamKey,
        "awayTeam": awayTeamKey,
        }

    daysEvents = dict()
    augmentationKey = sched_compute_augmentation_hash(ScheduleEvent(**comparand))
    if augmentationKey in sched.keys():
        daysEvents = sched[augmentationKey]
    else:
        comparand["homeTeam"] = awayTeamKey
        comparand["awayTeam"] = homeTeamKey
        augmentationKey = sched_compute_augmentation_hash(ScheduleEvent(**comparand))
        if augmentationKey in sched.keys():
            daysEvents = sched[augmentationKey]

    for evt in daysEvents.values():
        qualifyingEvents.append(evt)
        
    return qualifyingEvents
