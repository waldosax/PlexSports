import urllib2
import certifi
import requests

netLock = Thread.Lock()

# Keep track of success/failures in a row.
successCount = 0
failureCount = 0

MIN_RETRY_TIMEOUT = 2
RETRY_TIMEOUT = MIN_RETRY_TIMEOUT
TOTAL_TRIES = 1
BACKUP_TRIES = -1

def GetResultFromNetwork(url, headers: dict=None, fetchContent=True):
    global successCount, failureCount, RETRY_TIMEOUT # I don't know what this does

    url = url.replace(' ', '%20') # TODO: implement a REAL urlencode

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

                # Fast fail a not found.
                if e.code == 404:
                    return None

                failureCount += 1
                Log("Failure (%d in a row)" % failureCount)
                successCount = 0
                time.sleep(RETRY_TIMEOUT)

                if failureCount > 5:
                    RETRY_TIMEOUT = min(10, RETRY_TIMEOUT * 1.5)
                    failureCount = 0

    finally:
        netLock.release()

    return None