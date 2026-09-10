const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const {spawn}=require('node:child_process');
(async()=>{
 const server=spawn('python3',['-m','http.server','4174','--bind','127.0.0.1','--directory','.local-preview/media-output'],{stdio:'ignore'});
 let browser;
 try {
  for(let attempt=0;attempt<30;attempt++){
   try {const response=await fetch('http://127.0.0.1:4174'); if(response.ok) break;} catch {}
   if(attempt===29) throw Error('Media fixture server failed to start');
   await new Promise(resolve=>setTimeout(resolve,100));
  }
  browser=await chromium.launch({headless:true});
  const page=await browser.newPage(); const errors=[]; page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:4174');
  await page.waitForSelector('[data-aid-player][data-state="ready"]');
  assert.equal(await page.locator('[data-aid-content]').getAttribute('src'),null);
  await page.locator('[data-aid-play]').click();
  await page.waitForSelector('[data-state="disclosure"]');
  assert.equal(await page.locator('[data-aid-content]').getAttribute('src'),null);
  await page.waitForSelector('[data-state="content"]');
  await page.waitForFunction(()=>document.querySelector('[data-aid-content]').currentTime>0);
  await page.locator('[data-aid-play]').click();
  assert.equal(await page.locator('[data-aid-content]').evaluate(e=>e.paused),true);
  await page.locator('[data-aid-player]').evaluate(e=>e.dataset.source='changed.wav');
  await page.waitForSelector('[data-state="invalid"]');
  assert.equal(await page.locator('[data-aid-content]').getAttribute('src'),null);
  await page.reload(); await page.route('**/notice.wav',r=>r.abort());
  await page.locator('[data-aid-play]').click();
  await page.waitForSelector('[data-state="error"]');
  assert.equal(await page.locator('[data-aid-content]').getAttribute('src'),null);
  const nojs=await browser.newPage({javaScriptEnabled:false}); await nojs.goto('http://127.0.0.1:4174');
  assert.equal(await nojs.locator('[data-aid-play]').isDisabled(),true);
  assert.equal(await nojs.locator('[data-aid-content]').getAttribute('src'),null);
  assert.equal(await nojs.locator('.aid-notice').isVisible(),true);
  assert.deepEqual(errors,[]);
  console.log('PASS: real audio sequencing, pause, configuration invalidation, notice failure, no-JS visibility. Silence fixture does not validate spoken wording.');
 } finally {if(browser) await browser.close(); server.kill();}
})().catch(e=>{console.error(e);process.exit(1)});
