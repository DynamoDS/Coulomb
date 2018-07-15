---
layout: page
title: Best practices for writing a new feature extractor
permalink: /04-writing-a-new-query/02-new-features/
---

## When you need to do this

New feature extractors are needed when the existing feature datasets do not contain the information needed to answer the question. For example, the features do not currently contain information about the spatial layout of the nodes, so if you wanted to kno whow spread out nodes typically are, then you'd need to write a new feature extractor.

It is preferable to add a new feature extractor than a new measurement,


## Impact

Cost is O(n) CPU/IO in dataset, O(n) CPU/IO in new sessions

New feature extractors have to read each sorted session, this takes a few thousand CPU/IO hours for the dataset cerca July 2018, and a read cost associated with the dataset. The infrastructure automatically parallelises the task, however the index computation still imposes some delay.

The features must be incrementally computed for each update to the data.


## Design considerations

  - To operate correctly feature extractors should be idempotent, and should in general complete in O(n) time
  - It is strongly preferable for union of all the output of the feature extractors, decompressed, to fit in the RAM of a single workstation. Target is currently < 16Gb per feature set. This makes subsequent analysis much faster. 
  - As with all parts of infrastructure, reliable delivery of messages from the client cannot be assumed.
  - Feature extractors must accept both XML and JSON sessions, it's not required to return results for both formats
  - If the feature extractor encounters an error for a session, it's highly recomended to delete any previously reported results for that session. Otherwise the effect on the sampling can be very difficult to compute
   
## Testing

  - Feature extractors must process unicode content correctly
  - Feature extractors should be developed against a shard of the data. Each three letter pack contains 1/4096th of the data, in practice this seems to be a reasonable test set for catching most issues
