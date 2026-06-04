---
status: accepted
date: 2024-03-13
deciders: Mattias Jansson, Manuel Lang
consulted: Pablo Arroyo, Paul Sharpe
---

# ADR-00003: Auth tokens for sub-repos

## Context and Problem Statement

For the sake of controlling access to restricted content, a Lore repository can be comprised of
multiple sub-repositories, each with its own access controls. As we begin to consider the
implementation details for authentication, we need to decide how to represent auth data as it
pertains to a repo and all of its sub-repositories.

## Decision Drivers

- Ensure compatibility with all necessary network transports.
- Minimize client complexity.
- Minimize server complexity.
- Minimize the overhead of verifying authorization.

## Considered Options

- One auth token containing all necessary authorization data for an entire repository.
- One auth token per repository, client swaps between auth tokens as necessary.
- One auth token that only identifies the user, the server looks up authorization independently.

## Decision Outcome

Chosen option: "One auth token per repository, client swaps between auth tokens as necessary,"
because we can handle auth in a manner that won't break HTTP use cases while
also minimizing complexity elsewhere in the stack.

### Consequences

- Good, because there is no danger in generating an auth token so large that it doesn't fit within
  standard HTTP header limits.
- Good, because the server logic around authenticating connections doesn't need to change.
- Good, because the overhead of verifying authentication in the server is minimal.
- Bad, because the client needs to exchange for multiple auth tokens (one for each sub-repository
  involved in the command), and, in the QUIC scenario, establish one connection per token.

## Pros and Cons of the Options

### One auth token containing all necessary authorization data for an entire repository

In this model, the client identifies all repositories that would be impacted by a CLI operation and
exchanges the user-identifying token for a single JWT that describes the user's access to all
repositories. In the degenerate case, this could be on the order of multiple hundred separate
repositories. If we assume 18 bytes of authorization data per repository (16 bytes for the
repository id, and one byte each for read/write flags), this would translate to 24 bytes of base64
encoded data in a JWT claim. If we extrapolate that out to a command that impacts 300 repositories
we could start to see JWTs that are in the 7KB range. The commonly accepted limit for HTTP
header length is 8KiB, so it's clear that we could see a future where we approach this limit.

- Good, because it simplifies client logic, removing the need to request multiple tokens, or swap
  between them.
- Good, because it simplifies the QUIC server logic, the server receives a single token that it can
  use to authorize all streams for a connection.
- Good, because it simplifies the gRPC server logic, the auth token is included as metadata with
  each gRPC request and can be used to authorize the request.
- Neutral, because there is some degree of overhead around the server parsing hundreds of repo
  authorizations and searching those in an efficient manner.
- Bad, because the size of the token can approach or exceed HTTP header limits.

### One auth token per repository, client swaps between auth tokens as necessary

In this model, the client still identifies all repositories that would be impacted by a CLI
operation, but rather than requesting a single JWT that covers all repositories, it requests one JWT
per repository. When sending QUIC requests, the client will establish one connection per repository
(and because of that, per token), but can still utilize multiple streams within that connection.

- Good, because it simplifies the QUIC server logic, the server receives a single token that it can
  use to authorize all streams for a connection.
- Good, because it simplifies the gRPC server logic, the auth token is included as metadata with
  each gRPC request and can be used to authorize the request.
- Good, because the size of the token will be bounded.
- Good, because the logic for the server to authorize a request doesn't require searching through
  an unbounded list of repo authorizations.
- Bad, because the client must manage multiple tokens and connections based on the number of
  repositories impacted by the operation.

### One auth token that only identifies the user, the server looks up authorization independently

In this model, the client doesn't exchange the token for a repo-specific token at all, instead the
server is responsible for verifying authorization for the user identified by the token for each
repository being acted upon

- Good, because the size of the token will be bounded.
- Good, because the client logic is simple.
- Bad, because the server must perform authorization logic for each connection established which may
  involve coordinating with external services, or some other form of IO to establish what the
  authenticated user is allowed to do.
