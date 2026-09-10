/* WordPress editor integration. Private facts remain in the authenticated admin UI. */
wp.domReady(() => {
  const panel = document.querySelector('.aid-editor');
  const config = window.aiDisclosureEditor;
  if (!panel || !config) return;
  const field = name => panel.querySelector(`[data-aid-field="${name}"]`);
  const load = panel.querySelector('[data-aid-load]');
  const save = panel.querySelector('[data-aid-save]');
  const withdraw = panel.querySelector('[data-aid-withdraw]');
  const fields = panel.querySelector('[data-aid-fields]');
  const status = panel.querySelector('[data-aid-status]');
  let loaded = null;
  let busy = false;

  function message(text, error = false) { status.textContent = text; status.dataset.error = String(error); }
  function source() {
    const editor = wp.data.select('core/editor');
    if (editor?.getEditedPostAttribute && Number(editor.getCurrentPostId()) === Number(config.postId)) {
      return Object.fromEntries(['title', 'content', 'excerpt'].map(key => [key, String(editor.getEditedPostAttribute(key) ?? '')]));
    }
    const text = document.getElementById('content');
    if (!text) throw new Error('The editor is not ready. Try loading the text again.');
    const visual = window.tinymce?.get('content');
    return { title: document.getElementById('title')?.value ?? '',
      content: visual && !visual.isHidden() ? visual.getContent() : text.value,
      excerpt: document.getElementById('excerpt')?.value ?? '' };
  }
  async function request(path, body) {
    const response = await fetch(config.restRoot + path, { method: 'POST', credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-WP-Nonce': config.nonce }, body: JSON.stringify(body) });
    let result;
    try { result = await response.json(); }
    catch { throw new Error('Could not read the assessment response. Reload the editor before retrying.'); }
    if (!response.ok) throw new Error(result.message || 'The request failed. Reload the assessment before retrying.');
    return result;
  }
  function toggle() {
    panel.querySelector('[data-aid-responsibility]').hidden = !field('review').checked;
    panel.querySelector('[data-aid-amendment]').hidden = !loaded?.assessment;
    withdraw.hidden = !loaded?.assessment || loaded.assessment.decision === 'withdrawn';
  }
  function populate(info) {
    const facts = info.assessment?.facts ?? {};
    field('role').value = info.assessment ? 'publisher' : 'unknown';
    field('origin').value = facts.origin ?? 'unknown';
    for (const name of ['applicable', 'public_interest']) field(name).value = typeof facts[name] === 'boolean' ? String(facts[name]) : 'unknown';
    field('evidence').value = facts.evidence ?? '';
    field('review').checked = info.assessment?.decision !== 'withdrawn' && facts.review?.substantive_human_review === true && facts.review?.revision === info.revision;
    field('responsible_entity').value = field('review').checked ? facts.review.responsible_entity : '';
    field('amendment_reason').value = '';
    toggle();
  }
  function canonical(value) {
    if (value && typeof value === 'object' && !Array.isArray(value)) return Object.fromEntries(Object.keys(value).sort().map(key => [key, canonical(value[key])]));
    return value;
  }
  async function perform(action) {
    if (busy) return;
    busy = true; load.disabled = true; fields.disabled = true;
    try { await action(); } catch (error) { message(error.message, true); }
    finally { busy = false; load.disabled = false; fields.disabled = !loaded?.supported_text; }
  }
  load.addEventListener('click', () => perform(async () => {
    message('Loading current text…');
    loaded = null;
    const text = source();
    const info = await request('inspection', text);
    if (JSON.stringify(text) !== JSON.stringify(source())) throw new Error('The text changed while loading. Load the current text again.');
    loaded = { ...info, source: text };
    populate(info);
    message(info.supported_text ? (info.assessment ? (info.assessment.decision === 'withdrawn' ? 'This assessment was withdrawn. Establish facts again and provide a reason to restore it.' : 'Current assessment loaded. Changes require a reason.') : 'No assessment recorded for this text. Supply established facts below.')
      : 'This text contains markup or media the current adapter cannot cover. A separate integration is required.', !info.supported_text);
  }));
  withdraw.addEventListener('click', () => perform(async () => {
    if (!loaded?.assessment || JSON.stringify(source()) !== JSON.stringify(loaded.source)) throw new Error('Load the current saved text before withdrawing.');
    if (!field('amendment_reason').value.trim()) throw new Error('Give a reason for withdrawing this assessment.');
    const result = await request('withdrawal', { revision: loaded.revision, replaces: loaded.assessment.record_id, reason: field('amendment_reason').value });
    loaded.assessment = result;
    populate(loaded);
    message('Assessment withdrawn. This version cannot be republished until explicitly reassessed.');
  }));
  field('review').addEventListener('change', toggle);
  save.addEventListener('click', () => perform(async () => {
    if (!loaded?.supported_text) throw new Error('Load the current text first.');
    const text = source();
    if (JSON.stringify(text) !== JSON.stringify(loaded.source)) {
      loaded = null;
      throw new Error('The text changed since loading. Load it again before recording an assessment.');
    }
    message('Checking this version…');
    const latest = await request('inspection', text);
    if (latest.assessment?.record_id !== loaded.assessment?.record_id) {
      loaded = null;
      throw new Error('Another assessment was recorded. Load it before making changes.');
    }
    const facts = { origin: field('origin').value, evidence: field('evidence').value };
    for (const name of ['applicable', 'public_interest']) facts[name] = field(name).value === 'unknown' ? null : field(name).value === 'true';
    if (field('review').checked) facts.review = { revision: loaded.revision, substantive_human_review: true, responsible_entity: field('responsible_entity').value };
    const payload = { ...text, role: field('role').value, facts };
    if (loaded.assessment) {
      const prior = { ...loaded.assessment.facts };
      for (const name of ['id', 'kind', 'revision']) delete prior[name];
      if (loaded.assessment.decision === 'withdrawn' || JSON.stringify(canonical(prior)) !== JSON.stringify(canonical(facts))) {
        if (!field('amendment_reason').value.trim()) throw new Error('Give a reason for changing this assessment.');
        payload.replaces = loaded.assessment.record_id;
        payload.amendment_reason = field('amendment_reason').value;
      }
    }
    const result = await request('assessment', payload);
    if (JSON.stringify(text) !== JSON.stringify(source())) {
      loaded = null;
      throw new Error('The earlier text was assessed, but the editor has changed. Load the current text again.');
    }
    loaded.assessment = { record_id: result.record_id, decision: result.decision, facts };
    toggle();
    message(result.decision === 'disclose' ? 'Assessment recorded. This version requires a visible notice when published.' : 'Assessment recorded. No extra text notice is required by these declared facts.');
  }));
});
