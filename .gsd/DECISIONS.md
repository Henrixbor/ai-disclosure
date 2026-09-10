# API decisions

- The developing WordPress adapter uses `/ai-disclosure/v1/posts/{id}/assessment` for private per-post inspection and evidence-backed assessment. It reuses WordPress authentication and capability checks; it does not create a separate credential system.
- Assessment recording and publication are separate operations bound by the exact title/content/excerpt revision. Non-autoloaded options retain active policy/version records. Explicit amendments name the prior record and reason, archive it, and use a byte-exact database compare-and-swap to reject stale writers. Identical retries preserve the record ID and avoid duplicate cache events.
- WordPress-native error objects and private/no-store HTTP responses form the development contract. Publishing bypasses and unsupported surfaces remain explicit coverage gaps, not implicit exemptions.
- Classic and block editor controls use a private, read-only POST inspection endpoint to bind facts to proposed text. They never publish articles, infer unknown provenance, or submit evidence through the ordinary post form. The existing publication gate checks the actual saved revision.
