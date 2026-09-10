/* Optional browser QA: NODE_PATH can point to a preinstalled Playwright runtime. */
const assert = require('node:assert/strict');
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    for (const width of [390, 1440]) {
      const context = await browser.newContext({ viewport: { width, height: 1000 }, javaScriptEnabled: false, reducedMotion: 'reduce' });
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(String(error)));
      const response = await page.goto(process.env.AI_DISCLOSURE_PREVIEW_URL || 'http://127.0.0.1:4173/');
      assert.equal(response.status(), 200);
      const layout = await page.evaluate(() => {
        const notices = [...document.querySelectorAll('[data-ai-disclosure]')].map(element => {
          const rect = element.getBoundingClientRect();
          const style = getComputedStyle(element);
          return { id: element.getAttribute('data-ai-disclosure'), width: rect.width, height: rect.height,
            display: style.display, visibility: style.visibility, text: element.textContent,
            top: rect.top, background: style.backgroundColor, color: style.color };
        });
        return { notices, scrollWidth: document.documentElement.scrollWidth,
          width: innerWidth, slots: document.documentElement.innerHTML.includes('<!-- ai-disclosure -->') };
      });
      assert.equal(layout.notices.length, 2);
      assert.equal(layout.slots, false);
      assert.ok(layout.scrollWidth <= layout.width, 'Page must not overflow horizontally');
      for (const notice of layout.notices) {
        assert.ok(notice.width > 30 && notice.height > 10);
        assert.notEqual(notice.display, 'none');
        assert.notEqual(notice.visibility, 'hidden');
        assert.equal(notice.text, 'AI-generated');
        assert.notEqual(notice.background, 'rgba(0, 0, 0, 0)', 'Local disclosure stylesheet must load');
      }
      assert.ok(layout.notices.find(n => n.id === 'website').top < 250, 'Page notice must be present at entry');
      await page.getByRole('link', { name: 'Start with the skill' }).click();
      assert.ok(await page.locator('#install').evaluate(e => Math.abs(e.getBoundingClientRect().top) < 100));
      await page.screenshot({ path: `.local-preview/preview-${width}.png`, fullPage: true });
      assert.deepEqual(errors, []);
      await context.close();
      console.log(`PASS ${width}px: visible static notices, local CSS, no overflow, installation navigation, no page errors`);
    }
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
