import re
import datetime
from dateutil.parser import parse
from dateutil.tz import *

UTC = gettz("Etc/UTC")
EasternTime = gettz("America/New_York")




def ParseISO8601Date(dateStr):
	return parse(dateStr)

def ParseISO8601Time(dateStr):
	return parse(dateStr).time()

def FormatISO8601Date(dt):
	return dt.isoformat()

def FormatISO8601Time(dt):
	return dt.strftime("%H:%M:%S%z")

def IsISO8601Date(s):
	return not re.match("^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[+\-]\d{2,4})?$", s) == None

def IsISO8601Time(s):
	return not re.match("^\d{2}:\d{2}:\d{2}(?:[+\-]\d{2,4})?$", s) == None
