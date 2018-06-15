# This tool exports changes that occur in a workspace during a session

import gzip
import json
import base64
import sys
import traceback
import time

import os
import sys

import xml.etree.ElementTree as ET

VERBOSE = False

def log(s):
    if VERBOSE:
        print time.strftime("%Y-%m-%d %H:%M:%S"), s

def printData(m, decoded):
    print str(m["SessionID"]) + "|" + str(m["MicroTime"]) + "|" + str(m["Tag"]) + "|" + str(decoded)

def barePrintData(m, decoded):
    print str(m["Tag"]), + "|" + str(decoded)

def compareElements(e1, e2, data):
    for k in e1.attrib.keys():
        if e1.attrib[k] != e2.attrib[k]:
            printData (data, "CHANGED|" + e1.attrib["guid"] + "|" + k + "|" + e1.attrib[k].replace("\n", "\\n") + " -> " + e2.attrib[k].replace("\n", "\\n"))


if len(sys.argv) < 2:
    print "Usage: python extract_deltas.py path_to_sessions"
    print "List the deltas for a session"
    exit(1)

path = sys.argv[1]
bare = False

if len(sys.argv) == 3:
    bare = sys.argv[2] == "clean"

tagToShow = "Workspace"

linesCount = 0
workspacesTotal = 0
tags = set()

for root, subdirs, files in os.walk(path):
    for ff in files:
        path = os.path.join(root, ff)
        if not path.endswith(".gz.sorted.gz"):
            continue
        f = gzip.open(path)
        workspacesCount = 0
        last_nodes = {}

        first = True

        for ln in f:
            try:
                linesCount += 1
                if linesCount % 1000 == 0 and not bare:
                    log("Lines: " + str(linesCount) + " Workspaces: " + str(workspacesTotal))

                data = json.loads(ln)
                tag = str(data["Tag"])
                uuid = ""

                next_nodes = {}

                # Workspace data is post-fixed with the GUID of the workspace
                if tag.startswith("Workspace-"):
                    if tag.find("-") > 0:
                        uuid = tag.split("-")[1]
                    tag = "Workspace"

                if not tag.startswith(tagToShow):
                    continue

                workspacesTotal += 1
                workspacesCount += 1

                workspaceString = base64.b64decode(data["Data"])

                if workspaceString == "":
                    continue
                workspaceRoot = ET.fromstring(workspaceString)
                for elements in workspaceRoot.findall('Elements'):
                    for n in elements:
                        next_nodes[n.attrib['guid']] = n

                for k in next_nodes.keys():
                    if not last_nodes.has_key(k):
                        if not first:
                            printData (data, "ADDED:" + k + "|" + next_nodes[k].tag + "|" + str(next_nodes[k].attrib))
                    else:
                            compareElements(last_nodes[k], next_nodes[k], data)

                for k in last_nodes.keys():
                    if not next_nodes.has_key(k):
                        printData (data, "DELETED:" + k + "|" + last_nodes[k].tag)


                last_nodes = next_nodes

                first = False
            except Exception as e:
                print "FAIL: " + path + " |" + str(e)