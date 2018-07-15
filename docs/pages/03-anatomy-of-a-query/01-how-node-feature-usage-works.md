---
layout: page
title: How node feature usage works
---

A brief reminder from the [summary of the instrumentation architecture section](../02-summary-of-instrumentation-architecture/), the directory structure that the data is organised in looks something like this:


```
├── 000
|   ├── 0001289a-c091-10ab-1200-12809d99da00.gz
|   ├── 0001289a-c091-10ab-1200-12809d99da00.gz.sorted.gz
|   ├── 00039871-1720-a92e-b90e-2198a9e0bb10.gz
|   ├── 00039871-1720-a92e-b90e-2198a9e0bb10.gz.sorted.gz
|       ...
├── 001
|   ├── 0015928a-a8a0-1280-0ab0-120809dcc095.gz
|   ├── 0015928a-a8a0-1280-0ab0-120809dcc095.gz.sorted.gz
|   ├── 00169128-3829-9641-1a09-12898a989c93.gz
|   ├── 00169128-3829-9641-1a09-12898a989c93.gz.sorted.gz
|       ...
├── 002
    ...
```

Each `.gz` file above is a user session, with the `sorted.gz` files containing the session sorted by the time of the messages.

A file can have many lines, where each line is a JSON message. A message can look something like this:

```json
{
  "b75e7a7f_ServerDate": "2018-02-01",
  "UserID": "430f3c7c-9879-4bc4-bf7e-7e25cde039cf",
  "DateTime": "2018-02-01 08:35:17",
  "Priority": "Info",
  "SessionID": "000b7b9b-a9f0-4dc0-9fd7-1f515408955f",
  "Tag": "Workspace",
  "MicroTime": "65013",
  "AppIdent": "Dynamo",
  "RandomToken-b75e7a7f-dc90-48a1-8637-dbc123175a4d": 0.3421572082480505,
  "Data": "<Workspace Version=\"1.3.2.2480\ [...] >"
}
```

Let's see how one writes analyses this user data by looking at the feature extractor script [feature_usage_extractor.py](https://github.com/DynamoDS/Coulomb/blob/master/SessionTools/feature_usage_extractor.py).

```python
if len(sys.argv) != 2:
    print ("Usage: python feature_usage_extractor.py PathToSessions")

path = sys.argv[1]

paths = []
```

The first thing the script checks is that the arguments that it receives are the expected ones. This script takes a single argument: `PathToSessions`, which is then assigned to the variable `path`. `paths` is initialized as an empty list and it will contain the list of files to be processed.


The script also maintains a version number which is appended to the output files. This is to avoid accidentally overriding previously generated files: before running the script, don't forget to update the version number:
```python
VERSION="2018-07-03"
```

Now, onto processing the data.

```python
print ('Enumerating files')

for root, subdirs, files in os.walk(path):
    for ff in files:
        # print progress every 1000 files processed
        ...
        # filter our files that are not sorted
        path = join(root,ff)
        if (not path.endswith('sorted.gz')):
            continue
        paths.append(path)

random.shuffle(paths)
print ('Paths to process: ' + str(len(paths)))
```
Next, the script collects all files contained under the `path` and selects only those that end with `sorted.gz` to add to the list of `paths` to be processed. After all the files have been added, the `paths` list is shuffled (the order of the elements is randomized) in order to balance the workload when running the script on multiple machines, but data is read and written on a single hard disk. When running the script locally on a single machine, this step is less important.

