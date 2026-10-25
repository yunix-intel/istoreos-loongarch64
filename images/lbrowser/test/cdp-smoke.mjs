import fs from 'node:fs';
import path from 'node:path';

const engine = process.env.CDP_ENGINE || 'playwright-core';
const { chromium } = await import(engine);

const endpoint = process.env.CDP_ENDPOINT || 'http://127.0.0.1:19222';
const outDir = process.env.OUT_DIR || '/tmp/lbrowser-smoke';
fs.mkdirSync(outDir, { recursive: true });

const result = { engine, endpoint, browserVersion: null, status: null, title: null, contentBytes: null, screenshotBytes: null, errors: [] };
let browser;
try {
  browser = await chromium.connectOverCDP(endpoint, { timeout: 15_000 });
  result.browserVersion = browser.version();
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  const response = await page.goto('https://example.com', { waitUntil: 'domcontentloaded', timeout: 60_000 });
  result.status = response?.status() ?? null;
  result.title = await page.title();
  result.contentBytes = Buffer.byteLength(await page.content());
  const screenshotPath = path.join(outDir, 'cdp.png');
  await page.screenshot({ path: screenshotPath, fullPage: true });
  result.screenshotBytes = fs.statSync(screenshotPath).size;
} catch (err) {
  result.errors.push(err instanceof Error ? `${err.name}: ${err.message}` : String(err));
  process.exitCode = 1;
} finally {
  if (browser) await browser.close();
  console.log(JSON.stringify(result, null, 2));
}
