---
layout: page
title: Feature extractors
permalink: /03-anatomy-of-a-query/01-feature-extractors/
---

Feature extractors refine the dataset, extracting properties of interest from each sorted session file. This allows subsequent analysis to be done interactively. 

**TODO: Location on the diagram**

## Input

**Sorted session files**

The directory structure that the data is organised in looks something like this:

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
|       ...
├── 002
    ...
```

The feature extractor will read the .sorted.gz files. Each line in thses files looks somewhat like: 

```json
{
  "b75e7a7f_ServerDate": "2018-02-01",
  "UserID": "_REDACTED_",
  "DateTime": "2018-02-01 08:35:17",
  "Priority": "Info",
  "SessionID": "0001289a-c091-10ab-1200-12809d99da0",
  "Tag": "Workspace",
  "MicroTime": "65013",
  "AppIdent": "Dynamo",
  "RandomToken-b75e7a7f-dc90-48a1-8637-dbc123175a4d": 0.3421572082480505,
  "Data": "..."
}
```

## Output

**Feature files, 1 per feature extractor, per sorted session**

For a feature called '2018-07-15', the result after the extractor has run would be:

```
├── 000
|   ├── 0001289a-c091-10ab-1200-12809d99da00.gz
|   ├── 0001289a-c091-10ab-1200-12809d99da00.gz.sorted.gz
|   ├── 0001289a-c091-10ab-1200-12809d99da00.gz.sorted.gz.features.2018-07-15
|   ├── 00039871-1720-a92e-b90e-2198a9e0bb10.gz
|   ├── 00039871-1720-a92e-b90e-2198a9e0bb10.gz.sorted.gz
|   ├── 00039871-1720-a92e-b90e-2198a9e0bb10.gz.sorted.gz.features.2018-07-15
|       ...
├── 002
    ...
```

These feature files contain a summary of the main session files. A sample output is:

```json
{
  "Searches": {},
  "Date": "2018-02-06",
  "SessionDuration": 86301371,
  "WorkspaceVersion": "1.3.2.2480",
  "Tags": ["Node-usage", "Nodes-with-errors", "Workspace"],
  "FeatureUsageMap": {"HiddenNodes": false, "UpstreamHiddenNodes": false, "ListAtLevel": false, "ShortestLacing": true},
  "SearchesNodeAdded": {},
  "UserID": "_REDACTED_",
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

This summarises feature usage across the whole sessions (e.g. in this case, we saw one or more usages of shortest lacing, but no usages of list at level)


## Example Source

The most extensively commented extractor is [feature_usage_extractor.py](https://github.com/DynamoDS/Coulomb/blob/master/SessionTools/feature_usage_extractor.py)

## Notes

- If you need the feature extractor to rerun for existing data (you probably do if you're modifying the code), you need up update the 'VERSION' field.


Once you have updated and rerun the feature extractors, you'll need to rerun the condenser to copy all the results into a single place, and you'll then be in a good place to write a reducer that extract the information you want from these files in a form that is easy to visualise. 
