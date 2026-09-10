'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { mkdtemp, mkdir, rm, writeFile, readdir } = require('node:fs/promises');
const { tmpdir } = require('node:os');
const { join } = require('node:path');
const client = require(process.env.AI_DISCLOSURE_MODULE ?? '../skills/ai-disclosure/scripts/node.cjs');
const html = '<article data-ai-content="article"><h1>Town news — café</h1><!-- ai-disclosure --><p>A new park.</p></article>';

async function fixture(t) {
  const base = await mkdtemp(join(tmpdir(), 'ai-disclosure-node-'));
  t.after(() => rm(base, { recursive: true, force: true }));
  const root = join(base, 'assets with spaces');
  await mkdir(root);
  const inventory = await client.inspectFragment({ root, html });
  assert.deepEqual(inventory.gaps, []);
  const manifest = { version: 1, role: 'publisher', items: [{
    id: 'article', revision: inventory.records[0].revision, kind: 'text', origin: 'ai_generated',
    applicable: true, public_interest: true, evidence: 'Explicit fictional test declaration',
  }] };
  return { root, manifest };
}

test('Node publishing renders one notice and keeps evidence private without files', async t => {
  const { root, manifest } = await fixture(t);
  const before = JSON.stringify(manifest);
  const result = await client.renderFragment({ root, html, manifest });
  assert.equal((result.html.match(/class="aid-notice"/g) ?? []).length, 1);
  assert.ok(result.html.includes('Town news — café'));
  assert.ok(!result.html.includes('Explicit fictional test declaration'));
  assert.ok(result.assets['ai-disclosure.css']);
  assert.equal(result.report.implementation_verified, false);
  assert.equal(JSON.stringify(manifest), before);
  assert.deepEqual(await readdir(root), []);
});

test('changed content and unknown facts cannot replace the published version', async t => {
  const { root, manifest } = await fixture(t);
  let published = (await client.renderFragment({ root, html, manifest })).html;
  const oldVersion = published;
  const stale = await client.renderFragment({ root, html: html.replace('A new park.', 'Another claim.'), manifest });
  assert.equal(stale.html, null);
  assert.deepEqual(stale.assets, {});
  if (stale.html !== null) published = stale.html;
  assert.equal(published, oldVersion);
  manifest.items[0].origin = 'unknown';
  assert.equal((await client.renderFragment({ root, html, manifest })).html, null);
});

test('declared current review suppresses the notice but cannot cover an edit', async t => {
  const { root, manifest } = await fixture(t);
  manifest.items[0].review = { revision: manifest.items[0].revision,
    substantive_human_review: true, responsible_entity: 'Fixture publisher' };
  const result = await client.renderFragment({ root, html, manifest });
  assert.ok(result.html);
  assert.ok(!result.html.includes('class="aid-notice"'));
  assert.equal((await client.renderFragment({ root, html: html.replace('park', 'library'), manifest })).html, null);
});

test('export preserves disclosure and escapes the title', async t => {
  const { root, manifest } = await fixture(t);
  const result = await client.exportDocument({ root, html, manifest, title: '<News>', language: 'en' });
  assert.ok(result.html.includes('&lt;News&gt;'));
  assert.ok(result.html.includes('AI-generated'));
  assert.ok(result.html.includes('Content-Security-Policy'));
});

test('local image byte replacement invalidates its recorded revision', async t => {
  const { root } = await fixture(t);
  const source = '<figure class="aid-media" data-ai-content="image"><!-- ai-disclosure --><img src="image.svg" alt="Fixture"></figure>';
  await writeFile(join(root, 'image.svg'), '<svg xmlns="http://www.w3.org/2000/svg"></svg>');
  const inspected = await client.inspectFragment({ root, html: source });
  const manifest = { version: 1, role: 'publisher', items: [{ id: 'image',
    revision: inspected.records[0].revision, kind: 'image', origin: 'ai_generated',
    applicable: true, deepfake: true, evidence: 'Explicit fixture declaration' }] };
  assert.ok((await client.renderFragment({ root, html: source, manifest })).html);
  await writeFile(join(root, 'image.svg'), '<svg xmlns="http://www.w3.org/2000/svg"><title>Changed</title></svg>');
  assert.equal((await client.renderFragment({ root, html: source, manifest })).html, null);
});

test('invalid requests and unavailable Python reject instead of returning HTML', async t => {
  const { root, manifest } = await fixture(t);
  await assert.rejects(client.renderFragment({ root, html, manifest: {} }), /operation failed/);
  await assert.rejects(client.renderFragment({ root, html, manifest, command: 'inspect' }), /without a command/);
  await assert.rejects(client.renderFragment({ root: 'relative', html, manifest }), /operation failed/);
  await assert.rejects(client.renderFragment({ root, html, manifest }, { timeoutMs: 0 }), /timeoutMs/);
  await assert.rejects(client.renderFragment({ root, html, manifest }, { python: join(root, 'missing-python') }), /operation failed/);
  await assert.rejects(client.inspectFragment({ root, html, page: '../escape.html' }), /operation failed/);
});
