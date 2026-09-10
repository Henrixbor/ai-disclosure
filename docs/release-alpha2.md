# AI Disclosure 0.1.0-alpha.2

Adds a shared component renderer for CMS and server publishing. Inspect one rendered component, bind its revision to evidenced facts, and render the same minimal notices used by the static builder. A stale or unresolved update returns no publishable HTML, allowing the application to retain its previous published version.

The five-step agent skill remains unchanged. The publishing reference documents command-line and Python integration, static assets, version-aware caching and trusted template requirements. The renderer is not an HTML sanitizer or a complete CMS integration.

Validation: 46 Python tests, plus Chromium checks for a recorded dynamic update and a held stale update, alongside existing media/chat/static checks. Role gaps, arbitrary framework/native/export surfaces, provider marking and independent legal review remain outstanding. This is a prerelease for pilot integration, not legal certification or universal production coverage.

Upgrade by replacing the installed skill/plugin with this version after reviewing changes. Existing declared manifests remain version 1. Keep content and facts in your own publishing pipeline; installing the update alone does not integrate future content. Release 0.1.0-alpha.1 remains available unchanged.
