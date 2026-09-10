# API decisions

- The developing WordPress adapter uses `/ai-disclosure/v1/posts/{id}/assessment` for private per-post inspection and evidence-backed assessment. It reuses WordPress authentication and capability checks; it does not create a separate credential system.
- Assessment recording and publication are separate operations bound by the exact title/content/excerpt revision. Immutable, non-autoloaded options retain policy/version records; conflicting declarations require an amendment workflow that is still outstanding.
- WordPress-native error objects and private/no-store HTTP responses form the development contract. Publishing bypasses and unsupported surfaces remain explicit coverage gaps, not implicit exemptions.
