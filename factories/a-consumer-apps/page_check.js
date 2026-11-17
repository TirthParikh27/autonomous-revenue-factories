#!/usr/bin/env node
/* Open a test page the way a phone visitor would, walk its funnel, and save what it looked like.

   node page_check.js demand/<id>/site [out dir, default demand/<id>/check]

   The page reads its settings from window.LAUNCH (see demand/config.js). This script supplies fake
   settings, blocks every real network call, then uses each element marked data-walk="1", "2", ...
   in order: it fills inputs, ticks boxes and clicks the rest. It prints the events the page sent,
   whether a sign-up was posted, anything the page tried to load from outside, and the screenshots
   to look at. Nothing leaves the machine. Needs Playwright (see README, "Set up once"). */
const path = require("path");
const fs = require("fs");
const { chromium } = require("playwright");

const FAKE = "https://check.invalid";

(async () => {
  const site = path.resolve(process.argv[2] || "");
  const index = path.join(site, "index.html");
  if (!fs.existsSync(index)) { console.error(`no index.html in ${site}`); process.exit(2); }
  const out = path.resolve(process.argv[3] || path.join(site, "..", "check"));
  fs.mkdirSync(out, { recursive: true });

  const report = { page: index, events: [], signup_posted: false, external_requests: [], console_errors: [], steps: [], screenshots: [] };
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
  await page.addInitScript((fake) => {
    window.LAUNCH = { pixelId: "", signupEndpoint: fake + "/signup", signupKey: "check", eventEndpoint: fake + "/event" };
  }, FAKE);
  await page.route(/^https?:/, (route) => {
    const req = route.request();
    const url = req.url();
    if (url.startsWith(FAKE + "/event")) {
      try { report.events.push(JSON.parse(req.postData() || "{}").event || "(unnamed)"); } catch { report.events.push("(unreadable)"); }
      return route.fulfill({ status: 204, body: "" });
    }
    if (url.startsWith(FAKE + "/signup")) {
      report.signup_posted = true;
      return route.fulfill({ status: 200, contentType: "application/json", body: "{}" });
    }
    report.external_requests.push(url);
    return route.abort();
  });
  page.on("console", (m) => { if (m.type() === "error" && !/net::ERR_(FAILED|FILE_NOT_FOUND)/.test(m.text())) report.console_errors.push(m.text()); });
  page.on("pageerror", (e) => report.console_errors.push(String(e)));

  const shot = async (name, fullPage = false) => {
    const file = path.join(out, name);
    await page.screenshot({ path: file, fullPage });
    report.screenshots.push(file);
  };

  await page.goto("file://" + index);
  await page.waitForTimeout(400);
  report.sideways_scroll = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
  await shot("first-screen.png");
  await shot("full-page.png", true);

  const marks = await page.$$eval("[data-walk]", (els) => [...new Set(els.map((e) => e.getAttribute("data-walk")))]);
  marks.sort((a, b) => Number(a) - Number(b));
  let failed = false;
  for (const mark of marks) {
    const el = page.locator(`[data-walk="${mark}"]`).first();
    const kind = await el.evaluate((e) => (e.tagName + ":" + (e.type || "")).toLowerCase());
    try {
      if (kind.startsWith("input:email")) await el.fill("check@example.com", { timeout: 3000 });
      else if (kind.startsWith("input:checkbox") || kind.startsWith("input:radio")) await el.check({ timeout: 3000 });
      else if (kind.startsWith("input:") || kind.startsWith("textarea")) await el.fill("check", { timeout: 3000 });
      else if (kind.startsWith("select")) await el.selectOption({ index: 1 }, { timeout: 3000 });
      else await el.click({ timeout: 3000 });
      await page.waitForTimeout(300);
      report.steps.push({ step: mark, element: kind, ok: true });
    } catch (e) {
      failed = true;
      report.steps.push({ step: mark, element: kind, ok: false, error: String(e).split("\n")[0] });
    }
    await shot(`step-${mark}.png`);
  }
  await browser.close();
  console.log(JSON.stringify(report, null, 2));
  process.exit(failed ? 1 : 0);
})().catch((e) => { console.error(String(e)); process.exit(2); });
