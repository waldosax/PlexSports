import re, time, unicodedata, hashlib, types

from Constants import *

def __sort_by_len(x):
    return len(x)
def __sort_by_len_key(x):
    return len(x[0])
def __sort_by_len_value(x):
    return len(x[1])

def __strip_parentheticals(s):
    return s

def __index_of(s, sub, start=0, end=None):
    try:
        return s.index(sub, start, end)
    except ValueError:
        return -1

def __strip_to_alphanumeric_and_at(s):
    (ret, grit) = Boil(s, ALPHANUMERIC_CHARACTERS_AND_AT)
    return ret

def __strip_to_alphanumeric(s):
    (ret, grit) = Boil(s, ALPHANUMERIC_CHARACTERS)
    return ret

def __trim_word_separators(s):
    if not s:
        return s
    return re.sub("(?:^%s+)|(?:%s+$)" % (EXPRESSION_SEPARATOR, EXPRESSION_SEPARATOR), "", s)

def CloseEnough(s1, s2):
    return Util.LevenshteinDistance(s1, s2) == 0


def __expressions_from_literal(literal, escape=True):
    expressions = []

    pieces = re.split(r"%s+" % EXPRESSION_SEPARATOR, literal)

    expr = ""
    expr2 = ""
    for i in range(0, len(pieces)):
        if escape:
            expr += re.escape(pieces[i])
            expr2 += re.escape(pieces[i])
        else:
            expr += pieces[i]
            expr2 += pieces[i]

        # (?P<sp>[\s\.\-_])+
        # (?P=sp)+
        if i < len(pieces) - 1:
            if i == 0:
                expr += "(?P<sp>%s)+" % EXPRESSION_SEPARATOR
            else:
                expr += "(?P=sp)+"

    expressions.append(expr)
    expressions.append(expr2)

    return list(set(expressions))

def Eat(s, exp, eat_once=True):
    """Eats out a regular expression, one or more times, from a string and returns the bites it took as well the remaining string,"""
    if not s:
        return None
    
    bites = []
    m = None
    ms = []
    chewed = s

    p = re.compile(exp, re.IGNORECASE)
    if eat_once:
        m = p.search(s)
        if m:
            bites = [(m, m.string[m.start():m.end()])]
            ms = [m]
    else:
        ms = p.findall(s)
        if ms and len(ms) > 0:
            for m in ms:
                bites.append((m, m.string[m.start():m.end()]))
    chewed = __trim_word_separators(p.sub("", s, count = 1 if eat_once else 0))

    return (bites, chewed, ms)


def Boil(food, charset=ALPHANUMERIC_CHARACTERS_AND_AT):
    """Boils down a string to only character within the specified character set."""
    if not food:
        return (food, [])

    boiled = ""
    map = []
    for i in range(0, len(food)):
        c = food[i].lower()
        if __index_of(charset, c) >= 0:
            boiled += c
            map.append(i)
    return (boiled, map)


CHUNK_BOILED_INDEX = 0
CHUNK_FOOD_INDEX = 1
CHUNK_BOILED_LENGTH = 2
CHUNK_NEXT_FOOD_INDEX = 3


def Taste(boiled, grit, search, startBoiledIndex=0):
    """Returns a chunk tuple with relevant indeces and lengths if search is found within the given boiled string."""
    boiledIndex = __index_of(boiled, search, startBoiledIndex)
    if (boiledIndex >= 0):
        foodIndex = grit[boiledIndex]
        boiledLength = len(search)
        nextFoodIndex = grit[boiledIndex + boiledLength] if (boiledIndex + boiledLength) < len(grit) else -1

        chunk = (boiledIndex, foodIndex, boiledLength, nextFoodIndex)
        return chunk
    return None


def Chew(chunks, grit, food):
    """Reconstitutes a food string, given a list of chunks and a grit mapping, removing the specified chunks."""
    bites = []
    foodIndex = 0
    for chunk in chunks:
        if chunk:
            bites.append(food[foodIndex:grit[chunk[CHUNK_BOILED_INDEX]]])
            foodIndex = chunk[CHUNK_NEXT_FOOD_INDEX]
    bites.append(food[foodIndex:])

    return "".join(bites)

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
