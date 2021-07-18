import sys
import unittest
import bootstrapper

(PlexSportsScanner, UnitTests) = bootstrapper.BootstrapScannerAndUnitTests()

rootDir = r"F:\Code\Plex\PlexSportsLibrary"

def assert_meta_value(meta, key, expected):
    if meta is None:
        raise UnitTests.AssertionException("Expected meta to be a dict, but was None.")
    
    if not isinstance(meta, dict):
        raise UnitTests.AssertionException("Expected meta to be a dict, but was %s.)" % type(meta), meta=meta)

    actual = None
    if not expected and key not in meta.keys():
        pass
    else:
        if not key in meta.keys():
            raise UnitTests.AssertionException("Expected key '%s' to exist in meta.)" % key, meta=meta)
        actual = meta[key]
            
    if not (actual or "") == (expected or ""):
        raise UnitTests.AssertionException("Expected '%s' for key '%s', but was '%s'.)" % (expected, key, actual), meta=meta)

class ForAnyInference(unittest.TestCase):
    def test_ShouldHaveBaseInfoFilledOut(self):
        try:
            # Arrange
            relPath = r"NHL\2018\Playoffs\Quarterfinals\Eastern Conference\2018.04.12.NJ@TB.Game.1.mp4"
            file = r"%s\%s" % (rootDir, relPath)
            meta = dict()

            # Act
            PlexSportsScanner.Metadata.Infer(relPath, file, meta)
            
            # Assert
            assert_meta_value(meta, PlexSportsScanner.METADATA_PATH_KEY, file)
            assert_meta_value(meta, PlexSportsScanner.METADATA_FILENAME_KEY, r"2018.04.12.NJ@TB.Game.1.mp4")
            assert_meta_value(meta, PlexSportsScanner.METADATA_FOLDER_KEY, r"NHL\2018\Playoffs\Quarterfinals\Eastern Conference")
        except Exception, e:
            self.fail(e.message)


class WhenReadingFolderStructure(unittest.TestCase):
    pass

class WhenReadingSportFromFolderStructure(WhenReadingFolderStructure):
    def test_IfSportIsPresent_ShouldHaveSportInfoFilledOut(self):
        for league in PlexSportsScanner.known_leagues.keys():
            try:
                # Arrange
                (leagueName, sport) = PlexSportsScanner.known_leagues[league]
                relPath = r"%s\%s\2018\Playoffs\foo@bar.mp4" % (sport, league)
                file = r"%s\%s" % (rootDir, relPath)
                meta = dict()

                # Act
                PlexSportsScanner.Metadata.Infer(relPath, file, meta)
            
                # Assert
                assert_meta_value(meta, PlexSportsScanner.METADATA_SPORT_KEY, sport)
            except Exception, e:
                self.fail(e.message)


class WhenReadingLeagueFromFolderStructure(WhenReadingFolderStructure):
    def test_IfSportIsNotPresentButKnownLeagueIsPresent_ShouldInferSportFromLeague(self):
        for league in PlexSportsScanner.known_leagues.keys():
            try:
                # Arrange
                (leagueName, sport) = PlexSportsScanner.known_leagues[league]
                relPath = r"%s\2018\Playoffs\foo@bar.mp4" % league
                file = r"%s\%s" % (rootDir, relPath)
                meta = dict()

                # Act
                PlexSportsScanner.Metadata.Infer(relPath, file, meta)
            
                # Assert
                assert_meta_value(meta, PlexSportsScanner.METADATA_SPORT_KEY, sport)
                assert_meta_value(meta, PlexSportsScanner.METADATA_LEAGUE_KEY, league)
            except Exception, e:
                self.fail(e.message)

    def test_IfSportIsPresentAndKnownLeagueIsPresent_ShouldHaveSportAndLeagueInfoFilledOut(self):
        for league in PlexSportsScanner.known_leagues.keys():
            try:
                # Arrange
                (leagueName, sport) = PlexSportsScanner.known_leagues[league]
                relPath = r"%s\%s\2018\Playoffs\foo@bar.mp4" % (sport, league)
                file = r"%s\%s" % (rootDir, relPath)
                meta = dict()

                # Act
                PlexSportsScanner.Metadata.Infer(relPath, file, meta)
            
                # Assert
                assert_meta_value(meta, PlexSportsScanner.METADATA_SPORT_KEY, sport)
                assert_meta_value(meta, PlexSportsScanner.METADATA_LEAGUE_KEY, league)
            except Exception, e:
                self.fail(e.message)

class WhenReadingSeasonFromFolderStructure(WhenReadingFolderStructure):
    pass

class WhenReadingMultiYearSeasonFromFolderStructure(WhenReadingSeasonFromFolderStructure):
    def test_IfSeasonIsPresent_ShouldHaveSeasonInfoFilledOut(self):
        try:
            # Arrange
            relPath = r"NFL\2018-2019\Playoffs\foo@bar.mp4"
            file = r"%s\%s" % (rootDir, relPath)
            meta = dict()

            # Act
            PlexSportsScanner.Metadata.Infer(relPath, file, meta)
            
            # Assert
            assert_meta_value(meta, PlexSportsScanner.METADATA_SEASON_KEY, "2018-2019")
            assert_meta_value(meta, PlexSportsScanner.METADATA_SEASON_BEGIN_YEAR_KEY, 2018)
            assert_meta_value(meta, PlexSportsScanner.METADATA_SEASON_END_YEAR_KEY, 2019)
        except Exception, e:
            self.fail(e.message)

class WhenReadingSingleYearSeasonFromFolderStructure(WhenReadingSeasonFromFolderStructure):
    def test_IfSeasonIsPresent_ShouldHaveSeasonInfoFilledOut(self):
        try:
            # Arrange
            relPath = r"NFL\2018\Playoffs\foo@bar.mp4"
            file = r"%s\%s" % (rootDir, relPath)
            meta = dict()

            # Act
            PlexSportsScanner.Metadata.Infer(relPath, file, meta)
            
            # Assert
            assert_meta_value(meta, PlexSportsScanner.METADATA_SEASON_KEY, "2018")
            assert_meta_value(meta, PlexSportsScanner.METADATA_SEASON_BEGIN_YEAR_KEY, 2018)
            assert_meta_value(meta, PlexSportsScanner.METADATA_SEASON_END_YEAR_KEY, None)
        except Exception, e:
            self.fail(e.message)


