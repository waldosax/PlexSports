# Python framework
import re, os, os.path, random
from pprint import pprint

# Plex native
import Media, VideoFiles, Stack, Utils

# Local package
from Constants import *
from Teams import *
from Metadata import *


#all_teams = GetAllTeams()



def Scan(path, files, mediaList, subdirs, language=None, root=None, **kwargs):
    """"""
    print("Scanning for files at '" + path + "' ...")
    NFL.Touchdown()

    # Scan for video files.
    VideoFiles.Scan(path, files, mediaList, subdirs, root)

    # Iterate over all the files
    for file in files:
    #    done = False
    #    folders = os.path.dirname(file)
    #    fileName = os.path.basename(file)
    #    (fileNameWithoutExtension, ext) = os.path.splitext(fileName)
    #    #print("%s | %s | %s" % (folders, fileNameWithoutExtension, ext))

        # Extract all the metadata possible from the folder structure/file name
        meta = __discover_metadata(path, file, root)
        print(meta)

    # See if we need to tie any parted video files (.part1.mp4, .part2.mp4, etc) to a single file
    if files:
        Stack.Scan(path, files, mediaList, subdirs)
        print(files)

def __get_relative_path(path, file, root):
    relPath = os.path.relpath(file, root) if root else path + os.path.basename(file) if os.path.isabs(path) == False else os.path.relPath(file, path)
    return relPath

def __discover_metadata(path, file, root):
    meta = dict()
    relPath = __get_relative_path(path, file, root)

    Metadata.Infer(relPath, meta)




    return meta

