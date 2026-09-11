# Interactive showcase

The website combines installation instructions with a disclosure field guide. Text and image explanations, local scripted chat, synthetic audio, an animated image, a portable HTML document and recorded/stale publishing outcomes are demonstrable. The coverage table identifies formats without shipped adapters.

`python3 scripts/build_web.py --output /fresh/output/path` builds from `web`. The output directory must not already exist. The build uses the real renderer for the page notice, hero article, two publishing outcomes and article/image HTML export. Other field-guide labels are authored presentation examples. The browser fetches precomputed publishing outcomes; it does not enforce a server publishing transaction. The chat uses local fixed replies and no model service.

## Asset provenance

- `web/assets/pavilion.png`: original imagegen output, generated 11 September 2026 without reference images. Fictional coastal limestone pavilion, sea and olive tree; no real location claimed. SHA-256 `19b71e4e6caa6a6dc66f63ccc926c892c5e005b7dc267f2d28df2c62a89d918d`.
- `web/assets/narration.mp3`: macOS Samantha synthetic voice reading the visible transcript, including the opening synthetic-voice notice; converted to MP3 with ffmpeg. No real person's cloned voice.
- `web/assets/pavilion.mp4`: eight-second zoom of the generated still, made with ffmpeg; an HTML-rendered disclosure strip is embedded in every frame. This is a prepared demonstration, not a newly shipped media watermarking feature.
- `web/assets/video.vtt`: caption identifying the silent fictional scene.

The fictional image is voluntarily labeled. The build does not assert it meets the deepfake test. Text is conservatively disclosed based on known AI authorship. No reviewer approval, general content detection or universal compliance is claimed.

## Verification on 11 September 2026

Chromium at 390px and 1440px: static/no-JavaScript notices; installation navigation; no page overflow; expanded image notice and Escape dismissal; local chat and reset; successful recorded update and held stale update preserving the publication; site statement dialog; progressing audio/video playback; embedded-image HTML export; no page errors. Video and audio durations independently read as 8.000 and 16.531 seconds. Desktop image example visually inspected. This does not certify physical mobile devices, assistive technology, all browsers or legal sufficiency.
