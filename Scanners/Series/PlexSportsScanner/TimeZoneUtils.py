import re
import datetime
from dateutil.parser import parse
from dateutil.tz import *

UTC = gettz("Etc/UTC")
EasternTime = gettz("America/New_York")



def ParseISO8601Date(dateStr):
	return parse(dateStr)

def FormatISO8601(dt):
	#return dt.strftime("%Y-%m-%dT%H:%M:%S%z")
	return dt.isoformat()

def IsISO8601Date(s):
	return not re.match("\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[+\-]\d{2,4})?", s) == None