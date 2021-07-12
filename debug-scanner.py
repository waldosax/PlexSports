# Boostrap necessary modules for debugging Plex scanner

import os, sys, types

# Anywhere I might resolve an import directive from
sys.path.append(os.path.abspath("Backups\\Scanners.bundle\\Contents\\Resources\\Common"))

# Run C:\Python27\Scripts\pip install requests to install relevant packages
# sys.path.append(os.path.abspath("PlexSportsAgent.bundle\\Contents\\Libraries\\Shared"))
sys.path.append(os.path.abspath("C:\\Python27\\Lib\\site-packages"))

sys.path.append(os.path.abspath("Scanners\\Series"))
sys.modules["PlexSportsScanner"] = PlexSportsScanner = __import__("PlexSportsScanner")

# Load up search results
if __name__ == "__main__":
    root = None # Plex Root

    #path = argv[1]
    #path = "Z:\\Staging\\Sports" # argv[0]
    path = "L:\\Staging\\Sports" # argv[0]
    mdeia = []

    files = [os.path.join(path, file) for file in os.listdir(path)]
    if sys.platform != "win32": path = path[1:]
    
    print (path)
    print(files)

    PlexSportsScanner.Scan(path, files, mdeia, [], root=root)
    
    print(media)