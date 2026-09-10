'use strict';
const { execFile } = require('node:child_process');
const { promisify } = require('node:util');
const { mkdtemp, readFile, rm } = require('node:fs/promises');
const { tmpdir } = require('node:os');
const { join, resolve } = require('node:path');
const { createHash } = require('node:crypto');

module.exports = async function wordpressPackage() {
  const dir = await mkdtemp(join(tmpdir(), 'aid-wordpress-package-'));
  try {
    const output = join(dir, 'ai-disclosure-wordpress.zip');
    await promisify(execFile)('python3', [resolve(__dirname, 'package_skill.py'), '--format', 'wordpress', '--output', output], { timeout: 30000 });
    const bytes = await readFile(output);
    const sha256 = createHash('sha256').update(bytes).digest('hex');
    console.log('WordPress archive SHA-256: ' + sha256);
    return { bytes, sha256 };
  } finally { await rm(dir, { recursive: true, force: true }); }
};
