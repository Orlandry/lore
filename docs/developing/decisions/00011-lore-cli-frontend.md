---
status: accepted
date: 2025-10-14
deciders: Jamie Higgins
consulted: Mattias Jansson, Raghav Narula
---

# ADR-00011: CLI frontend decisions

## Context and Problem Statement

We want to add styling and various visual improvements to the CLI. There are existing solutions for some of these, but there are also smaller versions of these features that we can implement ourselves. We need to determine which options to use.

## Decision Drivers

- Added dependencies
- Compile times
- Dependency churn
- Avoid reinventing the wheel where possible
- Balance immediate needs with long term goals

## Considered Options

- Third-party libraries:
  - General frontend: [Ratatui](https://ratatui.rs/)
  - Progress bars: [indicatif](https://github.com/console-rs/indicatif)
  - Pagination: [minus](https://github.com/AMythicDev/minus)
  - Colors and ANSI styling: [anstyle](https://github.com/rust-cli/anstyle)
- External pagination
- Custom pagination tool
- Custom progress bar
- Custom ANSI code handler

## Decision Outcome

Chosen options: "anstyle," "external pagination," and "custom progress bar."

The other considered libraries add a large number of external dependencies, and the features they give us aren't necessary (as of now.)

### Consequences

- Good, because we've avoided adding the extra dependencies (and all that entails.)
- Good, because the features are relatively simple to add.
- Good, because the added features can be replaced with any of the above libraries at a future date, if necessary.
- Bad, because we now have to maintain these features ourselves, some of which involve lower level code.

## Pros and Cons of the Options

### Third-party libraries

#### Ratatui

Ratatui is a popular framework for writing CLI applications. The framework uses a render loop style architecture, and includes various widgets and tools for making complex CLI user interfaces.

- Good, because applications aren't limited to one off commands.
- Good, because it simplifies making the application pretty.
- Good, because it's widely used.
- Bad, because would necessitate a rewrite of most of the CLI frontend.
- Bad, because the tools it's geared toward making are better suited as an application built on top of or alongside lore-client.
- Bad, because it introduces a large number of dependencies.

#### Indicatif

Indicatif is a library for creating spinners and progress bars.

- Good, because it handles many different scenarios (spinners, multiple progress bars, and more)
- Good, because it's popular and well-maintained.
- Neutral, because we currently don't need most of its features.
- Bad, because it introduces a number of new dependencies.

#### Minus

Minus is a library for adding pagination to a CLI app.

- Good, because it doesn't rely on using an external pager.
- Bad, because it's no longer maintained.
- Bad, because it's a large dependency to add (in addition to having its own dependencies.)

#### Anstyle

Anstyle is a small library for managing ANSI codes and styling.

- Good, because it's relatively small and does one simple thing well.
- Good, because it's maintained by the Rust CLI team.
- Good, because it's widely used across the Rust ecosystem (including cargo itself.)
- Good, because it includes tools for stripping ANSI codes when they're unsupported.
- Good, because it allows us to create styles out of composable functions (using the builder pattern.)

### External pagination

This option relies on the user deciding on their own paginator (for example, `less` or `more`)

- Good, because it's an expected solution across other CLI applications.
- Good, because the user has the freedom to make their own choice here (including no pagination.)
- Good, because it doesn't require much maintenance.
- Good, because it's simple to replace in the future if necessary.
- Bad, because the default Windows pager is mediocre (`more`.)
- Bad, because it's more complicated for the end user than something that's part of the app.

### Custom pagination tool

This would involve writing code to handle pagination ourselves.

- Good, because it would not rely on an external application.
- Bad, because it would require high development and maintenance costs, as it's a complex feature.

### Custom progress bar

This would involve creating our own progress bar.

- Good, because it's a relatively simple feature to add and avoids new dependencies.
- Good, because we can control when and where it appears, and how logging avoids writing over it.
- Bad, because it creates a new maintenance cost.
- Bad, because it doesn't include any complex features unless we add them.

### Custom ANSI code handler

This would involve managing formatting and styling codes ourselves.

- Good, because it's a simple feature to add and would avoid extra dependencies.
- Bad, because ANSI codes are easy to make mistakes with (for example, typos.)
- Bad, because we would need to come up with solutions for creating and managing styles.
