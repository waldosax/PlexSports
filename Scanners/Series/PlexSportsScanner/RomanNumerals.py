import re

roman_numerals_expression = r"[ivxlcdm]+"
roman_numeral_values = {
	"I": 1,
	"V": 5,
	"X": 10,
	"L": 50,
	"C": 100,
	"D": 500,
	"M": 1000
}

integer_values = {
	1000: "M",
	900: "CM",
	500: "D",
	400: "CD",
	100: "C",
	90: "XC",
	50: "L",
	40: "XL",
	10: "X",
	9: "IX",
	5: "V",
	4: "IV",
	1: "I"
	}


def Parse(s):
	"""Converts a Roman Numeral set (or an integral string) to an integer value."""
	if not s:
		return 0
	if not re.match(roman_numerals_expression, s, re.IGNORECASE):
		try: return int(s)
		except: return 0

	prevValue = roman_numeral_values[s[-1:].upper()]
	value = prevValue

	for c in list(s)[-2::-1]:
		v = roman_numeral_values[c.upper()]
		if v < prevValue:
			value -= v
		else:
			value += v
		prevValue = v

	return value


def Format(n):
	"""Converts a number to a Roman Numeral set."""

	if n == None: return None
	n = int(n) # If not already an integer

	val = sorted(integer_values.keys(), reverse=True)
	roman_num = ''
	i = 0
	while  n > 0:
		for _ in range(n // val[i]):
			roman_num += integer_values[val[i]]
			n -= val[i]
		i += 1
	return roman_num
