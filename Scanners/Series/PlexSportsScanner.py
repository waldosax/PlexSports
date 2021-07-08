import re, os, os.path, random
import Media, VideoFiles, Stack, Utils
from pprint import pprint
from PlexSportsScanner.Constants import *
from PlexSportsScanner.NFL import *




def Scan(path: str, files: [], mediaList: [], subdirs: []):
    """"""
    print("Scanning for files at " + path + " ...")
    Touchdown()

    # Scan for video files.
    VideoFiles.Scan(path, files, mediaList, subdirs)
    #print(files)

    # Iterate over all the files
    for file in files:
        done = False
        folders = os.path.dirname(file)
        fileName = os.path.basename(file)
        (fileNameWithoutExtension, ext) = os.path.splitext(fileName)
        #print("%s | %s | %s" % (folders, fileNameWithoutExtension, ext))

        meta = dict()
        #Extract all the metadata possible from the folder structure/file name

