---
layout: page
title: Best practices for adding new reducers
permalink: /04-writing-a-new-query/01-new-reducers/
---

## When you need to do this

In general each new question will require a new reducer to process features into a form of visualisation. 

Prefer to write new reducers, than change any other part of the infrastructure.

## Impact

Impact of a new query over an existing condensed feature set is low. It is preferable for the operation to fit in memory. if this is not possible the reducer is expected to implement its own storage and parallelisation strategy.

## Design considerations

 - Reducers are very cheap to execute, it's best to have a number of small reducers than a large more complicated one. E.g. implement seperate reducers to produce files for seperate graphs in a spreadsheet.
 
 - If the reducer needs to do more complicated operations that fit linerally in memory developing it on a single shard is usually reasonable. 
 
 - Reducers should generally not be more than O(n.log(n)) in complexity, they should expect to intake files up to 16Gb 
   
## Testing

 - Testing considerations for reducers are more towards correctness than impact on infrastructure.
