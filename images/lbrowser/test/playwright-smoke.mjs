import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright-core';

const executablePath = process.env.LBROWSER_EXECUTABLE || '/opt/apps/lbrowser/lbrowser';
const outDir = process.env.OUT_DIR || '/tmp/lbrowser-smoke';
fs.mkdirSync(outDir, { recursive: true });

const result = {
  engine: `playwright-core ${JSON.parse(fs.readFileSync(new URL('../node_modules/playwright-core/package.json', import.meta.url))).version}`,
  executablePath,
  browserVersion: null,
  status: null,
  title: null,
  contentBytes: null,
  screenshotBytes: null,
  pdfBytes: null,
  pdfSupported: null,
  errors: [],
};

let browser;
try {
  browser = await chromium.launch({
    executablePath,
    headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  });
  result.browserVersion = browser.version();

  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  const response = await page.goto('https://example.com', {
    waitUntil: 'domcontentloaded',
    timeout: 60_000,
  });
  result.status = response?.status() ?? null;
  result.title = await page.title();

  const content = await page.content();
  result.contentBytes = Buffer.byteLength(content);
  if (!content.includes('Example Domain')) {
    throw new Error('page content did not contain "Example Domain"');
  }

  const screenshotPath = path.join(outDir, 'playwright.png');
  await page.screenshot({ path: screenshotPath, fullPage: true });
  result.screenshotBytes = fs.statSync(screenshotPath).size;
  if (result.screenshotBytes < 1000) throw new Error('screenshot is suspiciously small');

  try {
    const pdfPath = path.join(outDir, 'playwright.pdf');
    await page.pdf({ path: pdfPath, format: 'A4' });
    result.pdfBytes = fs.statSync(pdfPath).size;
    const magic = fs.readFileSync(pdfPath).subarray(0, 5).toString('ascii');
    if (magic !== '%PDF-') throw new Error(`bad PDF magic: ${JSON.stringify(magic)}`);
    result.pdfSupported = true;
  } catch (err) {
    result.pdfSupported = false;
    result.errors.push(`pdf: ${err instanceof Error ? err.message : String(err)}`);
  }
} catch (err) {
  result.errors.push(err instanceof Error ? `${err.name}: ${err.message}` : String(err));
  process.exitCode = 1;
} finally {
  if (browser) await browser.close();
  console.log(JSON.stringify(result, null, 2));
}
