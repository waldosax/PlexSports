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
    grit = [] # grit[index_in_boiled_string] = index_in_original_string
    for i in range(0, len(food)):
        c = food[i].lower()
        if __index_of(charset, c) >= 0:
            boiled += c
            grit.append(i)
    return (boiled, grit)


CHUNK_BOILED_INDEX = 0
CHUNK_FOOD_INDEX = 1
CHUNK_BOILED_LENGTH = 2
CHUNK_NEXT_BOILED_INDEX = 3
CHUNK_NEXT_FOOD_INDEX = 4


def Taste(boiled, grit, search, startBoiledIndex=0):
    """Returns a chunk tuple with relevant indeces and lengths if search is found within the given boiled string."""
    boiledIndex = __index_of(boiled, search, startBoiledIndex)
    if (boiledIndex >= 0):
        foodIndex = grit[boiledIndex]
        boiledLength = len(search)
        nextBoiledIndex = boiledIndex + boiledLength if (boiledIndex + boiledLength) < len(boiled) else -1
        nextFoodIndex = grit[boiledIndex + boiledLength] if (boiledIndex + boiledLength) < len(grit) else -1

        chunk = (boiledIndex, foodIndex, boiledLength, nextBoiledIndex, nextFoodIndex)
        return chunk
    return None


def Chew(chunks, grit, food):
    """Reconstitutes a food string, given a list of chunks and a grit mapping, removing the specified chunks."""
    bites = []
    foodIndex = 0
    for chunk in chunks:
        if chunk:
            bites.append(food[foodIndex:chunk[CHUNK_FOOD_INDEX]])
            foodIndex = chunk[CHUNK_NEXT_FOOD_INDEX]
            if foodIndex < 0: break
    if foodIndex >= 0: bites.append(food[foodIndex:])

    return "".join(bites)
