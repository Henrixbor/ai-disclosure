'use strict';

// Publishing/build-time only. Python and the bundled sibling files are required.
const { execFile } = require('node:child_process');
const { join } = require('node:path');
const MAX_INPUT = 32 * 1024 * 1024;

function run(command, input, options = {}) {
  return new Promise((resolve, reject) => {
    if (!input || typeof input !== 'object' || Array.isArray(input) || 'command' in input) {
      throw new TypeError('Expected publishing input without a command field');
    }
    const timeout = options.timeoutMs ?? 30000;
    if (!Number.isInteger(timeout) || timeout < 1 || timeout > 300000) {
      throw new TypeError('timeoutMs must be between 1 and 300000');
    }
    const payload = JSON.stringify({ ...input, command });
    if (Buffer.byteLength(payload) > MAX_INPUT) throw new RangeError('Request exceeds 32 MiB');
    const child = execFile(options.python ?? process.env.AI_DISCLOSURE_PYTHON ?? 'python3',
      [join(__dirname, 'bridge.py')],
      { encoding: 'utf8', timeout, maxBuffer: 64 * 1024 * 1024, windowsHide: true,
        env: { ...process.env, PYTHONIOENCODING: 'utf-8' } },
      (error, stdout, stderr) => {
        if (error && (error.code !== 1 || error.killed || error.signal)) {
          const failure = new Error('AI Disclosure operation failed; do not publish this update');
          failure.cause = error;
          // Private diagnostics; never send them or the result report to visitors.
          failure.diagnostics = stderr;
          reject(failure);
          return;
        }
        try {
          const result = JSON.parse(stdout);
          if (!result || typeof result !== 'object' || Array.isArray(result) ||
              (command === 'inspect' ? !Array.isArray(result.gaps) :
                !(result.html === null || typeof result.html === 'string'))) {
            throw new Error('Invalid publishing response');
          }
          resolve(result);
        } catch (cause) {
          reject(new Error('Invalid AI Disclosure response; do not publish this update', { cause }));
        }
      });
    // Early process failures can close stdin before the request is delivered.
    // execFile's completion callback remains the single outcome authority.
    child.stdin.on('error', () => {});
    child.stdin.end(payload, 'utf8');
  });
}

module.exports = {
  inspectFragment: (input, options) => run('inspect', input, options),
  renderFragment: (input, options) => run('render', input, options),
  exportDocument: (input, options) => run('export', input, options),
};
