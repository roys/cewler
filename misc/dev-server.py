"""
Just a script to run a server in tests/server/. :)
"""
import os

cmd = f"cd tests/server;python3 -m http.server"

os.system(cmd)