class WhenReadingSubseasonFromFolderStructure(WhenReadingFolderStructure):
    def test_IfLeagueAndOrSeasonAreNotKnown_ShouldDoNothing(self):
        for prefix in [r"Football\NFL", r"NFL"]:
            try:
                # Arrange
                relPath = r"%s\Playoffs\foo@bar.mp4" % prefix
                file = r"%s\%s" % (rootDir, relPath)
                meta = dict()

                # Act
                PlexSportsScanner.Metadata.Infer(relPath, file, meta)
            
                # Assert
                assert_meta_value(meta, PlexSportsScanner.METADATA_SUBSEASON_INDICATOR_KEY, None)
                assert_meta_value(meta, PlexSportsScanner.METADATA_SUBSEASON_KEY, None)
            except Exception, e:
                self.fail(e.message)












# NFL-Specific Tests

class WhenReadingNFLSubseasonFromFolderStructure(WhenReadingFolderStructure):
    def test_IfLeagueAndSeasonArePresent_ShouldHaveSubseasonInfoFilledOut(self):
        for (prefix, expected, ind) in [
            ("Preseason", PlexSportsScanner.NFL.NFL_SUBSEASON_PRESEASON, PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_PRESEASON),
            ("Postseason", PlexSportsScanner.NFL.NFL_SUBSEASON_POSTSEASON, PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_POSTSEASON),
            ("Playoffs", PlexSportsScanner.NFL.NFL_SUBSEASON_PLAYOFFS, PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_POSTSEASON),
            ("Regular Season", PlexSportsScanner.NFL.NFL_SUBSEASON_REGULAR_SEASON, PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_REGULAR_SEASON),
            ("RegularSeason", "RegularSeason", PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_REGULAR_SEASON),
            ("AnythingElse", None, None)
            ]:
            try:
                # Arrange
                relPath = r"NFL\2018\%s\foo@bar.mp4" % prefix
                file = r"%s\%s" % (rootDir, relPath)
                meta = dict()

                # Act
                PlexSportsScanner.Metadata.Infer(relPath, file, meta)
            
                # Assert
                assert_meta_value(meta, PlexSportsScanner.METADATA_SUBSEASON_INDICATOR_KEY, ind)
                assert_meta_value(meta, PlexSportsScanner.METADATA_SUBSEASON_KEY, expected)
            except Exception, e:
                self.fail(e.message)

    # TODO: Answer cache
    def test_IfSubseasonIsPlayoffRound_ShouldHavePlayoffRoundFilledOut(self):
        for (prefix, expected, round, ind) in [
            ("AFC Wildcard Round", "AFC Wildcard Round", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_WILDCARD, PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_POSTSEASON),
            ("NFC Wildcard Round", "NFC Wildcard Round", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_WILDCARD, PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_POSTSEASON),
            ("AFC Wildcard", "AFC Wildcard", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_WILDCARD, PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_POSTSEASON),
            ("NFC Wildcard", "NFC Wildcard", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_WILDCARD, PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_POSTSEASON),
            
            ("Wildcard Round", "Wildcard Round", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_WILDCARD, PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_POSTSEASON),
            ("Wildcard", "Wildcard", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_WILDCARD, PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_POSTSEASON),
            

            ("AFC Divisional Round", "AFC Divisional Round", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_DIVISION, PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_POSTSEASON),
            ("NFC Divisional Round", "NFC Divisional Round", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_DIVISION, PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_POSTSEASON),
            ("AFC Division Playoffs", "AFC Division Playoffs", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_DIVISION, PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_POSTSEASON),
            ("NFC Division Playoffs", "NFC Division Playoffs", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_DIVISION, PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_POSTSEASON),

            ("Divisional Round", "Divisional Round", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_DIVISION, PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_POSTSEASON),
            ("Division Playoffs", "Division Playoffs", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_DIVISION, PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_POSTSEASON),
            

            ("AFC Championship Round", "AFC Championship Round", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_CHAMPIONSHIP, PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_POSTSEASON),
            ("NFC Championship Round", "NFC Championship Round", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_CHAMPIONSHIP, PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_POSTSEASON),
            ("AFC Championship", "AFC Championship", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_CHAMPIONSHIP, PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_POSTSEASON),
            ("NFC Championship", "NFC Championship", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_CHAMPIONSHIP, PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_POSTSEASON),

            ("Championship Round", "Championship Round", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_CHAMPIONSHIP, PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_POSTSEASON),
            
            ("Superbowl XXXIX", "Superbowl XXXIX", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_SUPERBOWL, PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_POSTSEASON),
            ("Superbowl LII", "Superbowl LII", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_SUPERBOWL, PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_POSTSEASON),
            ("Superbowl 40", "Superbowl 40", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_SUPERBOWL, PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_POSTSEASON),
            ("Superbowl 23", "Superbowl 23", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_SUPERBOWL, PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_POSTSEASON),
            
            # TODO: Fix expression for superbowl without number
            #("Superbowl", "Superbowl", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_SUPERBOWL, PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_POSTSEASON),
            #("Super bowl", "Super bowl", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_SUPERBOWL, PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_POSTSEASON),
            
            ("AnythingElse", None, None, None)
            ]:
            try:
                # Arrange
                relPath = r"NFL\2018\%s\foo@bar.mp4" % prefix
                file = r"%s\%s" % (rootDir, relPath)
                meta = dict()

                # Act
                PlexSportsScanner.Metadata.Infer(relPath, file, meta)
            
                # Assert
                assert_meta_value(meta, PlexSportsScanner.METADATA_SUBSEASON_KEY, expected)
                assert_meta_value(meta, PlexSportsScanner.METADATA_SUBSEASON_INDICATOR_KEY, ind)
                assert_meta_value(meta, PlexSportsScanner.METADATA_PLAYOFF_ROUND_KEY, round)
                assert_meta_value(meta, PlexSportsScanner.METADATA_EVENT_NAME_KEY, expected)
            except Exception, e:
                self.fail(e.message)

