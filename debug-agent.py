import importlib
import os
import sys

bundlePath = "PlexSportsAgent.bundle"
sharedLibraryPath = os.path.join(bundlePath, "Contents/Libraries/Shared")

PlexAgent = importlib.import_module("Debug.Plex.Agent")
PlexAudioCodec = importlib.import_module("Debug.Plex.AudioCodec")
PlexVideoCodec = importlib.import_module("Debug.Plex.VideoCodec")
PlexContainer = importlib.import_module("Debug.Plex.Container")

agentSpec = importlib.util.spec_from_file_location("PlexSportsAgent", "PlexSportsAgent.bundle/Contents/Code/__init__.py")
sharedLibraries = os.listdir(sharedLibraryPath)
sharedLibrarySpecs = list(
    map(
        lambda lib: 
            (lib, importlib.util.spec_from_file_location(lib, os.path.join(sharedLibraryPath, lib, "__init__.py"))),
        sharedLibraries
    )
)
for shared in sharedLibrarySpecs:
    sys.modules[shared[0]] = shared[1]

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
