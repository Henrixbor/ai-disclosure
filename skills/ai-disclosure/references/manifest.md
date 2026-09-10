# Minimal publisher assessment input

Run `python3 <skill-directory>/scripts/assess.py PATH`. Python 3.9+, no dependencies or network calls. Output is JSON. Exit 0 means all supplied records have a supported assessment; 1 means review is needed; 2 means invalid input. **None means the site is compliant or fixed.**

```json
{
  "version": 1,
  "role": "publisher",
  "items": [
    {
      "id": "/news/example",
      "revision": "content-version-7",
      "kind": "text",
      "origin": "ai_generated",
      "applicable": true,
      "public_interest": true,
      "evidence": "CMS generation record and publisher scope assessment",
      "review": {
        "revision": "content-version-7",
        "substantive_human_review": true,
        "responsible_entity": "Example Publisher"
      }
    }
  ]
}
```

Required top-level fields: `version: 1`, `role`, nonempty `items`. Roles: `publisher`, `provider`, `both`, `unknown`. The last three receive a separate unresolved-role result; publisher content is still assessed.

Each item requires unique nonempty `id`, nonempty `revision`, `kind` and `origin`.

- `kind`: `text`, `image`, `audio`, `video`, `code`, `chatbot`, `other`.
- `origin`: `human`, `ai_generated`, `ai_modified`, `unknown`.
- `applicable`: true/false/null. This is an evidence-backed scope/timing assessment for this item, NOT "does it need a badge?" Missing/null means unresolved. It must account for role, jurisdiction, dates and exceptions outside the tool. Never guess it from a file timestamp.
- `evidence`: nonempty explanation/reference supporting concrete facts. No confidential prompts needed. The tool cannot authenticate it.
- `public_interest`: true/false/null for text; whether this is published to inform the public on matters of public interest.
- `deepfake`: true/false/null for image/audio/video; result of contextual assessment.
- Optional `creative_work`: true/false/null for media; an established qualifying creative-work assessment.
- Optional `review`: exact fields shown above. The tool checks version equality, a true substantive-human-review declaration and nonempty editorial-responsibility entity. It cannot establish that the review occurred. Use only for text; publish appropriate editorial contact separately.

Unknown optional facts use null or omission. No extra fields are accepted: this catches misspelled decisions rather than silently applying defaults. Store fuller provenance, dates and integration coverage in the project's own content records or report. Resolve inherited collection facts into these records before assessment.

This deliberately narrow tool does not infer legal facts, implement notices, inspect a site, verify exports, implement provider marking, grant a chatbot exception, or support every Article 50 case. The agent handles supported edits and documents the remaining gaps.

For the experimental HTML video player, declare `audio_deepfake` (boolean): whether the video contains deepfake audio. This controls the spoken-notice requirement and is a declared fact, not an audio detector result.
