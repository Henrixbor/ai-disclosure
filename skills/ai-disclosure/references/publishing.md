# HTML publishing adapter

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

This is an experimental adapter, not production media coverage. Caption tracks and alternative sources are currently rejected, not stripped. Downloads, direct asset URLs, external players, live streams, picture-in-picture, exported clips and people joining midway need separate solutions. Do not use it where those surfaces or accessibility needs remain unresolved. Playback sequencing tests use silent test files and do not establish the adequacy of an actual spoken disclosure.

Asset revisions include locally referenced media, posters and notices. Remote assets, missing files and paths escaping the public root are unresolved. Replacing media bytes invalidates the old manifest even when HTML is unchanged. Freeze the source build during inventory, recording and staging.

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
