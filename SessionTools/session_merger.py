import gzip
import os
import random
import time
import sys

VERBOSE = True

def log(s):
  if VERBOSE:
    print (time.strftime("%Y-%m-%d %H:%M:%S") + " " + str(s))

if len(sys.argv) != 3:
  print ("Usage: python session_merger.py PathToInSessions PathToTargetSessions")
  exit(1)

inSessionsPath = sys.argv[1]
print(inSessionsPath)
outSessionsPath = sys.argv[2]
print(outSessionsPath)

inChecksumMap = {}
outChecksumMap = {}

def countLinesInGzipFile(path):
  nr_lines = 0
  with gzip.open(path) as f:
    for _ in f:
      nr_lines = nr_lines + 1
  return nr_lines

def checksumFiles(paths):
  c = 0
  checksumMap = {}
  for path in paths:
    c += 1

    if c % 1000 == 0:
      log ('checksumming' + c + ":" + str(c/len(paths)) )
    if os.path.isfile(path):
      checksumMap[path] = countLinesInGzipFile(path)
    else:
      checksumMap[path] = 0
  return checksumMap

inPaths = []
i = 0

log('Enumerating and checksumming the input files')
for root, subdirs, files in os.walk(inSessionsPath):
  for ff in files:
    i = i + 1
    if i % 1000 == 0:
        log (i)
    path = os.path.join(root, ff)
    if (not path.endswith('.gz')):
        continue
    inPaths.append(path)

log('Paths to process: ' + str(len(inPaths)))

outPaths = {}
for inPath in inPaths:
  outPaths[inPath] = inPath.replace(inSessionsPath, outSessionsPath)

log('Computing file length checksums')
inChecksumMap = checksumFiles(inPaths)
outChecksumMap = checksumFiles(outPaths.itervalues())

i = 0

log('Moving input files')
for inPath in inPaths:
  fin = gzip.open(inPath)

  outPath = outPaths[inPath]
  if not os.path.exists(os.path.dirname(outPath)):
    os.makedirs(os.path.dirname(outPath))
  fout = gzip.open(outPath, 'ab')

  for ln in fin:
    fout.write(ln)

  # check that the checksum fails when it should by introducing an extra line in a file
  # if (outPath == 'session_merger_test_out/a/1/100.gz'):
  #   fout.write('checksum test\n')
  
  fin.close()
  fout.close()

log('Verifying the checksum of the output files')
newOutChecksumMap = checksumFiles(outPaths.itervalues())

for inPath in inPaths:
  inChecksum = inChecksumMap[inPath]
  outChecksum = outChecksumMap[outPaths[inPath]]
  newOutChecksum = newOutChecksumMap[outPaths[inPath]]
  if (newOutChecksum != inChecksum + outChecksum):
    log("Checksum doesn't match for file " + outPaths[inPath] + ": expected " + str(inChecksum + outChecksum) + ", got " + str(newOutChecksum))
  else:
    os.remove(inPath)
