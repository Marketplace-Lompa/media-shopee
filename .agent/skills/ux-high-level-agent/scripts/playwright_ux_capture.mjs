#!/usr/bin/env node
import fs from "node:fs/promises";
import { createRequire } from "node:module";
import path from "node:path";

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith("--")) continue;
    const key = token.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith("--")) {
      args[key] = true;
      continue;
    }
    args[key] = next;
    i += 1;
  }
  return args;
}

const argv = parseArgs(process.argv.slice(2));
const targetUrl = argv.url;
const outDir = argv["out-dir"] ? path.resolve(argv["out-dir"]) : null;
const label = argv.label || "capture";
const waitMs = Number(argv["wait-ms"] || 1200);
const hidePromos = argv["hide-promos"] !== "false";
const includeFullPage = argv["full-page"] === "true";
const playwrightFrom = argv["playwright-from"];

async function loadPlaywright() {
  const scriptRequire = createRequire(import.meta.url);
  try {
    return scriptRequire("playwright");
  } catch {
    // Fall through.
  }

  try {
    const cwdPkg = path.join(process.cwd(), "package.json");
    const cwdRequire = createRequire(cwdPkg);
    return cwdRequire("playwright");
  } catch {
    // Fall through.
  }

  if (playwrightFrom) {
    try {
      const customRequire = createRequire(path.resolve(playwrightFrom));
      return customRequire("playwright");
    } catch {
      // Fall through.
    }
  }

  throw new Error(
    "Could not resolve 'playwright'. Run this script from a project with playwright installed, or pass --playwright-from <path/to/package.json>."
  );
}

if (!targetUrl || !outDir) {
  console.error(
    "Usage: node playwright_ux_capture.mjs --url <url> --out-dir <dir> [--label case-02] [--wait-ms 1200] [--hide-promos true|false] [--full-page true|false]"
  );
  process.exit(1);
}

const SHOTS = [
  { name: "desktop-top", viewport: { width: 1440, height: 900 }, scroll: 0 },
  { name: "desktop-hero-progress", viewport: { width: 1440, height: 900 }, scroll: 420 },
  { name: "desktop-hero-aligned", viewport: { width: 1440, height: 900 }, scroll: 760 },
  { name: "tablet-top", viewport: { width: 834, height: 1112 }, scroll: 0 },
  { name: "tablet-mid", viewport: { width: 834, height: 1112 }, scroll: 900 },
  { name: "mobile-top", viewport: { width: 390, height: 844 }, scroll: 0 },
  { name: "mobile-mid", viewport: { width: 390, height: 844 }, scroll: 980 },
  { name: "mobile-feature", viewport: { width: 390, height: 844 }, scroll: 1800 },
];

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function ensureDir(dir) {
  await fs.mkdir(dir, { recursive: true });
}

async function tryDismissButtons(page) {
  const selectors = [
    'button:has-text("Accept")',
    'button:has-text("Allow")',
    'button:has-text("Got it")',
    'button:has-text("Close")',
    'button:has-text("No thanks")',
    'button:has-text("Dismiss")',
    'button:has-text("Remove")',
    '[aria-label="Close"]',
    '[data-framer-name="Remove Button"]',
  ];
  for (const selector of selectors) {
    try {
      const loc = page.locator(selector).first();
      if (await loc.isVisible({ timeout: 200 })) {
        await loc.click({ timeout: 500 });
        await sleep(150);
      }
    } catch {
      // ignore
    }
  }
}

async function hidePromotionalFixedOverlays(page) {
  if (!hidePromos) return [];
  const hidden = await page.evaluate(() => {
    const keywords = /(framer|template|unlock|components|made in framer)/i;
    const hiddenNodes = [];
    const markHidden = (el, reason) => {
      if (!el || !(el instanceof HTMLElement)) return;
      if (el.getAttribute("data-ux-hidden-overlay") === "1") return;
      const rect = el.getBoundingClientRect();
      hiddenNodes.push({
        reason,
        tag: el.tagName.toLowerCase(),
        id: el.id || null,
        className: typeof el.className === "string" ? el.className : null,
        text: ((el.textContent || "").replace(/\s+/g, " ").trim()).slice(0, 160),
        rect: { x: rect.x, y: rect.y, w: rect.width, h: rect.height },
      });
      el.setAttribute("data-ux-hidden-overlay", "1");
      el.style.setProperty("display", "none", "important");
    };

    // Framer badge/promo widgets are common and can pollute UX screenshots.
    document
      .querySelectorAll(
        "#__framer-badge-container, a.__framer-badge, [class*='__framer-badge'], [data-framer-name='Remove This Buy Promo'], [data-framer-name='Remove This Buy Button'], [data-framer-name='Remove Button']"
      )
      .forEach((el) => markHidden(el, "framer-badge"));

    const nodes = Array.from(document.querySelectorAll("body *"));
    for (const el of nodes) {
      if (!(el instanceof HTMLElement)) continue;
      if (el.getAttribute("data-ux-hidden-overlay") === "1") continue;
      const style = window.getComputedStyle(el);
      if (style.position !== "fixed") continue;
      const rect = el.getBoundingClientRect();
      if (rect.width < 80 || rect.height < 24) continue;
      if (rect.width > window.innerWidth * 0.45 || rect.height > window.innerHeight * 0.45) continue;
      const nearBottomRight =
        rect.right >= window.innerWidth - 24 && rect.bottom >= window.innerHeight - 24;
      const text = (el.textContent || "").replace(/\s+/g, " ").trim();
      if (!nearBottomRight) continue;
      if (!keywords.test(text)) continue;
      markHidden(el, "generic-fixed-promo");
    }
    return hiddenNodes;
  });
  return hidden;
}

