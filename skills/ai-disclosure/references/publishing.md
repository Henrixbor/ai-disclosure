# Publishing integrations

## Choose the existing publication path

Inspect the project before selecting an adapter. Reuse its existing content store, templates and deployment process.

| Project path | Integration |
| --- | --- |
| Static HTML output | Use the bundled inventory, record, plan and build commands below. |
| Node/server-rendered components | Use the bundled fragment client below inside the existing publication transaction. |
| WordPress posts/pages | Read the [WordPress adapter guide](https://github.com/Henrixbor/ai-disclosure/blob/main/integrations/wordpress/README.md) and [migration guide](https://github.com/Henrixbor/ai-disclosure/blob/main/integrations/wordpress/MIGRATION.md). The PHP plugin and migration CLI are repository-only development integrations, not bundled in this skill. |
| Other CMSs, native apps or external widgets | Implement the notice in the owning component and publishing path; retain unsupported surfaces in the report. |

For WordPress, use an existing trusted repository checkout or obtain the public repository at an explicit revision. Keep the PHP plugin and migration client on the same policy version; do not combine an older catalog install with arbitrary newer runtime files. Follow the adapter's isolated-site verification before activating its publication gates. From that checkout, `python3 scripts/wordpress_migrate.py --discover --api-url https://example.com/wp-json` reads the authenticated inventory using credentials supplied privately as documented. It creates no origin facts. Establish evidence, plan the batch, then apply within the authorized migration scope. Connect future creation/editorial jobs to assessment recording before normal publication, and verify the actual templates, feeds and caches. A completed scan is not complete site coverage.

These links describe development main and may be newer than an installed release. Check the selected revision's requirements and release status. Installing this skill does not install or activate a CMS plugin.

## HTML publishing adapter

This adapter renders local, static article and image disclosures. An experimental local audio/video player is also available, with the limitations below. A local HTML chat wrapper can carry interaction notices. Canvas and external frames still require dedicated integration; builds report these gaps rather than claim coverage. Use the customer's existing build output as input and deploy only the new output after browser verification.

## Bind once in the source template

```html
<article data-ai-content="article-123">
  <h1>Article title</h1>
  <!-- ai-disclosure -->
  <p>Article content.</p>
</article>

<figure class="aid-media" data-ai-content="image-456">
  <!-- ai-disclosure -->
  <img src="illustration.jpg" alt="Description of the image">
</figure>
```

Use stable distinct IDs for independently encountered assets. The comment is a build slot, not a visible disclosure by itself. Preserve it in pre-publication HTML (disable comment stripping until this tool runs). A human-origin/exempt item may use the same template: no visible label is emitted. Never place image slots under media or article slots after body text. The adapter adds its stylesheet, which the site's Content Security Policy must permit. Host CSS can affect visibility; browser tests remain required.

## Inventory existing output

```sh
python3 <skill-directory>/scripts/site.py inventory --root dist
```

The JSON inventory lists actual SHA-256 region revisions, candidate gaps and explicit decorative exclusions. Discovery covers articles, images, audio/video, frames, canvas and explicit bindings; ordinary unannotated divs, routes not in the build and runtime content are not proved covered. Do not equate zero discovered gaps with exhaustive inventory. Existing content still needs evidence-backed origin and legal-context decisions.

## Record facts at generation or editorial publication

The creation hook writes an item JSON file using the assessment manifest fields except `revision` (computed by the tool). It must supply current origin and context evidence. Then:

```sh
python3 <skill-directory>/scripts/site.py record --root dist --manifest ai-disclosure.json --facts item-facts.json --role publisher
```

Use `--role` to initialise an assessed role; omission on a new manifest leaves it unknown. Existing roles are preserved. Each record replaces the old item completely, preventing stale review/evidence inheritance. Repeated identical records do not rewrite the manifest. Current declared review can be supplied explicitly with the inventory revision. The tool cannot verify that the human review occurred.

Run record operations serially: the current file-backed registry is not a concurrent multi-writer database. Use your CMS's transaction queue for parallel creation jobs. Keep facts outside the public directory and do not use this command just to silence stale-content failures. Generation/publishing hooks are the trusted origin source; record is not an AI detector.

## Plan and stage

```sh
python3 <skill-directory>/scripts/site.py plan --root dist --manifest ai-disclosure.json
python3 <skill-directory>/scripts/site.py build --root dist --manifest ai-disclosure.json --output release-site
```

`plan` never writes. `build` refuses an existing destination, source symlinks, stale facts, unresolved assessments and unsupported required rendering. It stages the site locally before moving it into the new destination; it does not deploy. Input must already be a public build directory; do not point it at a repository containing secrets. Dotfiles are omitted, but that is not a secret scanner. Retain original source assets; the tool does not modify media metadata or implement provider marking.

JSON evidence goes to stdout; redirect it to a private CI artifact outside public output. Exit 0 means the requested operation succeeded, 1 means gaps remain, 2 means input/operation error. Build output still needs browser checks for visibility, placement, no-JavaScript behaviour, direct links and the production stylesheet/CSP. Review substantive policy changes separately.

## Integrate into existing frameworks and CMSs

For static exports (including frameworks or CMSs that produce HTML), add bindings to the existing templates and run record/plan/build between the original build and deployment. Generation jobs provide facts; pure layout builds must not silently re-attest content history.

Server-rendered, dynamic and personalised sites need equivalent calls in their content pipeline and disclosure output in their templates, plus runtime verification. This static adapter is not a drop-in runtime for those sites. Keep unsupported routes in the report until integrated.

## Experimental local media playback

Wrap one local `<audio>` or `<video>` in `figure.aid-media`, with an ID and disclosure slot before the media. Supply an explicit local `src`, a closing tag, and `data-ai-notice-src="notice.wav"` for audio deepfakes. Video facts must declare `audio_deepfake` as true or false. A required spoken notice must be an intelligible, accurate recording in the audience's language; this tool checks its presence and revision, not its words or audibility.

The generated player holds the content source until its spoken notice finishes. A notice loading failure prevents content playback. Visible labels remain in the player frame, including its fullscreen view. Without JavaScript the label remains and playback is disabled. Permit the local player script under the site's CSP. Changing configuration invalidates a mounted player; render a fresh version-bound fragment instead.

This is an experimental adapter, not production media coverage. Local caption/subtitle tracks are preserved with a selector; audio displays timed text and video uses native captions. Each track needs `src`, `srclang` and `label`, with at most one `default`. Alternative sources and other track types are reported as unsupported, not stripped. Downloads, direct asset URLs, external players, live streams, picture-in-picture, exported clips and people joining midway need separate solutions. Do not use it where those surfaces or accessibility needs remain unresolved. Playback sequencing tests use silent test files and do not establish the adequacy of an actual spoken disclosure.

Asset revisions include locally referenced media, posters and notices. Remote assets, missing files and paths escaping the public root are unresolved. Replacing media bytes invalidates the old manifest even when HTML is unchanged. Freeze the source build during inventory, recording and staging. The staged snapshot is assessed again before publication output is created, catching changes during copying.

## Chat interaction wrapper

Use the site's existing conversation component with this source structure:

```html
<section class="aid-chat" data-ai-content="support-chat">
  <h2>Support</h2>
  <!-- ai-disclosure -->
  <div role="log" aria-label="Conversation"><!-- existing conversation --></div>
  <form><!-- existing labelled composer and controls --></form>
</section>
```

Record `kind: "chatbot"`, `direct_ai_interaction: true`, scope and evidence. Keep the slot a direct child before conversation and controls. The adapter writes a visible interaction notice; its default sticky placement retains it when a visitor follows a deep link to the composer. Verify against the site's scroll containers, headers and CSS. Reuse the rendered wrapper for new and resumed sessions. Do not insert only a composer or transcript while leaving the notice behind. The notice has no acceptance or dismissal state and needs no JavaScript.

This is presentation support for a declared AI interaction, not a chatbot service or automatic widget discovery. It neither generates replies nor intercepts network requests. Provider/both/unknown roles still receive unresolved-role findings for duties this package does not implement. An existing publisher can use it to present its provider's interaction disclosure; building an AI product may make that customer a provider and requires that separate assessment. External widget frames, voice interactions and native apps need their own integration. Do not reclassify the customer's role merely to pass a build. No obvious-interaction exception is automated.

Chat facts bind the component revision. Conversation replies are not individually represented by that template hash; independently published answers or exported transcripts require their own records and appropriate notices. Browser fixtures test presentation and template replacement, with no connected model.

## CMS and server-rendered components

The fragment path runs the same assessment and placement rules against an in-memory rendered component, without crawling other pages or writing a temporary HTML document. It is available as Python functions `fragment_inventory` and `render_fragment` in `scripts/site.py`, or as CLI commands:

```sh
python3 <skill-directory>/scripts/site.py inspect-fragment --root public-assets --html component.html --page news/index.html
python3 <skill-directory>/scripts/site.py render-fragment --root public-assets --html component.html --page news/index.html --manifest component-facts.json
```

Input must be exactly one closed `data-ai-content` root, using the same article, figure or chat templates. Nested independently encountered media needs its own binding and fact record. `--page` is the actual relative public document location used to resolve local asset URLs. Prefer root-relative asset URLs for components reused across routes. Keep private facts outside the public asset root.

At a generation/editorial transaction, inspect the actual rendered component to obtain its revision, then save that revision together with evidenced origin, context and any valid review in the CMS's own transactional records. Do not refresh facts during a routine read just to eliminate a stale-record error. The renderer does not mutate those records or verify their authenticity.

A successful render returns `html`, `assets` and a private `report`. `assets` maps required local filenames to contents: stylesheet and, for media, player script. Serve versioned copies once through the application's existing static asset pipeline and load them in the enclosing page. Load the player runtime before inserting dynamic media; its observer mounts newly inserted rendered players. Resolve content and asset versions atomically. Cache results by content revision, asset revisions, declared facts and toolkit version, not content ID alone.

On any unresolved finding, `html` is null and `assets` is empty. Hold that update and retain the previous published version; never treat null as an instruction to delete existing content or publish the original unlabelled component. Initial server rendering and client navigation must use the same rendered component, including the notice. Do not expose the private report or CMS origin evidence in a public JSON response.

This tool is not an HTML sanitizer. Pass trusted template output with user content escaped/sanitized by the host application; it preserves existing HTML. It is a rendering integration point, not automatic support for every CMS, framework, iframe, native client or export. Verify the final route, scrolling, CSS/CSP, accessibility and application caching. The browser fixture exercises a recorded update and holds an unrecorded one; it does not stand in for production integration tests.

## JavaScript publishing client

Node projects can call the same engine without temporary HTML/manifest files. The optional CommonJS module has no npm dependencies; it needs Node 22+ and Python 3.9+ on the publishing worker. Keep it out of browser bundles and edge runtimes. Run it during generation, editorial publication or a build, then serve the saved result without starting Python for each visitor.

```js
const { renderFragment } = require('./.agents/skills/ai-disclosure/scripts/node.cjs');

const result = await renderFragment({
  root: '/absolute/path/to/public-assets',
  html: trustedRenderedComponent,
  manifest: savedEvidenceForThisVersion,
  page: 'news/index.html',
});
if (result.html === null) {
  // Retain the last published version; send result.report to a private review queue.
  throw new Error('Disclosure review required before publishing this update');
}
// Store result.html and result.assets together in the existing publication transaction.
// Load returned assets once in the enclosing page. Keep result.report private.
```

`inspectFragment({root, html, page})` returns the inventory used when recording evidence. `renderFragment({root, html, manifest, page})` returns HTML/assets/report. `exportDocument` accepts the same fields plus `title` and `language`, returning the portable document result described below. All return promises. Input is trusted application data, not a public request body; HTML is not sanitized. Do not automatically regenerate evidence when inspection detects a new revision.

An unresolved assessment resolves with `html: null`; invalid input, missing Python, timeout or process failure rejects. Both outcomes must hold the update. Each call starts a local process with JSON over stdin and no shell. The optional second argument accepts `python` (one executable path, no arguments) and `timeoutMs` (1–300000, default 30000). `AI_DISCLOSURE_PYTHON` can set the executable instead. Requests are limited to 32 MiB and captured output to 64 MiB. Batch/cache in the host pipeline where appropriate; the client provides no job queue, database transaction or retry policy. This is an integration API, not a completed adapter for every framework.

## Portable document export

`export-document` renders an assessed article/image component as a standalone HTML document with its own styles, visible notices and embedded PNG/JPEG/GIF/WebP images:

```sh
python3 <skill-directory>/scripts/site.py export-document --root public-assets --html component.html --manifest export-facts.json --title "Publication title" --language en
```

Like fragment rendering, this returns JSON. Save only its `html` field as the downloadable `.html` document; keep its `report` private. `html: null` means no export may be published. The function `export_document` exposes the same operation for a publishing integration. An export SHA-256 identifies the exact generated HTML. The operation does not overwrite files or mutate records.

Assess the export's own publication context. A conversation transcript must be recorded as publication text; the interaction notice from a live chatbot is not a substitute. Existing review exceptions require current evidence and version matching. Do not carry a scope decision into a materially different publication without reassessing it.

The export accepts an explicit semantic subset of publication HTML. It rejects active/unsupported elements, hidden content, inline styles, relative navigation links, responsive image alternatives and images over 20 MiB. It removes source classes and behavioral attributes, retaining the supported document structure, text, hyperlinks and image alt text. The host's CSS and scripts are not included. Root-relative asset paths resolve against the supplied asset directory, then image bytes are embedded and checked against the assessed hash. HTTP(S)/mailto links and document anchors remain usable; the document makes no automatic external requests.

Notices remain available offline and in print styling. Images are embedded byte-for-byte, preserving their original metadata. This does not add machine-readable provider marking, authenticate existing provenance, burn labels into raster pixels, or make a separately extracted raw image carry the document's label. Distribute the document as a unit. Raw media downloads, audio/video exports, PDF/Word generation and native/social sharing still need dedicated integrations and verification. Language identifies the document language; default notices are currently English and localized wording still requires an implementation decision.
