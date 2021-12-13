import re, os, sys
import json
from datetime import datetime, date, time
from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup
import bs4
from pprint import pprint
import threading, Queue

from Constants import *
from bs4 import BeautifulSoup
import bs4
from pprint import pprint

from Constants import *
from TimeZoneUtils import *

from Data.WikipediaDownloader import *


__selectors = {
	"toc": "div.toc",
	"toc-first-level": "ul > li.toclevel-1",
	"toc-second-level": "ul > li.toclevel-2",
}

def Process(markup):
	processed_info = dict()

	selectors = __selectors
	if not markup: return processed_info
	soup = BeautifulSoup(markup, "html5lib")

	tsoup.select(selectors["toc"])

	pass
