import re
import datetime
from dateutil.parser import parse
from dateutil.tz import *
from pprint import pprint

UTC = gettz("Etc/UTC")
EasternTime = gettz("America/New_York")




def ParseISO8601Date(dateStr):
	if isinstance(dateStr, (datetime.datetime, datetime.date)): return dateStr
	return parse(dateStr)

def ParseISO8601Time(dateStr):
	if isinstance(dateStr, (datetime.datetime, datetime.date, datetime.time)): return dateStr
	return parse(dateStr).time()


# Naive
dt1 = ParseISO8601Date("2021-06-25T16:45:13")
pprint(dt1)
tm1 = dt1.time()
pprint(tm1)
if not tm1: print("Time is not truthy.")
print

dt2 = ParseISO8601Date("2021-06-25T00:00:00")
pprint(dt2)
tm2 = dt2.time()
pprint(tm2)
if not tm2: print("Time is not truthy.")
print

dt3 = ParseISO8601Date("2021-06-25")
pprint(dt3)
tm3 = dt3.time()
pprint(tm3)
if not tm3: print("Time is not truthy.")
print


# Aware
dt4 = ParseISO8601Date("2021-06-25T16:45:13Z")
pprint(dt4)
tm4 = dt4.time()
pprint(tm4)
if not tm4: print("Time is not truthy.")
print

dt5 = ParseISO8601Date("2021-06-25T00:00:00Z")
pprint(dt5)
tm5 = dt5.time()
pprint(tm5)
if not tm5: print("Time is not truthy.")
print

dt6 = ParseISO8601Date("2021-06-25T00:00:00+0000")
pprint(dt6)
tm6 = dt6.time()
pprint(tm6)
if not tm6: print("Time is not truthy.")
print


# Aware (Explicitly UTC)
dt7 = ParseISO8601Date("2021-06-25T16:45:13Z")
dt7 = dt7.replace(tzinfo=UTC)
pprint(dt7)
tm7 = dt7.time()
pprint(tm7)
if not tm7: print("Time is not truthy.")
print

dt8 = ParseISO8601Date("2021-06-25")
dt8 = dt8.replace(tzinfo=UTC)
pprint(dt8)
tm8 = dt8.time()
pprint(tm8)
if not tm8: print("Time is not truthy.")
print

dt9 = ParseISO8601Date("2021-06-25T00:00:00")
dt9 = dt9.replace(tzinfo=UTC)
pprint(dt9)
tm9 = dt9.time()
pprint(tm9)
if not tm9: print("Time is not truthy.")
print

dt10 = ParseISO8601Date("2021-06-25T00:00:00Z")
dt10 = dt10.replace(tzinfo=UTC)
pprint(dt10)
tm10 = dt10.time()
pprint(tm10)
if not tm10: print("Time is not truthy.")
print
