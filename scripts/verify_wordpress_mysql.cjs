'use strict';
const { execFile } = require('node:child_process');
const { randomBytes } = require('node:crypto');
const { readFile } = require('node:fs/promises');
const { resolve } = require('node:path');
const { setTimeout: delay } = require('node:timers/promises');
const { siteChecks } = require('./verify_wordpress.cjs');
const concurrencyChecks = require('./wordpress_concurrency.cjs');
const cacheChecks = require('./wordpress_cache.cjs');
const wordpressPackage = require('./wordpress_package.cjs');
const replacementChecks = require('./wordpress_replacement.cjs');

const WORDPRESS = 'wordpress:7.1-php8.3-apache@sha256:5a93c470ae8220fddf71f6ebe3bc94e615ddc2ae4d9810f795b830fb11c41a17';
const MYSQL = 'mysql:8.4@sha256:3466ba4a4828aa8d46fb7c3bc16b67b781c98413cf4ea0fac6feaa6e881faa26';
function docker(args, input = '', timeout = 120000) {
  return new Promise((accept, reject) => {
    const child = execFile('docker', args, { timeout, maxBuffer: 4 * 1024 * 1024 }, (error, stdout, stderr) => {
      // Never print execFile's command text: container arguments contain disposable passwords.
      if (error) reject(new Error('Docker operation ' + args[0] + ' failed: ' + stderr));
      else accept(stdout.trim());
    });
    child.stdin.on('error', () => {});
    child.stdin.end(input);
  });
}
async function main() {
  const archive = await wordpressPackage();
  const name = 'aid-mysql-test-' + randomBytes(6).toString('hex');
  const db = name + '-db';
  const web = name + '-web';
  const password = randomBytes(24).toString('hex');
  let networkCreated = false;
  try {
    await docker(['network', 'create', name]);
    networkCreated = true;
    await docker(['run', '-d', '--name', db, '--network', name, '--network-alias', 'db', '--memory', '768m', '--pids-limit', '256',
      '-e', 'MYSQL_ROOT_PASSWORD=' + password, '-e', 'MYSQL_DATABASE=aid_fixture', '-e', 'MYSQL_USER=aid_fixture', '-e', 'MYSQL_PASSWORD=' + password, MYSQL]);
    await docker(['run', '-d', '--name', web, '--network', name, '--memory', '512m', '--pids-limit', '256', '-p', '127.0.0.1::80',
      '-e', 'WORDPRESS_DB_HOST=db', '-e', 'WORDPRESS_DB_USER=aid_fixture', '-e', 'WORDPRESS_DB_NAME=aid_fixture', '-e', 'WORDPRESS_DB_PASSWORD=' + password, WORDPRESS]);
    const port = await docker(['port', web, '80/tcp']);
    if (!/^127\.0\.0\.1:\d+$/.test(port)) throw new Error('Unexpected fixture port binding');
    const base = 'http://' + port;
    let ready = false;
    for (let attempt = 0; attempt < 90; attempt++) {
      try {
        await docker(['exec', web, 'php', '-r', 'mysqli_report(MYSQLI_REPORT_OFF); if (!file_exists("/var/www/html/wp-config.php")) exit(1); $db = @new mysqli("db", "aid_fixture", getenv("WORDPRESS_DB_PASSWORD"), "aid_fixture"); exit($db->connect_errno ? 1 : 0);'], '', 5000);
        ready = true; break;
      } catch { await delay(1000); }
    }
    if (!ready) throw new Error('Disposable MySQL fixture did not become ready');
    await docker(['exec', web, 'ln', '-s', '/var/www/html', '/wordpress']);
    console.log('MySQL fixture ready; installing WordPress and running the shared PHP checks');
    await docker(['exec', '-i', web, 'php'], '<?php\ndefine("WP_INSTALLING", true); require "/wordpress/wp-load.php"; require_once ABSPATH . "wp-admin/includes/upgrade.php";\n'
      + 'wp_install("AI Disclosure fixture", "admin", "fixture@example.invalid", false, "", ' + JSON.stringify(password) + ');\n'
      + 'update_option("siteurl", ' + JSON.stringify(base) + '); update_option("home", ' + JSON.stringify(base) + ');\n'
      + 'require_once ABSPATH . "wp-admin/includes/plugin.php"; require_once ABSPATH . "wp-admin/includes/class-wp-upgrader.php";\n'
      + 'define("FS_METHOD", "direct"); file_put_contents("/tmp/aid-plugin.zip", base64_decode("' + archive.bytes.toString('base64') + '", true));\n'
      + 'if (hash_file("sha256", "/tmp/aid-plugin.zip") !== "' + archive.sha256 + '") throw new Exception("Plugin archive digest mismatch");\n'
      + '$upgrader = new Plugin_Upgrader(new Automatic_Upgrader_Skin()); $installed = $upgrader->install("/tmp/aid-plugin.zip"); if ($installed !== true) throw new Exception("Plugin archive installation failed: " . (is_wp_error($installed) ? $installed->get_error_message() : "filesystem error"));\n'
      + '$r = activate_plugin("ai-disclosure/ai-disclosure.php"); if (is_wp_error($r)) throw new Exception($r->get_error_message());\n');
    const runtime = JSON.parse(await docker(['exec', '-i', web, 'php'], '<?php require "/wordpress/wp-load.php"; global $wpdb, $wp_version; echo wp_json_encode(["mysql" => $wpdb->get_var("SELECT VERSION()"), "php" => PHP_VERSION, "wordpress" => $wp_version, "theme" => get_option("template"), "collation" => $wpdb->get_var("SELECT @@collation_server")]);'));
    if (!runtime.mysql.startsWith('8.4.') || !runtime.php.startsWith('8.3.') || !/^7\.1(?:\.0)?$/.test(runtime.wordpress)) throw new Error('Unexpected fixture runtime versions');
    console.log('Verified runtime: ' + JSON.stringify(runtime));
    const code = await readFile(resolve(__dirname, '../tests/wordpress-integration.php'), 'utf8');
    console.log(await docker(['exec', '-i', web, 'php'], code));
    await concurrencyChecks(docker, web, base);
    // The editor fixture is generated by the PHP suite; Apache must be able to read it.
    await siteChecks(base, password);
    await replacementChecks(docker, web, base, password, archive);
    await cacheChecks(docker, web, base);
    console.log('Official WordPress 7.1/PHP 8.3 with MySQL 8.4: shared PHP and browser checks passed');
  } finally {
    if (networkCreated) {
      const removed = await Promise.allSettled([docker(['rm', '-fv', web]), docker(['rm', '-fv', db])]);
      for (const result of removed) if (result.status === 'rejected' && !result.reason.message.includes('No such container')) console.error(result.reason.message);
      await docker(['network', 'rm', name]);
    }
  }
}
main().catch(error => { console.error(error.message); process.exitCode = 1; });
