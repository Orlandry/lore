---
status: accepted
date: 2026-04-10
deciders: Mattias Jansson
consulted: Jeff Roberts
---

# ADR-00016: Switch default compression to Zstd level 6

## Context and Problem Statement

Lore uses Oodle Kraken for fragment compression with a default level of 6 (Optimal2). While Oodle
achieves excellent compression ratios, level 6 compresses at only ~2 MiB/s which severely impacts
commit throughput. Additionally, Oodle is a proprietary library requiring platform-specific static
libraries, creating distribution and portability constraints.

We benchmarked LZ4, LZ4 HC, Zstd, and Oodle Kraken across multiple compression levels using the
Silesia corpus (202 MiB tar archive, 3 iterations averaged).

## Decision Drivers

- Compression ratio (storage and transfer cost)
- Compression speed (commit throughput)
- Decompression speed (checkout/read throughput)
- Library availability and portability (open source, cross-platform)

## Benchmark results

| Algorithm              | Ratio | Compress (MiB/s) | Decompress (MiB/s) |
|------------------------|------:|-----------------:|-------------------:|
| LZ4 default            | 47.6% |            718.7 |             2494.5 |
| LZ4 HC 4               | 37.7% |            114.7 |             2494.3 |
| LZ4 HC 9               | 36.7% |             49.4 |             2494.2 |
| LZ4 HC 12              | 36.5% |             16.3 |             2496.8 |
| Zstd 1                 | 34.5% |            602.0 |             1363.1 |
| Zstd 3                 | 31.2% |            353.1 |             1261.8 |
| Zstd 6                 | 28.9% |            136.5 |             1284.9 |
| Zstd 12                | 27.3% |             44.2 |             1332.7 |
| Zstd 19                | 24.9% |              3.4 |             1147.9 |
| Oodle Kraken 2 (VFast) | 29.8% |            207.8 |             1377.1 |
| Oodle Kraken 3 (Fast)  | 28.2% |             95.6 |             1413.1 |
| Oodle Kraken 4 (Norm)  | 26.7% |             41.2 |             1271.4 |
| Oodle Kraken 5 (Opt1)  | 24.8% |              5.0 |             1272.3 |
| Oodle Kraken 6 (Opt2)  | 23.9% |              2.2 |             1312.6 |

## Considered Options

- **Keep Oodle Kraken level 6** (status quo)
- **Switch to Oodle Kraken level 3** (faster, slightly worse ratio)
- **Switch to Zstd level 6** (open source, good ratio/speed balance)
- **Switch to LZ4** (fastest, but poor ratio)

## Decision Outcome

Chosen option: **Zstd level 6**, because it offers the best balance of compression ratio, speed,
and portability.

Zstd level 6 achieves 28.9% ratio at 136 MiB/s compression and ~1285 MiB/s decompression. Compared
to Oodle Kraken level 3 (the closest competitor at 28.2% ratio, 96 MiB/s), Zstd is:

- 42% faster to compress at a comparable ratio tier (136 vs 96 MiB/s)
- Open source and widely available (BSD license, no proprietary library dependency)
- Available on all platforms without platform-specific static libraries
- A well-established industry standard (used by the Linux kernel, Facebook, and others)

The Oodle default level is also changed from 6 (Optimal2) to 3 (Fast) as a 43x compression speed
improvement (2.2 -> 95.6 MiB/s) with only a 4.3 percentage point ratio increase (23.9% -> 28.2%).
The previous level 6 default was unacceptably slow for interactive use.

All existing Oodle and LZ4 compressed data remains readable indefinitely.

As part of this change, fragment flag bit allocation is reorganized to group compression and
obliteration flags into contiguous ranges:

- Bit 0: PayloadFragmented
- Bits 1-7: Compression algorithms (LZ4, Oodle, Zstd, + 4 reserved) with group mask
- Bits 8-9: Obliteration state (Obliterated, Obliterating) with group mask
- Bits 17+: Storage metadata (unchanged)

This replaces the previous interleaved layout where obliteration flags (bits 3-4) sat between
compression flags (bits 1-2, 5), leaving no room for future compression algorithms without gaps.

### Consequences

- Good, because Zstd eliminates the proprietary Oodle library dependency for new data
- Good, because 136 MiB/s compression is fast enough for interactive commit workflows
- Good, because all existing Oodle and LZ4 compressed data remains readable indefinitely
- Good, because contiguous flag ranges allow adding compression algorithms without bit fragmentation
- Neutral, because Oodle decompression support must remain for backward compatibility

## Pros and Cons of the Options

### Zstd level 6

- Good, because 28.9% ratio at 136 MiB/s is an excellent speed/ratio tradeoff
- Good, because open source (BSD license), available everywhere
- Good, because ~1285 MiB/s decompression is fast enough for any storage back end

### Oodle Kraken level 3

- Good, because best-in-class decompression speed (~1413 MiB/s)
- Good, because slightly better ratio than Zstd 6 at similar speed tier (28.2% vs 28.9%)
- Bad, because proprietary library with platform-specific build requirements
- Bad, because no pure-Rust fallback

### LZ4

- Good, because fastest compression (719 MiB/s) and decompression (2495 MiB/s)
- Bad, because poor ratio (47.6%) approximately doubles storage and transfer costs vs Zstd/Oodle
