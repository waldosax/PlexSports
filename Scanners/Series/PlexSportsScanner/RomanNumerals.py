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

def Parse(s):
	if not s:
		return 0

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
	# TODO
	pass
