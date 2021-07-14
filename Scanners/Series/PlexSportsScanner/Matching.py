import re, time, unicodedata, hashlib, types

def __strip_punctuation(s):
    return s

def __strip_parentheticals(s):
    return s

def CloseEnough(s1, s2):
    return Util.LevenshteinDistance(s1, s2) == 0


def __expressions_from_literal(literal, escape=True):
    expressions = []

    pieces = re.split(r"[\s\.\-]+", literal)
    for separator in [" ", r"\.", r"\-"]:
        expr = ""
        for i in range(0, len(pieces)):
            if escape:
                expr += re.escape(pieces[i])
            else:
                expr += pieces[i]

            if i < len(pieces) - 1:
                expr += separator
        expressions.append(expr)

    return expressions