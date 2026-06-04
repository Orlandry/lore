---
status: accepted
date: 2024-05-03
deciders: Manuel Lang, Paul Sharpe, Joshua Cohen
consulted: Mattias Jansson, Krisl Bulman, Andy Buecker, Patrick Boyd
informed: Wouter Burgers, Valentin Ritzi, Hannes Muurinen, Mikko Repolainen
---

# ADR-00005: Web server frameworks for Rust

## Context and Problem Statement

We're adding a web server into the Lore Server ecosystem, but there’s no precedent within the project regarding the different choices. At a glance, other than building a web server from scratch (which isn’t our business), 3 main frameworks seem to be showing on any search: Axum, Actix and Rocket.

We’ll compare these frameworks for our use case.

## Decision Drivers

- Maturity of the frameworks
- Activity on the framework development
- Compatibility with our existing tools and frameworks
- Performance

## Considered Options

- Axum
- Actix
- Rocket

## Decision Outcome

Chosen option: "Axum," because it has great press, seems to be growing fast (16k stars on GitHub) and it’s the most seamless choice for integration, as it’s inherently designed to work with Tokio. Actix and Rocket are both solid options but would require some additional configuration to work with Tokio, and we’d be in the business of tuning that.

### Consequences

- Good, because we’re picking a framework that's most aligned to work in tandem with the other dependencies.
- Good, because it’s easy to use (an internal proof-of-concept took only a few hours). Not that our API is complex anyway, in principle.
- Neutral, because the other options have at least as much documentation.

## Pros and Cons of the Options

### Axum

See the [Axum documentation](https://docs.rs/axum/latest/axum/).

- Good, because is actively developed by the Tokio team
- Good, because it’s designed to work seamlessly with Tokio runtime
- Good, because it's performant and suited for large projects
- Neutral, because being newer to Actix and Rocket, it leverages maturity through underlying libraries like Hyper and Tower
- Good, because it's the recommendation from Blessed.rs

### Actix

See the [Actix website](https://actix.rs/).

- Good, because it has a large community. 20k stars on GitHub
- Good, because it’s mature, with versions from 2017
- Neutral, because it's performant but suited for medium projects
- Neutral, because it faced safety issues in the past
- Neutral, because it can be configured to use Tokio

### Rocket

See [Rocket on GitHub](https://github.com/rwf2/Rocket).

- Good, because it has the largest community. 23k stars on GitHub
- Good, because it’s mature, with versions from 2016
- Neutral, because there's discrepancy in the references regarding performance. Good at scale
- Bad, because versions are sparse
- Neutral, because it now supports async but was built with sync in mind

## More Information

### Dependencies added by each framework

- Axum: see its [`Cargo.toml` dependencies](https://github.com/tokio-rs/axum/blob/74eac39e0610d1f702fe297b84d04212c806738e/axum/Cargo.toml#L43).
- Actix: see its [`Cargo.toml` dependencies](https://github.com/actix/actix-web/blob/b6bee346f7c42b083b4e3cb44f4ff8d38ef8f0fe/actix-web/Cargo.toml#L85).
- Rocket: see its [`Cargo.toml` dependencies](https://github.com/rwf2/Rocket/blob/f50b6043e8b0c78ecf5b6f160190120887549e07/core/lib/Cargo.toml#L46).

### Performance

You can check several comparisons one-to-one (see references below), but we found the [TechEmpower benchmarks](https://www.techempower.com/benchmarks/) the clearest.

Where Axum is 6th, Actix 12th and Rocket doesn't feature (another post says it's 439th — see this [Rust users thread](https://users.rust-lang.org/t/which-framework-is-best-rocket-or-actix/91668)).

### Other references

You can check some references such as:

- [Blessed.rs networking crates](https://blessed.rs/crates#section-networking-subsection-http-foundations)
- [Axum vs Actix vs Rocket comparison](https://eternal-search.com/en/axum-vs-actix-vs-rocket)
- [LogRocket: top Rust web frameworks](https://blog.logrocket.com/top-rust-web-frameworks/)
- [Rust Rocket vs Axum hello-world performance](https://medium.com/deno-the-complete-reference/rust-rocket-vs-axum-hello-world-performance-2938ec1f0b12)
