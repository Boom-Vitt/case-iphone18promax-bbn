import http from 'node:http';
import { isIP } from 'node:net';
import { DatabaseSync } from 'node:sqlite';
import { randomBytes, scryptSync, timingSafeEqual, createHash } from 'node:crypto';
import { mkdirSync, readFileSync, writeFileSync, unlinkSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const MAX_FILE = 8 * 1024 * 1024;
export const products = [
  ['cognac', 'Cognac', 'หนังเรียบสีน้ำตาลคอนญัก', 'classic', 'tl', '#9d5129'],
  ['midnight', 'Midnight', 'หนังลายเกรนสีดำ', 'classic', 'tr', '#272625'],
  ['forest', 'Forest', 'หนังเรียบสีเขียวเข้ม', 'classic', 'bl', '#3b4b3c'],
  ['taupe', 'Taupe', 'หนังสีเทาเบจ ตะเข็บครีม', 'classic', 'br', '#b5a48c'],
  ['burgundy', 'Burgundy Emboss', 'หนังปั๊มลายสีเบอร์กันดี', 'texture', 'tl', '#6c262f'],
  ['weave', 'Chocolate Weave', 'หนังสานสีน้ำตาลช็อกโกแลต', 'texture', 'tr', '#63432d'],
  ['navy', 'Navy Crosshatch', 'หนังลายเส้นไขว้สีน้ำเงิน', 'texture', 'bl', '#2d4055'],
  ['quilt', 'Caramel Quilt', 'หนังบุนุ่มลายข้าวหลามตัด', 'texture', 'br', '#bd743a'],
  ['cardholder', 'Cardholder', 'เคสหนังพร้อมช่องใส่บัตร', 'everyday', 'tl', '#9f603c'],
  ['folio', 'Folio', 'เคสหนังฝาพับสีแซนด์', 'everyday', 'tr', '#c9b18e'],
  ['crossbody', 'Crossbody', 'เคสหนังพร้อมสายสะพาย', 'everyday', 'bl', '#70724d'],
  ['kickstand', 'Kickstand', 'เคสหนังพร้อมขาตั้ง', 'everyday', 'br', '#5d3b2b'],
].map(([id, name, description, collection, position, color]) => ({ id, name, description, collection, position, color }));
const hash = value => createHash('sha256').update(value).digest('hex');
const fail = (status, message) => { throw Object.assign(new Error(message), { status }); };
const text = (value, label, min, max) => {
  if (typeof value !== 'string' || value.trim().length < min || value.trim().length > max || /[\x00-\x08\x0B\x0C\x0E-\x1F]/.test(value)) fail(400, `${label}ไม่ถูกต้อง`);
  return value.trim();
};
const integer = (n, min, max, label) => {
  if (!Number.isInteger(n) || n < min || n > max) fail(400, `${label}ไม่ถูกต้อง`);
  return n;
};
export function fileType(bytes, name) {
  const ext = name.toLowerCase().split('.').pop();
  if (['png'].includes(ext) && bytes.subarray(0, 8).equals(Buffer.from('89504e470d0a1a0a', 'hex'))) return 'image/png';
  if (['jpg', 'jpeg'].includes(ext) && bytes[0] === 255 && bytes[1] === 216 && bytes[2] === 255) return 'image/jpeg';
  if (ext === 'pdf' && bytes.subarray(0, 5).toString() === '%PDF-') return 'application/pdf';
  fail(400, 'รองรับเฉพาะไฟล์ JPG, PNG หรือ PDF ที่ถูกต้อง');
}

export function clientIp(req, trustProxy) {
  const remote = req.socket.remoteAddress;
  if (trustProxy === 'loopback' && ['127.0.0.1', '::1', '::ffff:127.0.0.1'].includes(remote)) {
    const forwarded = req.headers['x-forwarded-for']?.split(',').at(-1).trim();
    if (forwarded && isIP(forwarded)) return forwarded;
  }
  return remote;
}

export function createApp(options = {}) {
  const config = { dataDir: process.env.DATA_DIR || './data', username: process.env.ADMIN_USERNAME, password: process.env.ADMIN_PASSWORD,
    origin: process.env.PUBLIC_ORIGIN || 'http://localhost:3018', secure: process.env.COOKIE_SECURE === 'true',
    trustProxy: process.env.TRUST_PROXY || '', googleUrl: process.env.GOOGLE_SCRIPT_URL || '', googleSecret: process.env.GOOGLE_SYNC_SECRET || '', sheetUrl: process.env.GOOGLE_SHEET_URL || '', ...options };
  if (!['', 'loopback'].includes(config.trustProxy)) throw new Error('TRUST_PROXY must be empty or loopback');
  if (!config.username || !config.password) throw new Error('Set ADMIN_USERNAME and ADMIN_PASSWORD in .env');
  if (!/^https?:\/\//.test(config.origin) || new URL(config.origin).origin !== config.origin) throw new Error('PUBLIC_ORIGIN must be an exact origin without trailing slash');
  if (new URL(config.origin).protocol === 'https:' && !config.secure) throw new Error('HTTPS requires COOKIE_SECURE=true');
  const dir = resolve(config.dataDir);
  mkdirSync(resolve(dir, 'slips'), { recursive: true, mode: 0o700 });
  const db = new DatabaseSync(resolve(dir, 'store.sqlite'));
  db.exec(`PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;
    CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY CHECK(id=1), value TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS sessions (token TEXT PRIMARY KEY, expires INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS orders (
      id TEXT PRIMARY KEY, lookup TEXT NOT NULL, created TEXT NOT NULL, product TEXT NOT NULL, model TEXT NOT NULL,
      quantity INTEGER NOT NULL, unit_price INTEGER NOT NULL, shipping INTEGER NOT NULL, total INTEGER NOT NULL,
      name TEXT NOT NULL, phone TEXT NOT NULL, address TEXT NOT NULL, postal TEXT NOT NULL,
      status TEXT NOT NULL, note TEXT NOT NULL DEFAULT '', slip_path TEXT NOT NULL, slip_type TEXT NOT NULL,
      slip_hash TEXT NOT NULL UNIQUE, updated TEXT NOT NULL, reviewed_by TEXT NOT NULL DEFAULT '',
      revision INTEGER NOT NULL DEFAULT 1, synced_revision INTEGER NOT NULL DEFAULT 0,
      drive_url TEXT NOT NULL DEFAULT '');
    CREATE INDEX IF NOT EXISTS orders_created ON orders(created);`);
  const initial = { price: 1090, shipping: 0, promptpay: '0899999999', recipient: '', shippingNote: '', contact: '', open: false };
  db.prepare('INSERT OR IGNORE INTO settings VALUES (1, ?)').run(JSON.stringify(initial));
  const settings = () => JSON.parse(db.prepare('SELECT value FROM settings WHERE id=1').get().value);
  const salt = randomBytes(32), passwordHash = scryptSync(config.password, salt, 64);
  const buckets = new Map();
  let syncing = false;
  const googleReady = Boolean(config.googleUrl && config.googleSecret);
  // ponytail: a single SQLite process and one sync worker; move to a shared database before multi-instance deployment.
  async function syncOrders() {
    if (syncing || !googleReady) return;
    syncing = true;
    try {
      const rows = db.prepare('SELECT * FROM orders WHERE synced_revision < revision ORDER BY created LIMIT 20').all();
      for (const order of rows) {
        try {
          const slip = order.drive_url ? null : { base64: readFileSync(resolve(dir, 'slips', order.slip_path)).toString('base64'), type: order.slip_type };
          const { lookup, slip_path, slip_hash, ...safeOrder } = order;
          const response = await fetch(config.googleUrl, { method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ secret: config.googleSecret, action: 'upsert', order: safeOrder, slip }), signal: AbortSignal.timeout(25000) });
          const result = await response.json();
          if (!response.ok || !result.ok) throw new Error('Sync rejected');
          db.prepare('UPDATE orders SET synced_revision=?, drive_url=? WHERE id=?').run(order.revision, result.driveUrl || order.drive_url, order.id);
        } catch { break; } // Preserve the pending revision for the next retry; never discard an order.
      }
    } finally { syncing = false; }
  }
  const timer = setInterval(() => { void syncOrders(); db.prepare('DELETE FROM sessions WHERE expires < ?').run(Date.now());
    for (const [key, entry] of buckets) if (entry.until < Date.now()) buckets.delete(key);
  }, 30000);
  timer.unref();
  const session = req => {
    const token = /(?:^|;\s*)bbn_session=([a-f0-9]{64})(?:;|$)/.exec(req.headers.cookie || '')?.[1];
    if (!token || !db.prepare('SELECT token FROM sessions WHERE token=? AND expires>?').get(hash(token), Date.now())) fail(401, 'กรุณาเข้าสู่ระบบ');
    return token;
  };
  function limit(req, route, count, seconds) {
    const key = `${route}:${clientIp(req, config.trustProxy)}`; // Forwarded IPs are accepted only from an explicitly trusted local proxy.
    let b = buckets.get(key);
    if (!b || b.until < Date.now()) { b = { count: 0, until: Date.now() + seconds * 1000 }; buckets.set(key, b); }
    if (++b.count > count) fail(429, 'ทำรายการถี่เกินไป กรุณารอสักครู่');
  }
  const cookie = (token, age = 28800) => `bbn_session=${token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=${age}${config.secure ? '; Secure' : ''}`;
  async function body(req, max = 16384) {
    if (Number(req.headers['content-length'] || 0) > max) fail(413, 'ไฟล์หรือข้อมูลมีขนาดใหญ่เกินไป');
    const chunks = []; let size = 0;
    for await (const chunk of req) { size += chunk.length; if (size > max) fail(413, 'ไฟล์หรือข้อมูลมีขนาดใหญ่เกินไป'); chunks.push(chunk); }
    return Buffer.concat(chunks);
  }
  async function jsonBody(req) {
    if (!req.headers['content-type']?.startsWith('application/json')) fail(415, 'รูปแบบข้อมูลไม่ถูกต้อง');
    try { const value = JSON.parse((await body(req)).toString()); if (!value || typeof value !== 'object' || Array.isArray(value)) fail(400, 'ข้อมูล JSON ต้องเป็น object'); return value; } catch (e) { if (e.status) throw e; fail(400, 'ข้อมูล JSON ไม่ถูกต้อง'); }
  }
  const server = http.createServer(async (req, res) => {
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('Referrer-Policy', 'same-origin');
    res.setHeader('X-Frame-Options', 'DENY');
    res.setHeader('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'");
    res.setHeader('Cache-Control', 'no-store');
    const send = (status, data) => { res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' }); res.end(JSON.stringify(data)); };
    try {
      const url = new URL(req.url, config.origin), route = url.pathname, method = req.method;
      if (route.startsWith('/api/')) limit(req, 'api', 180, 60);
      if (!['GET', 'HEAD'].includes(method) && (req.headers.origin !== config.origin || req.headers['x-requested-with'] !== 'BBN')) fail(403, 'คำขอไม่ได้มาจากหน้าร้านนี้');
      if (method === 'GET' && route === '/api/catalog') return send(200, { products, settings: settings() });
      if (method === 'POST' && route === '/api/login') {
        limit(req, 'login', 5, 300);
        const input = await jsonBody(req);
        const pass = text(input.password, 'รหัสผ่าน', 1, 256);
        if (!timingSafeEqual(scryptSync(pass, salt, 64), passwordHash) || input.username !== config.username) fail(401, 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง');
        const token = randomBytes(32).toString('hex');
        db.prepare('INSERT INTO sessions VALUES (?, ?)').run(hash(token), Date.now() + 8 * 3600000);
        res.setHeader('Set-Cookie', cookie(token)); return send(200, { ok: true });
      }
      if (method === 'POST' && route === '/api/logout') {
        const token = session(req); db.prepare('DELETE FROM sessions WHERE token=?').run(hash(token));
        res.setHeader('Set-Cookie', cookie('', 0)); return send(200, { ok: true });
      }
      if (method === 'POST' && route === '/api/orders') {
        limit(req, 'orders', 10, 3600);
        if (!req.headers['content-type']?.startsWith('multipart/form-data; boundary=')) fail(415, 'ส่งข้อมูลพร้อมสลิปให้ครบ');
        let form;
        try { form = await new Request(config.origin, { method: 'POST', headers: { 'Content-Type': req.headers['content-type'] }, body: await body(req, MAX_FILE + 32768) }).formData(); }
        catch (e) { if (e.status) throw e; fail(400, 'ข้อมูลอัปโหลดไม่ถูกต้อง'); }
        const s = settings(); if (!s.open) fail(409, 'ร้านยังไม่เปิดรับพรีออร์เดอร์');
        const product = text(form.get('product'), 'แบบเคส', 1, 30);
        if (!products.some(p => p.id === product)) fail(400, 'ไม่พบแบบเคสนี้');
        const model = form.get('model'); if (!['iPhone 18 Pro', 'iPhone 18 Pro Max'].includes(model)) fail(400, 'รุ่นโทรศัพท์ไม่ถูกต้อง');
        const quantity = integer(Number(form.get('quantity')), 1, 10, 'จำนวน');
        const name = text(form.get('name'), 'ชื่อผู้รับ', 2, 120);
        const phone = text(form.get('phone'), 'เบอร์โทร', 9, 16); if (!/^0\d{8,9}$/.test(phone.replace(/[- ]/g, ''))) fail(400, 'เบอร์โทรไม่ถูกต้อง');
        const address = text(form.get('address'), 'ที่อยู่', 10, 1000);
        const postal = text(form.get('postal'), 'รหัสไปรษณีย์', 5, 5); if (!/^\d{5}$/.test(postal)) fail(400, 'รหัสไปรษณีย์ไม่ถูกต้อง');
        if (form.get('consent') !== 'yes') fail(400, 'กรุณายอมรับเงื่อนไขพรีออร์เดอร์');
        if (Number(form.get('quotedTotal')) !== s.price * quantity + s.shipping) fail(409, 'ราคาเปลี่ยนแล้ว กรุณารีเฟรชและตรวจยอดก่อนโอน');
        const file = form.get('slip'); if (!file || typeof file.arrayBuffer !== 'function' || !file.size || file.size > MAX_FILE) fail(400, 'กรุณาแนบสลิปขนาดไม่เกิน 8 MB');
        const bytes = Buffer.from(await file.arrayBuffer()), type = fileType(bytes, file.name), digest = hash(bytes);
        if (db.prepare('SELECT id FROM orders WHERE slip_hash=?').get(digest)) fail(409, 'สลิปนี้ถูกใช้แล้ว กรุณาตรวจสถานะออเดอร์เดิมหรือติดต่อร้าน');
        const id = 'BBN-' + randomBytes(6).toString('hex').toUpperCase(), lookup = randomBytes(24).toString('hex');
        const filename = randomBytes(20).toString('hex'), now = new Date().toISOString();
        writeFileSync(resolve(dir, 'slips', filename), bytes, { mode: 0o600, flag: 'wx' });
        try {
          db.prepare(`INSERT INTO orders (id,lookup,created,product,model,quantity,unit_price,shipping,total,name,phone,address,postal,status,slip_path,slip_type,slip_hash,updated)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,'pending',?,?,?,?)`).run(id, hash(lookup), now, product, model, quantity, s.price, s.shipping, s.price * quantity + s.shipping, name, phone, address, postal, filename, type, digest, now);
        } catch (e) { unlinkSync(resolve(dir, 'slips', filename)); throw e; }
        void syncOrders(); return send(201, { id, token: lookup, total: s.price * quantity + s.shipping, status: 'pending' });
      }
      if (method === 'POST' && route === '/api/order-status') {
        limit(req, 'lookup', 30, 300);
        const input = await jsonBody(req);
        const id = text(input.id, 'เลขออเดอร์', 1, 40), token = text(input.token, 'รหัสติดตาม', 1, 100);
        const order = db.prepare('SELECT id,created,model,product,quantity,total,status,note FROM orders WHERE id=? AND lookup=?').get(id, hash(token));
        if (!order) fail(404, 'ไม่พบออเดอร์หรือรหัสติดตามไม่ถูกต้อง'); return send(200, order);
      }
      if (route.startsWith('/api/admin/')) {
        session(req);
        if (method === 'GET' && route === '/api/admin/dashboard') {
          const status = url.searchParams.get('status') || 'all';
          if (!['all', 'pending', 'approved', 'rejected'].includes(status)) fail(400, 'สถานะไม่ถูกต้อง');
          const page = integer(Number(url.searchParams.get('page') || 1), 1, 100000, 'หน้า');
          const orders = db.prepare(`SELECT id,created,product,model,quantity,total,name,phone,address,postal,status,note,updated,reviewed_by,revision,synced_revision,drive_url,slip_type FROM orders WHERE (?='all' OR status=?) ORDER BY created DESC LIMIT 50 OFFSET ?`).all(status, status, (page - 1) * 50);
          const count = db.prepare("SELECT count(*) AS count FROM orders WHERE (?='all' OR status=?)").get(status, status).count;
          const totals = db.prepare(`SELECT count(*) AS orders, coalesce(sum(quantity),0) AS units,
            coalesce(sum(CASE WHEN status='approved' THEN total ELSE 0 END),0) AS approvedRevenue,
            coalesce(sum(CASE WHEN status='pending' THEN 1 ELSE 0 END),0) AS pending,
            coalesce(sum(CASE WHEN revision>synced_revision THEN 1 ELSE 0 END),0) AS unsynced FROM orders`).get();
          const demand = db.prepare(`SELECT product,model,sum(quantity) AS units,sum(CASE WHEN status='approved' THEN quantity ELSE 0 END) AS approved FROM orders WHERE status!='rejected' GROUP BY product,model ORDER BY units DESC`).all();
          return send(200, { orders, count, page, totals, demand, settings: settings(), googleReady, sheetUrl: config.sheetUrl });
        }
        if (method === 'PUT' && route === '/api/admin/settings') {
          const input = await jsonBody(req);
          const next = { price: integer(input.price, 1, 100000, 'ราคา'), shipping: integer(input.shipping, 0, 10000, 'ค่าส่ง'),
            promptpay: text(input.promptpay, 'พร้อมเพย์', 10, 13), recipient: text(input.recipient, 'ชื่อผู้รับเงิน', 0, 120),
            shippingNote: text(input.shippingNote, 'กำหนดส่ง', 0, 500), contact: text(input.contact, 'ช่องทางติดต่อ', 0, 300), open: input.open === true };
          if (!/^(0\d{9}|\d{13})$/.test(next.promptpay)) fail(400, 'พร้อมเพย์ต้องเป็นเบอร์ 10 หลักหรือเลขประจำตัว 13 หลัก');
          if (next.open && (!next.recipient || !next.shippingNote || !next.contact)) fail(400, 'กรอกชื่อบัญชี กำหนดส่ง และช่องทางติดต่อก่อนเปิดร้าน');
          db.prepare('UPDATE settings SET value=? WHERE id=1').run(JSON.stringify(next)); return send(200, next);
        }
        const review = /^\/api\/admin\/orders\/(BBN-[A-F0-9]{12})$/.exec(route);
        if (method === 'PATCH' && review) {
          const input = await jsonBody(req);
          if (!['pending', 'approved', 'rejected'].includes(input.status)) fail(400, 'สถานะไม่ถูกต้อง');
          const note = text(input.note ?? '', 'หมายเหตุ', 0, 500);
          if (input.status === 'rejected' && !note) fail(400, 'กรุณาระบุเหตุผลที่ไม่อนุมัติ');
          const result = db.prepare('UPDATE orders SET status=?,note=?,updated=?,reviewed_by=?,revision=revision+1 WHERE id=? AND revision=?').run(input.status, note, new Date().toISOString(), config.username, review[1], integer(input.revision, 1, 1000000, 'เวอร์ชัน'));
          if (!result.changes) fail(409, 'ออเดอร์ถูกแก้ไขแล้ว กรุณาโหลดใหม่'); void syncOrders(); return send(200, { ok: true });
        }
        const slip = /^\/api\/admin\/slips\/(BBN-[A-F0-9]{12})$/.exec(route);
        if (method === 'GET' && slip) {
          const order = db.prepare('SELECT slip_path,slip_type FROM orders WHERE id=?').get(slip[1]); if (!order) fail(404, 'ไม่พบสลิป');
          res.setHeader('Content-Security-Policy', "sandbox; default-src 'none'");
          res.setHeader('Content-Type', order.slip_type);
          res.setHeader('Content-Disposition', `${order.slip_type === 'application/pdf' ? 'attachment' : 'inline'}; filename="${slip[1]}.${order.slip_type.split('/')[1]}"`);
          return res.end(readFileSync(resolve(dir, 'slips', order.slip_path)));
        }
        if (method === 'POST' && route === '/api/admin/sync') { await syncOrders(); return send(200, { ok: true, connected: googleReady }); }
      }
      if (['GET', 'HEAD'].includes(method)) {
        const files = { '/': 'index.html', '/admin': 'admin.html', '/app.js': 'app.js', '/admin.js': 'admin.js', '/style.css': 'style.css', '/favicon.svg': 'favicon.svg', '/assets/classic.png': 'assets/classic.png', '/assets/texture.png': 'assets/texture.png', '/assets/everyday.png': 'assets/everyday.png' };
        const filename = files[route]; if (!filename) fail(404, 'ไม่พบหน้านี้');
        const types = { html: 'text/html; charset=utf-8', js: 'text/javascript; charset=utf-8', css: 'text/css; charset=utf-8', svg: 'image/svg+xml', png: 'image/png' };
        res.setHeader('Content-Type', types[filename.split('.').pop()]);
        return res.end(method === 'HEAD' ? undefined : readFileSync(resolve(ROOT, 'public', filename)));
      }
      fail(404, 'ไม่พบรายการ');
    } catch (error) { if (!res.headersSent) send(error.status || 500, { error: error.status ? error.message : 'เกิดข้อผิดพลาด กรุณาลองใหม่' }); else res.end(); }
  });
  server.requestTimeout = 30000;
  server.headersTimeout = 10000;
  server.on('close', () => { clearInterval(timer); db.close(); });
  return { server, db, syncOrders, isSyncing: () => syncing };
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const app = createApp();
  app.server.listen(Number(process.env.PORT || 3018), process.env.HOST || '127.0.0.1', () => console.log(`BBN Case ready at ${process.env.PUBLIC_ORIGIN || 'http://localhost:3018'}`));
}
