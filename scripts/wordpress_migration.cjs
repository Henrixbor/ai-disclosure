'use strict';
const assert = require('node:assert/strict');
const { execFile } = require('node:child_process');
const { mkdtemp, writeFile, rm } = require('node:fs/promises');
const { tmpdir } = require('node:os');
const { join, resolve } = require('node:path');

module.exports = async function migrationChecks(docker, web, base) {
  const php = code => docker(['exec', '-i', web, 'php'], '<?php require "/wordpress/wp-load.php"; wp_set_current_user(1); ' + code);
  const fixture = JSON.parse(await php(`
    file_put_contents(WPMU_PLUGIN_DIR . '/aid-migration-fixture.php', '<?php add_filter("wp_is_application_passwords_available", "__return_true");');
    $GLOBALS['wp_rewrite']->set_permalink_structure('/%postname%/'); flush_rewrite_rules();
    $password = WP_Application_Passwords::create_new_application_password(1, ['name' => 'Disposable migration test']);
    if (is_wp_error($password)) throw new Exception('Could not create fixture application password');
    $items = []; global $wpdb;
    foreach (['ready', 'stale', 'unknown'] as $kind) {
      $id = wp_insert_post(['post_title' => 'Migration ' . $kind . ' fixture', 'post_content' => '<p>Fictional migration content.</p>', 'post_status' => 'draft'], true);
      $revision = \\AiDisclosure\\WordPress\\revision(\\AiDisclosure\\WordPress\\snapshot(get_post($id)));
      if ($kind === 'ready') { $wpdb->query($wpdb->prepare("UPDATE {$wpdb->posts} SET post_status = %s WHERE ID = %d", 'publish', $id)); clean_post_cache($id); }
      if ($kind === 'stale') wp_update_post(['ID' => $id, 'post_title' => 'Changed since migration inventory']);
      $items[] = ['id' => $id, 'revision' => $revision, 'facts' => ['origin' => $kind === 'unknown' ? 'unknown' : 'ai_generated', 'applicable' => true, 'public_interest' => true, 'evidence' => 'PRIVATE_BATCH_FIXTURE']];
    }
    echo wp_json_encode(['password' => $password[0], 'uuid' => $password[1]['uuid'], 'items' => $items]);`));
  const dir = await mkdtemp(join(tmpdir(), 'aid-migration-test-'));
  const batch = join(dir, 'batch.json');
  async function run(apply) {
    const args = [resolve(__dirname, 'wordpress_migrate.py'), batch, '--api-url', base + '/wp-json', '--allow-loopback-http'];
    if (apply) args.push('--apply');
    return new Promise((accept, reject) => {
      execFile('python3', args, { timeout: 90000, maxBuffer: 1024 * 1024,
        env: { ...process.env, AI_DISCLOSURE_WP_USER: 'admin', AI_DISCLOSURE_WP_PASSWORD: fixture.password } }, (error, stdout, stderr) => {
        if (error && error.code !== 1) return reject(new Error('Migration CLI failed; exit ' + String(error.code)));
        try {
          assert.ok(!stdout.includes(fixture.password) && !stderr.includes(fixture.password));
          assert.ok(!stdout.includes('PRIVATE_BATCH_FIXTURE') && !stderr.includes('PRIVATE_BATCH_FIXTURE'));
          accept({ report: JSON.parse(stdout), exit: error ? 1 : 0 });
        } catch { reject(new Error('Invalid or non-private migration report')); }
      });
    });
  }
  try {
    await writeFile(batch, JSON.stringify({ version: 1, role: 'publisher', items: fixture.items }), { mode: 0o600 });
    const plan = await run(false);
    assert.equal(plan.exit, 1);
    assert.deepEqual(plan.report.results.map(r => r.status), ['ready_to_submit', 'revision_conflict', 'needs_review']);
    const missing = await php(`foreach (${JSON.stringify(fixture.items.map(i => i.id))} as $id) { $r = \\AiDisclosure\\WordPress\\record_for($id, \\AiDisclosure\\WordPress\\snapshot(get_post($id))); if ($r !== null) throw new Exception('Plan wrote an assessment'); } echo 'unchanged';`);
    assert.equal(missing, 'unchanged');
    const applied = await run(true);
    assert.deepEqual(applied.report.results.map(r => r.status), ['recorded', 'revision_conflict', 'needs_review']);
    const retry = await run(true);
    assert.deepEqual(retry.report.results.map(r => r.status), ['already_recorded', 'revision_conflict', 'needs_review']);
    assert.equal(retry.report.results[0].record_id, applied.report.results[0].record_id);
    const html = await (await fetch(new URL('/?p=' + fixture.items[0].id, base))).text();
    assert.ok(html.includes('data-ai-disclosure="wp-' + fixture.items[0].id + '"'));
    assert.ok(!html.includes('PRIVATE_BATCH_FIXTURE'));
    console.log('WordPress migration CLI: real application-password auth; plan writes nothing; explicit apply labels legacy content; stale/unknown items held; retry reuses record; private report/output checks passed');
  } finally {
    await rm(dir, { recursive: true, force: true });
    await php(`WP_Application_Passwords::delete_application_password(1, '${fixture.uuid}'); unlink(WPMU_PLUGIN_DIR . '/aid-migration-fixture.php');`);
  }
};
