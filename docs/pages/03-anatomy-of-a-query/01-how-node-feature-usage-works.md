---
layout: page
title: How node feature usage works
permalink: /03-anatomy-of-a-query/01-how-node-feature-usage-works/
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


The script maintains a version number which is appended to the output files. This is to avoid accidentally overriding previously generated files.

*Before running the script, don't forget to update the version number!*

```python
VERSION="2018-07-03"
```

The first thing the script checks is that the arguments that it receives are the expected ones. This script takes a single argument: `PathToSessions`, which is then assigned to the variable `path`. `paths` is initialized as an empty list and it will contain the list of files to be processed.

```python
if len(sys.argv) != 2:
    print ("Usage: python feature_usage_extractor.py PathToSessions")

path = sys.argv[1]

paths = []
```

A list of all the features that are currently extracted for analysis:

```python
def emptyFeatureUsageMap():
    return {
        "ListAtLevel": False,
        "HiddenNodes": False,
        "UpstreamHiddenNodes": False,
        "ShortestLacing": False,
        "LongestLacing": False,
        "DisabledLacing": False,
        "CrossProductLacing": False,
        "Pinned": False,
        "Frozen": False,
        "CustomFunction": False
    }
```

Now, onto processing the data.

```python
print ('Enumerating files')

for root, subdirs, files in os.walk(path):
    for ff in files:
        ...
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
    # Prepare the output path, the name will look like: ".sorted.gz.features.VERSION"
    out_path = path + ".features" + "." + VERSION

    # Skip files that have been processed already
    if os.path.exists(out_path) and os.path.getmtime(out_path) > os.path.getmtime(path):
        skipped = skipped + 1
        continue

    try:
        # Open input and output files
        f = gzip.open (path)
        fo = open (out_path , 'w')
        processed = processed + 1
        isJSON = False

        # Initialize variables for storing the extracted data
        searchMap = {}
        searchNodeAdded = {}
        tags = set()
        featureUsageMap = emptyFeatureUsageMap()
        nodeUsageMap = {}
        userId = None
        version = None
        sessionStartMicroTime = 0
        sessionEndMicroTime = 0
        sessionDate = ''

        # A helper function to write the extracted data to the output file "fo".
        # Currently ignores JSON files.
        def writeDataToFile():
            if isJSON: # Don't write results for JSON files for now
                return

            print (json.dumps(
                {
                    "Searches" : searchMap,
                    "SearchesNodeAdded" : searchNodeAdded,
                    "Tags" : list(tags),
                    "FeatureUsageMap" : featureUsageMap,
                    "NodeUsageMap" : nodeUsageMap,
                    "UserID": userId,
                    "WorkspaceVersion": version,
                    "SessionDuration": sessionEndMicroTime - sessionStartMicroTime,
                    "Date": sessionDate
                }), file=fo)

        # Go through each line in the input file
        for ln in f:
            if ln.startswith("Downloading phase"):
                continue

            # Load the data from JSON format
            data = json.loads(ln)

            # If this is the first message in a session, record its time as the start of the session
            if sessionStartMicroTime == 0:
                sessionStartMicroTime = int(data["MicroTime"])
                sessionDate = data["DateTime"].split(" ")[0]

            # If the session covers multiple days, split the session
            if sessionDate != data["DateTime"].split(" ")[0]:
                print (path + " has session over multiple days")

                # Split the session: write session so far to file, then reset data collection.
                writeDataToFile()
                searchMap = {}
                searchNodeAdded = {}
                tags = set()
                featureUsageMap = emptyFeatureUsageMap()
                nodeUsageMap = {}
                sessionStartMicroTime = int(data["MicroTime"])
                sessionDate = data["DateTime"].split(" ")[0]

            # Update the time marking the end of the session seen so far
            sessionEndMicroTime = int(data["MicroTime"])

            # Extract the tags in the message if any
            tags.add(data["Tag"])

            # Decode the data and extract other features
            b64decodedData = base64.b64decode(data["Data"])

            # Was there a search?
            if data["Tag"] == "Search":
                searchMap[data["MicroTime"]] = b64decodedData

            # Was there a node added from a search?
            if data["Tag"] == "Search-NodeAdded":
                searchNodeAdded[data["MicroTime"]] = b64decodedData

            # Extract interesting features from the workspace
            if data["Tag"] == "Workspace":
                if b64decodedData == '':
                    continue

                # Select which feature extraction library to use depending on what version on the file format
                feature_lib = None
                if b64decodedData.startswith("<"):
                    feature_lib = features_XML
                else:
                    # Skip JSON workspaces for now
                    isJSON = True
                    print ("Skipping JSON based file: " + path)
                    if os.path.exists(out_path):
                        os.remove(out_path)

                # Extract features
                featureUsageMap["ListAtLevel"] = featureUsageMap["ListAtLevel"] or feature_lib.usesListAtLevel(b64decodedData)
                featureUsageMap["HiddenNodes"] = featureUsageMap["HiddenNodes"] or feature_lib.hasHiddenNodes(b64decodedData)
                featureUsageMap["UpstreamHiddenNodes"] = featureUsageMap["UpstreamHiddenNodes"] or feature_lib.hasUpstreamHiddenNodes(b64decodedData)
                featureUsageMap["ShortestLacing"] = featureUsageMap["ShortestLacing"] or feature_lib.hasShortestLacing(b64decodedData)
                featureUsageMap["LongestLacing"] = featureUsageMap["LongestLacing"] or feature_lib.hasLongestLacing(b64decodedData)
                featureUsageMap["DisabledLacing"] = featureUsageMap["DisabledLacing"] or feature_lib.hasDisabledLacing(b64decodedData)
                featureUsageMap["CrossProductLacing"] = featureUsageMap["CrossProductLacing"] or feature_lib.hasCrossProductLacing(b64decodedData)
                featureUsageMap["Pinned"] = featureUsageMap["Pinned"] or feature_lib.hasPinned(b64decodedData)
                featureUsageMap["Frozen"] = featureUsageMap["Frozen"] or feature_lib.hasFrozen(b64decodedData)

                # Extract node usage from an XML formatted workspace
                # Functions need some preprocessing, other nodes can be added directly
                workspaceElement = xmlElementTree.fromstring(b64decodedData)
                for element in workspaceElement.find('Elements'):
                    if (element.tag == 'Dynamo.Graph.Nodes.ZeroTouch.DSFunction'):
                        lib_name = element.attrib['assembly'].split('\\')[-1]
                        best_name = lib_name + ":" + element.attrib['function']
                        nodeUsageMap[best_name] = True
                    elif (element.tag == 'Dynamo.Graph.Nodes.ZeroTouch.DSVarArgFunction'):
                        lib_name = element.attrib['assembly'].split('\\')[-1]
                        best_name = lib_name + ":" + element.attrib['function']
                        nodeUsageMap[best_name] = True
                    elif (element.tag == 'Dynamo.Graph.Nodes.CustomNodes.Function'):
                        featureUsageMap["CustomFunction"] = True
                        custom_node_best_name = element.attrib['nickname'] + " (" + element.find('ID').attrib["value"] + ")"
                        nodeUsageMap["CustomFunction: " + custom_node_best_name] = True
                    else:
                        nodeUsageMap[element.attrib['type']] = True

                # Extract version number (first time only)
                if (version == None):
                    version = feature_lib.getVersion(b64decodedData)

            # Extract user ID (first time only)
            if userId == None:
                userId = data["UserID"]

    except Exception as e:
        ...
        # log exception
        ...
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
