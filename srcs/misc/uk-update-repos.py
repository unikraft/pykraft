# This script parses an app's Makefile and retrieves the list of external repos
# from the LIBS := line. It then goes into each of them and checks out the
# staging branch and does a git pull. It expects a UK_LIBS variable in the Makefile
# to exist, using it to derive the base path to the libs/repos
import os

f = open("Makefile", "r")
lines = f.readlines()
f.close()

repos = []

def get_base_path():
    for l in lines:
        if not l.strip().startswith("#") and l.find("UK_LIBS") != -1:
            return l.strip()[l.find("/") + 1:]
        
def parse_repos(line):
    tokens = line[line.find("$"):].split(":")
    # token: $(UK_LIBS)/pthread-embedded    
    for t in tokens:
        repos.append(t[t.rfind("/") + 1:])

for l in lines:
    if not l.strip().startswith("#") and l.find("LIBS :=") != -1:
        parse_repos(l.strip())

bp = get_base_path() + "/"
for r in repos:
    l = ""
    for x in range(0, 40):
        l += "="
    print(l + "\n"),
    print("Processing {} repo".format(r))
    print(l + "\n"),
    p = bp + str(r)
    cmd = "cd " + str(p) + " && git checkout staging && git pull"
    s = os.popen(cmd)
    o = s.read()
    print(o)

