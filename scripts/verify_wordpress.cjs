'use strict';
const { runCLI } = require('@wp-playground/cli');
const { readFile } = require('node:fs/promises');
const { resolve } = require('node:path');
const assert = require('node:assert/strict');
const { chromium } = require('playwright');
const { randomBytes } = require('node:crypto');

async function editorChecks(browser, base, result, password) {
  const context = await browser.newContext();
  const page = await context.newPage();
  page.setDefaultTimeout(10000);
  try {
    await page.goto(new URL('/wp-login.php', base).href);
    await page.locator('#user_login').fill('admin');
    await page.locator('#user_pass').fill(password);
    await Promise.all([page.waitForURL('**/wp-admin/**'), page.locator('#wp-submit').click()]);
    for (const [mode, id] of [['classic', result.classic_id], ['block', result.block_id]]) {
      await page.goto(new URL('/wp-admin/post.php?post=' + id + '&action=edit', base).href);
      if (mode === 'block') {
        await page.getByRole('dialog').filter({ hasText: 'Welcome to the editor' }).getByRole('button', { name: 'Close', exact: true }).click();
      } else {
        const textMode = page.locator('#content-html');
        if (await textMode.count()) await textMode.click();
      }
      const panel = page.locator('.aid-editor');
      if (mode === 'block' && !await panel.isVisible()) {
        const toggle = page.getByRole('button', { name: 'Meta Boxes', exact: true });
        await toggle.focus();
        await toggle.press('Enter');
      }
      await panel.waitFor({ timeout: 10000 });
      await panel.locator('[data-aid-load]').click();
      await page.waitForFunction(() => document.querySelector('[data-aid-fields]')?.disabled === false);
      if (mode === 'classic') await page.locator('#title').fill('Changed classic editor fixture');
      else await page.evaluate(() => wp.data.dispatch('core/editor').editPost({ title: 'Changed block editor fixture' }));
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
      // Publish through the actual editor after recording, not a direct API shortcut.
      if (mode === 'classic') {
        await Promise.all([page.waitForURL('**/post.php?**'), page.locator('#publish').click()]);
        await page.locator('#message').waitFor();
      } else {
        await page.getByRole('button', { name: 'Publish', exact: true }).click();
        await page.getByLabel('Editor publish', { exact: true }).getByRole('button', { name: 'Publish', exact: true }).click();
        await page.waitForFunction(() => wp.data.select('core/editor').getCurrentPost()?.status === 'publish');
      }
      const published = await (await fetch(new URL('/?rest_route=/wp/v2/posts/' + id, base))).json();
      assert.equal(published.status, 'publish', 'Editor publication must succeed with the assessed text');
      assert.ok(!published.content.rendered.includes('data-ai-disclosure='), 'Current declared review needs no extra label');
      console.log('Authenticated ' + mode + ' editor: stale text held, assessment recorded, review amended, native publication passed');
    }
  } catch (error) {
    console.error(JSON.stringify(await page.evaluate(() => ({
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
  const code = await readFile(resolve(__dirname, '../tests/wordpress-integration.php'), 'utf8');
  const password = randomBytes(24).toString('hex');
  const server = await runCLI({ command: 'server', wp: '7.1', php: '8.3', port: 0, workers: 1, quiet: true,
    mount: [{ hostPath: resolve(__dirname, '../integrations/wordpress'), vfsPath: '/wordpress/wp-content/plugins/ai-disclosure' }],
    blueprint: { steps: [
      { step: 'activatePlugin', pluginPath: '/wordpress/wp-content/plugins/ai-disclosure/ai-disclosure.php' },
      { step: 'runPHP', code },
      { step: 'runPHP', code: "<?php require '/wordpress/wp-load.php'; wp_set_password('" + password + "', 1);" },
    ] },
  });
  let browser;
  try {
    const base = server.serverUrl;
    const result = await (await fetch(new URL('/aid-test-result.json', base))).json();
    assert.equal(result.checks, 'passed');
    const anonymous = await fetch(new URL('/?rest_route=/ai-disclosure/v1/posts/' + result.id + '/assessment', base));
    assert.ok(anonymous.status >= 400);
    assert.equal(anonymous.headers.get('cache-control'), 'private, no-store');
    const history = await fetch(new URL('/?rest_route=' + result.history_route, base));
    assert.ok(history.status >= 400);
    assert.equal(history.headers.get('cache-control'), 'private, no-store');
    browser = await chromium.launch();
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
    console.log('WordPress 7.1: publishing, amendments, stale database writers, private history, no-JS notices and feed privacy passed');
  } finally {
    if (browser) await browser.close();
    await server[Symbol.asyncDispose]();
  }
}
main().catch(error => { console.error(error.message); process.exitCode = 1; });
