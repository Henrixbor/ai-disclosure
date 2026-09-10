'use strict';
const assert = require('node:assert/strict');
const { engine, browserType } = require('./browser_engine.cjs');
const login = require('./wordpress_login.cjs');

module.exports = async function replacementChecks(docker, web, base, password, archive) {
  const php = code => docker(['exec', '-i', web, 'php'], '<?php require "/wordpress/wp-load.php"; wp_set_current_user(1); ' + code);
  const fixture = await (await fetch(new URL('/aid-test-result.json', base))).json();
  const state = async () => JSON.parse(await php(`
    global $wpdb; require_once ABSPATH . 'wp-admin/includes/plugin.php';
    $records = $wpdb->get_results($wpdb->prepare("SELECT option_name, option_value FROM {$wpdb->options} WHERE option_name LIKE %s ORDER BY option_name", $wpdb->esc_like('ai_disclosure_') . '%'), ARRAY_A);
    if ($wpdb->last_error) throw new Exception('Could not inspect assessment records');
    $files = []; foreach (glob(WP_PLUGIN_DIR . '/ai-disclosure/*') as $path) if (is_file($path)) $files[basename($path)] = hash_file('sha256', $path); ksort($files);
    $post = get_post(${fixture.id});
    echo wp_json_encode(['active' => is_plugin_active('ai-disclosure/ai-disclosure.php'), 'records' => count($records), 'record_hash' => hash('sha256', wp_json_encode($records)), 'files' => $files, 'status' => $post->post_status, 'revision' => \\AiDisclosure\\WordPress\\revision(\\AiDisclosure\\WordPress\\snapshot($post))]);`));
  const before = await state();
  assert.ok(before.active && before.records > 0);
  assert.equal(before.status, 'publish');
  // Initial CLI installation created root-owned files. Model a writable hosting
  // installation for the web upload; do not grant access outside the fixture.
  await docker(['exec', web, 'chown', '-R', 'www-data:www-data', '/var/www/html/wp-content/plugins/ai-disclosure']);
  const browser = await browserType.launch();
  const page = await browser.newPage();
  let stage = 'login';
  try {
    await login(page, base, password);
    async function upload(buffer) {
      await page.goto(new URL('/wp-admin/plugin-install.php?tab=upload', base).href);
      await page.locator('input[name="pluginzip"]').setInputFiles({ name: 'ai-disclosure-wordpress.zip', mimeType: 'application/zip', buffer });
      await Promise.all([page.waitForNavigation({ waitUntil: 'load' }), page.getByRole('button', { name: 'Install Now', exact: true }).click()]);
    }
    stage = 'invalid archive';
    await upload(Buffer.from('Invalid archive fixture'));
    assert.match(await page.locator('body').innerText(), /Incompatible Archive|incompatible archive/);
    assert.deepEqual(await state(), before, 'Rejected upload must preserve activation, source files and private records');
    stage = 'unwritable staging directory';
    await upload(archive.bytes);
    assert.match(await page.locator('body').innerText(), /Could not create directory/);
    assert.deepEqual(await state(), before, 'Staging failure must preserve the installed plugin and private records');
    await docker(['exec', web, 'chown', '-R', 'www-data:www-data', '/var/www/html/wp-content/upgrade']);
    await php(`file_put_contents(WP_PLUGIN_DIR . '/ai-disclosure/replacement-sentinel.txt', 'Fictional old installation file');`);
    await docker(['exec', web, 'chown', 'www-data:www-data', '/var/www/html/wp-content/plugins/ai-disclosure/replacement-sentinel.txt']);
    stage = 'replacement upload';
    await upload(archive.bytes);
    const replace = page.getByRole('link', { name: 'Replace current with uploaded', exact: true });
    await replace.waitFor();
    stage = 'replacement confirmation';
    await Promise.all([page.waitForNavigation({ waitUntil: 'load' }), replace.click()]);
    assert.match(await page.locator('body').innerText(), /Plugin updated successfully/);
    assert.deepEqual(await state(), before, 'Replacement must retain activation and records while installing the exact package files');
    const rejected = await php(`$request = new WP_REST_Request('POST', '/wp/v2/posts/${fixture.id}'); $request->set_header('content-type', 'application/json'); $request->set_body(wp_json_encode(['content' => '<p>Unassessed replacement test edit.</p>'])); echo rest_do_request($request)->get_status();`);
    assert.equal(rejected, '409', 'Installed replacement must still hold an unassessed publication update');
    assert.deepEqual(await state(), before, 'Held update must preserve the approved publication and records');
    const publicPage = await fetch(new URL('/?p=' + fixture.id, base));
    const html = await publicPage.text();
    assert.equal(publicPage.status, 200);
    assert.ok(html.includes('data-ai-disclosure="wp-' + fixture.id + '"'));
    assert.ok(html.includes('AI-modified'));
    assert.ok(!html.includes('WORDPRESS_PRIVATE_EVIDENCE'));
    console.log('WordPress admin upload (' + engine + '): invalid ZIP and unwritable staging rejected without changes; same-version replacement preserves activation, private records, publication gate and notice; old files removed');
  } catch (error) {
    if (stage !== 'login') console.error('Plugin replacement screen:', stage, new URL(page.url()).pathname, (await page.locator('body').innerText({ timeout: 2000 }).catch(() => 'unavailable')).slice(-2500));
    throw error;
  } finally { await browser.close(); }
};
