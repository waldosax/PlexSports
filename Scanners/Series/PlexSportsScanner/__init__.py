import re, os, os.path, random
from pprint import pprint

import Media, VideoFiles, Stack, Utils

from Constants import *
from NFL import *
from Teams import *
from Matching import *




def Scan(path, files, mediaList, subdirs, root=None):
    """"""
    print("Scanning for files at " + path + " ...")
    Touchdown()

    # Scan for video files.
    VideoFiles.Scan(path, files, mediaList, subdirs, root)
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

        GetAllTeams()


