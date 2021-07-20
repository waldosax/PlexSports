import datetime
from dateutil.parser import parse
from dateutil.tz import *

UTC = gettz("Etc/UTC")
EasternTime = gettz("America/New_York")

def ParseIso8861Date(dateStr):
	return parse(dateStr)