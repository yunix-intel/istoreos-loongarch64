import { chromium } from 'playwright-core';

const executablePath = process.env.LBROWSER_EXECUTABLE || '/opt/apps/lbrowser/lbrowser';
const browser = await chromium.launch({
  executablePath,
  headless: true,
  args: ['--no-sandbox', '--disable-dev-shm-usage'],
});
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
const response = await page.goto('https://example.com', { waitUntil: 'domcontentloaded', timeout: 30000 });
const content = await page.content();
const screenshot = await page.screenshot({ type: 'png' });
let pdf = Buffer.alloc(0);
let pdfError = null;
try {
  pdf = await page.pdf({ format: 'A4' });
} catch (e) {
  pdfError = String(e);
}
const version = browser.version();
const title = await page.title();
await browser.close();
const result = {
  browserVersion: version,
  status: response?.status(),
  title,
  contentBytes: content.length,
  screenshotBytes: screenshot.length,
  pdfBytes: pdf.length,
  pdfMagic: pdf.subarray(0, 5).toString(),
  pdfError,
};
console.log(JSON.stringify(result, null, 2));
if (result.status !== 200 || result.contentBytes < 100 || result.screenshotBytes < 1000) process.exit(1);
if (!pdfError && result.pdfMagic !== '%PDF-') process.exit(1);
