import os

root = "Z:\\Staging\\Sports"
print (root)

paths = dict()
walk = [os.path.join(dirPath, fileName) for dirPath, dirNames, fileNames in os.walk(root) for fileName in fileNames]
for f in walk:
    relpath = os.path.relpath(os.path.dirname(f), root)
    file = os.path.basename(f)
    paths.setdefault(relpath, [])
    paths[relpath].append(file)

for path in paths.keys():
    files = paths[path]
    print("Scanning: %s\n\t%s" % (path, files)) 