async function captureShot(browser, shot) {
  const context = await browser.newContext({
    viewport: shot.viewport,
    locale: "en-US",
    timezoneId: "America/New_York",
    colorScheme: "light",
    reducedMotion: "no-preference",
    userAgent:
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    deviceScaleFactor: 2,
  });

  const page = await context.newPage();
  await page.addInitScript(() => {
    Object.defineProperty(navigator, "webdriver", { get: () => false });
  });

  await page.goto(targetUrl, { waitUntil: "domcontentloaded", timeout: 45000 });
  await page.waitForLoadState("networkidle", { timeout: 20000 }).catch(() => {});
  await sleep(waitMs);

  await tryDismissButtons(page);
  const hiddenOverlays = await hidePromotionalFixedOverlays(page);

  if (shot.scroll) {
    await page.evaluate((y) => window.scrollTo({ top: y, behavior: "instant" }), shot.scroll);
    await sleep(350);
    await tryDismissButtons(page);
  }

  const metadata = await page.evaluate(() => {
    const doc = document.documentElement;
    const body = document.body;
    const headings = Array.from(document.querySelectorAll("h1,h2,h3"))
      .map((el) => (el.textContent || "").replace(/\s+/g, " ").trim())
      .filter(Boolean)
      .slice(0, 20);
    const ctas = Array.from(document.querySelectorAll("a,button"))
      .map((el) => (el.textContent || "").replace(/\s+/g, " ").trim())
      .filter(Boolean)
      .filter((v) => v.length < 100)
      .slice(0, 40);
    return {
      title: document.title,
      scrollY: window.scrollY,
      innerWidth: window.innerWidth,
      innerHeight: window.innerHeight,
      scrollHeight: doc.scrollHeight,
      bodyWidth: body.scrollWidth,
      htmlWidth: doc.scrollWidth,
      hasHorizontalOverflow: Math.max(body.scrollWidth, doc.scrollWidth) > window.innerWidth + 1,
      headings,
      ctas,
    };
  });

  const filenameBase = `${label}-${shot.name}`;
  const pngPath = path.join(outDir, `${filenameBase}.png`);
  const jsonPath = path.join(outDir, `${filenameBase}.json`);
  await page.screenshot({ path: pngPath });
  await fs.writeFile(
    jsonPath,
    JSON.stringify(
      {
        ...metadata,
        viewport: shot.viewport,
        requestedScroll: shot.scroll,
        hiddenOverlays,
      },
      null,
      2
    ),
    "utf8"
  );

  let fullPageFile = null;
  if (includeFullPage && shot.name === "desktop-top") {
    fullPageFile = path.join(outDir, `${label}-desktop-fullpage.png`);
    await page.screenshot({ path: fullPageFile, fullPage: true, timeout: 60000 });
  }

  await context.close();
  return {
    shot: shot.name,
    png: pngPath,
    json: jsonPath,
    fullPageFile,
    hiddenOverlayCount: hiddenOverlays.length,
    overflow: metadata.hasHorizontalOverflow,
  };
}

async function main() {
  const { chromium } = await loadPlaywright();
  await ensureDir(outDir);
  const browser = await chromium.launch({
    headless: true,
    args: ["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"],
  });

  const startedAt = Date.now();
  const results = [];
  for (const shot of SHOTS) {
    results.push(await captureShot(browser, shot));
  }
  await browser.close();

  const summary = {
    url: targetUrl,
    label,
    generatedAt: new Date().toISOString(),
    durationMs: Date.now() - startedAt,
    hidePromos,
    shots: results,
  };
  await fs.writeFile(path.join(outDir, `${label}-summary.json`), JSON.stringify(summary, null, 2), "utf8");
  console.log(`Saved ${results.length} screenshots to ${outDir}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
