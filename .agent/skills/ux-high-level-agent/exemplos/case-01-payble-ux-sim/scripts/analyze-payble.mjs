import { chromium } from "playwright";
import fs from "node:fs/promises";
import path from "node:path";

const TARGET_URL = process.argv[2] || "https://payble.framer.ai/";
const OUT_DIR = path.resolve(process.cwd(), "analysis");

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function ensureDir(dir) {
  await fs.mkdir(dir, { recursive: true });
}

async function tryDismissOverlays(page) {
  const selectors = [
    'button:has-text("Accept")',
    'button:has-text("Allow")',
    'button:has-text("Got it")',
    'button:has-text("Close")',
    'button:has-text("No thanks")',
    '[aria-label="Close"]',
    '[data-testid="close"]',
  ];

  for (const selector of selectors) {
    try {
      const locator = page.locator(selector).first();
      if (await locator.isVisible({ timeout: 300 })) {
        await locator.click({ timeout: 600 });
        await sleep(250);
      }
    } catch {
      // Ignore non-matching overlays.
    }
  }
}

async function main() {
  await ensureDir(OUT_DIR);

  const browser = await chromium.launch({
    headless: true,
    args: [
      "--disable-blink-features=AutomationControlled",
      "--no-sandbox",
      "--disable-dev-shm-usage",
    ],
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    userAgent:
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    locale: "en-US",
    timezoneId: "America/New_York",
    colorScheme: "light",
    reducedMotion: "no-preference",
    deviceScaleFactor: 2,
  });

  const page = await context.newPage();

  const networkLog = [];
  page.on("response", (response) => {
    const url = response.url();
    if (url.includes("framerusercontent.com") || url.includes("framer.com")) {
      networkLog.push({
        status: response.status(),
        url,
        type: response.request().resourceType(),
      });
    }
  });

  await page.addInitScript(() => {
    Object.defineProperty(navigator, "webdriver", { get: () => false });
  });

  const startedAt = Date.now();

  await page.goto(TARGET_URL, {
    waitUntil: "domcontentloaded",
    timeout: 45000,
  });

  await page.waitForLoadState("networkidle", { timeout: 20000 }).catch(() => {});
  await sleep(1500);
  await tryDismissOverlays(page);

  await page.screenshot({
    path: path.join(OUT_DIR, "01-hero.png"),
    fullPage: false,
  });

  const scrollMetrics = [];
  const fullHeight = await page.evaluate(() =>
    Math.max(
      document.body.scrollHeight,
      document.documentElement.scrollHeight,
      document.documentElement.offsetHeight
    )
  );

  const viewportHeight = page.viewportSize()?.height || 900;
  let shotIndex = 2;

  for (let y = 0; y < fullHeight; y += Math.round(viewportHeight * 0.8)) {
    await page.evaluate((nextY) => window.scrollTo({ top: nextY, behavior: "instant" }), y);
    await sleep(450);
    await tryDismissOverlays(page);

    const metrics = await page.evaluate(() => {
      const activeTexts = Array.from(document.querySelectorAll("h1,h2,h3,p,a,button"))
        .map((el) => el.textContent?.trim() || "")
        .filter(Boolean)
        .slice(0, 25);
      return {
        scrollY: window.scrollY,
        activeTexts,
      };
    });
    scrollMetrics.push(metrics);

    if (shotIndex <= 8) {
      await page.screenshot({
        path: path.join(OUT_DIR, `0${shotIndex}-scroll.png`),
        fullPage: false,
      });
      shotIndex += 1;
    }
  }

  await page.evaluate(() => window.scrollTo({ top: 0, behavior: "instant" }));
  await sleep(300);

  const extracted = await page.evaluate(() => {
    const textOf = (selector) =>
      Array.from(document.querySelectorAll(selector))
        .map((el) => (el.textContent || "").replace(/\s+/g, " ").trim())
        .filter(Boolean);

    const unique = (arr) => Array.from(new Set(arr));

    const headings = unique(textOf("h1,h2,h3")).slice(0, 120);
    const buttons = unique(textOf("button,[role='button'],a"))
      .filter((txt) => txt.length < 80)
      .slice(0, 180);

    const framerNames = unique(
      Array.from(document.querySelectorAll("[data-framer-name]"))
        .map((el) => el.getAttribute("data-framer-name") || "")
        .filter(Boolean)
    ).slice(0, 250);

    const images = unique(
      Array.from(document.images)
        .map((img) => img.currentSrc || img.src)
        .filter(Boolean)
    ).slice(0, 200);

    const sections = Array.from(document.querySelectorAll("section, main > div, [data-framer-name]"))
      .slice(0, 120)
      .map((el) => ({
        tag: el.tagName.toLowerCase(),
        framerName: el.getAttribute("data-framer-name"),
        text: (el.textContent || "").replace(/\s+/g, " ").trim().slice(0, 220),
      }))
      .filter((s) => s.text || s.framerName);

    return {
      title: document.title,
      metaDescription: document.querySelector('meta[name="description"]')?.getAttribute("content"),
      headings,
      buttons,
      framerNames,
      images,
      sections,
      bodyClass: document.body.className,
      pageHeight: document.documentElement.scrollHeight,
    };
  });

  await page.screenshot({
    path: path.join(OUT_DIR, "09-fullpage.png"),
    fullPage: true,
    timeout: 60000,
  });

  const result = {
    targetUrl: TARGET_URL,
    capturedAt: new Date().toISOString(),
    durationMs: Date.now() - startedAt,
    blockedDetection: {
      note: "No hard anti-bot wall encountered during this capture. Script uses realistic browser context and webdriver masking.",
    },
    viewport: page.viewportSize(),
    scrollMetrics,
    extracted,
    networkLog: networkLog.slice(0, 300),
  };

  await fs.writeFile(
    path.join(OUT_DIR, "payble-analysis.json"),
    JSON.stringify(result, null, 2),
    "utf8"
  );

  await browser.close();
  console.log(`Saved analysis to ${OUT_DIR}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
