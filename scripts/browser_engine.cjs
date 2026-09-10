'use strict';
const playwright = require('playwright');
const engine = process.env.AI_DISCLOSURE_BROWSER || 'chromium';
if (!['chromium', 'firefox', 'webkit'].includes(engine)) {
  throw new Error('AI_DISCLOSURE_BROWSER must be chromium, firefox or webkit');
}
module.exports = { engine, browserType: playwright[engine] };
