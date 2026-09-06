# Decision: embedding model is `sentence-transformers/all-MiniLM-L6-v2`, not `BAAI/bge-small-en-v1.5`

**Date:** 2026-09-06

## Context

fastembed's own default model, and the same one the abandoned `ai-notes-server`/`context-store`
services used, is `BAAI/bge-small-en-v1.5` — a natural first choice for continuity.

## What happened

Benchmarking on the target machine (AMD Ryzen 5 5600H) measured `bge-small-en-v1.5`'s quantized
(int8) ONNX inference at ~480ms/chunk via `cProfile` — time spent almost entirely inside
`onnxruntime`'s `run()` call, not tokenization or Python overhead. Thread count (1/2/4/6) made no
measurable difference, which points at the int8 quant-kernel path itself rather than scheduling.
This is consistent with known onnxruntime CPU behavior: int8 quantized ops can be slower than fp32
on CPUs lacking VNNI/AVX-512 int8 acceleration, sometimes dramatically so. At that rate, embedding
the full workspace (~17.6k chunks) would take over two hours.

Switching to `sentence-transformers/all-MiniLM-L6-v2` — same size class (22M params vs 33M,
384-dim output either way, ~90MB vs ~67MB on disk) but shipped by fastembed as a plain fp32 ONNX
graph, not quantized — measured ~11ms/chunk on the same machine: a ~43x speedup. The full
workspace (2,347 docs, 17,611 chunks) then embedded in 4m9s wall time.

## Decision

Default to `all-MiniLM-L6-v2`. It is one of the most widely validated small sentence-embedding
models available, and for this tool's actual use case — short markdown chunks, brute-force top-k
cosine, not a leaderboard benchmark — its retrieval quality is within noise of bge-small. A 43x
speed difference is not.

## Note for future maintainers

If this ever gets re-benchmarked on different hardware (in particular anything with AVX-512 VNNI,
e.g. recent Intel server/desktop chips), quantized `bge-small-en-v1.5` may well be *faster* there
than it was here, and could be worth reconsidering as the default. Override for a one-off
comparison with `--model BAAI/bge-small-en-v1.5` on `index`/`search` without touching the default.
