'use strict';
const { runCLI } = require('@wp-playground/cli');
const { readFile } = require('node:fs/promises');
const { resolve } = require('node:path');
const assert = require('node:assert/strict');
const { engine, browserType } = require('./browser_engine.cjs');
const { randomBytes, createHash } = require('node:crypto');
const wordpressPackage = require('./wordpress_package.cjs');
const login = require('./wordpress_login.cjs');

async function editorChecks(browser, base, result, password) {
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.addInitScript(() => {
    window.__aidPointerSignals = [];
    for (const type of ['pointerdown', 'pointerup', 'click']) document.addEventListener(type, event => {
      const target = event.target instanceof Element ? event.target : null;
      const control = target?.closest('[data-aid-load], [data-aid-save], [data-aid-withdraw]');
      window.__aidPointerSignals.push({ type, tag: target?.tagName, id: target?.id,
        control: control?.hasAttribute('data-aid-load') ? 'load' : control?.hasAttribute('data-aid-save') ? 'save' : control ? 'withdraw' : null,
        trusted: event.isTrusted });
      if (window.__aidPointerSignals.length > 12) window.__aidPointerSignals.shift();
    }, true);
  });
  const inspections = [];
  page.on('response', response => {
    if (new URL(response.url()).pathname.endsWith('/inspection')) inspections.push(response.status());
  });
  const editorHash = createHash('sha256').update(await readFile(resolve(__dirname, '../integrations/wordpress/editor.js'))).digest('hex');
  const submitted = [];
  page.on('request', request => {
    if (request.method() === 'POST' && request.url().includes('/assessment')) submitted.push(request.postDataJSON());
  });
  page.setDefaultTimeout(10000);
  // Cold admin requests through the single-worker WASM server can exceed the
  // control timeout on CI. Keep navigation bounded independently of UI actions.
  page.setDefaultNavigationTimeout(60000);
  // Preferences hydrate asynchronously: the welcome guide may reopen and
  // the Meta Boxes area may collapse. Use native controls before each action.
  async function ensureEditor() {
    const guide = page.getByRole('dialog').filter({ hasText: 'Welcome to the editor' });
    if (await guide.isVisible()) {
      await guide.getByRole('button', { name: 'Close', exact: true }).click();
      await guide.waitFor({ state: 'hidden' });
    }
    const toggle = page.getByRole('button', { name: 'Meta Boxes', exact: true });
    if (await toggle.count() && await toggle.getAttribute('aria-expanded') === 'false') await toggle.press('Enter');
  }
  await page.addLocatorHandler(page.locator('body'), ensureEditor, { noWaitAfter: true });
  try {
    await login(page, base, password);
    for (const [mode, id] of [['classic', result.classic_id], ['block', result.block_id]]) {
      await page.goto(new URL('/wp-admin/post.php?post=' + id + '&action=edit', base).href);
      const script = await page.locator('#ai-disclosure-editor-js').getAttribute('src');
      assert.equal(new URL(script, base).searchParams.get('ver'), editorHash, 'Editor cache version follows the installed script bytes');
      if (mode === 'classic') {
        const textMode = page.locator('#content-html');
        if (await textMode.count()) await textMode.click();
      }
      const panel = page.locator('.aid-editor');
      await panel.locator('[data-aid-load]').click();
      await page.waitForFunction(() => document.querySelector('[data-aid-fields]')?.disabled === false);
      if (mode === 'classic') await page.locator('#title').fill('Changed classic editor fixture');
      else {
        await page.evaluate(() => wp.data.dispatch('core/editor').editPost({ title: 'Changed block editor fixture' }));
        // Reproduce the native collapse observed after preference hydration.
        await page.getByRole('button', { name: 'Meta Boxes', exact: true }).press('Enter');
      }
      await panel.locator('[data-aid-save]').click();
      await page.waitForFunction(() => document.querySelector('[data-aid-status]').textContent.includes('text changed since loading'));
      await panel.locator('[data-aid-load]').click();
      await page.waitForFunction(() => document.querySelector('[data-aid-fields]')?.disabled === false);
      for (const [name, value] of Object.entries({ role: 'publisher', origin: 'ai_generated', applicable: 'true', public_interest: 'true' })) {
        await panel.locator(`[data-aid-field="${name}"]`).selectOption(value);
      }
      await panel.locator('[data-aid-field="evidence"]').fill('WORDPRESS_PRIVATE_EVIDENCE: explicit editor fixture declaration.');
      await panel.locator('[data-aid-save]').click();
      await page.waitForFunction(() => document.querySelector('[data-aid-status]').textContent.includes('Assessment recorded. This version requires'));
      await panel.locator('[data-aid-field="review"]').check();
      await panel.locator('[data-aid-field="responsible_entity"]').fill('Fictional review fixture');
      await panel.locator('[data-aid-field="amendment_reason"]').fill('Record the explicit review assumption for this UI test.');
      await panel.locator('[data-aid-save]').click();
      await page.waitForFunction(() => document.querySelector('[data-aid-status]').textContent.includes('No extra text notice'));
      assert.ok(!(await page.locator('[data-aid-status]').innerText()).includes('compliant'));
      // Save the assessed text as a draft, withdraw through the panel, then restore explicitly.
      if (mode === 'classic') {
        await Promise.all([page.waitForNavigation({ waitUntil: 'load' }), page.locator('#save-post').click()]);
      } else {
        await page.evaluate(() => wp.data.dispatch('core/editor').savePost());
      }
      await panel.locator('[data-aid-load]').click();
      await page.waitForFunction(() => !document.querySelector('[data-aid-fields]').disabled);
      await panel.locator('[data-aid-field="amendment_reason"]').fill('Withdraw fixture evidence for the editor test.');
      await panel.locator('[data-aid-withdraw]').click();
      await page.waitForFunction(() => document.querySelector('[data-aid-status]').textContent.includes('Assessment withdrawn.'));
      assert.ok(!(await panel.locator('[data-aid-field="review"]').isChecked()), 'Withdrawn review must not be silently reselected');
      await panel.locator('[data-aid-field="review"]').check();
      await panel.locator('[data-aid-field="responsible_entity"]').fill('Fictional review fixture');
      await panel.locator('[data-aid-field="amendment_reason"]').fill('Re-establish the fixture facts after withdrawal.');
      await panel.locator('[data-aid-save]').click();
      await page.waitForFunction(() => document.querySelector('[data-aid-status]').textContent.includes('No extra text notice'));
      // Publish through the actual editor after recording, not a direct API shortcut.
      if (mode === 'classic') {
        await Promise.all([page.waitForNavigation({ waitUntil: 'load' }), page.locator('#publish').click()]);
        await page.locator('#message').waitFor();
      } else {
        await page.getByRole('button', { name: 'Publish', exact: true }).click();
        await page.getByLabel('Editor publish', { exact: true }).getByRole('button', { name: 'Publish', exact: true }).click();
        await page.waitForFunction(() => wp.data.select('core/editor').getCurrentPost()?.status === 'publish');
      }
      const published = await (await fetch(new URL('/?rest_route=/wp/v2/posts/' + id, base))).json();
      assert.equal(published.status, 'publish', 'Editor publication must succeed with the assessed text');
      assert.ok(!published.content.rendered.includes('data-ai-disclosure='), 'Current declared review needs no extra label');
      console.log('Authenticated ' + mode + ' editor: stale text held, assessment recorded, review amended, withdrawn and restored, native publication passed');
    }
    assert.ok(submitted.length > 0, 'Editor must actually submit assessment requests');
    for (const body of submitted) {
      assert.match(body.expected_revision, /^sha256:[a-f0-9]{64}$/);
      const snapshot = { title: body.title, content: body.content, excerpt: body.excerpt };
      assert.equal(body.expected_revision, 'sha256:' + createHash('sha256').update(JSON.stringify(snapshot)).digest('hex'), 'Editor binds the exact submitted source');
    }
  } catch (error) {
    console.error('Editor inspection response statuses:', JSON.stringify(inspections));
    console.error(JSON.stringify(await page.evaluate(() => ({
      pointerSignals: window.__aidPointerSignals,
      loadDisabled: document.querySelector('[data-aid-load]')?.disabled,
      fieldsDisabled: document.querySelector('[data-aid-fields]')?.disabled,
      panels: [...document.querySelectorAll('.aid-editor')].map(el => {
        const parents = []; for (let node = el; node && parents.length < 7; node = node.parentElement) parents.push({ tag: node.tagName, id: node.id, class: node.className, display: getComputedStyle(node).display });
        return parents;
      }),
      buttons: [...document.querySelectorAll('button')].filter(el => el.getClientRects().length).map(el => el.getAttribute('aria-label') || el.textContent),
      dialogs: [...document.querySelectorAll('[role=dialog]')].map(el => el.textContent.slice(0, 1000)),
      status: [...document.querySelectorAll('[data-aid-status]')].map(el => el.textContent),
    })), null, 2));
    throw error;
  } finally { await context.close(); }
}

