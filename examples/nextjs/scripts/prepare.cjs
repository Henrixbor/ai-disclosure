'use strict';
const { readFile, mkdir, writeFile } = require('node:fs/promises');
const { resolve, join } = require('node:path');
const { renderFragment } = require(process.env.AI_DISCLOSURE_MODULE ??
  '../../../skills/ai-disclosure/scripts/node.cjs');

async function prepare(project = resolve(__dirname, '..')) {
  const [html, rawFacts] = await Promise.all([
    readFile(join(project, 'content/article.html'), 'utf8'),
    readFile(join(project, 'content/facts.json'), 'utf8'),
  ]);
  const result = await renderFragment({
    root: join(project, 'public'), html, manifest: JSON.parse(rawFacts), page: 'news/index.html',
  });
  if (result.html === null) {
    // The build fails before compilation. Existing published output is left alone.
    const error = new Error('Disclosure review required: article or assets no longer match supported facts');
    error.report = result.report;
    throw error;
  }
  if (Object.keys(result.assets).some(name => name !== 'ai-disclosure.css')) {
    throw new Error('This article example does not implement media player assets');
  }
  const generated = join(project, '.generated');
  await mkdir(generated, { recursive: true });
  // No report or origin evidence enters the data imported by React.
  await writeFile(join(generated, 'article.json'), JSON.stringify({ html: result.html }));
  await writeFile(join(generated, 'disclosure.css'), result.assets['ai-disclosure.css'] ?? '');
}

module.exports = { prepare };
