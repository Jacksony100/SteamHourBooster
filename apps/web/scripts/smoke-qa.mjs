import { existsSync } from "node:fs";
import { chromium } from "playwright-core";

const WEB_URL = process.env.QA_WEB_URL || "http://localhost:3000";
const API_URL = process.env.QA_API_URL || "http://localhost:8000";
const QA_USERNAME = process.env.QA_USERNAME || "demo";
const QA_PASSWORD = process.env.QA_PASSWORD || "demo-password-123";

const browserCandidates = [
  process.env.QA_BROWSER_PATH,
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
  `${process.env.LOCALAPPDATA || ""}\\Google\\Chrome\\Application\\chrome.exe`,
  "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
  "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  `${process.env.LOCALAPPDATA || ""}\\Microsoft\\Edge\\Application\\msedge.exe`
].filter(Boolean);

function browserPath() {
  const match = browserCandidates.find((candidate) => existsSync(candidate));
  if (!match) {
    throw new Error("No system Chrome/Edge found. Set QA_BROWSER_PATH to a Chromium-compatible browser executable.");
  }
  return match;
}

async function waitFor(url, label) {
  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {}
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  throw new Error(`${label} is not reachable at ${url}`);
}

function createReporter() {
  const results = [];
  const issues = [];
  return {
    assert(name, condition, extra = "") {
      results.push({ name, ok: Boolean(condition), extra });
      if (!condition) issues.push(`${name}: ${extra}`);
    },
    done() {
      console.log(JSON.stringify({ results, issues }, null, 2));
      if (issues.length) process.exitCode = 2;
    }
  };
}

async function bodyText(page) {
  return page.locator("body").innerText();
}

await waitFor(WEB_URL, "web");
await waitFor(`${API_URL}/health`, "api");

const qa = createReporter();
const browser = await chromium.launch({ executablePath: browserPath(), headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 950 }, locale: "en-US" });
const page = await context.newPage();
const consoleErrors = [];
const pageErrors = [];
const httpErrors = [];

page.on("console", (message) => {
  if (["error", "warning"].includes(message.type())) consoleErrors.push(`${message.type()}: ${message.text()}`);
});
page.on("pageerror", (error) => pageErrors.push(error.message));
page.on("response", (response) => {
  if (response.status() >= 400) httpErrors.push(`${response.status()} ${response.url()}`);
});

await page.goto(WEB_URL, { waitUntil: "networkidle" });
await page.evaluate(() => localStorage.clear());
await page.reload({ waitUntil: "networkidle" });

let text = await bodyText(page);
qa.assert("landing renders DeckPilot", text.includes("DeckPilot"));
qa.assert("landing has CTA", await page.locator('a[href="/register"]').first().isVisible());

await page.getByRole("button", { name: /Light/i }).click();
qa.assert("light theme applies", await page.evaluate(() => document.documentElement.classList.contains("light")));
await page.getByRole("button", { name: /Full dark/i }).click();
qa.assert("full dark theme applies", await page.evaluate(() => document.documentElement.classList.contains("full-dark")));
await page.getByRole("button", { name: /^Dark$/i }).click();
qa.assert("dark theme applies", await page.evaluate(() => document.documentElement.classList.contains("dark")));

const langSelect = page.locator("select").first();
for (const [code, expectedLang] of [
  ["en", "en"],
  ["ru", "ru"],
  ["de", "de"],
  ["zh", "zh-CN"]
]) {
  await langSelect.selectOption(code);
  await page.waitForTimeout(150);
  const state = await page.evaluate(() => ({
    htmlLang: document.documentElement.lang,
    stored: localStorage.getItem("deckpilot-language"),
    value: document.querySelector("select")?.value
  }));
  qa.assert(`language ${code} applies`, state.htmlLang === expectedLang && state.stored === code && state.value === code, JSON.stringify(state));
}

const anonymousContext = await browser.newContext({ viewport: { width: 1280, height: 900 }, locale: "en-US" });
const anonymousPage = await anonymousContext.newPage();
await anonymousPage.goto(`${WEB_URL}/dashboard`, { waitUntil: "networkidle" });
qa.assert("anonymous dashboard redirects to login", anonymousPage.url().includes("/login"), anonymousPage.url());
await anonymousContext.close();

await langSelect.selectOption("en");
await page.goto(`${WEB_URL}/login`, { waitUntil: "networkidle" });
await page.locator('input[autocomplete="username"]').fill(QA_USERNAME);
await page.locator('input[autocomplete="current-password"]').fill(QA_PASSWORD);
await page.locator('button[type="submit"]').click();
await page.waitForURL("**/dashboard", { timeout: 15_000 }).catch(() => {});
await page.locator("aside").waitFor({ timeout: 10_000 });
await page.waitForTimeout(1500);
text = await bodyText(page);
qa.assert("login redirects to dashboard", page.url().includes("/dashboard"), page.url());
qa.assert("dashboard shell renders", await page.locator("aside").count() > 0);
qa.assert("dashboard data loads", !text.includes("ACCOUNTS\n-"), text.slice(0, 300));
qa.assert("non-admin nav hides Admin", (await page.locator('aside a[href="/admin"]').count()) === 0);

await page.goto(`${WEB_URL}/billing`, { waitUntil: "networkidle" });
text = await bodyText(page);
qa.assert("billing page shows current plan", text.includes("Current plan"), text.slice(0, 300));
qa.assert("billing pricing cards render", text.includes("Pricing"), text.slice(0, 300));

await page.goto(`${WEB_URL}/settings`, { waitUntil: "networkidle" });
text = await bodyText(page);
qa.assert("settings security controls render", text.includes("Account security"), text.slice(0, 300));
qa.assert("settings active sessions render", text.includes("Active sessions"), text.slice(0, 300));

await page.goto(`${WEB_URL}/admin`, { waitUntil: "networkidle" });
qa.assert("non-admin admin route redirects away", page.url().includes("/dashboard"), page.url());

await page.setViewportSize({ width: 390, height: 844 });
await page.goto(`${WEB_URL}/dashboard`, { waitUntil: "networkidle" });
const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 2);
qa.assert("mobile app has no horizontal overflow", !overflow);

qa.assert("no page errors", pageErrors.length === 0, pageErrors.join("\n"));
qa.assert("no relevant HTTP 4xx/5xx", httpErrors.filter((item) => !item.includes("/favicon.ico")).length === 0, httpErrors.join("\n"));
qa.assert("no console errors/warnings", consoleErrors.filter((item) => !item.includes("Download the React DevTools")).length === 0, consoleErrors.join("\n"));

await browser.close();
qa.done();
