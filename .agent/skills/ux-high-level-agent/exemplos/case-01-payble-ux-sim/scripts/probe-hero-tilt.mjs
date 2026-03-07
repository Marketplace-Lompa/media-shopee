import { chromium } from 'playwright';

const url = 'https://payble.framer.ai/';

const candidateSelectors = [
  '[data-framer-name="IPad Pro 11"]',
  '[data-framer-name="Ipad Content"]',
  '[data-framer-name*="IPad"]',
  '[data-framer-name*="Ipad"]',
  '[data-framer-name*="Pad"]',
  'img[src*="ri1DEppM1Ulk4Cs9ufk6fyC4SSY"]',
];

const browser = await chromium.launch({ headless: true, args: ['--disable-blink-features=AutomationControlled'] });
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
  locale: 'en-US',
  timezoneId: 'America/New_York',
});
const page = await context.newPage();
await page.addInitScript(() => {
  Object.defineProperty(navigator, 'webdriver', { get: () => false });
});
await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
await page.waitForLoadState('networkidle', { timeout: 20000 }).catch(() => {});
await page.waitForTimeout(1500);

const candidates = await page.evaluate((sels) => {
  const rows = [];
  for (const sel of sels) {
    document.querySelectorAll(sel).forEach((el, idx) => {
      const cs = getComputedStyle(el);
      const rect = el.getBoundingClientRect();
      rows.push({
        sel,
        idx,
        tag: el.tagName.toLowerCase(),
        framerName: el.getAttribute('data-framer-name'),
        className: el.className,
        transform: cs.transform,
        opacity: cs.opacity,
        rect: { x: rect.x, y: rect.y, w: rect.width, h: rect.height },
      });
    });
  }
  return rows;
}, candidateSelectors);

console.log('\nCANDIDATES');
console.log(JSON.stringify(candidates, null, 2));

const target = await page.evaluateHandle(() => {
  const exact = document.querySelector('[data-framer-name="IPad Pro 11"]');
  if (exact) return exact;
  const img = document.querySelector('img[src*="ri1DEppM1Ulk4Cs9ufk6fyC4SSY"]');
  if (img) return img;
  const names = [...document.querySelectorAll('[data-framer-name]')].filter((el) => /ipad|pad/i.test(el.getAttribute('data-framer-name') || ''));
  return names[0] || null;
});

const exists = await target.evaluate((el) => !!el).catch(() => false);
if (!exists) {
  console.log('No target found for tilt probe');
  await browser.close();
  process.exit(0);
}

const sampleAt = async (y) => {
  await page.evaluate((v) => window.scrollTo({ top: v, behavior: 'instant' }), y);
  await page.waitForTimeout(250);
  const data = await target.evaluate((el) => {
    const rect = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    const chain = [];
    let cur = el;
    let depth = 0;
    while (cur && depth < 7) {
      const style = getComputedStyle(cur);
      const r = cur.getBoundingClientRect();
      chain.push({
        tag: cur.tagName.toLowerCase(),
        framerName: cur.getAttribute?.('data-framer-name') || null,
        className: typeof cur.className === 'string' ? cur.className : null,
        transform: style.transform,
        opacity: style.opacity,
        filter: style.filter,
        rect: { x: r.x, y: r.y, w: r.width, h: r.height },
      });
      cur = cur.parentElement;
      depth += 1;
    }

    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    const topElem = document.elementFromPoint(Math.max(0, Math.min(window.innerWidth - 1, centerX)), Math.max(0, Math.min(window.innerHeight - 1, centerY)));

    return {
      scrollY: window.scrollY,
      viewport: { w: window.innerWidth, h: window.innerHeight },
      target: {
        tag: el.tagName.toLowerCase(),
        framerName: el.getAttribute('data-framer-name'),
        className: el.className,
        transform: cs.transform,
        transformOrigin: cs.transformOrigin,
        rect: { x: rect.x, y: rect.y, w: rect.width, h: rect.height },
      },
      topElemAtCenter: topElem ? {
        tag: topElem.tagName.toLowerCase(),
        framerName: topElem.getAttribute?.('data-framer-name') || null,
        className: typeof topElem.className === 'string' ? topElem.className : null,
      } : null,
      chain,
    };
  });
  return data;
};

const samples = [];
for (const y of [0, 120, 240, 360, 480, 600, 760, 920, 1100]) {
  samples.push(await sampleAt(y));
}

console.log('\nSAMPLES');
console.log(JSON.stringify(samples, null, 2));

await browser.close();
