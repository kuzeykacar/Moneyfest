// End-to-end browser test of the whole demo flow (needs the app running on :8010).
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const shot = process.argv[2];
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1400, height: 1200 } });
  p.on('dialog', (d) => d.accept());
  p.on('pageerror', (e) => console.log('PAGE ERROR', e.message));
  await p.goto('http://127.0.0.1:8010'); await p.click('#resetBtn'); await p.waitForTimeout(500);
  await p.click('#aiBtn'); await p.waitForTimeout(500);
  await p.click('#publishBtn'); await p.waitForTimeout(600);
  await p.click('#fakeBtn'); await p.waitForTimeout(500);
  console.log('fake:', (await p.textContent('#tnDocs')).includes('REJECTED') ? 'rejected' : 'NOT rejected');
  await p.click('#samplesBtn'); await p.waitForTimeout(1200);
  const t0 = Date.now();
  await p.click('#proveBtn');
  await p.waitForSelector('#sendBtn', { timeout: 120000 });
  console.log('proof made in browser, ms', Date.now() - t0);
  await p.click('#sendBtn');
  await p.waitForFunction(() => document.querySelector('#llInbox').textContent.includes('learned'), null, { timeout: 60000 });
  console.log('landlord:', (await p.textContent('#llInbox')).replace(/\s+/g, ' ').slice(0, 400));
  await p.waitForSelector('.confirm button.go', { timeout: 20000 });
  await p.click('.confirm button.go');
  await p.waitForFunction(() => document.querySelector('#llDeposit').textContent.includes('received'), null, { timeout: 30000 });
  console.log('deposit:', (await p.textContent('#llDeposit')).trim(), '|', (await p.textContent('#tnBal')).trim());
  await p.screenshot({ path: shot, fullPage: true });
  await b.close();
})().catch((e) => { console.log('E2E FAIL', e.message); process.exit(1); });
