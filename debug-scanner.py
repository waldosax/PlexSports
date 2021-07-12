# Boostrap necessary modules for debugging Plex scanner

import os, sys, types

# Anywhere I might resolve an import directive from
sys.path.append(os.path.abspath("Backups\\Scanners.bundle\\Contents\\Resources\\Common"))

# Run C:\Python27\Scripts\pip install requests to install relevant packages
# sys.path.append(os.path.abspath("PlexSportsAgent.bundle\\Contents\\Libraries\\Shared"))
sys.path.append(os.path.abspath("C:\\Python27\\Lib\\site-packages"))

sys.path.append(os.path.abspath("Scanners\\Series"))
sys.modules["PlexSportsScanner"] = PlexSportsScanner = __import__("PlexSportsScanner")

# Load up search results
if __name__ == "__main__":
	# argv1 = argv[1]
	# argv1 = "Z:\\Staging\\Sports"
	argv1 = "L:\\Staging\\Sports"

	# argv2 = len(argv) > 2 and argv[2].lower in ["--fullscan"]
	argv2 = True
	# argv2 = False

	fullscan = argv2
	root = None # Library Location Root
	path = argv1 # 
	mediaList = []


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

	#files = [os.path.join(path, file) for file in os.listdir(path)]
	#if sys.platform != "win32": path = path[1:]
	
	root = "F:\\Code\\Plex\PlexSportsLibrary"
	paths = [
		("", [
			"F:\\Code\\Plex\\PlexSportsLibrary\\.plexignore",
			"F:\\Code\\Plex\\PlexSportsLibrary\\Phillies vs. Red Sox Game Highlights (7_10_21) _ MLB Highlights.mp4",
			"F:\\Code\\Plex\\PlexSportsLibrary\\yt1s.com - Phillies vs Cubs Game Highlights 70821  MLB Highlights.mp4",
			"F:\\Code\\Plex\\PlexSportsLibrary\\yt1s.com - Phillies vs Red Sox Game Highlights 7921  MLB Highlights.mp4"
			], [
				"F:\\Code\\Plex\\PlexSportsLibrary\\.git",
				"F:\\Code\\Plex\\PlexSportsLibrary\\Boxing",
				"F:\\Code\\Plex\\PlexSportsLibrary\\MLB",
				"F:\\Code\\Plex\\PlexSportsLibrary\\NBA",
				"F:\\Code\\Plex\\PlexSportsLibrary\\NFL",
				"F:\\Code\\Plex\\PlexSportsLibrary\\NHL",
				"F:\\Code\\Plex\\PlexSportsLibrary\\UFC",
			], root),
		("F:\\Code\\Plex\\PlexSportsLibrary\\Boxing", [], [], root),
		("F:\\Code\\Plex\\PlexSportsLibrary\\MLB", [], ["F:\\Code\\Plex\\PlexSportsLibrary\\2021"], root),
		("F:\\Code\\Plex\\PlexSportsLibrary\\NBA", [], [], root),
		("F:\\Code\\Plex\\PlexSportsLibrary\\NFL", [
			"F:\\Code\\Plex\\PlexSportsLibrary\\NFL\\Super.Bowl.LII.2018.02.04.Eagles.vs.Patriots.1080p.HDTV.x264.Merrill-Hybrid-5.1-PHillySPECIAL.mkv"
			], [
				"F:\\Code\\Plex\\PlexSportsLibrary\\NFL\\2004-2005",
				], root),
		("F:\\Code\\Plex\\PlexSportsLibrary\\NFL\\2004-2005", [
			"F:\\Code\\Plex\\PlexSportsLibrary\\NFL\\2004-2005\\NFL.Super Bowl.XXXIX.Patriots.vs.Eagles.720p.HD.TYT.mp4",
			"F:\\Code\\Plex\\PlexSportsLibrary\\NFL\\2004-2005\\NFL.Super Bowl.XXXIX.Patriots.vs.Eagles.720p.HD.TYT.ts"
			], [], root),
		("F:\\Code\\Plex\\PlexSportsLibrary\\NHL", [], [], root),
		("F:\\Code\\Plex\\PlexSportsLibrary\\UFC", [], [], root)
		]

	mediaList = []
	for (path, files, subdirs, root) in paths:

		#print (path)
		#print(files)

		PlexSportsScanner.Scan(path, files, mediaList, subdirs, root=root)
	
	print(mediaList)