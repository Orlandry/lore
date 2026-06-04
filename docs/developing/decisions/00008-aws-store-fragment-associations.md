---
status: accepted
date: 2024-10-21
deciders: Paul Sharpe, Mattias Jansson
---

# ADR-00008: Optimize AWS store fragment association lookups

## Context and Problem Statement

Previously in [ADR-00006](00006-s3-storage-options-reconsidered.md) we described the structure for
storing fragments and their associations with repositories and files entirely in S3. Under load we
discovered that the implementation for tracking these associations wasn't performant
due to the reliance on S3 ListObjects calls when querying fragments. This updated ADR describes the
considered options for addressing this performance issue.

### The problem with ListObjects

In the previous ADR we had assumed that ListObjects calls would be an efficient way to query S3, but
this turned out not to be the case. This problem was exacerbated by the fact
that `Store::query_immutable` is our most frequently accessed code path in the server due to the
fact that the client issued a query before putting a fragment, and then the server also issued its
own query when processing the put fragment. Since we always walked up the specificity hierarchy,
that meant that in a worst case scenario where a fragment didn't exist at all, we were making 6
ListObjects calls for every put fragment call. This proved particularly problematic when the client
was performing operations that involved putting many fragments (for example, pushing a large
commit).

## Decision Drivers

- Support efficient querying for fragments at varying levels of match specificity.
- Utilize technologies already in use by the Lore back end.

## Considered Options

- Replace applicable ListObjects calls with HeadObject.
- Move storage of fragment/repository/file associations to DynamoDB.

## Decision Outcome

Chosen option: "Move storage of fragment/repository/file associations to DynamoDB," because it's
performant while still making use of existing technologies used by the AWS Store
implementation.

### Consequences

- Good, because querying DynamoDB is much more efficient than S3 ListObjects.
- Good, because we already use DynamoDB for the AWS mutable store implementation.
- Bad, because we no longer rely on S3 alone for the immutable store.
- Bad, because all fragment associations that existed prior to the migration would become invalid.

## Pros and Cons of the Options

### Replace applicable ListObjects calls with HeadObject

There are three levels of `StoreMatch` specificity used by `query_immutable`:

1. MatchHash
2. MatchRepository
3. MatchFull

Previously the fully S3-based implementation of the AWS Store would start at `MatchFull` and perform
a ListObjects call for `<fragment>/<repository>/<context>`, if that failed to find an object in S3,
it would then go up one level and make a ListObjects call for `<fragment>/<repository>`, if that
also failed to find an object it would go up one more level and make a ListObjects call
for `<fragment>`. The astute reader may note that of those three calls, two of them are for exact
object keys (`fragment` and `fragment/repo/context`), while only the repository level match is
actually doing a ListObjects for a prefix. It stands to reason that we could optimize this call path
by replacing two of the ListObjects calls with explicit HeadObject calls.

- Good, because it reduces the number of ListObjects calls from 3 to 1.
- Good, because it maintains immutable data storage entirely in S3.
- Bad, because there's still one ListObjects call remaining which can still cause performance issues
  for non-existent fragments.

### Move storage of fragment/repository/file associations to DynamoDB

In this scenario we move fragment associations to a DynamoDB table:

| hash | repository_context |
|------|--------------------|

Where `hash` is partition key containing the fragment hash bytes, and `repository_context` is a
composite sort key containing the repository bytes and the context bytes concatenated together. This
allows us to efficiently find fragment associations either only by hash, or by hash and repo (
using a `begins_with` query) or hash, repo and context.

- Good, because querying DynamoDB is much more efficient than S3 ListObjects.
- Good, because we already use DynamoDB for the AWS mutable store implementation.
- Bad, because we no longer rely on S3 alone for the immutable store.
- Bad, because all fragment associations that existed prior to the migration would become invalid.
