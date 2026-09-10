const { PHASE_PRODUCTION_BUILD, PHASE_DEVELOPMENT_SERVER } = require('next/constants');
const { prepare } = require('./scripts/prepare.cjs');

module.exports = async phase => {
  // Also runs for direct `next build`: no npm lifecycle hook can be bypassed.
  if (phase === PHASE_PRODUCTION_BUILD || phase === PHASE_DEVELOPMENT_SERVER) {
    await prepare();
  }
  return { output: 'export', trailingSlash: true, poweredByHeader: false, outputFileTracingRoot: __dirname };
};
