---
status: accepted
date: 2024-12-20
deciders: Hannes Muurinen, Mattias Jansson, Joshua Cohen, Raghav Narula, Manuel Lang
---

# ADR-00009: Lore library JavaScript binding options

## Context and Problem Statement

We want to be able to call the Lore library from JavaScript applications. The first application that needs this is the Visual Studio Code plugin, and the same library might be also used by future Electron applications or server-side JavaScript-based code that needs access to Lore functionality.

We need to determine which approach to use to expose the library for JS applications.

## Decision Drivers

- Support direct Lore library calls from JavaScript
- Avoid the old method of spawning Lore CLI processes and parsing the text output, which is brittle
- Avoid the extra process spawn overhead to make the Lore calls faster

## Considered Options

- Bindings written in Rust using [napi-rs](https://napi.rs/)
- Bindings written in Rust using [neon-rs](https://neon-rs.dev/)
- Bindings written in C or C++ using the [Node.js native API](https://nodejs.org/api/n-api.html)
- Using [node-ffi-napi](https://github.com/node-ffi-napi/node-ffi-napi) to autogenerate JS bindings from `lore.h`

## Decision Outcome

Chosen option: "Bindings written in Rust using napi-rs", because the developer experience was superior to any of the other alternatives. It allows us to work on native Rust code without needing to introduce much extra boilerplate code to handle JS-to-Rust and Rust-to-JS type conversions. It also supports async calls through JS Promises automatically without needing to write code that starts threads manually.

### Consequences

- Good, because allows us to use the same programming language that's used for the rest of the Lore library implementation
- Good, because has a minimal amount of boilerplate code, making it easy to maintain
- Good, because autogenerates the TypeScript interface from the Rust code
- Good, because handles async Promise handling automatically without needing to write the async handlers manually
- Neutral, because the autogeneration removes some control from us

## Pros and Cons of the Options

### Bindings written in Rust using napi-rs

A proof of concept using napi-rs was written internally. The developer experience of the library is excellent, and the library is able to generate and expose a JavaScript interface automatically by adding `#[napi(object)]` and `#[napi]` decorators for `struct`s and functions that should be exposed to JavaScript. The functions can use native Rust data types for input and output, and these are automatically converted to corresponding JS data types under the hood. The amount of both Rust and JavaScript/TypeScript boilerplate is minimal, since the library autogenerates most of the code.

It also supports async functions without any extra boilerplate code, and any async functions tagged with the decorators are automatically turned into functions returning JavaScript Promises. The async code returns a Promise to the JavaScript caller, and the async function is run automatically in Tokio runtime.

- Good, because allows us to use the same programming language that's used for the rest of the Lore library implementation
- Good, because autogenerates cross-compiled multiplatform code that selects the binary implementation based on the system architecture
- Good, because the developer experience is superior to any of the other alternatives
- Good, because supports async Promises natively without any extra boilerplate
- Good, because autogenerates the TypeScript interface, minimizing maintenance work and human errors
- Neutral, because the autogeneration removes some control from us

### Bindings written in Rust using neon-rs

A proof of concept using neon-rs was written internally. The library requires the user to write wrapper functions that use special `JSObject`, `JSArray`, `JSString`, `JSNumber` and similar data types for input and output. Conversion from Rust data types to these types needs to be done manually. Functions with this kind of interface can be exposed to JS through the library, and it autogenerates the JavaScript code that can be used to call the Rust functions. However, it doesn't autogenerate a TypeScript interface, and a TS interface needs to be written manually.

The library supports async JS Promises, but they need to be handled manually. Async code can be executed by creating a `JSPromise` in the Rust side handler function, and spawning manually a thread that can call `resolve` or `reject` for that object. This introduces some boilerplate code for all the async calls.

- Good, because allows us to use the same programming language that's used for the rest of the Lore library implementation
- Good, because autogenerates cross-compiled multiplatform code that selects the binary implementation based on the system architecture
- Neutral, because gives us more control by not relying so much on autogeneration
- Bad, because requires a lot of boilerplate code to handle the basic data type conversions
- Bad, because requires a lot of boilerplate code to handle async calls
- Bad, because doesn't autogenerate a TypeScript interface

### Bindings written in C or C++ using the Node.js native API

A proof of concept using the Node.js native API was written internally. The native C API gives us the most control, but at the same time requires us to write everything manually.

The native API supports async JS Promises, but they need to be handled manually. Async code can be executed by creating a Promise object with `napi_create_promise`, and spawning a worker thread using `napi_create_async_work` and `napi_queue_async_work`. The worker code needs to handle Promise resolving or rejection manually, and requires a lot of boilerplate code for each library function.

- Neutral, because gives us more control by not relying on autogeneration
- Bad, because requires a lot of boilerplate code to handle the basic data type conversions
- Bad, because requires a lot of boilerplate code to handle async calls
- Bad, because doesn't autogenerate a TypeScript interface
- Bad, because C code is harder to make secure and memory safe than Rust code

### Using node-ffi-napi to autogenerate JS bindings from `lore.h`

Some effort was used to try to use `node-ffi-napi` library to autogenerate a JavaScript interface from `lore.h` and a precompiled DLL. This turned out not to work at all due to issues in the library. The library hasn't received updates for more than two years, so it might just be unmaintained and broken.

Also even if it did work, it would have trouble working directly with the current `lore.h` interface, which exposes the function return payload through a series of Rust side function callbacks. Turning this output into something the JS side can use would require some intermediary code that gathers the events and forms a JS side response out of it.

- Bad, because the library seems to be unmaintained
- Bad, because requires a lot of boilerplate code to handle the calls
