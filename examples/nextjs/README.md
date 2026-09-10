# Next.js publishing integration

A runnable App Router static export using the shared AI Disclosure engine. It demonstrates an AI-generated fictional civic-news article, not a real publisher's legal assessment. The fixture's origin is recorded in `content/facts.json`; applicability and public-interest status are explicit test assumptions. Replace those declarations with evidence for your own deployment.

From the repository root, with Node 22+ and Python 3.9+:

```sh
npm --prefix examples/nextjs ci --ignore-scripts
NEXT_TELEMETRY_DISABLED=1 npm --prefix examples/nextjs run build
python3 -m http.server 4175 --bind 127.0.0.1 --directory examples/nextjs/out
```

Open `http://127.0.0.1:4175/news/`. The article notice is present in the generated HTML before JavaScript runs. The same rendered content is used for client navigation. No Python process, model call or disclosure service runs for visitors. Dependencies are pinned to Next.js 16.3.4 and React 19.3.0; the core skill does not depend on them.

## How the integration works

`next.config.js` calls `scripts/prepare.cjs` before development startup or a production build, including direct `next build` commands. It reads trusted article HTML and saved facts, calls `renderFragment`, and writes only publishable HTML and disclosure CSS into `.generated`. React imports those generated files. Facts and assessment reports are never imported into the application or copied to `public`.

Unknown facts, changed content, changed referenced assets and unsupported rendering stop preparation with an error. Compilation does not proceed. A failed build must never be deployed; keep the last successful deployment. The toolkit does not operate your hosting platform or make a deployment atomic. Use an isolated build workspace and switch the whole successful `out` directory as one deployment. Do not run concurrent builds in the same checkout.

To demonstrate the stale-content check, change the article text without changing its facts and run the build. It fails with `Disclosure review required`. Restore the article to run the fixture again. Do not regenerate revisions just to pass this check: new generation/editorial transactions must provide current origin, context and any applicable review evidence. A routine layout build cannot establish those facts. For automated content creation, call `inspectFragment` after rendering the new content and save its revision with the generation job's evidence in the same transaction; the next build assesses that saved version.

## Adapt to an existing project

Install the skill into the project and point the preparation script at its `scripts/node.cjs`, or set `AI_DISCLOSURE_MODULE` to that absolute file path. The checked-in example defaults to the shared skill in this repository. `AI_DISCLOSURE_PYTHON` optionally selects one Python executable path. Keep these values under application-owner control.

Add bindings and a disclosure slot to the existing trusted content template. Escape/sanitize user-supplied HTML before rendering; the disclosure renderer is not a sanitizer. Pass only the rendered HTML into React, and include returned assets through the framework's stylesheet pipeline. Reuse your existing design and verify its final CSS/CSP and accessible presentation. The example rejects player assets because it implements article/image HTML, not an audio/video player integration.

The fixture covers a static article route. Other routes, CMS authentication/webhooks, live content, ISR, personalized responses, media exports and editorial workflows need their own integration. Development preparation runs at startup; restart after content changes. The example does not certify complete inventory or legal compliance.

## Verification

With the repository's Playwright development dependency and Chromium installed:

```sh
npm run test:next
```

This runs the real production build, scans the exported files for the private fixture evidence/report fields, and checks mobile/desktop direct visits with JavaScript disabled, client navigation and browser history. A separate temporary project changes the article and verifies that the actual Next build fails while leaving a previous output file intact. It does not modify the checked-in article or deploy anything.

Framework behavior follows the official [Next.js static export documentation](https://nextjs.org/docs/app/guides/static-exports). Legal policy and remaining review questions are maintained in the shared skill references and the repository's legal review package.