class WhenReadingNFLWeekFromFolderStructure(WhenReadingFolderStructure):
    def test_IfLeagueAndSeasonArePresent_ShouldHaveWeekInfoFilledOut(self):
        for (prefix, expected, ind) in [
            (r"Preseason\Week 1", "Week 1", PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_PRESEASON),
            (r"Preseason\week 2", "week 2", PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_PRESEASON),
            (r"Preseason\Week3", "Week3", PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_PRESEASON),
            (r"Preseason\Week 04", "Week 04", PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_PRESEASON),
            
            (r"Regular Season\Week 1", "Week 1", PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_REGULAR_SEASON),
            (r"Regular Season\Week 2", "Week 2", PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_REGULAR_SEASON),
            (r"Regular Season\Week 3", "Week 3", PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_REGULAR_SEASON),
            (r"Regular Season\Week 4", "Week 4", PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_REGULAR_SEASON),
            (r"Regular Season\Week 5", "Week 5", PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_REGULAR_SEASON),
            (r"Regular Season\Week 6", "Week 6", PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_REGULAR_SEASON),
            (r"Regular Season\Week 7", "Week 7", PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_REGULAR_SEASON),
            (r"Regular Season\Week 8", "Week 8", PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_REGULAR_SEASON),
            (r"Regular Season\Week 9", "Week 9", PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_REGULAR_SEASON),
            (r"Regular Season\Week 10", "Week 10", PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_REGULAR_SEASON),
            (r"Regular Season\Week 11", "Week 11", PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_REGULAR_SEASON),
            (r"Regular Season\Week 12", "Week 12", PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_REGULAR_SEASON),
            (r"Regular Season\Week 13", "Week 13", PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_REGULAR_SEASON),
            (r"Regular Season\Week 14", "Week 14", PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_REGULAR_SEASON),
            (r"Regular Season\Week 15", "Week 15", PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_REGULAR_SEASON),
            (r"Regular Season\Week 16", "Week 16", PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_REGULAR_SEASON),
            (r"Regular Season\Week 17", "Week 17", PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_REGULAR_SEASON),
            
            (r"Week 1", "Week 1", None),
            (r"Week 2", "Week 2", None),
            (r"Week 3", "Week 3", None),
            (r"Week 4", "Week 4", None),
            (r"Week 5", "Week 5", None),
            (r"Week 6", "Week 6", None),
            (r"Week 7", "Week 7", None),
            (r"Week 8", "Week 8", None),
            (r"Week 9", "Week 9", None),
            (r"Week 10", "Week 10", None),
            (r"Week 11", "Week 11", None),
            (r"Week 12", "Week 12", None),
            (r"Week 13", "Week 13", None),
            (r"Week 14", "Week 14", None),
            (r"Week 15", "Week 15", None),
            (r"Week 16", "Week 16", None),
            (r"Week 17", "Week 17", None),
            ("AnythingElse", None, None)
            ]:
            try:
                # Arrange
                relPath = r"NFL\2018\%s\foo@bar.mp4" % prefix
                file = r"%s\%s" % (rootDir, relPath)
                meta = dict()

                # Act
                PlexSportsScanner.Metadata.Infer(relPath, file, meta)
            
                # Assert
                assert_meta_value(meta, PlexSportsScanner.METADATA_SUBSEASON_INDICATOR_KEY, ind)
                assert_meta_value(meta, PlexSportsScanner.METADATA_WEEK_KEY, expected)
            except Exception, e:
                self.fail(e.message)

class WhenReadingNFLPostseasonConferenceFromFolderStructure(WhenReadingFolderStructure):
    def test_IfLeagueAndSeasonArePresent_ShouldHaveConferenceInfoFilledOut(self):
        for (prefix, expected) in [
            ("American Football Conference", PlexSportsScanner.NFL.NFL_CONFERENCE_AFC),
            ("National Football Conference", PlexSportsScanner.NFL.NFL_CONFERENCE_NFC),
            ("AFC", PlexSportsScanner.NFL.NFL_CONFERENCE_AFC),
            ("NFC", PlexSportsScanner.NFL.NFL_CONFERENCE_NFC),
            ("AnythingElse", None)
            ]:
            try:
                # Arrange
                relPath = r"NFL\2018\Playoffs\%s\foo@bar.mp4" % prefix
                file = r"%s\%s" % (rootDir, relPath)
                meta = dict()

                # Act
                PlexSportsScanner.Metadata.Infer(relPath, file, meta)
            
                # Assert
                assert_meta_value(meta, PlexSportsScanner.METADATA_CONFERENCE_KEY, expected)
            except Exception, e:
                self.fail(e.message)

