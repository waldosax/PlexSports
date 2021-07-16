# Boostrap necessary modules for debugging Plex scanner

import os, sys, types, functools

# Anywhere I might resolve an import directive from
sys.path.append(os.path.abspath("Backups\\Scanners.bundle\\Contents\\Resources\\Common"))

# Run C:\Python27\Scripts\pip install requests to install relevant packages
# sys.path.append(os.path.abspath("PlexSportsAgent.bundle\\Contents\\Libraries\\Shared"))
sys.path.append(os.path.abspath("C:\\Python27\\Lib\\site-packages"))

sys.path.append(os.path.abspath("Scanners\\Series"))
sys.modules["PlexSportsScanner"] = PlexSportsScanner = __import__("PlexSportsScanner")





def BeginScan(root):
	root = root
	path = root
	mediaList = []

	(path, files, subdirs) = GetFilesAndSubdirs(path)
		
	ScanRecursive(path, files, mediaList, subdirs, root)
	return mediaList

def GetFilesAndSubdirs(path, relsubdir = None):
	x = path
	if (relsubdir):
		x = os.path.join(x, relsubdir)
	files = []
	subdirs = []
	mediaList = []
	l = os.listdir(x)
	for i in l:
		p = os.path.join(x, i)
		if os.path.isfile(p):
			files.append(p)
		elif os.path.isdir(p):
			subdirs.append(p)
	return (x, files, subdirs)

def ScanRecursive(path, files, mediaList, subdirs, root):
	PlexSportsScanner.Scan(path, files, mediaList, subdirs, root=root)
	for s in subdirs:
		relsubdir = os.path.relpath(s, path or root)
		(newpath, newfiles, newsubdirs) = GetFilesAndSubdirs(path or root, relsubdir)
		ScanRecursive(newpath, newfiles, mediaList, newsubdirs, root)






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


	mediaList = BeginScan(root)
	print(mediaList)
