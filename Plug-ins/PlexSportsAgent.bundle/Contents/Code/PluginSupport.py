import os

APP_IDENTIFIER = "com.mayosolutions.plexsports"

PLEX_HOME = "F:\\Code\\Plex\\PlexSports\\"
#PLEX_HOME = "C:\\Code\\MayoSolutions\\Plex\\PlexSports\\"
#TODO: Try to figure out how to consistently get this without hard-coding
#PLEX_HOME = os.path.expandvars("%PLEX_HOME%")

#* '%LOCALAPPDATA%\Plex Media Server\'                                        # Windows Vista/7/8
#* '%USERPROFILE%\Local Settings\Application Data\Plex Media Server\'         # Windows XP, 2003, Home Server
#* '$HOME/Library/Application Support/Plex Media Server/'                     # Mac OS
#* '$PLEX_HOME/Library/Application Support/Plex Media Server/',               # Linux
#* '/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/', # Debian,Fedora,CentOS,Ubuntu
#* '/usr/local/plexdata/Plex Media Server/',                                  # FreeBSD
#* '/usr/pbi/plexmediaserver-amd64/plexdata/Plex Media Server/',              # FreeNAS
#* '${JAIL_ROOT}/var/db/plexdata/Plex Media Server/',                         # FreeNAS
#* '/c/.plex/Library/Application Support/Plex Media Server/',                 # ReadyNAS
#* '/share/MD0_DATA/.qpkg/PlexMediaServer/Library/Plex Media Server/',        # QNAP
#* '/volume1/Plex/Library/Application Support/Plex Media Server/',            # Synology, Asustor
#* '/raid0/data/module/Plex/sys/Plex Media Server/',                          # Thecus
#* '/raid0/data/PLEX_CONFIG/Plex Media Server/'                               # Thecus Plex community

PLUGINS_PATH = "Plug-ins/"

PLUGINS_SUPPORT_PATH = "Plug-in Support/"
PLUGINS_SUPPORT_DATA_PATH = "Data/"
PLUGINS_SUPPORT_CACHES_PATH = r"Caches/"
PLUGINS_SUPPORT_HTTP_CACHES_PATH = r"HTTP.system/"
PLUGINS_SUPPORT_HTTP_LOCAL_CACHES_PATH = r"HTTP.local/"

# TODO: Rename
DATA_PATH = r"DataItems/"
DATA_PATH_LEAGUES = DATA_PATH + r"Leagues/"
CACHES_PATH = r"CacheItems/"
CACHES_PATH_LEAGUES = CACHES_PATH + r"Leagues/"

def GetDataPathForLeague(league):
	return os.path.abspath("%s%s%s%s/%s%s" % (PLEX_HOME, PLUGINS_SUPPORT_PATH, PLUGINS_SUPPORT_DATA_PATH, APP_IDENTIFIER, DATA_PATH_LEAGUES, league))

def GetCachesPathForLeague(league):
	return os.path.abspath("%s%s%s%s/%s%s" % (PLEX_HOME, PLUGINS_SUPPORT_PATH, PLUGINS_SUPPORT_CACHES_PATH, APP_IDENTIFIER, CACHES_PATH_LEAGUES, league))

def GetHTTPCachesPath():
	return os.path.abspath("%s%s%s%s/%s" % (PLEX_HOME, PLUGINS_SUPPORT_PATH, PLUGINS_SUPPORT_CACHES_PATH, APP_IDENTIFIER, PLUGINS_SUPPORT_HTTP_CACHES_PATH))

def GetHTTPLocalCachesPath():
	return os.path.abspath("%s%s%s%s/%s" % (PLEX_HOME, PLUGINS_SUPPORT_PATH, PLUGINS_SUPPORT_CACHES_PATH, APP_IDENTIFIER, PLUGINS_SUPPORT_HTTP_LOCAL_CACHES_PATH))
