
import bootstrapper

(PlexSportsScanner, UnitTests) = bootstrapper.BootstrapScannerAndUnitTests()

#def assert_meta_value(meta, key, expected):
#	if meta is None:
#		raise AssertionException("Expected meta to be a dict, but was None.")
	
#	if not isinstance(meta, dict):
#		raise AssertionException("Expected meta to be a dict, but was %s.)" % type(meta))

#	if not key in meta.keys():
#		raise AssertionException("Expected key '%s' to exist in meta.)" % key)

#	actual = meta[key]
#	if not actual == expected:
#		raise AssertionException("Expected '%s' for key '%s', but was '%s'.)" % (expected, key, actual))


def TestMetadata_Infer():
	relPath = r"NHL\2018\Playoffs\Quarterfinals\Eastern Conference\2018.04.12.NJ@TB.Game.1.mp4"
	file = "F:\Code\Plex\PlexSportsLibrary\NHL\2018\Playoffs\Quarterfinals\Eastern Conference\2018.04.12.NJ@TB.Game.1.mp4"
	meta = dict()

	PlexSportsScanner.Metadata.Infer(relPath, file, meta)

	pass




if __name__ == "__main__":
	TestMetadata_Infer()
