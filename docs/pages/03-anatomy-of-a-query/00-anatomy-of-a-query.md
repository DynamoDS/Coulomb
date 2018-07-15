---
layout: page
title: Anatomy of a query
permalink: /03-anatomy-of-a-query/
---

The query infrastructure takes a set of session files as an input, and produces results that can be loaded in a spreadsheet for visualisation.

(**TODO: Sub-part of the architecture diagram**)

The total set of sessions is much too large to effectively visualise, however many queries can be written using broadly the same aggregated data. Consequently, the process of answering a query occurs in multiple parts:

1. Features are extracted from the sorted sessions and stored in feature files (~1k hours of CPU/IO)
2. These features are condensed into a single file (~10 hours of CPU/IO)
3. A reducer is run over these feature files to produce a file that can be opened in a spreadsheet (~10 seconds of CPU/IO)

The following sections explain these stages in detail:
 [Feature Extractors](http://dynamods.github.io/Coulomb/03-anatomy-of-a-query/01-feature-extractors/)
 [Condensers](http://dynamods.github.io/Coulomb/03-anatomy-of-a-query/02-condensers/)
 [Reducers](http://dynamods.github.io/Coulomb/03-anatomy-of-a-query/02-reducers/)
