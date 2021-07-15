import re, time, unicodedata, hashlib, types

from Constants import *

def __sort_by_len(x):
    return len(x)
def __sort_by_len_key(x):
    return len(x[0])
def __sort_by_len_value(x):
    return len(x[1])

def __strip_punctuation(s):
    return s

def __strip_parentheticals(s):
    return s

def __index_of(s, sub, start=0, end=None):
    try:
        return s.index(sub, start, end)
    except ValueError:
        return -1

def __strip_to_alphanumeric_and_at(s):
    if not s:
        return s

    ret = ""
    for i in range(0, len(s)):
        c = s[i].lower()
        if __index_of(ALPHANUMERIC_CHARACTERS_AND_AT, c) >= 0:
            ret += c
    return ret

def __strip_to_alphanumeric(s):
    if not s:
        return s

    ret = ""
    for i in range(0, len(s)):
        c = s[i].lower()
        if __index_of(ALPHANUMERIC_CHARACTERS, c) >= 0:
            ret += c
    return ret

def __trim_word_separators(s):
    if not s:
        return s
    return re.sub("(?:^[\s\.\-_]+)|(?:[\s\.\-_]+$)", "", s)

def CloseEnough(s1, s2):
    return Util.LevenshteinDistance(s1, s2) == 0


def __expressions_from_literal(literal, escape=True):
    expressions = []

    pieces = re.split(r"[\s\.\-_]+", literal)
    for separator in [" ", r"\.", r"\-", "_"]:
        expr = ""
        for i in range(0, len(pieces)):
            if escape:
                expr += re.escape(pieces[i])
            else:
                expr += pieces[i]

            if i < len(pieces) - 1:
                expr += separator
        expressions.append(expr)

    return list(set(expressions))

def Eat(s, exp, eat_once=True):
    if not s:
        return None
    
    bites = []
    m = None
    chewed = s

    p = re.compile(exp, re.IGNORECASE)
    if eat_once:
        m = p.search(s)
        if m:
            bites = [(m, m.string[m.start():m.end()])]
    else:
        ms = p.findall(s)
        if ms and len(ms) > 0:
            for m in ms:
                bites.append((m, m.string[m.start():m.end()]))
    chewed = __trim_word_separators(p.sub("", s, count = 1 if eat_once else 0))

    return (bites, chewed)

#def __trim_chars(s, chars=[' ']):
#    return __ltrim_chars(__rtrim_chars(s, chars), chars)

#def __ltrim_chars(s, chars=[' ']):
#    if not s:
#        return s

#    startIndex = 0
#    current = 0
#    while True:
#        foundLeadingChar = False
#        for c in chars:
#            if foundLeadingChar:
#                break
#            if s[current:len(c)] == c:
#                startIndex = current + len(c)
#                current = startIndex
#                foundLeadingChar = True
#        if not foundLeadingChar:
#            break

#    retun s[startIndex:]

#def __rtrim_chars(s, chars=[' ']):
#    if not s:
#        return s

#    endPosition = len(s)
#    current = len(s)
#    while True:
#        foundTrailingChar = False
#        for c in chars:
#            if foundTrailingChar:
#                break
#            if s[current-len(c)-1:current:] == c:
#                endPosition = current - len(c)
#                current = endPosition
#                foundTrailingChar = True
#        if not foundTrailingChar:
#            break

#    retun s[:endPosition]
