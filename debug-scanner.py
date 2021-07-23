# Boostrap necessary modules for debugging Plex scanner

import os, sys, types, functools
from pprint import pprint

import localscanner








# Load up search results
if __name__ == "__main__":
	# argv1 = argv[1]
	# argv1 = "Z:\\Staging\\Sports"
	# argv1 = "L:\\Staging\\Sports"
	argv1 = "F:\\Code\\Plex\\PlexSportsLibrary"

	root = argv1

	# /
	#	mnt/Media/
	# 		Video/
	# 			Sports/		<-- Sports library
	# 				Boxing/
	# 				MLB/
	# 					2021/
	# 				NBA/
	#				NFL/
	#					2004-2005/
	#						NFL.Super Bowl.XXXIX.Patriots.vs.Eagles.720p.HD.TYT.mp4
	#						NFL.Super Bowl.XXXIX.Patriots.vs.Eagles.720p.HD.TYT.ts
	#					Super.Bowl.LII.2018.02.04.Eagles.vs.Patriots.1080p.HDTV.x264.Merrill-Hybrid-5.1-PHillySPECIAL.mkv
	#				NHL/
	#				UFC/
	#				.plexignore
	#				Phillies vs. Red Sox Game Highlights (7_10_21) _ MLB Highlights.mp4
	#				yt1s.com - Phillies vs Cubs Game Highlights 70821  MLB Highlights.mp4
	#				yt1s.com - Phillies vs Red Sox Game Highlights 7921  MLB Highlights.mp4


	mediaList = localscanner.BeginScanRecursive(root)
	#pprint(mediaList)
