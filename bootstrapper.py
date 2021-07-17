import os, sys

# Run C:\Python27\Scripts\pip install requests to install relevant packages
# sys.path.append(os.path.abspath("PlexSportsAgent.bundle\\Contents\\Libraries\\Shared"))
sys.path.append(os.path.abspath("C:\\Python27\\Lib\\site-packages"))

def BootstrapScanner():

	# Dependencies: Anywhere I might resolve an import directive from
	__add_to_sys_path("Backups\\Scanners.bundle\\Contents\\Resources\\Common")

	# Import the actual module
	__add_to_sys_path("Scanners\\Series")
	PlexSportsScanner = __import_module("PlexSportsScanner")

	return PlexSportsScanner

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

def __import_module(moduleName):
	if moduleName not in sys.modules.keys():
		sys.modules[moduleName] = module = __import__(moduleName)
		return module
	else:
		return sys.modules[moduleName]
