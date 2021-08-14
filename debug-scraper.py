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

	PlexSportsAgent.Data.NFL.ProFootballReference.Scrape()
	PlexSportsAgent.Data.NFL.ProFootballReference.Export()