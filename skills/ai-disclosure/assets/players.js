/* AI Disclosure local media controls. No network calls except user-requested media. */
(() => {
  'use strict';
  if (window.AIDisclosurePlayers) return;
  const instances = new WeakMap();
  const selector = '[data-aid-player]';
  const each = (node, fn) => {
    if (node.nodeType !== 1 && node.nodeType !== 9) return;
    if (node.matches?.(selector)) fn(node);
    node.querySelectorAll(selector).forEach(fn);
  };
  function mount(root) {
    if (instances.has(root)) return;
    const player = root.querySelector('[data-aid-content]');
    const notice = root.querySelector('[data-aid-notice]');
    const play = root.querySelector('[data-aid-play]');
    const seek = root.querySelector('[data-aid-seek]');
    const status = root.querySelector('[data-aid-status]');
    const mute = root.querySelector('[data-aid-mute]');
    const fullscreen = root.querySelector('[data-aid-fullscreen]');
    if (!player || !notice || !play || !seek || !status || !mute) return;
    const abort = new AbortController();
    const on = (element, event, handler) => element.addEventListener(event, handler, { signal: abort.signal });
    let announced = !root.dataset.notice, invalid = false, noticeFailed = false;
    const source = root.dataset.source;
    const noticeSource = root.dataset.notice;
    function localURL(value) {
      const url = new URL(value, location.href);
      if (!value || url.origin !== location.origin || !['http:', 'https:'].includes(url.protocol)) throw Error('Invalid media URL');
      return url.href;
    }
    function message(text) { status.textContent = text; }
    function dispose() {
      invalid = true;
      abort.abort();
      player.pause(); notice.pause();
      player.removeAttribute('src'); notice.removeAttribute('src');
      player.load(); notice.load();
      play.disabled = true; seek.disabled = true; mute.disabled = true;
      instances.delete(root);
    }
    function invalidate() {
      dispose();
      // Keep a tombstone: only a fresh, server-rendered player can be remounted.
      instances.set(root, { dispose, invalidate: () => {} });
      root.dataset.state = 'invalid';
      message('Content configuration changed. Reload the updated player.');
    }
    instances.set(root, { dispose, invalidate });
    try { localURL(source); if (noticeSource) localURL(noticeSource); }
    catch { invalidate(); return; }
    root.dataset.state = 'ready';
    play.disabled = false;
    function update() {
      const active = announced ? player : notice;
      play.textContent = active.paused ? (announced ? 'Play' : 'Play disclosure') : (announced ? 'Pause' : 'Pause disclosure');
      const duration = player.duration;
      seek.disabled = !announced || !Number.isFinite(duration) || duration <= 0;
      mute.disabled = !announced;
      if (!seek.disabled) {
        seek.value = String(player.currentTime / duration * 100);
        seek.setAttribute('aria-valuetext', `${Math.floor(player.currentTime)} of ${Math.floor(duration)} seconds`);
      }
    }
    async function startContent() {
      if (invalid) return;
      if (!player.hasAttribute('src')) player.src = localURL(source);
      root.dataset.state = 'content';
      message('');
      try { await player.play(); }
      catch { if (!invalid) message('Playback could not start. Press Play to try again.'); }
      update();
    }
    on(play, 'click', async () => {
      if (invalid) return;
      const active = announced ? player : notice;
      if (!active.paused) { active.pause(); update(); return; }
      if (announced) { await startContent(); return; }
      root.dataset.state = 'disclosure';
      message('Playing the AI disclosure before the recording.');
      if (!notice.hasAttribute('src') || noticeFailed) {
        noticeFailed = false;
        notice.src = localURL(noticeSource);
        notice.load();
      }
      try { await notice.play(); }
      catch { if (!invalid) { noticeFailed = true; message('The disclosure could not play. Retry to listen.'); } }
      update();
    });
    on(notice, 'ended', async () => {
      if (invalid || noticeFailed) return;
      announced = true;
      await startContent();
    });
    on(notice, 'error', () => { noticeFailed = true; root.dataset.state = 'error'; message('The disclosure could not load. Retry to listen.'); update(); });
    on(player, 'error', () => { root.dataset.state = 'error'; message('The recording could not load. Please try again later.'); update(); });
    for (const media of [player, notice]) for (const event of ['play', 'pause', 'ended', 'loadedmetadata', 'timeupdate']) on(media, event, update);
    on(seek, 'input', () => {
      if (!seek.disabled && Number.isFinite(player.duration)) player.currentTime = Number(seek.value) / 100 * player.duration;
    });
    on(mute, 'click', () => { player.muted = !player.muted; mute.textContent = player.muted ? 'Unmute' : 'Mute'; mute.setAttribute('aria-pressed', String(player.muted)); });
    if (fullscreen) {
      const frame = root.closest('.aid-media');
      if (frame?.requestFullscreen && document.fullscreenEnabled) {
        fullscreen.hidden = false;
        on(fullscreen, 'click', async () => {
          try { if (document.fullscreenElement) await document.exitFullscreen(); else await frame.requestFullscreen(); }
          catch { message('Fullscreen is unavailable in this browser.'); }
        });
        on(document, 'fullscreenchange', () => { fullscreen.textContent = document.fullscreenElement === frame ? 'Exit fullscreen' : 'Fullscreen'; });
      }
    }
    update();
  }
  const initialise = node => each(node, mount);
  const observer = new MutationObserver(records => {
    for (const record of records) {
      if (record.type === 'attributes') { instances.get(record.target)?.invalidate(); continue; }
      record.removedNodes.forEach(node => each(node, root => { if (!root.isConnected) instances.get(root)?.dispose(); }));
      record.addedNodes.forEach(node => { if (node.isConnected) initialise(node); });
    }
  });
  initialise(document);
  observer.observe(document.documentElement, { childList: true, subtree: true, attributes: true,
    attributeFilter: ['data-source', 'data-notice', 'data-aid-player'] });
  window.AIDisclosurePlayers = Object.freeze({ mount: initialise });
})();
