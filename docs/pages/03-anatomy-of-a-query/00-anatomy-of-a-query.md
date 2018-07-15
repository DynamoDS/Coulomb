---
layout: page
title: Anatomy of a query
permalink: /03-anatomy-of-a-query/
---

The query infrastructure takes a set of session files as an input, and produces results that can be loaded in a spreadsheet for visualisation.

[![](/Coulomb/assets/instrumentation_pipeline_analysis.png)](/Coulomb/assets/instrumentation_pipeline_analysis.png)

The total set of sessions is much too large to effectively visualise, however many queries can be written using broadly the same aggregated data. Consequently, the process of answering a query occurs in multiple parts:

1. [Feature Extractors](http://dynamods.github.io/Coulomb/03-anatomy-of-a-query/01-feature-extractors/) take the sorted sessions and compute the feature files summarising the information in a session (~1k hours of CPU/IO)
2. [Condensers](http://dynamods.github.io/Coulomb/03-anatomy-of-a-query/02-condensers/) shuffle these summaries into a single file (~10 hours of CPU/IO)
3.  [Reducers](http://dynamods.github.io/Coulomb/03-anatomy-of-a-query/03-reducers/) take these summaries and produces files that can be opened in visualisation tools such as spreadsheets (~10 seconds of CPU/IO)

 
 

