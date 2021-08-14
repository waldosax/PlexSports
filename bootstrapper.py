import os, sys
from pprint import pprint

# Run C:\Python27\Scripts\pip install requests to install relevant packages
# pip install requests
# pip install python-dateutil
# pip install html5lib
# pip install beautifulsoup4
#sys.path.append(os.path.abspath("Backups\\Framework.bundle\\Contents\\Resources\\Platforms\\Shared\\Libraries"))
#sys.path.append(os.path.abspath("C:\\Python27\\Lib\\site-packages"))
# sys.path.append(os.path.abspath("PlexSportsAgent.bundle\\Contents\\Libraries\\Shared"))

def BootstrapScanner():

	# Dependencies: Anywhere I might resolve an import directive from
	__add_to_sys_path("Backups\\Scanners.bundle\\Contents\\Resources\\Common")
	Media = __import_module("Media")
	Utils = __add_to_builtins(__import_module("Utils"))

	# Import the actual module
	__add_to_sys_path("Scanners\\Series")
	PlexSportsScanner = __import_module("PlexSportsScanner")

	return PlexSportsScanner

def BootstrapAgent():

	# Dependencies: Anywhere I might resolve an import directive from
	__add_to_sys_path("Backups\\Scanners.bundle\\Contents\\Resources\\Common")

	# Simulated dependencies (builtins)
	__add_to_sys_path("Debug\\Plex")
	Agent = __import_module("Agent")
	AudioCodec = __import_module("AudioCodec")
	VideoCodec = __import_module("VideoCodec")
	Container = __import_module("Container")
	Utils = __add_to_builtins(__import_module("Utils"))
	MetadataSearchResult = __import__("MetadataSearchResult")
	__add_to_builtins(MetadataSearchResult.MetadataSearchResult)

	# Import the actual module
	#__add_to_sys_path("Plug-ins/PlexSportsAgent.bundle/Contents/Libraries/Shared")
	__add_to_sys_path("Plug-ins/PlexSportsAgent.bundle/Contents")
	PlexSportsAgent = __import_module("Code", "PlexSportsAgent")

	return PlexSportsAgent

def BootstrapScannerAndUnitTests():

	# Import the actual module
	PlexSportsScanner = BootstrapScanner()

	# Import the unit test module
	UnitTests = __import_module("UnitTests")

	return (PlexSportsScanner, UnitTests)


def __add_to_sys_path(relPath):
	abspath = os.path.abspath(relPath)
	if not abspath in sys.path:
		sys.path.append(abspath)

def __import_module(moduleName, alias=None):
	if moduleName not in sys.modules.keys():
		module = __add_to_builtins(__add_to_sys_modules(__import__(moduleName), alias))
		if alias:
			module.__name__ = alias
		return module
	else:
		return sys.modules[moduleName]

def __add_to_sys_modules(module, alias=None):
	moduleName = alias or module.__name__
	if moduleName not in sys.modules.keys():
		sys.modules[moduleName] = module
		return module
	else:
		return sys.modules[moduleName]

def __add_to_builtins(module, alias=None):
	moduleName = alias or module.__name__
	if moduleName not in __builtins__.keys():
		__builtins__[moduleName] = module
		return module
	else:
		return __builtins__[moduleName]
