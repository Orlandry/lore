---
status: accepted
date: 2023-12-23
deciders: Mattias Jansson, Manuel Lang, Joshua Cohen
consulted: Yuriy O'Donnell, Stefan Boberg
informed:
---
# ADR-00001: Use FastCDC, a well-documented content-defined chunking strategy

## Context and Problem Statement

Lore currently has an inefficient chunking strategy which utilizes xxHash, stepping one byte at a time, hashing 64 bytes and inserting a chunk border if the hash matches a certain pattern using modulo operator. We want to use a well-defined and tested content-defined chunking strategy which can ideally be adopted in the greater engine ecosystem.

## Decision Drivers

* Performance
* Deduplication ratio
* Ease of adoption in greater ecosystem

## Considered Options

* Current algorithm (xxHash with modulo)
* FastCDC

## Decision Outcome

FastCDC, due to increased performance while maintaining deduplication ratio in test data sets.

### Consequences

* Good, because performance of chunking is increased

### Confirmation

A test was setup where the UE5 main repo was committed to Lore and statistics on total execution time, chunk size distribution and deduplication ratio was output. Results as follows.

#### FastCDC

```text
Command executed in 326s

Chunk distribution, interesting ranges (around expected chunk size and at chunk size threshold)
Bucket [39424-39680): 39486 (2.29%)
Bucket [65280-65536): 2910 (0.17%)

Deduplication ratios
Deduplicated chunks 573100/2809256: 20.40%
Deduplicated bytes 12267781682/238314614264: 5.15%
```

#### xxHash with modulo

```text
Command executed in 372s

Chunk distribution, interesting ranges (around expected chunk size and at chunk size threshold)
Bucket [39424-39680): 51624 (3.08%)
Bucket [65280-65536): 2148 (0.13%)

Deduplication ratios
Deduplicated chunks 518552/2719374: 19.07%
Deduplicated bytes 12298549446/237621986814: 5.18%
```

## Pros and Cons of the Options

### FastCDC

[FastCDC paper (USENIX ATC '16)](https://www.usenix.org/system/files/conference/atc16/atc16-paper-xia.pdf)

* Good, because the hash is a rolling hash with shift, add and array lookup `(fp << 1) + G[b]`
* Good, because reasonably easy to configure to use case with bitmasks for hash pattern matching
* Good, because it's a well-documented algorithm that can be widely adopted
* Bad, because algorithm depends on inherent magic numbers specific to each implementation

### Current algorithm

xxHash of 64 bytes, step one byte at a time, modulo hash with magic number to find pattern

* Good, because it can be tweaked to the exact use case
* Bad, because it's slow to calculate hash and step one byte at a time
* Bad, because it's Lore-specific and hard for the greater ecosystem to adopt
