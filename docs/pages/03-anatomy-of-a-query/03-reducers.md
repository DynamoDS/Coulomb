---
layout: page
title: Reducers
permalink: /03-anatomy-of-a-query/03-reducers/
---

Reducers take the output of a condenser, transform and filter it so that it is easy to visualise.

[![](/Coulomb/assets/instrumentation_pipeline_reducer.png)](/Coulomb/assets/instrumentation_pipeline_reducer.png)

## Input

** TODO **

## Output

** TODO **


## Source

** TODO **


**TODO: Look again at whether this is best done with comments in code instead of narrative**

This example will show how to create a csv file for analysis and visualisation in Excel. This is the feature_reducer.py

In order to process the right files, the `VERSION` number between feature_distribution_extractor.py and feature_reducer.py must match.

```python
VERSION="2018-05-16" # this is the version of the feature_usage_extractor.py script
```

The first thing the script checks is that the arguments that it receives are the expected ones. This script takes a single argument: `PathToSessions`, which is then assigned to the variable `featuresPath`.

```python
if len(sys.argv) != 2:
    print ("Usage: python feature_usage_merger.py PathToFeatures")
    exit(1)

featuresPath = sys.argv[1]
```

Next, it opens the output file and writes the header:

```python
# Open the output file as a csv
out_path = join(featuresPath, "features.usage.merged" + "." + VERSION + ".csv")
out_csv = open(out_path, "w+")
csvwriter = csv.writer(out_csv)

# Write the header of the csv table
header = [
    "Date",
    "Feature",
    "Session",
    "User"
]
csvwriter.writerow(header)
```

The main part of the processing comes next: going through all of the files and writing them into the csv file.

```python
# Go through all of the files under the given path
for root, subdirs, files in os.walk(featuresPath):

  for ff in files:
    path = join(root, ff)
    # Skip files that are not feature files and who don't match the version
    if (not path.endswith(".features" + "." + VERSION)):
      continue

    # Open the feature file for reading
    f = open(path)

    # Each line in the feature file corresponds to a subsession (a multi-day session has been split into daily subsession).
    # Keep track of the index to label the subsessions
    subsession = 0
    for ln in f:
      try:
        data = json.loads(ln)
        featureUsageMap = data["FeatureUsageMap"]

        # Add all features to the csv file, keeping track of the subsession
        for feature, value in featureUsageMap.iteritems():
          if (value):
            row = [
              data["Date"],
              feature,
              ff.split(".")[0] + str(subsession),
              data["UserID"]
            ]
            csvwriter.writerow(row)
      except Exception as e:
        print (e)
      subsession = subsession + 1

# We're done, so close the csv file.
out_csv.close()
```

This is a sample of the expected output:

Date | Feature | Session | User
--- | --- | --- | ---
2017-08-29 | ShortestLacing | ...-692e360a33600 | f6d9eeed-...
2017-08-30 | HiddenNodes | ...-692e360a33601 | f6d9eeed-...
... | ... | ... | ...

Now we can take this csv file and import it into Excel, Tableau or even Python to aggregate the features, plot distributions etc.
