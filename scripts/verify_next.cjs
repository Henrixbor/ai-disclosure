'use strict';
const assert = require('node:assert/strict');
const { execFile } = require('node:child_process');
const { promisify } = require('node:util');
const { createServer } = require('node:http');
const { readFile, writeFile, readdir, stat, cp, symlink, mkdtemp, mkdir, rm } = require('node:fs/promises');
const { resolve, join, extname, sep } = require('node:path');
const { tmpdir } = require('node:os');
const { chromium } = require('playwright');
const execute = promisify(execFile);
const project = resolve(__dirname, '../examples/nextjs');
const output = join(project, 'out');
const next = join(project, 'node_modules/next/dist/bin/next');
const env = { ...process.env, NEXT_TELEMETRY_DISABLED: '1',
  AI_DISCLOSURE_MODULE: resolve(__dirname, '../skills/ai-disclosure/scripts/node.cjs') };

async function checkPrivateFiles(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) await checkPrivateFiles(path);
    else {
      const bytes = await readFile(path);
      assert.ok(!bytes.includes(Buffer.from('NEXTJS_FIXTURE_ORIGIN_RECORD')), 'Private origin evidence leaked');
      assert.ok(!bytes.includes(Buffer.from('implementation_verified')), 'Private report leaked');
      assert.ok(!['facts.json', 'article.json', 'bridge.py', 'node.cjs'].includes(entry.name), 'Private source leaked');
    }
  }
}

async function checkFailedBuild() {
  const temporary = await mkdtemp(join(tmpdir(), 'ai-disclosure-next-'));
  try {
    for (const name of ['app', 'content', 'public', 'scripts', 'next.config.js', 'package.json']) {
      await cp(join(project, name), join(temporary, name), { recursive: true });
    }
    await symlink(join(project, 'node_modules'), join(temporary, 'node_modules'), 'dir');
    await mkdir(join(temporary, 'out'));
    await writeFile(join(temporary, 'out/previous.html'), 'Previously published version');
    const content = join(temporary, 'content/article.html');
    await writeFile(content, (await readFile(content, 'utf8')).replace('reading room', 'unrecorded stadium'));
    let failure;
    try { await execute(process.execPath, [next, 'build', '--webpack'], { cwd: temporary, env, timeout: 60000 }); }
    catch (error) { failure = error; }
    assert.ok(failure && failure.code !== 0, 'Stale content must fail the actual Next build');
    assert.match(failure.stderr + failure.stdout, /Disclosure review required/);
    assert.equal(await readFile(join(temporary, 'out/previous.html'), 'utf8'), 'Previously published version');
    assert.deepEqual(await readdir(join(temporary, 'out')), ['previous.html']);
    console.log('Actual Next build rejected stale content and retained previous output');
  } finally { await rm(temporary, { recursive: true, force: true }); }
}

async function checkNotice(page) {
  assert.equal(await page.locator('[data-ai-disclosure]').count(), 1);
  assert.equal(await page.locator('[data-ai-disclosure]').innerText(), 'AI-generated');
  const visual = await page.evaluate(() => {
    const notice = document.querySelector('[data-ai-disclosure]');
    const box = notice.getBoundingClientRect();
    const style = getComputedStyle(notice);
    return { width: box.width, height: box.height, top: box.top, bottom: box.bottom,
      paragraph: document.querySelector('article p').getBoundingClientRect().top,
      visibility: style.visibility, opacity: style.opacity, background: style.backgroundColor,
      viewport: innerWidth, scroll: document.documentElement.scrollWidth };
  });
  assert.ok(visual.width > 30 && visual.height > 10);
  assert.equal(visual.visibility, 'visible');
  assert.equal(visual.opacity, '1');
  assert.equal(visual.background, 'rgb(242, 250, 246)');
  assert.ok(visual.bottom <= visual.paragraph && visual.top >= 0);
  assert.ok(visual.scroll <= visual.viewport);
}

async function main() {
  await execute(process.execPath, [next, 'build', '--webpack'], { cwd: project, env, timeout: 180000, maxBuffer: 4 * 1024 * 1024 });
  await checkPrivateFiles(output);
  await checkFailedBuild();
  const types = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.txt': 'text/plain', '.ico': 'image/x-icon' };
  const server = createServer(async (request, response) => {
    try {
      let path = resolve(output, '.' + decodeURIComponent(new URL(request.url, 'http://localhost').pathname));
      if (path !== output && !path.startsWith(output + sep)) throw new Error('Invalid path');
      if ((await stat(path)).isDirectory()) path = join(path, 'index.html');
      response.setHeader('Content-Type', types[extname(path)] ?? 'application/octet-stream');
      response.end(await readFile(path));
    } catch { response.statusCode = 404; response.end('Not found'); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const base = 'http://127.0.0.1:' + server.address().port;
  let browser;
  try {
    browser = await chromium.launch();
    for (const width of [390, 1440]) {
      const context = await browser.newContext({ viewport: { width, height: 1000 }, javaScriptEnabled: false });
      const page = await context.newPage();
      assert.equal((await page.goto(base + '/news/')).status(), 200);
      await checkNotice(page);
      await context.close();
    }
    const context = await browser.newContext();
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(String(error)));
    await page.goto(base + '/');
    await page.evaluate(() => { window.navigationSentinel = 'retained'; });
    await page.getByRole('link', { name: 'Read the example article' }).click();
    await page.waitForURL(base + '/news/');
    await checkNotice(page);
    assert.equal(await page.evaluate(() => window.navigationSentinel), 'retained', 'Expected actual client navigation');
    await page.goBack();
    await page.waitForURL(base + '/');
    await page.goForward();
    await page.waitForURL(base + '/news/');
    await checkNotice(page);
    assert.deepEqual(errors, []);
    await context.close();
    console.log('Next export: direct mobile/desktop visits without JS, client navigation, back/forward and private-output checks passed');
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
