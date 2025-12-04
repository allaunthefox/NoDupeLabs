NoDupe similarity index formats
=================================

This document describes the two human-readable index formats that NoDupe supports for similarity indices:

- JSON (.json) — a single JSON object containing metadata and vectors
- JSON Lines (.jsonl) — one JSON object per line, streaming-friendly

Both formats are intentionally chosen to be easy to inspect with plain text tools and compatible with LLMs.

Conformance rules
------------------

JSON (.json)

- Must be a single JSON object
- Required top-level keys: `format`, `format_version`, `dim`, `ids`, `vectors`
  - `format`: string, must equal `nodupe.similarity.index`
  - `format_version`: string, semantic version like `1.0`
  - `dim`: integer >= 1 (embedding dimension)
  - `ids`: array of strings — each id corresponds to an item
  - `vectors`: array-of-arrays containing numeric values; shape must be `[len(ids)][dim]`
- Optional key: `meta` object with free-form metadata

JSONL (.jsonl)

- Must be newline-delimited JSON (one JSON object per line). See https://jsonlines.org/
- Each line must be a JSON object with required fields: `id` (string) and `vector` (array of numbers)
- Optional `meta` object may be included on each line but is not required

Compatibility
-------------
Files produced by NoDupe adhere to the above schema and include a JSON Schema under `nodupe/schemas/`.
Use standard tools (jq, sed, grep, python, text editors) to inspect or process these files.
