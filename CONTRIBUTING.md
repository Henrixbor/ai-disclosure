# Contributing

Keep the agent entrypoint short and the local tools dependency-free. New functionality must show the actual disclosure outcome, preserve uncertainty and avoid broad compliance claims.

For a bug, provide an anonymised manifest, minimal HTML, command, actual output and expected outcome. For a legal-rule change, include a dated primary source and distinguish statutory requirements, interpretive guidance and optional product defaults. Do not copy proprietary legal advice or confidential content into an issue.

Run `python3 -m unittest discover -s tests -v`. For UI changes, run `npm ci --ignore-scripts`, `npx playwright install chromium firefox webkit`, build the demo into a new directory with `python3 scripts/build_web.py --output .local-preview/site`, serve it on 127.0.0.1:4173, then run `npm run test:browser`. Remove or rename an earlier output explicitly; the build deliberately refuses to overwrite it.

Add behavioural tests for changed decisions, evidence invalidation and publication outcomes. Avoid tests that merely copy the implementation's text. Provider marking, arbitrary runtime surfaces and export handling require separate evidence; a passing manifest test is insufficient.

Contributions to original project code and documentation are under the MIT licence. Preserve attribution and third-party licence boundaries. Maintain source links and the documented support matrix.

Media mechanics: build fresh fixtures with `python3 scripts/build_media_fixture.py`, then run `node scripts/browser_media.cjs`. The runner serves them locally on port 4174 and stops its server. Fixtures are silent, so these checks do not validate spoken-notice wording or intelligibility.

Linux headless media tests need an audio output device. CI starts PulseAudio with a virtual `module-null-sink` before the media checks and stops it afterward. Without an audio server, Firefox reports a media error in the disclosure fixture and the player correctly keeps the recording unloaded. Do not bypass this by muting the disclosure, mocking `play()` or skipping the sequencing assertion. Failure output includes the player state and media errors.

The demo and media runners accept `AI_DISCLOSURE_BROWSER=chromium|firefox|webkit` (default Chromium). Run each engine, for example `AI_DISCLOSURE_BROWSER=firefox npm run test:browser` and `AI_DISCLOSURE_BROWSER=webkit node scripts/browser_media.cjs`. CI runs all three against the same generated fixtures; an unknown engine is an error. Screenshots include the engine name. These are Playwright browser builds and desktop contexts at different viewport widths, not certification of installed Safari/Chrome, physical mobile devices or assistive technologies. The WordPress and Next.js integration runners currently use Chromium.
