// End-to-end test of the simple tenant + landlord screens (app on :8010). Saves screenshots to argv[2] dir.
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const dir = process.argv[2];
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1440, height: 900 } });
  const L = await ctx.newPage(), T = await ctx.newPage();
  for (const p of [L, T]) { p.on('pageerror', (e) => console.log('PAGE ERROR', e.message)); p.on('dialog', (d) => d.accept()); }
  const shot = (p, n) => p.screenshot({ path: `${dir}/${n}.png`, fullPage: true });
  await L.goto('http://127.0.0.1:8010/landlord.html'); await L.waitForTimeout(800);
  await L.click('#fReset'); await L.waitForTimeout(800);
  await shot(L, '01_landlord_start');
  await L.click('#fill'); await L.waitForSelector('#publish'); await L.waitForTimeout(300);
  await shot(L, '02_landlord_form');
  await L.click('#publish'); await L.waitForSelector('.code'); await L.waitForTimeout(500);
  await shot(L, '03_landlord_published');
  const code = (await L.textContent('.code')).trim(); console.log('code', code, 'landlord url', L.url());
  await T.goto('http://127.0.0.1:8010/a/' + code); await T.waitForSelector('#next1'); await T.waitForTimeout(800);
  await shot(T, '04_tenant_request');
  await T.click('#next1'); await T.waitForTimeout(400);
  const I = await ctx.newPage(); I.on('dialog', (d) => d.accept()); I.on('pageerror', (e) => console.log('PAGE ERROR', e.message));
  await I.goto('http://127.0.0.1:8010/issuer.html'); await I.waitForSelector('#send'); await I.click('#send');
  await I.waitForFunction(() => document.body.innerText.includes('Delivered'), null, { timeout: 30000 }); await shot(I, '04b_issuer_done');
  await T.bringToFront(); await T.waitForSelector('#useWallet', { timeout: 20000 }); await shot(T, '04c_tenant_wallet');
  await T.click('#useWallet'); await T.waitForTimeout(1200);
  await T.click('#fake'); await T.waitForTimeout(1500);
  await shot(T, '05_tenant_fake_rejected');

  await shot(T, '06_tenant_docs_ok');
  await T.click('#next2'); await T.waitForTimeout(300);
  await T.click('#prove'); await T.waitForSelector('#send', { timeout: 120000 });
  await shot(T, '07_tenant_proof_ready');
  await T.click('#send'); await T.click('#mYes'); await T.waitForTimeout(500);
  await L.bringToFront();
  await L.waitForFunction(() => document.body.innerText.includes('meets all'), null, { timeout: 60000 });
  await L.waitForTimeout(800);
  await shot(L, '08_landlord_result');
  await T.bringToFront(); await T.waitForSelector('#pay', { timeout: 30000 }); await T.waitForTimeout(500);
  await shot(T, '09_tenant_deposit');
  await T.click('#pay'); await T.click('#mYes');
  await T.waitForFunction(() => document.body.innerText.includes('Deposit paid'), null, { timeout: 30000 });
  await shot(T, '10_tenant_done');
  await L.waitForFunction(() => document.body.innerText.includes('received'), null, { timeout: 30000 });
  await shot(L, '11_landlord_done');
  console.log('E2E simple OK');
  await b.close();
})().catch((e) => { console.log('E2E FAIL', e.message); process.exit(1); });
