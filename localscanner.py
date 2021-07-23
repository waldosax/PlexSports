import os, sys, types, functools

import bootstrapper
Scanner = bootstrapper.BootstrapScanner()

def BeginScanRecursive(root):
	startPath = root
	mediaList = []

	(path, files, subdirs) = GetFilesAndSubdirs(startPath)
		
	ScanRecursive(path, files, mediaList, subdirs, root)
	return mediaList

def GetFilesAndSubdirs(path, relsubdir = None):
	x = path
	if (relsubdir):
		x = os.path.join(x, relsubdir)
	files = []
	subdirs = []
	l = os.listdir(x)
	for i in l:
		p = os.path.join(x, i)
		if os.path.isfile(p):
			files.append(p)
		elif os.path.isdir(p):
			subdirs.append(p)
	return (x, files, subdirs)

def ScanRecursive(path, files, mediaList, subdirs, root):
	ScanFolder(path, files, mediaList, subdirs, root=root)
	for s in subdirs:
		relsubdir = os.path.relpath(s, path or root)
		(newpath, newfiles, newsubdirs) = GetFilesAndSubdirs(path or root, relsubdir)
		ScanRecursive(newpath, newfiles, mediaList, newsubdirs, root)

def ScanFolder(path, files, mediaList, subdirs, root):
	Scanner.Scan(path, files, mediaList, subdirs, root=root)

def BeginScanFolder(startPath):
	mediaList = []

	(path, files, subdirs) = GetFilesAndSubdirs(startPath)
	ScanFolder(path, files, mediaList, subdirs, root=None)
	
	return mediaList

def BeginScanFile(filePath, root=None):
	mediaList = []

	files = [filePath]
	path = os.path.dirname(filePath)
	subdirs = []

	ScanFolder(path, files, mediaList, subdirs, root)
	
	return mediaList
