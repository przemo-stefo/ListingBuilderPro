// deploy/anna130/messenger-bot/server.js
// Purpose: HTTP API that sends Facebook Messenger messages via Puppeteer
// NOT for: Receiving messages, running permanently — Chrome launches only per-request

const express = require('express');
const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(express.json());

const COOKIES_PATH = path.join(__dirname, 'data', 'fb-cookies.json');
const PORT = process.env.PORT || 3111;

// Track if a send is in progress (only one Chrome instance at a time)
let sending = false;

function loadCookies() {
  if (!fs.existsSync(COOKIES_PATH)) return null;
  try {
    return JSON.parse(fs.readFileSync(COOKIES_PATH, 'utf8'));
  } catch {
    return null;
  }
}

function saveCookies(cookies) {
  const dir = path.dirname(COOKIES_PATH);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(COOKIES_PATH, JSON.stringify(cookies, null, 2));
}

async function launchBrowser() {
  return puppeteer.launch({
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu',
      '--single-process',
      '--disable-extensions',
      '--disable-background-networking',
      '--disable-default-apps',
      '--disable-sync',
      '--disable-translate',
      '--no-first-run',
      '--disable-features=site-per-process',
      '--js-flags=--max-old-space-size=128'
    ]
  });
}

// Send a message to a specific FB user via Messenger
async function sendMessage(recipientId, text) {
  const cookies = loadCookies();
  if (!cookies || cookies.length === 0) {
    throw new Error('No cookies found. Upload cookies first via POST /cookies');
  }

  const browser = await launchBrowser();
  try {
    const page = await browser.newPage();

    // Minimal viewport to save memory
    await page.setViewport({ width: 800, height: 600 });

    // Set cookies before navigating
    await page.setCookie(...cookies);

    // Navigate to Messenger conversation with recipient
    const messengerUrl = `https://www.messenger.com/t/${recipientId}`;
    await page.goto(messengerUrl, { waitUntil: 'networkidle2', timeout: 30000 });

    // Check if logged in (look for message input)
    const loggedIn = await page.evaluate(() => {
      return !!document.querySelector('[role="textbox"]') ||
             !!document.querySelector('[contenteditable="true"]');
    });

    if (!loggedIn) {
      // Try alternative: check if redirected to login
      const url = page.url();
      if (url.includes('login') || url.includes('checkpoint')) {
        throw new Error('Cookies expired — need fresh login. Upload new cookies via POST /cookies');
      }
      // Wait a bit more for slow load
      await page.waitForSelector('[role="textbox"], [contenteditable="true"]', { timeout: 15000 });
    }

    // Find and click the message input
    const textbox = await page.$('[role="textbox"]') || await page.$('[contenteditable="true"]');
    if (!textbox) {
      throw new Error('Could not find message input box');
    }

    await textbox.click();

    // Type message in chunks (more human-like, avoids detection)
    // Split by newlines — Messenger uses Shift+Enter for newlines
    const lines = text.split('\n');
    for (let i = 0; i < lines.length; i++) {
      if (i > 0) {
        await page.keyboard.down('Shift');
        await page.keyboard.press('Enter');
        await page.keyboard.up('Shift');
      }
      if (lines[i].length > 0) {
        await page.keyboard.type(lines[i], { delay: 5 });
      }
    }

    // Small delay before sending
    await new Promise(r => setTimeout(r, 500));

    // Press Enter to send
    await page.keyboard.press('Enter');

    // Wait for message to appear in chat
    await new Promise(r => setTimeout(r, 2000));

    // Save refreshed cookies
    const freshCookies = await page.cookies();
    saveCookies(freshCookies);

    return { status: 'sent', recipientId, textLength: text.length };
  } finally {
    await browser.close();
  }
}

// Health check
app.get('/health', (req, res) => {
  const hasCookies = fs.existsSync(COOKIES_PATH);
  res.json({
    status: 'ok',
    cookies: hasCookies ? 'loaded' : 'missing',
    sending
  });
});

// Upload cookies (JSON array from browser)
app.post('/cookies', (req, res) => {
  const { cookies } = req.body;
  if (!Array.isArray(cookies) || cookies.length === 0) {
    return res.status(400).json({ error: 'Body must contain { cookies: [...] }' });
  }
  saveCookies(cookies);
  res.json({ status: 'saved', count: cookies.length });
});

// Send message
app.post('/send', async (req, res) => {
  const { recipientId, text } = req.body;

  if (!recipientId || !text) {
    return res.status(400).json({ error: 'Required: { recipientId, text }' });
  }

  if (sending) {
    return res.status(429).json({ error: 'Another message is being sent. Try again in 30s.' });
  }

  sending = true;
  try {
    const result = await sendMessage(recipientId, text);
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  } finally {
    sending = false;
  }
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Messenger bot listening on :${PORT}`);
  console.log(`Cookies: ${fs.existsSync(COOKIES_PATH) ? 'loaded' : 'MISSING — upload via POST /cookies'}`);
});
