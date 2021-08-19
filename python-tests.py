import datetime
from dateutil.parser import parse
from dateutil.tz import *
EasternTime2 = gettz("EDT")
print(EasternTime2)
EasternTime3 = gettz("-05:00")
print(EasternTime3)