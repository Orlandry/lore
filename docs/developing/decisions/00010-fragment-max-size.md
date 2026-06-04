---
status: accepted
date: 2025-01-08
deciders: Paul Sharpe, Mattias Jansson, Joshua Cohen
---

# ADR-00010: Increasing fragment max size

## Context and Problem Statement

Previously in [ADR-00001](00001-fast-cdc.md) we described the content-defined chunking algorithm
for chunking large data blocks into smaller fragments based on content patterns found by FastCDC
algorithm. The fragment max size was set to 64KiB as this seemed like a good tradeoff at the time.
After further investigation it seems this decision leads to too many fragments being defined by
the max size limit rather than content patterns.

The algorithm also defines an "expected" chunk size where the distribution normalization kicks in
and shifts the pattern matching to make it more likely to find a content pattern match. This is
currently set at ~38KiB.

Max size fragments are less likely to be deduplicated as the content border will most likely not
be identical when data changes, either content or size, which can lead to cascading chunk changes
for a large data buffer. A content-defined chunk border is more likely to be identified under change
and yield proper deduplication of later chunks in the data buffer.

## Decision Drivers

- Ratio between content-defined chunk borders (hash pattern matching) and max size limit
- Memory max pressure from max number of fragments in flight times the maximum fragment size

## Considered Options

- Keep the current 64KiB limit
- Increase max limit to 256KiB with an expected chunk size at 64KiB
- Larger max limit or expected chunk size

## Decision Outcome

Chosen option: 256KiB max size and 64KiB expected chunk size

Memory usage issues can be mitigated/controlled by the local immutable store max capacity eviction
already implemented to put an upper bound on the static memory usage on server, as well as quick
scaling of new clean nodes to spread client induced dynamic memory load from parallel requests.

### Consequences

- Good, because larger max size means more content-defined chunk borders and less max size fragments
- Good, because maximum memory pressure is still within reasonable limits
`256KiB * 10k fragment requests in flight = 2.45GiB`
with an expected chunk size of 64KiB
`64KiB * 10k fragment requests in flight = 625MiB`
- Bad, because we increase the expected memory pressure on client

As an example, fragmenting precompiled binaries for a large project (7k files, ~8GiB data) yields the
following fragment size distribution and stats - which indicates the theoretical memory max pressure\
is unlikely to occur

```text
Commit stats
  Written fragments         : 95330
  Written raw bytes         : 8809162313
  Written payload bytes     : 2236219589 (74% compression)
  Deduplicated fragments    : 8841 (9%)
  Deduplicated raw bytes    : 770017646 (8%)
  Deduplicated payload bytes: 306894679 (13%)
  Written final bytes:      : 1929324910 (21%)
  Written list fragments    : 5759
  Written state fragments   : 28
Chunk size distribution:
     0 -   4096: *******                                  (1425  ) 1.49%
  4096 -   8192:                                          (59    ) 0.06%
  8192 -  12288:                                          (89    ) 0.09%
 12288 -  16384: *                                        (245   ) 0.26%
 16384 -  20480: *                                        (217   ) 0.23%
 20480 -  24576: *                                        (182   ) 0.19%
 24576 -  28672:                                          (123   ) 0.13%
 28672 -  32768:                                          (147   ) 0.15%
 32768 -  36864: ****************                         (2968  ) 3.11%
 36864 -  40960: ***************                          (2780  ) 2.92%
 40960 -  45056: ***************                          (2734  ) 2.87%
 45056 -  49152: **************                           (2572  ) 2.70%
 49152 -  53248: *************                            (2518  ) 2.64%
 53248 -  57344: **************                           (2643  ) 2.77%
 57344 -  61440: ***********                              (2149  ) 2.25%
 61440 -  65536: ***********                              (2075  ) 2.18%
 65536 -  69632: **************************************** (7283  ) 7.64%
 69632 -  73728: *************************************    (6839  ) 7.17%
 73728 -  77824: *******************************          (5691  ) 5.97%
 77824 -  81920: ***************************              (5067  ) 5.32%
 81920 -  86016: *************************                (4706  ) 4.94%
 86016 -  90112: ***********************                  (4306  ) 4.52%
 90112 -  94208: *******************                      (3532  ) 3.71%
 94208 -  98304: *****************                        (3147  ) 3.30%
 98304 - 102400: ****************                         (3082  ) 3.23%
102400 - 106496: **************                           (2638  ) 2.77%
106496 - 110592: **************                           (2694  ) 2.83%
110592 - 114688: ***********                              (2040  ) 2.14%
114688 - 118784: ***********                              (2020  ) 2.12%
118784 - 122880: *********                                (1744  ) 1.83%
122880 - 126976: ********                                 (1547  ) 1.62%
126976 - 131072: *******                                  (1365  ) 1.43%
131072 - 135168: *****                                    (1088  ) 1.14%
135168 - 139264: *****                                    (1083  ) 1.14%
139264 - 143360: *****                                    (1011  ) 1.06%
143360 - 147456: *****                                    (958   ) 1.00%
147456 - 151552: ****                                     (748   ) 0.78%
151552 - 155648: ****                                     (796   ) 0.83%
155648 - 159744: ***                                      (608   ) 0.64%
159744 - 163840: ***                                      (646   ) 0.68%
163840 - 167936: **                                       (512   ) 0.54%
167936 - 172032: **                                       (485   ) 0.51%
172032 - 176128: ***                                      (574   ) 0.60%
176128 - 180224: **                                       (445   ) 0.47%
180224 - 184320: **                                       (427   ) 0.45%
184320 - 188416: *                                        (320   ) 0.34%
188416 - 192512: *                                        (301   ) 0.32%
192512 - 196608: *                                        (285   ) 0.30%
196608 - 200704: *                                        (281   ) 0.29%
200704 - 204800: *                                        (233   ) 0.24%
204800 - 208896: *                                        (250   ) 0.26%
208896 - 212992: *                                        (208   ) 0.22%
212992 - 217088:                                          (165   ) 0.17%
217088 - 221184: *                                        (282   ) 0.30%
221184 - 225280:                                          (149   ) 0.16%
225280 - 229376:                                          (138   ) 0.14%
229376 - 233472:                                          (137   ) 0.14%
233472 - 237568:                                          (123   ) 0.13%
237568 - 241664:                                          (131   ) 0.14%
241664 - 245760:                                          (104   ) 0.11%
245760 - 249856:                                          (99    ) 0.10%
249856 - 253952:                                          (101   ) 0.11%
253952 - 258048:                                          (91    ) 0.10%
258048 - 262144: **********                               (1924  ) 2.02%
```

