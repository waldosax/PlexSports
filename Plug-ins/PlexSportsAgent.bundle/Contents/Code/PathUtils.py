import os

def EnsureDirectory(dir):
	if os.path.exists(dir): pass
	nodes = Utils.SplitPath(dir)
	agg = None
	for node in nodes:
		agg = os.path.join(agg, node) if agg else node
		if os.path.exists(agg) == False:
			os.mkdir(agg)
	
	pass

