// End-to-end test of the product flow: home -> landlord listing -> tenant drops PDFs -> proof -> deposit -> receipt.
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const dir = process.argv[2], D = __dirname + '/../demo_docs/';
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1300, height: 900 } });
  const L = await ctx.newPage(), T = await ctx.newPage();
  for (const p of [L, T]) p.on('pageerror', (e) => console.log('PAGE ERROR', e.message));
  const shot = (p, n) => p.screenshot({ path: `${dir}/${n}.png`, fullPage: true });
  await L.request.post('http://127.0.0.1:8010/api/reset', { data: {} });
  await L.goto('http://127.0.0.1:8010/'); await L.waitForTimeout(500); await shot(L, '00_home');
  await L.goto('http://127.0.0.1:8010/admin.html'); await L.waitForTimeout(500); await shot(L, '00b_admin');
  await L.goto('http://127.0.0.1:8010/landlord.html'); await L.waitForTimeout(800);
  await L.click('#fill'); await L.waitForSelector('#publish'); if (process.env.SEX) { await L.selectOption('#sex', process.env.SEX); await L.waitForTimeout(500); } await L.fill('#fAddr', 'Via Nizza 45, 10125 Torino');
  await L.waitForTimeout(300); await shot(L, '02_landlord_form');
  await L.click('#publish'); await L.waitForSelector('.code'); await L.waitForTimeout(500);
  await shot(L, '03_landlord_published');
  const code = (await L.textContent('.code')).trim();
  await T.goto('http://127.0.0.1:8010/a/' + code); await T.waitForSelector('#next1'); await T.waitForTimeout(800);
  await shot(T, '04_tenant_request');
  await T.click('#next1'); await T.waitForSelector('#dropIn', { state: 'attached' }); await shot(T, '05_tenant_docs_empty');
  await T.setInputFiles('#dropIn', [D + '2_Income_statement_Elena_Rossi_EDITED.pdf']); await T.waitForSelector('.notice.bad'); await T.waitForTimeout(800);
  await shot(T, '06_tenant_fake_rejected');
  if (process.env.REAL_PDFS) { await T.setInputFiles('#dropIn', process.env.REAL_PDFS.split(',')); await T.waitForTimeout(2500); await shot(T, '06b_tenant_real_docs'); }
  await T.setInputFiles('#dropIn', ['1_Identity_codice_fiscale_Elena_Rossi.pdf', '2_Income_statement_Elena_Rossi.pdf', '3_Enrolment_certificate_Elena_Rossi.pdf',
    '4_Balance_certificate_Elena_Rossi.pdf', '5_Guarantor_income_Marco_Rossi.pdf'].map((f) => D + f));
  await T.waitForSelector('#next2:not([disabled])', { timeout: 20000 }); await T.waitForTimeout(500);
  await shot(T, '07_tenant_docs_ok');
  await T.click('#next2'); await T.click('#prove'); await T.waitForSelector('#send', { timeout: 120000 });
  await T.click('#send'); await T.click('#mYes');
  await L.bringToFront(); await L.waitForFunction(() => document.body.innerText.includes('meets all'), null, { timeout: 60000 });
  await L.waitForTimeout(800); await shot(L, '08_landlord_result');
  await T.bringToFront(); await T.waitForSelector('#pay', { timeout: 30000 });
  await T.waitForTimeout(1500); await T.click('#pay'); await T.waitForSelector('#mYes', { state: 'visible' }); await T.click('#mYes');
  await T.waitForFunction(() => document.body.innerText.includes('All done'), null, { timeout: 30000 }); await shot(T, '10_tenant_done');
  await L.waitForFunction(() => document.body.innerText.includes('All done'), null, { timeout: 30000 }); await shot(L, '11_landlord_done');
  const R = await ctx.newPage(); R.on('pageerror', (e) => console.log('PAGE ERROR', e.message));
  await R.goto('http://127.0.0.1:8010/receipt.html'); await R.waitForSelector('.band'); await R.waitForTimeout(500); await shot(R, '12_receipt');
  const P = await ctx.newPage(); await P.setViewportSize({ width: 390, height: 844 });
  await P.goto('http://127.0.0.1:8010/a/' + code); await P.waitForTimeout(1200); await shot(P, '13_phone_tenant');
  console.log('E2E real OK');
  await b.close();
})().catch((e) => { console.log('E2E FAIL', e.message); process.exit(1); });
