# Python framework
import re, os, os.path, random
from pprint import pprint

# Plex native
import Media, VideoFiles, Stack, Utils

# Local package
from Constants import *
from Teams import *
from Matching import *




def Scan(path, files, mediaList, subdirs, language=None, root=None, **kwargs):
    """"""
    print("Scanning for files at " + path + " ...")

    # Scan for video files.
    VideoFiles.Scan(path, files, mediaList, subdirs, root)

    # Iterate over all the files
    #for file in files:
    #    done = False
    #    folders = os.path.dirname(file)
    #    fileName = os.path.basename(file)
    #    (fileNameWithoutExtension, ext) = os.path.splitext(fileName)
    #    #print("%s | %s | %s" % (folders, fileNameWithoutExtension, ext))

    #    meta = dict()
    #    #Extract all the metadata possible from the folder structure/file name

    GetAllTeams()

    if files:
        Stack.Scan(path, files, mediaList, subdirs)