## Pros and Cons of the Options

### Keep the current 64KiB limit

- Bad, because there is a significant number of fragments defined by max size limit
- Good, because maximum memory pressure is kept low
`64KiB * 10k fragment requests in flight = 625MiB`
with an expected chunk size of 38KiB
`38KiB * 10k fragment requests in flight = 371MiB`

Fragment size distribution and stats of the same data set as above

```text
Commit stats
  Written fragments         : 186774
  Written raw bytes         : 8809162313
  Written payload bytes     : 2366061490 (73% compression)
  Deduplicated fragments    : 16665 (8%)
  Deduplicated raw bytes    : 773995346 (8%)
  Deduplicated payload bytes: 308108407 (13%)
  Written final bytes:      : 2057953083 (23%)
  Written list fragments    : 5772
  Written state fragments   : 29
Chunk size distribution:
     0 -   2048: **                                       (1360  ) 0.73%
  2048 -   4096:                                          (84    ) 0.04%
  4096 -   6144:                                          (39    ) 0.02%
  6144 -   8192:                                          (54    ) 0.03%
  8192 -  10240:                                          (46    ) 0.02%
 10240 -  12288:                                          (66    ) 0.04%
 12288 -  14336:                                          (49    ) 0.03%
 14336 -  16384:                                          (90    ) 0.05%
 16384 -  18432:                                          (94    ) 0.05%
 18432 -  20480:                                          (141   ) 0.08%
 20480 -  22528:                                          (144   ) 0.08%
 22528 -  24576: ***                                      (2083  ) 1.12%
 24576 -  26624: ****                                     (2815  ) 1.51%
 26624 -  28672: ****                                     (2689  ) 1.44%
 28672 -  30720: ****                                     (2709  ) 1.45%
 30720 -  32768: ****                                     (2757  ) 1.48%
 32768 -  34816: ****                                     (2658  ) 1.42%
 34816 -  36864: ****                                     (2572  ) 1.38%
 36864 -  38912: ***                                      (2441  ) 1.31%
 38912 -  40960: ***************************************  (24761 ) 13.26%
 40960 -  43008: **************************************   (24034 ) 12.87%
 43008 -  45056: *****************************            (18547 ) 9.93%
 45056 -  47104: ************************                 (15227 ) 8.15%
 47104 -  49152: *******************                      (12376 ) 6.63%
 49152 -  51200: ****************                         (10578 ) 5.66%
 51200 -  53248: *************                            (8182  ) 4.38%
 53248 -  55296: **********                               (6465  ) 3.46%
 55296 -  57344: *********                                (5818  ) 3.11%
 57344 -  59392: ********                                 (5074  ) 2.72%
 59392 -  61440: ******                                   (4203  ) 2.25%
 61440 -  63488: *****                                    (3631  ) 1.94%
 63488 -  65536: **************************************** (24987 ) 13.38%
```

### Larger max limit or expected chunk size

- Good, because the larger the maximum chunk size and difference between max
  and expected size the more likely to identify content-defined chunk borders
- Bad, because maximum memory pressure grows with fragment size
- Bad, because there are diminishing returns on content-defined chunk border
  ratio as size increases
