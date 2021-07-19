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
	mediaList = localscanner.BeginScan(root)
	#pprint(mediaList)

	PlexSportsAgent.Start()
	agent = PlexSportsAgent.PlexSportsAgent()
	for media in mediaList:
		results = []
		agent.search(results, media, None, False)