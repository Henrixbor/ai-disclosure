'use strict';
const assert = require('node:assert/strict');
const { createHash } = require('node:crypto');
const { mkdtemp, writeFile, rm } = require('node:fs/promises');
const { tmpdir } = require('node:os');
const { join } = require('node:path');
const { setTimeout: delay } = require('node:timers/promises');

module.exports = async function cacheChecks(docker, web, base) {
  const response = await fetch('https://downloads.wordpress.org/plugin/wp-super-cache.3.1.3.zip', { signal: AbortSignal.timeout(30000) });
  assert.equal(response.status, 200);
  const zip = Buffer.from(await response.arrayBuffer());
  assert.equal(createHash('sha256').update(zip).digest('hex'), 'e2773f2146be15c088d5fa4e6280d433b6c08c4d155257be5580b0d69dfcf270');
  const dir = await mkdtemp(join(tmpdir(), 'aid-cache-test-'));
  try {
    await writeFile(join(dir, 'cache.zip'), zip);
    await docker(['cp', join(dir, 'cache.zip'), web + ':/tmp/aid-cache.zip']);
  } finally { await rm(dir, { recursive: true, force: true }); }
  const php = code => docker(['exec', '-i', web, 'php'], '<?php require "/wordpress/wp-load.php"; wp_set_current_user(1); ' + code);
  await php(`$zip = new ZipArchive(); if ($zip->open('/tmp/aid-cache.zip') !== true) throw new Exception('Cache archive could not be opened');
    for ($i = 0; $i < $zip->numFiles; $i++) { $name = $zip->getNameIndex($i); if (!str_starts_with($name, 'wp-super-cache/') || str_contains($name, '..') || str_contains($name, '\\\\')) throw new Exception('Unexpected archive path'); }
    if (!$zip->extractTo(WP_PLUGIN_DIR)) throw new Exception('Cache extraction failed'); $zip->close();
    require_once ABSPATH . 'wp-admin/includes/plugin.php'; $activated = activate_plugin('wp-super-cache/wp-cache.php'); if (is_wp_error($activated)) throw new Exception($activated->get_error_message());
    wp_cache_enable(); wp_super_cache_enable(); wp_cache_setting('cache_rebuild_files', 0); wp_cache_setting('wpsc_served_header', true); wp_cache_setting('wp_cache_slash_check', 1);
    $GLOBALS['wp_rewrite']->set_permalink_structure('/%postname%/'); flush_rewrite_rules();`);
  await docker(['exec', web, 'chown', '-R', 'www-data:www-data', '/var/www/html/wp-content/cache', '/var/www/html/wp-content/wp-cache-config.php']);
  const fixture = JSON.parse(await php(`
    $id = wp_insert_post(['post_title' => 'Cache assessment fixture', 'post_name' => 'cache-assessment-fixture', 'post_content' => '<p>Fictional cache test article.</p>', 'post_status' => 'draft'], true);
    $revision = \\AiDisclosure\\WordPress\\revision(\\AiDisclosure\\WordPress\\snapshot(get_post($id)));
    $facts = ['origin' => 'ai_generated', 'applicable' => true, 'public_interest' => true, 'evidence' => 'CACHE_PRIVATE_FIXTURE', 'review' => ['revision' => $revision, 'substantive_human_review' => true, 'responsible_entity' => 'Fictional reviewer']];
    $request = new WP_REST_Request('POST', '/ai-disclosure/v1/posts/' . $id . '/assessment'); $request->set_header('content-type', 'application/json'); $request->set_body(wp_json_encode(['role' => 'publisher', 'facts' => $facts]));
    $record = rest_do_request($request); if ($record->get_status() !== 200) throw new Exception('Cache fixture assessment failed');
    wp_update_post(['ID' => $id, 'post_status' => 'publish']); echo wp_json_encode(['id' => $id, 'url' => get_permalink($id), 'record_id' => $record->get_data()['record_id']]);`));
  assert.equal(new URL(fixture.url).origin, new URL(base).origin);
  async function cacheHit(url = fixture.url) {
    let response, body;
    for (let attempt = 0; attempt < 30; attempt++) {
      response = await fetch(url);
      body = await response.text();
      if ((response.headers.get('x-wp-super-cache') || '').includes('Served')) return { response, body };
      await delay(250);
    }
    throw new Error('No confirmed cache hit: ' + JSON.stringify({ status: response.status, headers: Object.fromEntries(response.headers), tail: body.slice(-600) }));
  }
  const hit = await cacheHit();
  const cached = hit.response;
  const cachedBody = hit.body;
  assert.equal(cached.status, 200);
  assert.match(cached.headers.get('x-wp-super-cache') || '', /Served/);
  assert.ok(!cachedBody.includes('data-ai-disclosure="wp-' + fixture.id + '"'));
  assert.ok(!cachedBody.includes('CACHE_PRIVATE_FIXTURE'));
  await php(`$request = new WP_REST_Request('POST', '/ai-disclosure/v1/posts/${fixture.id}/assessment'); $request->set_header('content-type', 'application/json');
    $request->set_body(wp_json_encode(['role' => 'publisher', 'facts' => ['origin' => 'ai_generated', 'applicable' => true, 'public_interest' => true, 'evidence' => 'CACHE_PRIVATE_FIXTURE'], 'replaces' => '${fixture.record_id}', 'amendment_reason' => 'Withdraw fixture review exemption']));
    $result = rest_do_request($request); if ($result->get_status() !== 200) throw new Exception('Cache fixture amendment failed');`);
  const updated = await fetch(fixture.url);
  const updatedBody = await updated.text();
  assert.ok(updatedBody.includes('data-ai-disclosure="wp-' + fixture.id + '"'));
  assert.ok(!updatedBody.includes('CACHE_PRIVATE_FIXTURE'));
  const recached = await cacheHit();
  assert.ok(recached.body.includes('AI-generated'));
  await php(`$current = rest_do_request(new WP_REST_Request('GET', '/ai-disclosure/v1/posts/${fixture.id}/assessment'))->get_data();
    wp_update_post(['ID' => ${fixture.id}, 'post_status' => 'draft']);
    $request = new WP_REST_Request('POST', '/ai-disclosure/v1/posts/${fixture.id}/withdrawal'); $request->set_header('content-type', 'application/json');
    $request->set_body(wp_json_encode(['revision' => $current['revision'], 'replaces' => $current['assessment']['record_id'], 'reason' => 'Withdraw cached fixture']));
    if (rest_do_request($request)->get_status() !== 200) throw new Exception('Cached fixture withdrawal failed');`);
  const withdrawn = await fetch(fixture.url);
  assert.equal(withdrawn.status, 404);
  assert.ok(!(await withdrawn.text()).includes('Fictional cache test article.'));
  const legacy = JSON.parse(await php(`$id = wp_insert_post(['post_title' => 'Legacy cache fixture', 'post_name' => 'legacy-cache-fixture', 'post_content' => '<p>Fictional legacy cache text.</p>', 'post_status' => 'draft'], true);
    global $wpdb; $wpdb->query($wpdb->prepare("UPDATE {$wpdb->posts} SET post_status = %s WHERE ID = %d", 'publish', $id)); clean_post_cache($id);
    echo wp_json_encode(['id' => $id, 'url' => get_permalink($id)]);`));
  assert.equal(new URL(legacy.url).origin, new URL(base).origin);
  const legacyHit = await cacheHit(legacy.url);
  assert.ok(!legacyHit.body.includes('data-ai-disclosure="wp-' + legacy.id + '"'));
  await php(`$request = new WP_REST_Request('POST', '/ai-disclosure/v1/posts/${legacy.id}/assessment'); $request->set_header('content-type', 'application/json');
    $request->set_body(wp_json_encode(['role' => 'publisher', 'facts' => ['origin' => 'ai_generated', 'applicable' => true, 'public_interest' => true, 'evidence' => 'CACHE_PRIVATE_FIXTURE_LEGACY']]));
    if (rest_do_request($request)->get_status() !== 200) throw new Exception('Legacy cache assessment failed');`);
  const migrated = await (await fetch(legacy.url)).text();
  assert.ok(migrated.includes('data-ai-disclosure="wp-' + legacy.id + '"'));
  assert.ok(!migrated.includes('CACHE_PRIVATE_FIXTURE_LEGACY'));
  console.log('WP Super Cache 3.1.3: real cache hits, amendment/withdrawal/legacy-record purges and private evidence checks passed');
};