```python
for path in paths:
    # prepare the output path, the name will look like: ".sorted.gz.features.VERSION"
    out_path = path + ".features" + "." + VERSION

    # skip files that have been processed already
    if os.path.exists(out_path) and os.path.getmtime(out_path) > os.path.getmtime(path):
        skipped = skipped + 1
        continue

    try:
        # open input and output files
        f = gzip.open (path)
        fo = open (out_path , 'w')
        processed = processed + 1

        # initialize variables for storing the extracted data
        searchMap = {}
        searchNodeAdded = {}
        tags = set()
        usageMap = { # When adding features here, don't forget to add below as well
            "ListAtLevel": False
        }
        userId = None
        version = None
        sessionStartMicroTime = 0
        sessionEndMicroTime = 0
        sessionDate = ''

        # a helper function to write the extracted data to the output file "fo"
        def writeDataToFile():
            print (json.dumps(
                {
                    "Searches" : searchMap,
                    "SearchesNodeAdded" : searchNodeAdded,
                    "Tags" : list(tags),
                    "UsageMap" : usageMap,
                    "UserID": userId,
                    "WorkspaceVersion": version,
                    "SessionDuration": sessionEndMicroTime - sessionStartMicroTime,
                    "Date": sessionDate
                }), file=fo)

        # go through each line in the input file
        for ln in f:
            if ln.startswith("Downloading phase"):
                continue

            # load the data from JSON format
            data = json.loads(ln)

            # if this is the first message in a session, record its time as the start of the session
            if sessionStartMicroTime == 0:
                sessionStartMicroTime = int(data["MicroTime"])
                sessionDate = data["DateTime"].split(" ")[0]

            # if the session covers multiple days, split the session
            if sessionDate != data["DateTime"].split(" ")[0]:
                print (path + " has session over multiple days")

                # split the session: write session so far to file, then reset data collection.
                writeDataToFile()
                searchMap = {}
                searchNodeAdded = {}
                tags = set()
                usageMap = {
                    "ListAtLevel": False
                }
                sessionStartMicroTime = int(data["MicroTime"])
                sessionDate = data["DateTime"].split(" ")[0]

            # update the time marking the end of the session seen so far
            sessionEndMicroTime = int(data["MicroTime"])

            # extract the tags in the message if any
            tags.add(data["Tag"])

            # decode the data and extract other features
            b64decodedData = base64.b64decode(data["Data"])

            if data["Tag"] == "Search":
                searchMap[data["MicroTime"]] = b64decodedData

            if data["Tag"] == "Search-NodeAdded":
                searchNodeAdded[data["MicroTime"]] = b64decodedData

            if data["Tag"] == "Workspace":
                if b64decodedData == '':
                    continue

                if b64decodedData.startswith("<"):
                    usageMap["ListAtLevel"] = usageMap["ListAtLevel"] or usesListAtLevelXML(b64decodedData)
                    if (version == None):
                        version = getVersionXML(b64decodedData)
                else:
                    usageMap["ListAtLevel"] = usageMap["ListAtLevel"] or usesListAtLevelJSON(b64decodedData)
                    if (version == None):
                        version = getVersionJSON(b64decodedData)

            if userId == None:
                userId = data["UserID"]

    except Exception as e:
        # log exception
        continue

    # write the features to the output file
    writeDataToFile()
```

The comments in the code above describe in quite some detail what the script does: processes each file in turn by going line by line, recording any interesting features and creating one entry in the output file for each day that the session stretches over.

The output can look something like this:

```json
{
  "Searches": {},
  "Date": "2018-02-06",
  "SessionDuration": 86301371,
  "WorkspaceVersion": "1.3.2.2480",
  "Tags": ["Node-usage", "Nodes-with-errors", "Workspace"],
  "FeatureUsageMap": {"HiddenNodes": false, "UpstreamHiddenNodes": false, "ListAtLevel": false, "ShortestLacing": true},
  "SearchesNodeAdded": {},
  "UserID": "430f3c7c-9879-4bc4-bf7e-7e25cde039cf",
  "NodeUsageMap": {
    "DSCore.IO.File.ReadText@var": true,
    "CoreNodeModels.Input.DoubleInput": true,
    "CoreNodeModels.Input.Filename": true,
    "CoreNodeModels.Watch": true,
    "DSCore.String.Substring@string,int,int": true,
    "CoreNodeModels.CreateList": true,
    "DSOffice.Excel.WriteToFile@string,string,int,int,var[][],bool": true, "DSCore.String.Split@string,string[]": true,
    "DSCore.String.AllIndicesOf@string,string,bool": true,
    "Dynamo.Graph.Nodes.CodeBlockNodeModel": true,
    "CoreNodeModels.Input.BoolSelector": true,
    "CoreNodeModels.Input.StringInput": true
  }
}
```

Th result of running this script is one feature output file per input session file. Let's look at how to combine these files into a single .csv file for analysing the data in [Writing a query using existing features](../04-writing-a-new-query/01-existing-features/) or we can look at extracting some more features and analysing them in [Writing a query using new features](../04-writing-a-new-query/02-new-features/).
