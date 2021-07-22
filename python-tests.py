import re

lgexpr = r"(?:(?P<league>lg\:\w+)(?:\||$))?"
sznexpr = r"(?:(?P<season>s\:\d+)(?:\||$))?"
wkexpr = r"(?:(?P<week>wk\:\w+)(?:\||$))?"
dtexpr = r"(?:(?P<date>dt\:\d+)(?:\||$))?"
tm1expr = r"(?:(?P<team1>tm\:\w+)(?:\||$))?"
tm2expr = r"(?:(?P<team2>tm\:\w+)(?:\||$))?"

test = "lg:mlb|s:2021|dt:20210903|tm:PHI|tm:MIA"

expr = r"".join([lgexpr, sznexpr, wkexpr, dtexpr, tm1expr, tm2expr])
print(expr)
p = re.compile(expr, re.IGNORECASE)
m = p.search(test)

if m:
	print(m.string[m.start():m.end()])
	gd = m.groupdict()
	for key in gd.keys():
		g = gd[key]
		val = m.group(key)
		sliced = m.string[m.start(key):m.end(key)]
		print("val\t%s: %s" % (key, val))
		print("sliced\t%s: %s" % (key, sliced))
