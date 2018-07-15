---
layout: page
title: Best practices for a new query for new measurements
permalink: /04-writing-a-new-query/03-new-measurements/
---

## When you need to do this

New measurements are needed when the information to answer a question was not transmitted to the instrumentation service.

## Impact

Cost is O(4n) in storage, O(4n) CPU/IO in infrastructure, O(n) in network from client, O(2n) in memory on client.

New measurements should be added sparingly and with careful consideration. New measurements carry privacy implications as well as infrastructural cost.

This section only describes the technical considerations.

## Design considerations

  - Data sent should be associated with direct user activity (e.g. clicking run, select a node, etc), not system activity (e.g. computing the status of each node in the graph). This is necessary to maintain the operating efficency of the instrumentation service.

  - The buffer on the client is limited to prevent implementation mistakes causing resource exhaustion on the client. Sending too much data too quickly will result in the client discarding messages. Special care should be taken from reporting messages from highly parallel operations or in error states which might rapidly reoccur.
  
  - Ideally every message should be independently useful. For example, it's better to send an entire search term, rather than a change from the last term. This means that the impact of lost messages is localised to only that message, and decreases the hardware requirements on subsequent processing nodes. If it is necessary to send change messages, syncronisation messages should be periodically sent.

  - Performance measures can be bundled together. For example, sending a list of the last 100 execution times, rather than a message for each timing. This strategy increases the probability of loss of data but decreases the impact of measurement.
  
  - Measurements should be sent in raw form where possible (e.g. for performance a list of times rather than distributional statistics), this makes computing alternative metrics later on much simpler.

  - The correct operation of the tool must not depend on the availability of the instrumentation system
  
  - Measurements can be either passive observations (e.g. did the user click on a result of a search), or active requests for input (a text box asking what the user was looking for). Passive observations are less intrusive, however it can be harder to interpret the results. Active requests for input are more expensive to build, can be more intrusive, will collect less data, but can answer more targeted questions.
   
## Testing

 - New measurements should be rolled out to a fraction of users before general release
 - The entire processing pipeline should be tested on this fraction to ensure that the right data is being gathered as well as verifying the implementation
 - The entire compute pipeline should be verified before inclusion into a release
