#!/usr/bin/env node
/* Open a test page the way a phone visitor would, walk its funnel, and save what it looked like.

   node page_check.js demand/sites/<id> demand/<id>/check

   The page reads its settings from window.LAUNCH (see demand/sites/config.js). This script supplies fake
   settings, blocks every real network call, then uses each element marked data-walk="1", "2", ...
   in order: it fills inputs, ticks boxes and clicks the rest. It prints the events the page sent,
   whether a sign-up was posted, anything the page tried to load from outside, and the screenshots
   to look at. It exits 1 if a step could not be used, no sign-up or event was sent, a script failed
   or the page scrolls sideways. Nothing leaves the machine. Needs Playwright (see README, "Set up once"). */
const path = require("path");
const fs = require("fs");
const { chromium } = require("playwright");

const FAKE = "https://check.invalid";

(async () => {
  const site = path.resolve(process.argv[2] || "");
  const index = path.join(site, "index.html");
  if (!fs.existsSync(index)) { console.error(`no index.html in ${site}`); process.exit(2); }
  if (!process.argv[3]) { console.error("give an output folder outside the public sites folder"); process.exit(2); }
  const out = path.resolve(process.argv[3]);
  fs.mkdirSync(out, { recursive: true });

  const report = { page: index, events: [], signup_posted: false, external_requests: [], console_errors: [], steps: [], screenshots: [] };
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
  await page.addInitScript((fake) => {
    window.LAUNCH = { pixelId: "", signupEndpoint: fake + "/signup", signupKey: "check", eventEndpoint: fake + "/event", eventKey: "check" };
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
  const sideways = () => page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);
  report.sideways_scroll = await sideways();
  await shot("first-screen.png");
  await shot("full-page.png", true);

  // Walk the marks in order, looking again after every step, because a step can reveal the next one.
  const done = new Set();
  let failed = false;
  for (let guard = 0; guard < 40; guard++) {
    const marks = await page.$$eval("[data-walk]", (els) => [...new Set(els.map((e) => e.getAttribute("data-walk")))]);
    const mark = marks.filter((m) => !done.has(m)).sort((x, y) => Number(x) - Number(y))[0];
    if (mark === undefined) break;
    done.add(mark);
    const el = page.locator(`[data-walk="${mark}"]`).first();
    let kind = "?";
    try {
      kind = await el.evaluate((e) => (e.tagName + ":" + (e.type || "")).toLowerCase(), null, { timeout: 3000 });
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
  report.sideways_scroll = report.sideways_scroll || (await sideways().catch(() => false));
  // The page passes only if a visitor could get all the way through and it behaved.
  report.problems = [];
  if (failed) report.problems.push("a funnel step could not be used");
  if (!report.steps.length) report.problems.push("no data-walk steps on the page");
  if (!report.signup_posted) report.problems.push("no sign-up was posted");
  if (!report.events.includes("committed_signup")) report.problems.push("no committed_signup event was sent");
  if (report.console_errors.length) report.problems.push("script errors on the page");
  if (report.sideways_scroll) report.problems.push("the page scrolls sideways on a phone");
  await browser.close();
  console.log(JSON.stringify(report, null, 2));
  process.exit(report.problems.length ? 1 : 0);
})().catch((e) => { console.error(String(e)); process.exit(2); });
