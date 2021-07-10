# Boostrap necessary modules for debugging Plex Metadata agent

#import importlib
import os
import sys

sys.path.append(os.path.abspath("PlexSportsAgent.bundle/Contents/Libraries/Shared"))
sys.path.append(os.path.abspath("Debug\\Plex"))
sys.path.append(os.path.abspath("Backups"))

PlexAgent = importlib.import_module("Debug.Plex.Agent")
PlexAudioCodec = importlib.import_module("Debug.Plex.AudioCodec")
PlexVideoCodec = importlib.import_module("Debug.Plex.VideoCodec")
PlexContainer = importlib.import_module("Debug.Plex.Container")

agentSpec = importlib.util.spec_from_file_location("PlexSportsAgent", "PlexSportsAgent.bundle/Contents/Code/__init__.py")
PlexSportsAgent = importlib.util.module_from_spec(agentSpec)

sys.modules["AudioCodec"] = PlexAudioCodec
sys.modules["VideoCodec"] = PlexVideoCodec
sys.modules["Container"] = PlexContainer

PlexSportsAgent.__setattr__("Agent", PlexAgent)
PlexSportsAgent.__setattr__("AudioCodec", PlexAudioCodec)
PlexSportsAgent.__setattr__("VideoCodec", PlexVideoCodec)
PlexSportsAgent.__setattr__("Container", PlexContainer)

agentSpec.loader.exec_module(PlexSportsAgent)

agent = PlexSportsAgent.PlexSportsAgent()

PlexSportsAgent.Start()

# Load up search results
