import certifi
import requests
import urllib2
from requests.utils import requote_uri
from threading import Lock

netLock = Lock()
#netLock = Thread.Lock()

# Keep track of success/failures in a row.
successCount = 0
failureCount = 0

MIN_RETRY_TIMEOUT = 2
RETRY_TIMEOUT = MIN_RETRY_TIMEOUT
TOTAL_TRIES = 1
BACKUP_TRIES = -1

def GetResultFromNetwork(url, headers=None, fetchContent=True):
    global successCount, failureCount, RETRY_TIMEOUT # I don't know what this does yet

    url = requote_uri(url)
    print(">>GET %s" % url)

    try:
        netLock.acquire()
        #Log("SS: Retrieving URL: " + url)

        tries = TOTAL_TRIES
        while tries > 0:

            try:
                result = requests.get(url, headers=headers, verify=certifi.where())
                if fetchContent:
                    result = result.text

                failureCount = 0
                successCount += 1

                if successCount > 20:
                    RETRY_TIMEOUT = max(MIN_RETRY_TIMEOUT, RETRY_TIMEOUT / 2)
                    successCount = 0

                # DONE!
                return result

            except Exception, e:

                print(e) # TODO: Take a harder look at exception handling

                # Fast fail a not found.
                # if e.code == 404:
                #     return None

                failureCount += 1
                print("Failure (%d in a row)" % failureCount)
                successCount = 0
                time.sleep(RETRY_TIMEOUT)

                if failureCount > 5:
                    RETRY_TIMEOUT = min(10, RETRY_TIMEOUT * 1.5)
                    failureCount = 0

    finally:
        netLock.release()

    return None