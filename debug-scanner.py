# import imp
import importlib
import os
import sys

sys.path.append(os.path.abspath("Debug\\Plex"))
sys.path.append(os.path.abspath("Scanners\\Series"))
sys.path.append(os.path.abspath("Scanners\\Series\\PlexSportsScanner"))

PlexMedia = importlib.import_module("Debug.Plex.Media")
PlexStack = importlib.import_module("Debug.Plex.Stack")
PlexUtils = importlib.import_module("Debug.Plex.Utils")
PlexVideoFiles = importlib.import_module("Debug.Plex.VideoFiles")

PlexAudioCodec = importlib.import_module("Debug.Plex.AudioCodec")
PlexVideoCodec = importlib.import_module("Debug.Plex.VideoCodec")
PlexContainer = importlib.import_module("Debug.Plex.Container")

scannerSpec = importlib.util.spec_from_file_location("PlexSportsScanner", "Scanners/Series/PlexSportsScanner.py")
PlexSportsScanner = importlib.util.module_from_spec(scannerSpec)

sys.modules["Media"] = PlexMedia
sys.modules["Stack"] = PlexStack
sys.modules["Utils"] = PlexUtils
sys.modules["VideoFiles"] = PlexVideoFiles
sys.modules["AudioCodec"] = PlexAudioCodec
sys.modules["VideoCodec"] = PlexVideoCodec
sys.modules["Container"] = PlexContainer

PlexSportsScanner.__setattr__("AudioCodec", PlexAudioCodec)
PlexSportsScanner.__setattr__("VideoCodec", PlexVideoCodec)
PlexSportsScanner.__setattr__("Container", PlexContainer)

scannerSpec.loader.exec_module(PlexSportsScanner)

root = "Z:\\Staging\\Sports" # argv[0]
print (root)
mediaList = []

paths = dict()
walk = [os.path.join(dirPath, fileName) for dirPath, dirNames, fileNames in os.walk(root) for fileName in fileNames]
for f in walk:
    relpath = os.path.relpath(os.path.dirname(f), root)
    file = os.path.basename(f)
    paths.setdefault(relpath, [])
    paths[relpath].append(file)

for path in paths.keys():
    files = paths[path]
    print("Scanning: %s\n\t%s" % (path, files)) 
    PlexSportsScanner.Scan(path, files, mediaList, [])

print(mediaList)


# Load up search results
