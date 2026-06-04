---
status: superseded by [ADR-00006](00006-s3-storage-options-reconsidered.md)
date: 2024-04-24
deciders: Mattias Jansson, Paul Sharpe
consulted: Manuel Lang
---

# ADR-00004: S3 storage options

## Context and Problem Statement

We plan to implement an S3-backed store as our primary durable store for both mutable and immutable
data managed by Lore. We need to determine how best to map the Lore store data to S3 buckets and
objects.

## Decision Drivers

- Support all Lore store operations durably via reads/writes to/from S3.
- Balance implementation complexity against potential cost savings.

## Considered Options

- Object per fragment
- Bundle objects into packfiles

## Decision Outcome

Store one object per fragment (actually two, counting metadata), and forego the benefits of
intelligent tiering for the time being. We can layer on additional processes in the future to bundle
infrequently accessed fragments together to gain these benefits if needed.

### Consequences

- Good, because there's an immediate path forward for durably storing Lore data that's easy to
  reason about and (relatively) easy to implement.
- Good, because we leave open the door to taking advantage of intelligent tiering in the future.
- Bad, because we won't take advantage of the storage savings offered by intelligent tiering in
  the near term.

## Pros and Cons of the Options

### Object per fragment

In this model, every store write operation (`store_mutable`, `put_immutable`) writes a separate
object (or multiple objects) to S3.

Metadata for immutable store fragments would be keyed as `<hash>/<repo id>/<context>` (the fragment
hash comes first in order to ensure S3 has sufficient entropy for partitioning), the content of the
object would be the serialized `lore_fragment_t`. The fragment payload itself would be stored
as a separate object, keyed as `<hash>`. This means we can check the existence of a fragment for
a repo/context while still deduplicating payloads across files/repos.

Mutable writes would be keyed as `<hash>/<repo id>`.

- Good, because the implementation is simple.
- Good, because it allows for straightforward queries by using ListObjectsV2 to find an object
  matching the desired prefix.
- Good, because we don't need to synchronize access to an index file, allowing for easy and
  efficient horizontal scaling of CAS instances.
- Bad, because fragments contain at most 64KiB of data, we can't take advantage of Intelligent
  Tiering.
- Bad, because each fragment is stored as a separate object, we must issue a separate GetObject call for each
  fragment we wish to retrieve.

### Bundle objects into packfiles

Similar to the LoreStore implementation, we maintain an index file which allows for efficient lookup
of a fragment’s location within a separate packfile.

- Good, because it enables us to bundle up fragments into larger objects so we can ensure
  intelligent tiering is possible.
- Good, because we can use byte range fetches to retrieve only the relevant data from an object.
- Good, because if we bundle fragments together intelligently we can reduce the number of GetObject
  calls.
- Bad, because we would need to ensure a distributed lock on index files if updating objects in the
  same bucket from multiple CAS instances.
- Bad, because there is no ability to append to S3 objects, we would need to get, append in memory
  and update the object, both for indexes and fragment packfiles.
- Bad, because we would need a mechanism for bundling fragments efficiently to ensure we're not
  stuffing a frequently accessed fragment in with an infrequently accessed one, obviating the
  benefits of intelligent tiering.
- Bad, because querying becomes more complicated (rather than performing a ListObjectsV2 call to see
  if an object exists, we need to retrieve the entire index file).
