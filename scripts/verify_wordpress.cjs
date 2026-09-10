'use strict';
const { runCLI } = require('@wp-playground/cli');
const { readFile } = require('node:fs/promises');
const { resolve } = require('node:path');
const assert = require('node:assert/strict');
const { chromium } = require('playwright');

async function main() {
  const code = await readFile(resolve(__dirname, '../tests/wordpress-integration.php'), 'utf8');
  const server = await runCLI({ command: 'server', wp: '7.1', php: '8.3', port: 0, workers: 1, quiet: true,
    mount: [{ hostPath: resolve(__dirname, '../integrations/wordpress'), vfsPath: '/wordpress/wp-content/plugins/ai-disclosure' }],
    blueprint: { steps: [
      { step: 'activatePlugin', pluginPath: '/wordpress/wp-content/plugins/ai-disclosure/ai-disclosure.php' },
      { step: 'runPHP', code },
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
    browser = await chromium.launch();
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
    console.log('WordPress 7.1: real publishing checks, anonymous denial, mobile/desktop notices without JS and feed privacy passed');
  } finally {
    if (browser) await browser.close();
    await server[Symbol.asyncDispose]();
  }
}
main().catch(error => { console.error(error.message); process.exitCode = 1; });
