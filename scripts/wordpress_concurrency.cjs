'use strict';
const assert = require('node:assert/strict');
const { readFile } = require('node:fs/promises');
const { resolve } = require('node:path');
const { setTimeout: delay } = require('node:timers/promises');

module.exports = async function concurrencyChecks(docker, web, base) {
  const code = await readFile(resolve(__dirname, '../tests/wordpress-concurrency.php'), 'utf8');
  const run = async (phase, mode) => JSON.parse(await docker(['exec', '-i', '-e', 'AID_RACE_PHASE=' + phase, '-e', 'AID_RACE_MODE=' + mode, web, 'php'], code, 40000));
  const marker = (phase, mode) => '/tmp/aid-race-' + phase + '-' + mode;
  async function waitReady(paths) {
    for (let attempt = 0; attempt < 100; attempt++) {
      const result = await docker(['exec', web, 'php', '-r', 'echo (int) (' + paths.map(path => 'is_file(' + JSON.stringify(path + '.ready') + ')').join(' && ') + ');']);
      if (result === '1') return;
      await delay(100);
    }
    throw new Error('Separate database writers did not reach their race barriers');
  }
  const release = paths => docker(['exec', web, 'touch', ...paths.map(path => path + '.go')]);

  const initial = await run('amend', 'setup');
  const amendMarkers = ['amend-a', 'amend-b'].map(mode => marker('amend', mode));
  const competing = Promise.allSettled(['amend-a', 'amend-b'].map(mode => run('amend', mode)));
  let barrierError;
  try { await waitReady(amendMarkers); }
  catch (error) { barrierError = error; }
  finally { await release(amendMarkers); }
  const settled = await competing;
  for (const result of settled) if (result.status === 'rejected') throw result.reason;
  if (barrierError) throw new Error(barrierError.message + ': ' + JSON.stringify(settled));
  const results = settled.map(result => result.value);
  assert.notEqual(results[0].connection_id, results[1].connection_id, 'Competing writers must use different database connections');
  assert.deepEqual(results.map(result => result.status).sort(), [200, 409]);
  const current = await run('amend', 'inspect');
  assert.equal(current.current.assessment.record_id, results.find(result => result.status === 200).body.record_id);
  assert.equal(current.history.record_id, initial.record.record_id);
  assert.equal(current.history.facts.evidence, initial.facts.evidence);
  console.log('Concurrent MySQL amendments: one committed winner, one conflict, original history retained');

  const withdrawSetup = await run('withdraw-first', 'setup');
  const publishMarker = marker('withdraw-first', 'publish-wait');
  const publishing = Promise.allSettled([run('withdraw-first', 'publish-wait')]);
  try {
    await waitReady([publishMarker]);
    assert.equal((await run('withdraw-first', 'withdraw')).status, 200);
  } finally { await release([publishMarker]); }
  const afterWriteMarker = marker('withdraw-first', 'after-write');
  try {
    await waitReady([afterWriteMarker]);
    const intermediate = await run('withdraw-first', 'inspect');
    assert.equal(intermediate.status, 'draft', 'Database must remain draft before corrective hooks run');
    const publicRead = await fetch(new URL('/?p=' + withdrawSetup.id, base));
    assert.equal(publicRead.status, 404, 'Intermediate anonymous reader must not see withdrawn content');
  } finally { await release([afterWriteMarker]); }
  const published = (await publishing)[0];
  if (published.status === 'rejected') throw published.reason;
  const withdrawn = await run('withdraw-first', 'inspect');
  assert.equal(withdrawn.status, 'draft');
  assert.equal(withdrawn.current.assessment.decision, 'withdrawn');
  const response = await fetch(new URL('/?p=' + withdrawn.current.assessment.facts.id.replace('wp-', ''), base));
  assert.equal(response.status, 404);
  console.log('Withdrawal during publication: draft and anonymous HTTP 404 verified before corrective hooks and after completion');

  await run('publish-first', 'setup');
  const withdrawMarker = marker('publish-first', 'withdraw-wait');
  const withdrawing = Promise.allSettled([run('publish-first', 'withdraw-wait')]);
  try {
    await waitReady([withdrawMarker]);
    assert.equal((await run('publish-first', 'publish')).status, 'publish');
  } finally { await release([withdrawMarker]); }
  const rejected = (await withdrawing)[0];
  if (rejected.status === 'rejected') throw rejected.reason;
  assert.equal(rejected.value.status, 409);
  const retained = await run('publish-first', 'inspect');
  assert.equal(retained.status, 'publish');
  assert.equal(retained.current.assessment.decision, 'disclose');
  console.log('Publication before withdrawal commits: draft guard rejects withdrawal and preserves the active notice decision');
};
