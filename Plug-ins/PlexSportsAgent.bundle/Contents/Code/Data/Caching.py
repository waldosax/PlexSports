import os
import hashlib
from urlparse import urlparse

import PathUtils
import PluginSupport

def __get_signature(url):
	signature = url.lower()
	return signature

def __get_cache_key(url):
	signature = __get_signature(url)
	m = hashlib.md5()
	m.update(signature)
	cacheKey = m.hexdigest().lower()
	return cacheKey

def __get_domain(url):
	uri = urlparse(url)
	return uri.netloc.lower()

def GetHTTPLocalCachesPathForUrl(url, extension=None):
	domain = __get_domain(url)
	cacheKey = __get_cache_key(url)
	localCachesPath = PluginSupport.GetHTTPLocalCachesPath()
	return os.path.join(localCachesPath, domain, cacheKey[:2], cacheKey) + extension

def GetResponseFromCache(url, extension=None):
	httpCacheFilePath = GetHTTPLocalCachesPathForUrl(url)
	#httpCachePath = os.path.dirname(httpCacheFilePath)
	#PathUtils.EnsureDirectory(httpCachePath)
	if os.path.exists(httpCacheFilePath):
		f = open(httpCacheFilePath, "rb")
		response = f.read()
		f.close()
		if response: return response

def CacheResponse(url, response, extension=None):
	httpCacheFilePath = GetHTTPLocalCachesPathForUrl(url)
	httpCachePath = os.path.dirname(httpCacheFilePath)
	PathUtils.EnsureDirectory(httpCachePath)
	f = open(httpCacheFilePath, "wb")
	f.write(response)
	f.close()
