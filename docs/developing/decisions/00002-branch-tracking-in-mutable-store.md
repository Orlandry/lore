---
status: accepted
date: 2024-03-10
deciders: Mattias Jansson, Paul Sharpe, Joshua Cohen
consulted: Manuel Lang, Wouter Burgers
informed:
---
# ADR-00002: Use mutable store for branch tracking

## Context and Problem Statement

Lore currently stores branch information and current latest pointer is a separate file per branch on client. This doesn't translate well to backends and the desire to use the same code for client and server through the shared core library. Spreading the serialized data in multiple places is also a bad idea as it makes backup and data relocation harder.

## Decision Drivers

* Ease of use both in library and from external protocols
* Consolidating storage in as few separate systems and serialized paths as possible

## Considered Options

* Use the current separate files
The branch latest pointers and name is written in a tracking file inside the .lore directory. The server will have to use the same or its own tracking serialization, and any data backup or transfer will have to know about and include these files in any operation. Special API commands for get/set the latest pointer and the branch configuration will be needed. Branch list will be either collected as a list of tracking files or in a separate list file.

* Use the mutable store
The branch latest pointer is stored in the mutable store using the repository ID and branch name as input to the hash key. Branch configuration is stored in the immutable store with a mutable pointer using the same input to the hash key. Branch list can also be stored in the immutable store with a mutable pointer using the repository ID as hash key. No additional API commands is needed as data can be read from mutable store API - but could be introduced for clarity. No additional considerations needed for data backup or transfer as everything is in the general data stores.

## Decision Outcome

Use the mutable store as this reduces the number of separate serialization methods and places and unifies the data storage for the client and server. The access into the store over network can always be designed to either be a raw read with the generic mutable store API, or through a specific API for each use case.

### Consequences

* Requires less specific serialization code as everything is put in the existing mutable and immutable stores.
* Obfuscates data a bit, making it less clear and harder to do forensics as one can't just dump the content of a file to see a branch.

### Confirmation

A test implementation was made to prove the viability. It removed the remaining need for per-repository storage and repositories are now ready to transition to only being an opaque identifier and not a complex data structure serialized in different places on disk.
