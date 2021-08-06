# Boostrap necessary modules for debugging Plex Metadata agent

import os, sys, types, functools
from pprint import pprint

import bootstrapper
import localscanner

PlexSportsAgent = bootstrapper.BootstrapAgent()



if __name__ == "__main__":
	# argv1 = argv[1]
	# argv1 = "Z:\\Staging\\Sports"
	# argv1 = "L:\\Staging\\Sports"
	argv1 = "F:\\Code\\Plex\\PlexSportsLibrary"

	root = argv1
	mediaList = localscanner.BeginScanRecursive(root)
	#mediaList = localscanner.BeginScanFile(os.path.join(root, "Phillies vs. Red Sox Game Highlights (7_10_21) _ MLB Highlights.mp4"), root)
	#pprint(mediaList)

	PlexSportsAgent.Start()
	agent = PlexSportsAgent.PlexSportsAgent()
	for media in mediaList:
		results = []
		print("Trying to find metadata for %s ..." % media.meta["path"])
		agent.search(results, media, None, False)
		if len(results) == 0:
			print("  No results found.")
		else:
			print("  Found %s result(s)." % len(results))
		print("")