class WhenReadingNFLPlayoffRoundFromFolderStructure(WhenReadingFolderStructure):
    # TODO: Answer cache
    def test_IfSubseasonIsNotPlayoffRound_ShouldHavePlayoffRoundFilledOut(self):
        for (prefix, expected, round) in [
            ("AFC Wildcard Round", "AFC Wildcard Round", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_WILDCARD),
            ("NFC Wildcard Round", "NFC Wildcard Round", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_WILDCARD),
            ("AFC Wildcard", "AFC Wildcard", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_WILDCARD),
            ("NFC Wildcard", "NFC Wildcard", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_WILDCARD),
            
            ("Wildcard Round", "Wildcard Round", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_WILDCARD),
            ("Wildcard", "Wildcard", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_WILDCARD),
            

            ("AFC Divisional Round", "AFC Divisional Round", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_DIVISION),
            ("NFC Divisional Round", "NFC Divisional Round", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_DIVISION),
            ("AFC Division Playoffs", "AFC Division Playoffs", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_DIVISION),
            ("NFC Division Playoffs", "NFC Division Playoffs", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_DIVISION),

            ("Divisional Round", "Divisional Round", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_DIVISION),
            ("Division Playoffs", "Division Playoffs", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_DIVISION),
            

            ("AFC Championship Round", "AFC Championship Round", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("NFC Championship Round", "NFC Championship Round", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("AFC Championship", "AFC Championship", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("NFC Championship", "NFC Championship", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_CHAMPIONSHIP),

            ("Championship Round", "Championship Round", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_CHAMPIONSHIP),
            
            ("Superbowl XXXIX", "Superbowl XXXIX", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_SUPERBOWL),
            ("Superbowl LII", "Superbowl LII", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_SUPERBOWL),
            ("Superbowl 40", "Superbowl 40", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_SUPERBOWL),
            ("Superbowl 23", "Superbowl 23", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_SUPERBOWL),
            
            # TODO: Fix expression for superbowl without number
            #("Superbowl", "Superbowl", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_SUPERBOWL),
            #("Super bowl", "Super bowl", PlexSportsScanner.NFL.NFL_PLAYOFF_ROUND_SUPERBOWL),
            
            ("AnythingElse", None, None)
            ]:
            try:
                # Arrange
                relPath = r"NFL\2018\Postseason\%s\foo@bar.mp4" % prefix
                file = r"%s\%s" % (rootDir, relPath)
                meta = dict()

                # Act
                PlexSportsScanner.Metadata.Infer(relPath, file, meta)
            
                # Assert
                assert_meta_value(meta, PlexSportsScanner.METADATA_SUBSEASON_KEY, "Postseason")
                assert_meta_value(meta, PlexSportsScanner.METADATA_SUBSEASON_INDICATOR_KEY, PlexSportsScanner.NFL.NFL_SUBSEASON_FLAG_POSTSEASON)
                assert_meta_value(meta, PlexSportsScanner.METADATA_PLAYOFF_ROUND_KEY, round)
                assert_meta_value(meta, PlexSportsScanner.METADATA_EVENT_NAME_KEY, expected)
            except Exception, e:
                self.fail(e.message)










# NBA-Specific Tests

class WhenReadingNBASubseasonFromFolderStructure(WhenReadingFolderStructure):
    def test_IfLeagueAndSeasonArePresent_ShouldHaveSubseasonInfoFilledOut(self):
        for (prefix, expected, ind) in [
            ("Preseason", PlexSportsScanner.NBA.NBA_SUBSEASON_PRESEASON, PlexSportsScanner.NBA.NBA_SUBSEASON_FLAG_PRESEASON),
            ("Postseason", PlexSportsScanner.NBA.NBA_SUBSEASON_POSTSEASON, PlexSportsScanner.NBA.NBA_SUBSEASON_FLAG_POSTSEASON),
            ("Playoffs", PlexSportsScanner.NBA.NBA_SUBSEASON_PLAYOFFS, PlexSportsScanner.NBA.NBA_SUBSEASON_FLAG_POSTSEASON),
            ("Regular Season", PlexSportsScanner.NBA.NBA_SUBSEASON_REGULAR_SEASON, PlexSportsScanner.NBA.NBA_SUBSEASON_FLAG_REGULAR_SEASON),
            ("RegularSeason", "RegularSeason", PlexSportsScanner.NBA.NBA_SUBSEASON_FLAG_REGULAR_SEASON),
            ("AnythingElse", None, None)
            ]:
            try:
                # Arrange
                relPath = r"NBA\2018\%s\foo@bar.mp4" % prefix
                file = r"%s\%s" % (rootDir, relPath)
                meta = dict()

                # Act
                PlexSportsScanner.Metadata.Infer(relPath, file, meta)
            
                # Assert
                assert_meta_value(meta, PlexSportsScanner.METADATA_SUBSEASON_INDICATOR_KEY, ind)
                assert_meta_value(meta, PlexSportsScanner.METADATA_SUBSEASON_KEY, expected)
            except Exception, e:
                self.fail(e.message)


    # TODO: Answer cache
    def test_IfSubseasonIsPlayoffRound_ShouldHavePlayoffRoundFilledOut(self):
        for (prefix, expected, ind, round) in [
            ("Eastern Conference Quarterfinals", "Eastern Conference Quarterfinals", PlexSportsScanner.NBA.NBA_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.NBA.NBA_PLAYOFF_ROUND_QUARTERFINALS),
            ("Western Conference Quarterfinals", "Western Conference Quarterfinals", PlexSportsScanner.NBA.NBA_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.NBA.NBA_PLAYOFF_ROUND_QUARTERFINALS),
            ("East Quarterfinals", "East Quarterfinals", PlexSportsScanner.NBA.NBA_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.NBA.NBA_PLAYOFF_ROUND_QUARTERFINALS),
            ("West Quarterfinals", "West Quarterfinals", PlexSportsScanner.NBA.NBA_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.NBA.NBA_PLAYOFF_ROUND_QUARTERFINALS),
            ("Quarterfinals", "Quarterfinals", PlexSportsScanner.NBA.NBA_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.NBA.NBA_PLAYOFF_ROUND_QUARTERFINALS),
            

            ("Eastern Conference Finals", "Eastern Conference Finals", PlexSportsScanner.NBA.NBA_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.NBA.NBA_PLAYOFF_ROUND_SEMIFINALS),
            ("Western Conference Finals", "Western Conference Finals", PlexSportsScanner.NBA.NBA_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.NBA.NBA_PLAYOFF_ROUND_SEMIFINALS),
            ("Eastern Conference Semifinals", "Eastern Conference Semifinals", PlexSportsScanner.NBA.NBA_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.NBA.NBA_PLAYOFF_ROUND_SEMIFINALS),
            ("Western Conference Semifinals", "Western Conference Semifinals", PlexSportsScanner.NBA.NBA_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.NBA.NBA_PLAYOFF_ROUND_SEMIFINALS),
            ("East Semifinals", "East Semifinals", PlexSportsScanner.NBA.NBA_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.NBA.NBA_PLAYOFF_ROUND_SEMIFINALS),
            ("West Semifinals", "West Semifinals", PlexSportsScanner.NBA.NBA_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.NBA.NBA_PLAYOFF_ROUND_SEMIFINALS),
            ("Semifinals", "Semifinals", PlexSportsScanner.NBA.NBA_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.NBA.NBA_PLAYOFF_ROUND_SEMIFINALS),
            

            ("Championship", "Championship", PlexSportsScanner.NBA.NBA_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.NBA.NBA_PLAYOFF_ROUND_FINALS),
            ("Finals", "Finals", PlexSportsScanner.NBA.NBA_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.NBA.NBA_PLAYOFF_ROUND_FINALS),
            
            ("AnythingElse", None, None, None)
            ]:
            try:
                # Arrange
                relPath = r"NBA\2018\%s\foo@bar.mp4" % prefix
                file = r"%s\%s" % (rootDir, relPath)
                meta = dict()

                # Act
                PlexSportsScanner.Metadata.Infer(relPath, file, meta)
            
                # Assert
                assert_meta_value(meta, PlexSportsScanner.METADATA_SUBSEASON_KEY, expected)
                assert_meta_value(meta, PlexSportsScanner.METADATA_SUBSEASON_INDICATOR_KEY, ind)
                assert_meta_value(meta, PlexSportsScanner.METADATA_PLAYOFF_ROUND_KEY, round)
                assert_meta_value(meta, PlexSportsScanner.METADATA_EVENT_NAME_KEY, expected)
            except Exception, e:
                self.fail(e.message)




class WhenReadingNBAPlayoffRoundFromFolderStructure(WhenReadingFolderStructure):
    # TODO: Answer cache
    def test_IfSubseasonIsNotPlayoffRound_ShouldHavePlayoffRoundFilledOut(self):
        for (prefix, expected, round) in [
            ("Eastern Conference Quarterfinals", "Eastern Conference Quarterfinals", PlexSportsScanner.NBA.NBA_PLAYOFF_ROUND_QUARTERFINALS),
            ("Western Conference Quarterfinals", "Western Conference Quarterfinals", PlexSportsScanner.NBA.NBA_PLAYOFF_ROUND_QUARTERFINALS),
            ("East Quarterfinals", "East Quarterfinals", PlexSportsScanner.NBA.NBA_PLAYOFF_ROUND_QUARTERFINALS),
            ("West Quarterfinals", "West Quarterfinals", PlexSportsScanner.NBA.NBA_PLAYOFF_ROUND_QUARTERFINALS),
            ("Quarterfinals", "Quarterfinals", PlexSportsScanner.NBA.NBA_PLAYOFF_ROUND_QUARTERFINALS),
            

            ("Eastern Conference Finals", "Eastern Conference Finals", PlexSportsScanner.NBA.NBA_PLAYOFF_ROUND_SEMIFINALS),
            ("Western Conference Finals", "Western Conference Finals", PlexSportsScanner.NBA.NBA_PLAYOFF_ROUND_SEMIFINALS),
            ("Eastern Conference Semifinals", "Eastern Conference Semifinals", PlexSportsScanner.NBA.NBA_PLAYOFF_ROUND_SEMIFINALS),
            ("Western Conference Semifinals", "Western Conference Semifinals", PlexSportsScanner.NBA.NBA_PLAYOFF_ROUND_SEMIFINALS),
            ("East Semifinals", "East Semifinals", PlexSportsScanner.NBA.NBA_PLAYOFF_ROUND_SEMIFINALS),
            ("West Semifinals", "West Semifinals", PlexSportsScanner.NBA.NBA_PLAYOFF_ROUND_SEMIFINALS),
            ("Semifinals", "Semifinals", PlexSportsScanner.NBA.NBA_PLAYOFF_ROUND_SEMIFINALS),
            

            ("Championship", "Championship", PlexSportsScanner.NBA.NBA_PLAYOFF_ROUND_FINALS),
            ("Finals", "Finals", PlexSportsScanner.NBA.NBA_PLAYOFF_ROUND_FINALS),
            
            ("AnythingElse", None, None)
            ]:
            try:
                # Arrange
                relPath = r"NBA\2018\Playoffs\%s\foo@bar.mp4" % prefix
                file = r"%s\%s" % (rootDir, relPath)
                meta = dict()

                # Act
                PlexSportsScanner.Metadata.Infer(relPath, file, meta)
            
                # Assert
                assert_meta_value(meta, PlexSportsScanner.METADATA_SUBSEASON_KEY, "Playoffs")
                assert_meta_value(meta, PlexSportsScanner.METADATA_SUBSEASON_INDICATOR_KEY, PlexSportsScanner.NBA.NBA_SUBSEASON_FLAG_POSTSEASON)
                assert_meta_value(meta, PlexSportsScanner.METADATA_PLAYOFF_ROUND_KEY, round)
                assert_meta_value(meta, PlexSportsScanner.METADATA_EVENT_NAME_KEY, expected)
            except Exception, e:
                self.fail(e.message)

class WhenReadingNBAPostseasonConferenceFromFolderStructure(WhenReadingFolderStructure):
    def test_IfLeagueAndSeasonArePresent_ShouldHaveConferenceInfoFilledOut(self):
        for (prefix, expected) in [
            ("Eastern Conference", PlexSportsScanner.NBA.NBA_CONFERENCE_EAST),
            ("Western Conference", PlexSportsScanner.NBA.NBA_CONFERENCE_WEST),
            ("East", PlexSportsScanner.NBA.NBA_CONFERENCE_EAST),
            ("West", PlexSportsScanner.NBA.NBA_CONFERENCE_WEST),
            ("AnythingElse", None)
            ]:
            try:
                # Arrange
                relPath = r"NBA\2018\Postseason\%s\foo@bar.mp4" % prefix
                file = r"%s\%s" % (rootDir, relPath)
                meta = dict()

                # Act
                PlexSportsScanner.Metadata.Infer(relPath, file, meta)
            
                # Assert
                assert_meta_value(meta, PlexSportsScanner.METADATA_CONFERENCE_KEY, expected)
            except Exception, e:
                self.fail(e.message)






# NHL-Specific Tests

class WhenReadingNHLSubseasonFromFolderStructure(WhenReadingFolderStructure):
    def test_IfLeagueAndSeasonArePresent_ShouldHaveSubseasonInfoFilledOut(self):
        for (prefix, expected, ind) in [
            ("Preseason", PlexSportsScanner.NHL.NHL_SUBSEASON_PRESEASON, PlexSportsScanner.NHL.NHL_SUBSEASON_FLAG_PRESEASON),
            ("Postseason", PlexSportsScanner.NHL.NHL_SUBSEASON_POSTSEASON, PlexSportsScanner.NHL.NHL_SUBSEASON_FLAG_POSTSEASON),
            ("Playoffs", PlexSportsScanner.NHL.NHL_SUBSEASON_PLAYOFFS, PlexSportsScanner.NHL.NHL_SUBSEASON_FLAG_POSTSEASON),
            ("Regular Season", PlexSportsScanner.NHL.NHL_SUBSEASON_REGULAR_SEASON, PlexSportsScanner.NHL.NHL_SUBSEASON_FLAG_REGULAR_SEASON),
            ("RegularSeason", "RegularSeason", PlexSportsScanner.NHL.NHL_SUBSEASON_FLAG_REGULAR_SEASON),
            ("Stanley Cup", PlexSportsScanner.NHL.NHL_SUBSEASON_STANLEY_CUP, PlexSportsScanner.NHL.NHL_SUBSEASON_FLAG_POSTSEASON),
            ("Stanley Cup Playoffs", "Stanley Cup Playoffs", PlexSportsScanner.NHL.NHL_SUBSEASON_FLAG_POSTSEASON),
            ("Stanleycup", "Stanleycup", PlexSportsScanner.NHL.NHL_SUBSEASON_FLAG_POSTSEASON),
            ("AnythingElse", None, None)
            ]:
            try:
                # Arrange
                relPath = r"NHL\2018\%s\foo@bar.mp4" % prefix
                file = r"%s\%s" % (rootDir, relPath)
                meta = dict()

                # Act
                PlexSportsScanner.Metadata.Infer(relPath, file, meta)
            
                # Assert
                assert_meta_value(meta, PlexSportsScanner.METADATA_SUBSEASON_INDICATOR_KEY, ind)
                assert_meta_value(meta, PlexSportsScanner.METADATA_SUBSEASON_KEY, expected)
            except Exception, e:
                self.fail(e.message)


    # TODO: Answer cache
    def test_IfSubseasonIsPlayoffRound_ShouldHavePlayoffRoundFilledOut(self):
        for (prefix, expected, ind, round) in [
            ("1st Round", "1st Round", PlexSportsScanner.NHL.NHL_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_1),
            ("First Round", "First Round", PlexSportsScanner.NHL.NHL_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_1),
            ("Round 1", "Round 1", PlexSportsScanner.NHL.NHL_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_1),
            
            ("2nd Round", "2nd Round", PlexSportsScanner.NHL.NHL_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_2),
            ("Second Round", "Second Round", PlexSportsScanner.NHL.NHL_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_2),
            ("Round 2", "Round 2", PlexSportsScanner.NHL.NHL_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_2),
            
            ("3rd Round", "3rd Round", PlexSportsScanner.NHL.NHL_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_3),
            ("Third Round", "Third Round", PlexSportsScanner.NHL.NHL_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_3),
            ("Round 3", "Round 3", PlexSportsScanner.NHL.NHL_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_3),
            ("Conference Finals", "Conference Finals", PlexSportsScanner.NHL.NHL_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_3),
            
            ("4th Round", "4th Round", PlexSportsScanner.NHL.NHL_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_STANLEY_CUP),
            ("Fourth Round", "Fourth Round", PlexSportsScanner.NHL.NHL_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_STANLEY_CUP),
            ("Round 4", "Round 4", PlexSportsScanner.NHL.NHL_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_STANLEY_CUP),
            ("Stanley Cup Finals", "Stanley Cup Finals", PlexSportsScanner.NHL.NHL_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_STANLEY_CUP),
            ("Stanley Cup Playoffs", "Stanley Cup Playoffs", PlexSportsScanner.NHL.NHL_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_STANLEY_CUP),
            ("Stanley Cup", "Stanley Cup", PlexSportsScanner.NHL.NHL_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_STANLEY_CUP),
            
            ("AnythingElse", None, None, None)
            ]:
            try:
                # Arrange
                relPath = r"NHL\2018\%s\foo@bar.mp4" % prefix
                file = r"%s\%s" % (rootDir, relPath)
                meta = dict()

                # Act
                PlexSportsScanner.Metadata.Infer(relPath, file, meta)
            
                # Assert
                assert_meta_value(meta, PlexSportsScanner.METADATA_SUBSEASON_KEY, expected)
                assert_meta_value(meta, PlexSportsScanner.METADATA_SUBSEASON_INDICATOR_KEY, ind)
                assert_meta_value(meta, PlexSportsScanner.METADATA_PLAYOFF_ROUND_KEY, round)
                assert_meta_value(meta, PlexSportsScanner.METADATA_EVENT_NAME_KEY, expected)
            except Exception, e:
                self.fail(e.message)

class WhenReadingNHLPlayoffRoundFromFolderStructure(WhenReadingFolderStructure):
    # TODO: Answer cache
    def test_IfSubseasonIsNotPlayoffRound_ShouldHavePlayoffRoundFilledOut(self):
        for (prefix, expected, round) in [
            ("1st Round", "1st Round", PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_1),
            ("First Round", "First Round", PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_1),
            ("Round 1", "Round 1", PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_1),
            
            ("2nd Round", "2nd Round", PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_2),
            ("Second Round", "Second Round", PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_2),
            ("Round 2", "Round 2", PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_2),
            
            ("3rd Round", "3rd Round", PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_3),
            ("Third Round", "Third Round", PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_3),
            ("Round 3", "Round 3", PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_3),
            ("Conference Finals", "Conference Finals", PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_3),
            
            ("4th Round", "4th Round", PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_STANLEY_CUP),
            ("Fourth Round", "Fourth Round", PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_STANLEY_CUP),
            ("Round 4", "Round 4", PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_STANLEY_CUP),
            ("Stanley Cup Finals", "Stanley Cup Finals", PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_STANLEY_CUP),
            ("Stanley Cup Playoffs", "Stanley Cup Playoffs", PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_STANLEY_CUP),
            ("Stanley Cup", "Stanley Cup", PlexSportsScanner.NHL.NHL_PLAYOFF_ROUND_STANLEY_CUP),
            
            ("AnythingElse", None, None)
            ]:
            try:
                # Arrange
                relPath = r"NHL\2018\Playoffs\%s\foo@bar.mp4" % prefix
                file = r"%s\%s" % (rootDir, relPath)
                meta = dict()

                # Act
                PlexSportsScanner.Metadata.Infer(relPath, file, meta)
            
                # Assert
                assert_meta_value(meta, PlexSportsScanner.METADATA_SUBSEASON_KEY, "Playoffs")
                assert_meta_value(meta, PlexSportsScanner.METADATA_SUBSEASON_INDICATOR_KEY, PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON)
                assert_meta_value(meta, PlexSportsScanner.METADATA_PLAYOFF_ROUND_KEY, round)
                assert_meta_value(meta, PlexSportsScanner.METADATA_EVENT_NAME_KEY, expected)
            except Exception, e:
                self.fail(e.message)










# MLB-Specific Tests

class WhenReadingMLBSubseasonFromFolderStructure(WhenReadingFolderStructure):
    def test_IfLeagueAndSeasonArePresent_ShouldHaveSubseasonInfoFilledOut(self):
        for (prefix, expected, ind) in [
            ("Preseason", PlexSportsScanner.MLB.MLB_SUBSEASON_PRESEASON, PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_PRESEASON),
            ("Spring Training", PlexSportsScanner.MLB.MLB_SUBSEASON_SPRING_TRAINING, PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_PRESEASON),
            ("Postseason", PlexSportsScanner.MLB.MLB_SUBSEASON_POSTSEASON, PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON),
            ("Playoffs", PlexSportsScanner.MLB.MLB_SUBSEASON_PLAYOFFS, PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON),
            ("Regular Season", PlexSportsScanner.MLB.MLB_SUBSEASON_REGULAR_SEASON, PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_REGULAR_SEASON),
            ("RegularSeason", "RegularSeason", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_REGULAR_SEASON),
            ("AnythingElse", None, None)
            ]:
            try:
                # Arrange
                relPath = r"MLB\2018\%s\foo@bar.mp4" % prefix
                file = r"%s\%s" % (rootDir, relPath)
                meta = dict()

                # Act
                PlexSportsScanner.Metadata.Infer(relPath, file, meta)
            
                # Assert
                assert_meta_value(meta, PlexSportsScanner.METADATA_SUBSEASON_INDICATOR_KEY, ind)
                assert_meta_value(meta, PlexSportsScanner.METADATA_SUBSEASON_KEY, expected)
            except Exception, e:
                self.fail(e.message)

    # TODO: Answer cache
    def test_IfSubseasonIsPlayoffRound_ShouldHavePlayoffRoundFilledOut(self):
        for (prefix, expected, ind, round) in [
            ("American League Wildcard Round", "American League Wildcard Round", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WILDCARD),
            ("National League Wildcard Round", "National League Wildcard Round", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WILDCARD),
            ("American League Wildcard Series", "American League Wildcard Series", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WILDCARD),
            ("National League Wildcard Series", "National League Wildcard Series", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WILDCARD),
            ("American League Wildcard", "American League Wildcard", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WILDCARD),
            ("National League Wildcard", "National League Wildcard", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WILDCARD),
            ("AL Wildcard Round", "AL Wildcard Round", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WILDCARD),
            ("NL Wildcard Round", "NL Wildcard Round", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WILDCARD),
            ("AL Wildcard Series", "AL Wildcard Series", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WILDCARD),
            ("NL Wildcard Series", "NL Wildcard Series", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WILDCARD),
            ("AL Wildcard", "AL Wildcard", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WILDCARD),
            ("NL Wildcard", "NL Wildcard", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WILDCARD),
            
            ("Wildcard Round", "Wildcard Round", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WILDCARD),
            ("Wildcard Series", "Wildcard Series", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WILDCARD),
            ("Wildcard", "Wildcard", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WILDCARD),
            

            ("American League Divisional Round", "American League Divisional Round", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("National League Divisional Round", "National League Divisional Round", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("American League Division Round", "American League Division Round", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("National League Division Round", "National League Division Round", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("American League Divisional Series", "American League Divisional Series", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("National League Divisional Series", "National League Divisional Series", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("American League Division Series", "American League Division Series", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("National League Division Series", "National League Division Series", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("American League Division Playoffs", "American League Division Playoffs", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("National League Division Playoffs", "National League Division Playoffs", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("AL Divisional Round", "AL Divisional Round", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("NL Divisional Round", "NL Divisional Round", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("AL Division Round", "AL Division Round", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("NL Division Round", "NL Division Round", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("AL Divisional Series", "AL Divisional Series", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("NL Divisional Series", "NL Divisional Series", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("AL Division Series", "AL Division Series", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("NL Division Series", "NL Division Series", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("AL Division Playoffs", "AL Division Playoffs", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("NL Division Playoffs", "NL Division Playoffs", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            
            ("ALDS", "ALDS", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("NLDS", "NLDS", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),

            ("Divisional Round", "Divisional Round", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("Division Round", "Division Round", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("Divisional Series", "Divisional Series", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("Division Series", "Division Series", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            

            ("American League Championship Round", "American League Championship Round", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("National League Championship Round", "National League Championship Round", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("American League Championship Series", "American League Championship Series", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("National League Championship Series", "National League Championship Series", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("American League Championship Series", "American League Championship Series", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("National League Championship Series", "National League Championship Series", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("American League Championship Playoffs", "American League Championship Playoffs", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("National League Championship Playoffs", "National League Championship Playoffs", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("AL Championship Round", "AL Championship Round", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("NL Championship Round", "NL Championship Round", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("AL Championship Series", "AL Championship Series", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("NL Championship Series", "NL Championship Series", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("AL Championship Series", "AL Championship Series", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("NL Championship Series", "NL Championship Series", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("AL Championship Playoffs", "AL Championship Playoffs", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("NL Championship Playoffs", "NL Championship Playoffs", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            
            ("ALCS", "ALCS", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("NLCS", "NLCS", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),

            ("Championship Round", "Championship Round", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("Championship Series", "Championship Series", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            

            ("World Series", "World Series", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WORLD_SERIES),
            ("worldseries", "worldseries", PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON, PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WORLD_SERIES),
            
            ("AnythingElse", None, None, None)
            ]:
            try:
                # Arrange
                relPath = r"MLB\2018\%s\foo@bar.mp4" % prefix
                file = r"%s\%s" % (rootDir, relPath)
                meta = dict()

                # Act
                PlexSportsScanner.Metadata.Infer(relPath, file, meta)
            
                # Assert
                assert_meta_value(meta, PlexSportsScanner.METADATA_SUBSEASON_KEY, expected)
                assert_meta_value(meta, PlexSportsScanner.METADATA_SUBSEASON_INDICATOR_KEY, ind)
                assert_meta_value(meta, PlexSportsScanner.METADATA_PLAYOFF_ROUND_KEY, round)
                assert_meta_value(meta, PlexSportsScanner.METADATA_EVENT_NAME_KEY, expected)
            except Exception, e:
                self.fail(e.message)




class WhenReadingMLBPlayoffRoundFromFolderStructure(WhenReadingFolderStructure):
    # TODO: Answer cache
    def test_IfSubseasonIsNotPlayoffRound_ShouldHavePlayoffRoundFilledOut(self):
        for (prefix, expected, round) in [
            ("American League Wildcard Round", "American League Wildcard Round", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WILDCARD),
            ("National League Wildcard Round", "National League Wildcard Round", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WILDCARD),
            ("American League Wildcard Series", "American League Wildcard Series", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WILDCARD),
            ("National League Wildcard Series", "National League Wildcard Series", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WILDCARD),
            ("American League Wildcard", "American League Wildcard", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WILDCARD),
            ("National League Wildcard", "National League Wildcard", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WILDCARD),
            ("AL Wildcard Round", "AL Wildcard Round", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WILDCARD),
            ("NL Wildcard Round", "NL Wildcard Round", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WILDCARD),
            ("AL Wildcard Series", "AL Wildcard Series", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WILDCARD),
            ("NL Wildcard Series", "NL Wildcard Series", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WILDCARD),
            ("AL Wildcard", "AL Wildcard", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WILDCARD),
            ("NL Wildcard", "NL Wildcard", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WILDCARD),
            
            ("Wildcard Round", "Wildcard Round", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WILDCARD),
            ("Wildcard Series", "Wildcard Series", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WILDCARD),
            ("Wildcard", "Wildcard", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WILDCARD),
            

            ("American League Divisional Round", "American League Divisional Round", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("National League Divisional Round", "National League Divisional Round", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("American League Division Round", "American League Division Round", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("National League Division Round", "National League Division Round", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("American League Divisional Series", "American League Divisional Series", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("National League Divisional Series", "National League Divisional Series", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("American League Division Series", "American League Division Series", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("National League Division Series", "National League Division Series", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("American League Division Playoffs", "American League Division Playoffs", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("National League Division Playoffs", "National League Division Playoffs", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("AL Divisional Round", "AL Divisional Round", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("NL Divisional Round", "NL Divisional Round", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("AL Division Round", "AL Division Round", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("NL Division Round", "NL Division Round", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("AL Divisional Series", "AL Divisional Series", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("NL Divisional Series", "NL Divisional Series", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("AL Division Series", "AL Division Series", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("NL Division Series", "NL Division Series", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("AL Division Playoffs", "AL Division Playoffs", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("NL Division Playoffs", "NL Division Playoffs", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            
            ("ALDS", "ALDS", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("NLDS", "NLDS", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),

            ("Divisional Round", "Divisional Round", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("Division Round", "Division Round", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("Divisional Series", "Divisional Series", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            ("Division Series", "Division Series", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_DIVISION),
            

            ("American League Championship Round", "American League Championship Round", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("National League Championship Round", "National League Championship Round", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("American League Championship Series", "American League Championship Series", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("National League Championship Series", "National League Championship Series", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("American League Championship Series", "American League Championship Series", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("National League Championship Series", "National League Championship Series", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("American League Championship Playoffs", "American League Championship Playoffs", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("National League Championship Playoffs", "National League Championship Playoffs", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("AL Championship Round", "AL Championship Round", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("NL Championship Round", "NL Championship Round", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("AL Championship Series", "AL Championship Series", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("NL Championship Series", "NL Championship Series", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("AL Championship Series", "AL Championship Series", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("NL Championship Series", "NL Championship Series", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("AL Championship Playoffs", "AL Championship Playoffs", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("NL Championship Playoffs", "NL Championship Playoffs", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            
            ("ALCS", "ALCS", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("NLCS", "NLCS", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),

            ("Championship Round", "Championship Round", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            ("Championship Series", "Championship Series", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_CHAMPIONSHIP),
            

            ("World Series", "World Series", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WORLD_SERIES),
            ("worldseries", "worldseries", PlexSportsScanner.MLB.MLB_PLAYOFF_ROUND_WORLD_SERIES),
            
            ("AnythingElse", None, None)
            ]:
            try:
                # Arrange
                relPath = r"MLB\2018\Playoffs\%s\foo@bar.mp4" % prefix
                file = r"%s\%s" % (rootDir, relPath)
                meta = dict()

                # Act
                PlexSportsScanner.Metadata.Infer(relPath, file, meta)
            
                # Assert
                assert_meta_value(meta, PlexSportsScanner.METADATA_SUBSEASON_KEY, "Playoffs")
                assert_meta_value(meta, PlexSportsScanner.METADATA_SUBSEASON_INDICATOR_KEY, PlexSportsScanner.MLB.MLB_SUBSEASON_FLAG_POSTSEASON)
                assert_meta_value(meta, PlexSportsScanner.METADATA_PLAYOFF_ROUND_KEY, round)
                assert_meta_value(meta, PlexSportsScanner.METADATA_EVENT_NAME_KEY, expected)
            except Exception, e:
                self.fail(e.message)







if __name__ == '__main__':
    unittest.main()
