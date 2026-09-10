'use strict';
const { engine } = require('./browser_engine.cjs');

// Preserve the native login interaction. On failure, report only structural
// signals and credential comparisons, never values, cookies or response bodies.
module.exports = async function login(page, base, password) {
  const signals = { engine, submitted: false, usernameMatches: null, passwordMatches: null, responseStatus: null };
  const isLogin = request => request.method() === 'POST' && new URL(request.url()).pathname === '/wp-login.php';
  const onRequest = request => {
    if (!isLogin(request)) return;
    const fields = new URLSearchParams(request.postData() || '');
    signals.submitted = true;
    signals.usernameMatches = fields.get('log') === 'admin';
    signals.passwordMatches = fields.get('pwd') === password;
  };
  const onResponse = response => {
    if (isLogin(response.request())) signals.responseStatus = response.status();
  };
  page.on('request', onRequest);
  page.on('response', onResponse);
  try {
    await page.goto(new URL('/wp-login.php', base).href);
    await page.locator('#user_login').fill('admin');
    await page.locator('#user_pass').fill(password);
    await Promise.all([page.waitForURL('**/wp-admin/**'), page.locator('#wp-submit').click()]);
  } catch (error) {
    signals.onLoginPage = new URL(page.url()).pathname === '/wp-login.php';
    signals.formState = await page.evaluate(() => ({
      present: !!document.querySelector('#loginform'),
      valid: document.querySelector('#loginform')?.checkValidity() ?? null,
      hasError: !!document.querySelector('#login_error'),
      usernameEmpty: document.querySelector('#user_login')?.value === '',
      passwordEmpty: document.querySelector('#user_pass')?.value === '',
    })).catch(() => null);
    console.error('WordPress login diagnostics:', JSON.stringify(signals));
    throw error;
  } finally {
    page.off('request', onRequest);
    page.off('response', onResponse);
  }
};
