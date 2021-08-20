from Constants import *
from ..UserAgent import *
from ..GetResultFromNetwork import *

NBAAPI_BASE_URL = "https://neulionms-a.akamaihd.net/nbad/player/v1/"

NBAAPI_GET_SPA_CONFIG = "nba/site_spa/config.json"

nba_api_headers = {
	"User-Agent": USER_AGENT
}


def DownloadSPAConfig():
	print("Getting SPA configuration from NBA API ...")
	url = NBAAPI_BASE_URL + NBAAPI_GET_SPA_CONFIG
	return GetResultFromNetwork(
		url,
		nba_api_headers, cacheExtension=EXTENSION_JSON)
