
# Local package
from Constants import *
from . import RomanNumerals

NFL_CONFERENCE_AFC = "AFC"
NFL_CONFERENCE_NFC = "NFC"

NFL_CONFERENCE_NAME_AFC = "American Football Conference"
NFL_CONFERENCE_NAME_NFC = "National Football Conference"

nfl_conferences = {
    NFL_CONFERENCE_AFC: NFL_CONFERENCE_NAME_AFC,
    NFL_CONFERENCE_NFC: NFL_CONFERENCE_NAME_NFC
    }

def Touchdown():
    print("Six points!")
    for roman in [
        "I", "II", "III", "IV", "V", "VI", "VII", "viii", "IX", "X",
        "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX",
        "MCMLXXXIV"
        ]:
        print("\t%s: %s" % (roman, RomanNumerals.Parse(roman)))






def InferSubseasonFromFolder(filename, folder, meta):
    pass