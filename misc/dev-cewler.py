"""
Just a script to run the cewler.py script with different arguments during development. :)
"""
import os

args = """
#roysolberg.com
http://localhost:8000
-o tests/results/wordlist-test.txt
--output-urls tests/results/urls-test.txt
--output-emails tests/results/emails-test.txt
--subdomain_strategy all
--depth 0
--include-js
--include-css
--include-pdf
#--min-word-length
#5
#--stream
#--lowercase
#--user-agent "CeWLeR - Custom Word List generator Redefined"
#--rate 1
#--without-numbers
--verbose
"""

args = " ".join([arg for arg in args.splitlines() if not arg.startswith("#")])

cmd = f"python3 src/cewler/cewler.py {args}"

print(f"Running command: {cmd}")

os.system(cmd)
