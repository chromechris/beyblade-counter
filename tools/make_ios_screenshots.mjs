// App Store screenshots of the web app at iPhone 6.9" size (1320 x 2868 = 440 x 956 points @3x).
//
//     node tools/make_ios_screenshots.mjs      ->  store/screenshots-ios/*.png
//
// Serves web/ itself on a free localhost port, starts its own headless Chrome (separate
// temporary profile, stopped by its own PID at the end) and drives the page over the
// DevTools protocol. Needs Node 22+ (built-in WebSocket) and Chrome or Edge installed.
import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync, existsSync, statSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const OUT = join(ROOT, 'store', 'screenshots-ios');
const W = 440, H = 956, SCALE = 3;
const BROWSERS = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/usr/bin/google-chrome',
];
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.webmanifest': 'application/manifest+json' };
const sleep = ms => new Promise(r => setTimeout(r, ms));

// ------------------------------------------------------------------ static server
const server = createServer((req, res) => {
  const path = normalize(decodeURIComponent(new URL(req.url, 'http://x').pathname)).replace(/^([/\\])+/, '');
  let file = join(ROOT, path);
  if (existsSync(file) && statSync(file).isDirectory()) file = join(file, 'index.html');
  if (!file.startsWith(ROOT) || !existsSync(file)) { res.writeHead(404).end(); return; }
  res.writeHead(200, { 'Content-Type': MIME[extname(file)] || 'application/octet-stream' }).end(readFileSync(file));
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const base = `http://127.0.0.1:${server.address().port}/web/index.html`;

// ------------------------------------------------------------------ browser
const exe = BROWSERS.find(p => existsSync(p));
if (!exe) throw new Error('Chrome or Edge not found');
const profile = mkdtempSync(join(tmpdir(), 'spin-shots-'));
const port = 9300 + Math.floor(Math.random() * 500);
const chrome = spawn(exe, ['--headless=new', `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--hide-scrollbars', '--disable-extensions', 'about:blank'], { stdio: 'ignore' });

let ws, nextId = 1;
const pending = new Map();
function send(method, params = {}) {
  const id = nextId++;
  ws.send(JSON.stringify({ id, method, params }));
  return new Promise((resolve, reject) => pending.set(id, { resolve, reject }));
}
async function js(expr) {
  const r = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.text + ' ' + (r.exceptionDetails.exception?.description || ''));
  return r.result.value;
}
async function shot(name) {
  await js(`Promise.all([...document.images].filter(i => !i.complete).map(i => new Promise(r => { i.onload = i.onerror = r; setTimeout(r, 4000); })))`);
  await sleep(600);
  const { data } = await send('Page.captureScreenshot', { format: 'png' });
  writeFileSync(join(OUT, name), Buffer.from(data, 'base64'));
  console.log('saved', name);
}

try {
  let target;
  for (let i = 0; i < 50 && !target; i++) {
    await sleep(200);
    try { target = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(t => t.type === 'page'); } catch { /* not up yet */ }
  }
  if (!target) throw new Error('browser did not start');
  ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
  ws.onmessage = e => {
    const m = JSON.parse(e.data);
    if (m.id && pending.has(m.id)) { const p = pending.get(m.id); pending.delete(m.id); m.error ? p.reject(new Error(m.error.message)) : p.resolve(m.result); }
  };

  mkdirSync(OUT, { recursive: true });
  await send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: SCALE, mobile: true });
  await send('Emulation.setTouchEmulationEnabled', { enabled: true });
  await send('Page.enable');
  await send('Page.navigate', { url: base });
  await js(`new Promise(r => { const t = setInterval(() => { if (/subject files/.test(document.querySelector('#tagline')?.textContent || '')) { clearInterval(t); r(); } }, 100); })`);

  // helpers inside the page: search a box and pick the first hit, as a user would
  await js(`window.__pick = (inputSel, text) => new Promise(r => {
      const i = document.querySelector(inputSel); i.focus(); i.value = text;
      i.dispatchEvent(new Event('input', { bubbles: true }));
      setTimeout(() => { const d = i.parentElement.querySelector('.drop-item');
        d.dispatchEvent(new MouseEvent('mousedown', { bubbles: true })); setTimeout(r, 300); }, 200); });
    window.__tab = name => document.querySelector('.tab[data-tab="' + name + '"]').click();
    window.__top = () => window.scrollTo(0, 0);
    window.__to = (sel, off = 0) => { const e = document.querySelector(sel); window.scrollTo(0, e.getBoundingClientRect().top + window.scrollY - off); };`);

  // 1. Target analysis: the subject file
  await js(`__pick('#oppSearch', 'DranBuster 1-60A').then(() => __top())`);
  await shot('01-target-analysis.png');
  // 2. Recommended assets with the assessment
  await js(`__to('.results-col h2', 150)`);
  await shot('02-recommended-assets.png');
  // 3. My arsenal with a few owned models
  for (const m of ['WizardRod 5-70DB', 'PhoenixWing 9-60GF', 'KnightShield 3-80N', 'HellsScythe 4-60T']) {
    await js(`(__tab('collection'), __pick('#colSearch', ${JSON.stringify(m)}))`);
  }
  await js(`__top()`);
  await shot('03-my-arsenal.png');
  // 4. Dossiers list
  await js(`(__tab('browse'), __top())`);
  await shot('04-dossiers.png');
  // 5. One full dossier
  await js(`(document.querySelector('#browseSearch').value = 'WizardRod 5-70DB', document.querySelector('#browseSearch').dispatchEvent(new Event('input')), document.querySelector('#browseCards .card').click())`);
  await shot('05-dossier-detail.png');
} finally {
  try { ws?.close(); } catch { /* ignore */ }
  chrome.kill();
  server.close();
  await sleep(500);
  try { rmSync(profile, { recursive: true, force: true }); } catch { /* Chrome may still hold files */ }
}
