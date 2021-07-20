
def __expand_year(year):
    if not year:
        return None

    intYear = 0
    if type(year) is str:
        intYear = int(year)
    elif type(year) is int:
        intYear = year

    if intYear < 100:
        if intYear < 40:
            intYear = 2000 + intYear
        else:
            intYear = 1900 + intYear

    return str(intYear)
