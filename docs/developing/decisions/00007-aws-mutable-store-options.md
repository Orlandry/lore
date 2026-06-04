---
status: accepted
date: 2024-06-03
deciders: Mattias Jansson, Paul Sharpe
---

# ADR-00007: AWS mutable store options

## Context and Problem Statement

As described in [the S3 storage options ADR](00004-s3-storage-options.md), we planned to store both
immutable and mutable data in S3. The mutable store needs to support a compare and
swap operation which isn't trivial to do directly on top of S3 due to the inability to perform any
sort of conditional update. This ADR covers the considered options and decided outcome for how to
proceed with a cloud-based, durable implementation of the Lore mutable store.

## Decision Drivers

- Support a compare-and-swap operation
- Complexity of the implementation
- Cost of the implementation
- Data winds up in S3 eventually

## Considered Options

- S3 with locking via external coordination
- S3 with native locking via pre-release put-if-absent
- DynamoDB
- Keyspaces
- MemoryDB
- Consul
- External management of mutable store with subsequent serialization to S3

## Decision Outcome

DynamoDB

### Consequences

- Good, because it allows us to implement a safe compare-and-swap.
- Good, because implementing compare-and-swap on top of DynamoDB isn't particularly complicated.
- Neutral, while likely not expensive, given the scale involved, the cost of DynamoDB is higher than
  the equivalent operations would be on S3.
- Bad, because the data doesn't live in S3.

## Pros and Cons of the Options

### S3 with locking via external coordination

In this option, we only store mutable store data in S3, but we use some external system to
coordinate locking. This allows us to ensure that only one caller is trying to update a given key in
the mutable store at any time.

- Good, because it allows us to implement a safe compare-and-swap.
- Good, because all mutable store data lives natively in S3.
- Neutral, the cost for S3 is minimal and the cost for whatever mechanism we use for external
  coordination should be moderate at worst.
- Bad, because it requires coordination via an external service.
- Bad, because it's always moderately complex to implement locking correctly.

### S3 with native locking via pre-release put-if-absent

In this option, we only store mutable store data in S3 and we rely on pre-release `put-if-absent`
functionality to implement locking entirely using S3.

- Good, because it allows us to implement a safe compare-and-swap.
- Good, because all mutable store data lives natively in S3.
- Good, because the cost should be minimal.
- Neutral, because we're not familiar with the exact mechanics of how `put-if-absent` will work: it
  may not actually support what we need for managing locks.
- Bad, because it's always moderately complex to implement locking correctly.
- Bad, because expiring locks created with put-if-absent would be extra complicated.

### DynamoDB

In this option, we store the mutable store data exclusively in DynamoDB. DynamoDB has support for
conditional updates, so implementing compare-and-swap is a straightforward affair.

- Good, because it allows us to implement a safe compare-and-swap.
- Good, because implementing compare-and-swap on top of DynamoDB isn't particularly complicated.
- Neutral, while likely not expensive, given the scale involved, the cost of DynamoDB is higher than
  the equivalent operations would be on S3.
- Bad, because the data doesn't live in S3.

### Keyspaces

Keyspaces is AWS's managed Cassandra-compatible database. Keyspaces has support for lightweight
transactions which provide a straightforward and efficient way to implement compare-and-swap
operations.

- Good, because it allows us to implement a safe compare-and-swap.
- Good, because implementing compare-and-swap on top of Keyspaces isn't particularly complicated.
- Neutral, while likely not expensive, given the scale involved, the cost of Keyspaces is higher
  than the equivalent operations would be on S3. Keyspaces is also about 13% more expensive than
  DynamoDB.
- Bad, because the data doesn't live in S3.

### MemoryDB

MemoryDB is AWS's managed Redis-compatible database with added durability. Being Redis compatible we
can make use of Redis transactions. In clustered mode, Redis transactions only work for keys that
hash to the same cluster slot. Since we'd only be operating on single keys, this shouldn't be a
problem.

- Good, because it allows us to implement a safe compare-and-swap.
- Good, because implementing compare-and-swap using Redis transactions isn't particularly
  complicated.
- Bad, of all the non-S3 options, MemoryDB would likely have the highest cost.
- Bad, because the data doesn't live in S3.

### Consul

Consul is HashiCorp's configuration-focused key-value store.

- Good, because it allows us to implement a safe compare-and-swap.
- Good, because implementing compare-and-swap on top of Consul isn't particularly complicated.
- Good, because we're already going to be running Consul to support other functionality for Lore.
- Bad, because Consul isn't meant to be used as a key-value store for high throughput operations.
  It's meant to support infrastructure-scale operations. As such its ability to handle Lore's
  workload (particularly when expanded to a large user base) is a large unknown.
- Bad, because we'd need to manage the Consul cluster ourselves, rather than relying on an AWS
  managed resource.
- Bad, because the data doesn't live in S3.

### External management of mutable store with subsequent serialization to S3

In this option, we use one of the above options for storing mutable data but also serialize the data
back into S3 after the fact.

- Good, because it allows us to implement a safe compare-and-swap.
- Good, because all mutable store data lives natively in S3.
- Bad, because we pay the cost for S3 and the cost for whatever external system we use as the
  primary storage layer.
- Bad, because we still need to implement the same level of locking via external coordination in
  order to ensure there are no races when updating S3, even if the update has been applied to
  the primary store.

## More Information

Worth noting, that in our meeting with AWS to talk about `put-if-absent` they mentioned additional
future work that would allow `put-if-match`, so we may want to revisit this decision when that
functionality is in place.