async function main() {
  const archive = await wordpressPackage();
  const code = await readFile(resolve(__dirname, '../tests/wordpress-integration.php'), 'utf8');
  const password = randomBytes(24).toString('hex');
  const server = await runCLI({ command: 'server', wp: '7.1', php: '8.3', port: 0, workers: 1, quiet: true,
    blueprint: { steps: [
      { step: 'installPlugin', pluginData: { resource: 'literal', name: 'ai-disclosure-wordpress.zip', contents: archive.bytes }, options: { activate: true, onError: 'throw' } },
      { step: 'runPHP', code },
      { step: 'runPHP', code: "<?php require '/wordpress/wp-load.php'; wp_set_password('" + password + "', 1);" },
    ] },
  });
  try { await siteChecks(server.serverUrl, password); }
  finally { await server[Symbol.asyncDispose](); }
}

async function siteChecks(base, password) {
  let browser;
  try {
    const result = await (await fetch(new URL('/aid-test-result.json', base))).json();
    assert.equal(result.checks, 'passed');
    const anonymous = await fetch(new URL('/?rest_route=/ai-disclosure/v1/posts/' + result.id + '/assessment', base));
    assert.ok(anonymous.status >= 400);
    assert.equal(anonymous.headers.get('cache-control'), 'private, no-store');
    const history = await fetch(new URL('/?rest_route=' + result.history_route, base));
    assert.ok(history.status >= 400);
    assert.equal(history.headers.get('cache-control'), 'private, no-store');
    const inventory = await fetch(new URL('/?rest_route=/ai-disclosure/v1/inventory', base));
    assert.ok(inventory.status >= 400);
    assert.equal(inventory.headers.get('cache-control'), 'private, no-store');
    browser = await browserType.launch();
    await editorChecks(browser, base, result, password);
    for (const width of [390, 1440]) {
      const context = await browser.newContext({ javaScriptEnabled: false, viewport: { width, height: 1000 } });
      const page = await context.newPage();
      await page.goto(new URL('/?p=' + result.id, base).href);
      const label = page.locator('[data-ai-disclosure="wp-' + result.id + '"]').first();
      assert.equal(await label.innerText(), 'AI-modified');
      assert.ok(await label.isVisible());
      assert.equal(await label.evaluate(el => getComputedStyle(el).backgroundColor), 'rgb(242, 250, 246)');
      assert.ok(!(await page.content()).includes('WORDPRESS_PRIVATE_EVIDENCE'));
      await context.close();
    }
    const feed = await (await fetch(new URL('/?feed=rss2', base))).text();
    assert.ok(feed.includes('AI-modified'));
    assert.ok(!feed.includes('WORDPRESS_PRIVATE_EVIDENCE'));
    console.log('WordPress 7.1 (' + engine + '): publishing, amendments, stale database writers, private history/inventory, no-JS notices and feed privacy passed');
  } finally {
    if (browser) await browser.close();
  }
}
module.exports = { siteChecks };
if (require.main === module) main().catch(error => { console.error(error.message); process.exitCode = 1; });
